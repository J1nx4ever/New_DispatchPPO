from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np

from .generated import dispatch_pb2
from .reward_config import RewardConfiguration, configuration_from_components
from .reward_contract import ADDITIVE_COMPONENTS
from .observation_contract import OBSERVATION_SCHEMA_ID, validate_observation
from .reward_contract import (
    REWARD_CONTRACT_ID,
    SHIFT_SECONDS,
    WINDOWS_PER_EPISODE,
    validate_reward_accounting,
    validate_window_summary,
    window_summary_to_dict,
)

SCHEMA_ID = OBSERVATION_SCHEMA_ID
ACTION_COUNT = 4


class ProtocolError(ValueError):
    """The AnyLogic callback violates the frozen dispatch protocol."""


@dataclass
class CallbackTicket:
    request: dispatch_pb2.DispatchRequest
    received_ns: int = field(default_factory=time.perf_counter_ns)
    response: Optional[dispatch_pb2.DispatchResponse] = None
    response_ready: threading.Event = field(default_factory=threading.Event)
    error: Optional[Exception] = None


def observation_array(request: dispatch_pb2.DispatchRequest) -> np.ndarray:
    if not request.HasField("obs"):
        raise ProtocolError("request.obs is required")
    try:
        return validate_observation(
            request.obs.schema_id, request.obs.values,
            terminal=request.kind == dispatch_pb2.EPISODE_END,
            truck_id=request.truck_id,
        )
    except ValueError as exc:
        raise ProtocolError(str(exc)) from exc



class DispatchCallbackBridge:
    """Thread-safe rendezvous between blocking gRPC handlers and Gymnasium."""

    def __init__(
        self,
        queue_capacity: int = 1,
        expected_episode_metadata: Optional[Sequence[tuple[int, int]]] = None,
        rollout_audit=None,
        window_grade_bounds: bool = True,
        reward_config: Optional[RewardConfiguration] = None,
        runtime_configuration: bool = False,
    ) -> None:
        self._incoming: queue.Queue[CallbackTicket] = queue.Queue(queue_capacity)
        self._lock = threading.Lock()
        self._tickets_by_request_id: dict[str, CallbackTicket] = {}
        self._request_bytes: dict[str, bytes] = {}
        self._last_sequence_by_episode: dict[str, int] = {}
        self._next_window_index_by_episode: dict[str, int] = {}
        self._metadata_by_episode: dict[str, tuple[int, int, str]] = {}
        self._seen_experiment_run_indices: set[int] = set()
        self._seen_experiment_seeds: set[int] = set()
        self._expected_episode_metadata = (
            tuple(expected_episode_metadata)
            if expected_episode_metadata is not None
            else None
        )
        self._started_episode_count = 0
        self._last_ticket_by_episode: dict[str, CallbackTicket] = {}
        self._closed = False
        self.rollout_audit = rollout_audit
        self.window_grade_bounds = window_grade_bounds
        self.runtime_configuration = runtime_configuration
        self.reward_config = reward_config if runtime_configuration else (reward_config or RewardConfiguration())
        self._configuration_ready = threading.Event()
        if self.reward_config is not None:
            self._configuration_ready.set()

    def submit_callback(
        self,
        request: dispatch_pb2.DispatchRequest,
        timeout: Optional[float] = None,
    ) -> dispatch_pb2.DispatchResponse:
        if self.rollout_audit is not None:
            self.rollout_audit.event("request_received", self._audit_info(request),
                                     action_required=bool(request.action_required))
        try:
            ticket = self._register(request)
        except Exception as exc:
            if self.rollout_audit is not None:
                self.rollout_audit.event("request_registration_rejected", self._audit_info(request),
                                         reason=str(exc), exception_type=type(exc).__name__)
            raise
        if self.rollout_audit is not None:
            self.rollout_audit.event("request_registration_accepted", self._audit_info(request),
                                     reason="request passed registration and was accepted")
        if self.rollout_audit is not None and request.action_required:
            self.rollout_audit.event("request_action_status", self._audit_info(request),
                                     waiting_for_action=not ticket.response_ready.is_set())
        if not request.action_required and not ticket.response_ready.is_set():
            self._set_response(
                ticket,
                dispatch_pb2.DispatchResponse(
                    has_action=False,
                    episode_id=request.episode_id,
                    decision_sequence=request.decision_sequence,
                ),
            )
        if not ticket.response_ready.wait(timeout):
            raise TimeoutError(
                f"timed out waiting for action for request_id={request.request_id}"
            )
        if ticket.error is not None:
            raise ticket.error
        assert ticket.response is not None
        return ticket.response

    def next_callback(self, timeout: Optional[float] = None) -> CallbackTicket:
        if self._closed:
            raise RuntimeError("bridge is closed")
        try:
            return self._incoming.get(timeout=timeout)
        except queue.Empty as exc:
            raise TimeoutError("timed out waiting for AnyLogic callback") from exc

    def respond_action(
        self,
        ticket: CallbackTicket,
        action: int,
        *,
        value: float = 0.0,
        logits: tuple[float, ...] = (),
    ) -> None:
        if not ticket.request.action_required:
            raise ProtocolError("cannot attach an action to this callback")
        if not 0 <= int(action) < ACTION_COUNT:
            raise ProtocolError(f"action must be in [0, 3], got {action}")
        if ticket.request.obs.values[19 + int(action)] != 1.0:
            raise ProtocolError(f"action {action} is masked out by ALP")
        latency_us = max(0, (time.perf_counter_ns() - ticket.received_ns) // 1000)
        if self.rollout_audit is not None:
            self.rollout_audit.event("action_response", self._audit_info(ticket.request),
                                     action=int(action), response_status="about_to_release_RPC_response",
                                     anylogic_execution="UNVERIFIED")
        self._set_response(
            ticket,
            dispatch_pb2.DispatchResponse(
                action=int(action),
                value=float(value),
                logits=logits,
                latency_us=latency_us,
                has_action=True,
                episode_id=ticket.request.episode_id,
                decision_sequence=ticket.request.decision_sequence,
            ),
        )

    def wait_for_configuration(self, timeout=None):
        if not self._configuration_ready.wait(timeout):
            raise TimeoutError('waiting for AnyLogic EPISODE_START runtime configuration')
        if self._closed:
            raise RuntimeError('bridge closed before runtime configuration was consumed')
        return self.reward_config

    def close(self) -> None:
        with self._lock:
            self._closed = True
            for ticket in self._tickets_by_request_id.values():
                if not ticket.response_ready.is_set():
                    ticket.error = RuntimeError('training service closed before action response')
                    ticket.response_ready.set()
            self._configuration_ready.set()

    @staticmethod
    def _audit_info(request):
        kind = dispatch_pb2.DispatchKind.DESCRIPTOR.values_by_number.get(request.kind)
        return {"episode_id": request.episode_id, "request_id": request.request_id,
                "decision_sequence": request.decision_sequence,
                "sim_time_seconds": request.sim_time_seconds,
                "run_index": int(request.experiment_run_index),
                "experiment_seed": int(request.experiment_seed),
                "dispatch_kind": kind.name if kind is not None else f"UNKNOWN({request.kind})",
                "action_required": bool(request.action_required),
                "truck_id": int(request.truck_id),
                "reward_contract_id": request.reward_contract_id,
                "observation_schema_id": request.obs.schema_id if request.HasField("obs") else None}

    def _register(self, request: dispatch_pb2.DispatchRequest) -> CallbackTicket:
        candidate = self.reward_config
        if self.runtime_configuration:
            try:
                incoming_config = configuration_from_components(request.reward_components)
            except ValueError as exc:
                raise ProtocolError(str(exc)) from exc
            if candidate is None:
                if request.kind != dispatch_pb2.EPISODE_START:
                    raise ProtocolError('first configuration must arrive with EPISODE_START')
                candidate = incoming_config
            elif incoming_config != candidate:
                raise ProtocolError('AnyLogic reward configuration changed during this run')
        self._validate_request(request, grade_bounds=self.window_grade_bounds, config=candidate)
        serialized = request.SerializeToString(deterministic=True)
        with self._lock:
            if self._closed:
                raise RuntimeError("bridge is closed")
            if self.runtime_configuration and self.reward_config is not None and candidate != self.reward_config:
                raise ProtocolError("concurrent runtime configuration changed")
            existing = self._tickets_by_request_id.get(request.request_id)
            if existing is not None:
                if self._request_bytes[request.request_id] != serialized:
                    raise ProtocolError(
                        "request_id was reused with different request contents"
                    )
                return existing
            last = self._last_ticket_by_episode.get(request.episode_id)
            if last is not None:
                if last.request.kind == dispatch_pb2.EPISODE_END:
                    raise ProtocolError("callback received after episode terminal")
                if last.response is None or not last.response.has_action:
                    raise ProtocolError("next transition arrived before previous action response")
                if request.previous_action != last.response.action:
                    raise ProtocolError("previous_action disagrees with last action response")
                if request.decision_sequence != last.request.decision_sequence + 1:
                    raise ProtocolError("decision_sequence must be contiguous")
                elapsed = request.sim_time_seconds - last.request.sim_time_seconds
                if elapsed < 0 or abs(elapsed - request.sim_time_delta_seconds) > 1e-6:
                    raise ProtocolError("simulation delta disagrees with previous callback time")
            previous = self._last_sequence_by_episode.get(request.episode_id)
            if request.kind == dispatch_pb2.EPISODE_START:
                if previous is not None:
                    raise ProtocolError("duplicate episode start with a new request_id")
                run_index = int(request.experiment_run_index)
                experiment_seed = int(request.experiment_seed)
                if self._expected_episode_metadata is not None:
                    if self._started_episode_count >= len(
                        self._expected_episode_metadata
                    ):
                        raise ProtocolError(
                            "received more EPISODE_START callbacks than the seed manifest"
                        )
                    expected = self._expected_episode_metadata[
                        self._started_episode_count
                    ]
                    if (run_index, experiment_seed) != expected:
                        raise ProtocolError(
                            "episode metadata does not match seed manifest at row "
                            f"{self._started_episode_count + 1}: expected "
                            f"run_index={expected[0]}, experiment_seed={expected[1]}, "
                            f"got run_index={run_index}, experiment_seed={experiment_seed}"
                        )
                if run_index in self._seen_experiment_run_indices:
                    raise ProtocolError("experiment_run_index was reused")
                if experiment_seed in self._seen_experiment_seeds:
                    raise ProtocolError("experiment_seed was reused")
                self._seen_experiment_run_indices.add(run_index)
                self._seen_experiment_seeds.add(experiment_seed)
                self._metadata_by_episode[request.episode_id] = (
                    run_index,
                    experiment_seed,
                    request.reward_contract_id,
                )
                self._next_window_index_by_episode[request.episode_id] = 0
                self._started_episode_count += 1
            elif previous is None:
                raise ProtocolError("DECISION/END received before EPISODE_START")
            elif request.decision_sequence <= previous:
                raise ProtocolError(
                    "decision_sequence must increase strictly within an episode"
                )
            else:
                expected_metadata = self._metadata_by_episode[request.episode_id]
                actual_metadata = (
                    int(request.experiment_run_index),
                    int(request.experiment_seed),
                    request.reward_contract_id,
                )
                if actual_metadata != expected_metadata:
                    raise ProtocolError("episode metadata changed before terminal callback")

            next_window_index = self._next_window_index_by_episode[request.episode_id]
            for summary in request.closed_windows:
                if summary.window_index != next_window_index:
                    raise ProtocolError(
                        "closed_windows must contain each T_win exactly once in order"
                    )
                next_window_index += 1
            if next_window_index > WINDOWS_PER_EPISODE:
                raise ProtocolError("episode reported more than four T_win summaries")
            if (
                request.kind == dispatch_pb2.EPISODE_END
                and next_window_index != WINDOWS_PER_EPISODE
            ):
                raise ProtocolError("EPISODE_END requires exactly four T_win summaries")
            self._next_window_index_by_episode[request.episode_id] = next_window_index
            ticket = CallbackTicket(request=request)
            self._tickets_by_request_id[request.request_id] = ticket
            self._request_bytes[request.request_id] = serialized
            self._last_sequence_by_episode[request.episode_id] = request.decision_sequence
            self._last_ticket_by_episode[request.episode_id] = ticket
            if self.runtime_configuration and self.reward_config is None:
                self.reward_config = candidate
        self._incoming.put(ticket)
        self._configuration_ready.set()
        return ticket

    @staticmethod
    def _set_response(
        ticket: CallbackTicket,
        response: dispatch_pb2.DispatchResponse,
    ) -> None:
        if ticket.response_ready.is_set():
            return
        ticket.response = response
        ticket.response_ready.set()

    @staticmethod
    def _validate_request(request: dispatch_pb2.DispatchRequest, *, grade_bounds: bool = False, config: Optional[RewardConfiguration] = None) -> None:
        if not request.episode_id or not request.request_id:
            raise ProtocolError("episode_id and request_id are required")
        if request.decision_sequence < 0:
            raise ProtocolError("decision_sequence must be non-negative")
        if request.kind not in (dispatch_pb2.EPISODE_START, dispatch_pb2.DECISION, dispatch_pb2.EPISODE_END):
            raise ProtocolError("unknown or unspecified request.kind")
        if request.kind != dispatch_pb2.EPISODE_END and (request.terminated or request.truncated):
            raise ProtocolError("START/DECISION cannot be terminal")
        if request.kind == dispatch_pb2.EPISODE_END:
            if request.action_required:
                raise ProtocolError("EPISODE_END must not require an action")
            if not request.terminated and not request.truncated:
                raise ProtocolError("EPISODE_END must be terminated or truncated")
            if abs(request.sim_time_seconds - SHIFT_SECONDS) > 1e-6:
                raise ProtocolError("EPISODE_END must occur at 28800 seconds")
        elif not request.action_required:
            raise ProtocolError("START/DECISION must require an action")
        if request.kind != dispatch_pb2.EPISODE_END and request.sim_time_seconds >= SHIFT_SECONDS:
            raise ProtocolError("action request cannot occur at or after shift cutoff")
        if request.kind == dispatch_pb2.EPISODE_START:
            if request.closed_windows or any(request.reward_components.get(k,0) != 0 for k in (*ADDITIVE_COMPONENTS,"delta_wait_vehicle_seconds")):
                raise ProtocolError("EPISODE_START cannot carry prior transition components/windows")
            if request.terminated or request.truncated:
                raise ProtocolError("EPISODE_START cannot be terminal")
            if request.previous_action != -1 or request.transition_reward != 0 or request.sim_time_delta_seconds != 0:
                raise ProtocolError("EPISODE_START must have previous_action=-1 and zero reward/delta")
            if request.decision_sequence != 0:
                raise ProtocolError("EPISODE_START decision_sequence must be zero")
        if not np.isfinite(request.transition_reward):
            raise ProtocolError("transition_reward must be finite")
        if not np.isfinite(request.sim_time_seconds) or not np.isfinite(request.sim_time_delta_seconds):
            raise ProtocolError("simulation times must be finite")
        if request.sim_time_seconds < 0 or request.sim_time_delta_seconds < 0:
            raise ProtocolError("simulation times must be non-negative")
        if request.experiment_run_index <= 0:
            raise ProtocolError("experiment_run_index must be positive")
        if request.experiment_seed <= 0:
            raise ProtocolError("experiment_seed must be positive")
        if request.reward_contract_id != REWARD_CONTRACT_ID:
            raise ProtocolError(
                f"reward_contract_id must be {REWARD_CONTRACT_ID!r}, "
                f"got {request.reward_contract_id!r}"
            )
        if "delta_wait_vehicle_seconds" not in request.reward_components:
            raise ProtocolError(
                "reward_components missing delta_wait_vehicle_seconds"
            )
        if request.kind != dispatch_pb2.EPISODE_END and any(request.reward_components.get(k,0) != 0 for k in ("waste","grade_shift","production")):
            raise ProtocolError("terminal-only reward appeared before episode end")
        if request.previous_action == 3 and request.reward_components.get('grade_action', 0) != 0:
            raise ProtocolError('WASTE action cannot carry grade_action reward in v4')
        if request.kind == dispatch_pb2.EPISODE_END:
            terminal_fields = {
                "grade_gap_shift",
                "grade_shift_reward_raw",
                "ore_tons_shift",
                "production_fraction_raw",
                "production_shortfall",
            }
            missing = terminal_fields.difference(request.reward_components)
            if missing:
                raise ProtocolError(
                    f"terminal reward_components missing fields: {sorted(missing)}"
                )
        try:
            windows = [window_summary_to_dict(summary) for summary in request.closed_windows]
            for summary in windows:
                validate_window_summary(summary, grade_bounds=grade_bounds)
            validate_reward_accounting(
                request.transition_reward,
                dict(request.reward_components),
                windows, config=config,
            )
        except ValueError as exc:
            raise ProtocolError(str(exc)) from exc
        observation_array(request)
