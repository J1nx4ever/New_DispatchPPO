from __future__ import annotations

from typing import Any, Optional, Protocol

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from .dispatch_bridge import (
    ACTION_COUNT,
    CallbackTicket,
    DispatchCallbackBridge,
    ProtocolError,
    observation_array,
)
from .generated import dispatch_pb2
from .observation_contract import OBSERVATION_LOW, OBSERVATION_HIGH, action_mask
from .reward_contract import window_summary_to_dict


class EpisodeRunner(Protocol):
    def start_episode(
        self,
        seed: Optional[int],
        options: Optional[dict[str, Any]],
    ) -> Optional[bool]: ...

    def close(self) -> None: ...


class DispatchEnv(gym.Env[np.ndarray, int]):
    metadata = {"render_modes": []}

    def __init__(
        self,
        bridge: DispatchCallbackBridge,
        runner: Optional[EpisodeRunner] = None,
        callback_timeout: float = 30.0,
    ) -> None:
        super().__init__()
        self.bridge = bridge
        self.runner = runner
        self.callback_timeout = callback_timeout
        self.action_space = spaces.Discrete(ACTION_COUNT)
        self.observation_space = spaces.Box(
            low=np.asarray(OBSERVATION_LOW, dtype=np.float32),
            high=np.asarray(OBSERVATION_HIGH, dtype=np.float32),
            dtype=np.float32,
        )
        self._pending: Optional[CallbackTicket] = None
        self._episode_id: Optional[str] = None
        self._last_observation: Optional[np.ndarray] = None

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        audit = self.bridge.rollout_audit
        if audit is not None:
            audit.event("reset_start")
        super().reset(seed=seed)
        if self._pending is not None:
            raise RuntimeError("cannot reset while an action callback is pending")
        if self.runner is not None:
            episode_available = self.runner.start_episode(seed, options)
            if episode_available is False:
                if self._last_observation is None:
                    raise RuntimeError("runner has no episode or terminal observation")
                if audit is not None:
                    audit.action_context = {}
                    audit.event("reset_end", experiment_complete=True, effective_episode_started=False)
                return self._last_observation.copy(), {"experiment_complete": True}
        ticket = self.bridge.next_callback(timeout=self.callback_timeout)
        request = ticket.request
        if request.kind != dispatch_pb2.EPISODE_START:
            raise ProtocolError(
                f"reset expected EPISODE_START, got kind={request.kind}"
            )
        self._pending = ticket
        self._episode_id = request.episode_id
        self._last_observation = observation_array(request)
        if audit is not None:
            audit.action_context = self._info(request)
            audit.event("reset_end", audit.action_context, effective_episode_started=True)
        return self._last_observation.copy(), self._info(request)

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if self._pending is None:
            raise RuntimeError("step called before reset or after episode end")
        if not self.action_space.contains(action):
            raise ValueError(f"invalid action: {action}")
        audit = self.bridge.rollout_audit
        if audit is not None:
            audit.event("step_start", self._info(self._pending.request), action=int(action))
        self.bridge.respond_action(self._pending, int(action))
        self._pending = None
        ticket = self.bridge.next_callback(timeout=self.callback_timeout)
        request = ticket.request
        if request.episode_id != self._episode_id:
            raise ProtocolError("episode_id changed before terminal callback")
        observation = observation_array(request)
        self._last_observation = observation
        reward = float(request.transition_reward)
        if request.kind == dispatch_pb2.EPISODE_END:
            terminated = bool(request.terminated)
            truncated = bool(request.truncated)
            self._episode_id = None
        elif request.kind == dispatch_pb2.DECISION:
            if request.terminated or request.truncated:
                raise ProtocolError("DECISION cannot be terminal")
            terminated = False
            truncated = False
            self._pending = ticket
        else:
            raise ProtocolError(f"unexpected callback kind={request.kind}")
        if audit is not None:
            audit.action_context = self._info(request) if self._pending is not None else {}
            audit.event("step_end", self._info(request),
                        previous_action_reported=int(request.previous_action))
        return observation, reward, terminated, truncated, self._info(request)

    def close(self) -> None:
        if self.runner is not None:
            self.runner.close()
        self.bridge.close()
        super().close()

    @staticmethod
    def _info(request: dispatch_pb2.DispatchRequest) -> dict[str, Any]:
        return {
            "action_mask": action_mask(request.obs.values).tolist(),
            "episode_id": request.episode_id,
            "decision_sequence": request.decision_sequence,
            "request_id": request.request_id,
            "sim_time_seconds": request.sim_time_seconds,
            "sim_time_delta_seconds": request.sim_time_delta_seconds,
            "previous_action": request.previous_action,
            "transition_reward_raw": float(request.transition_reward),
            "reward_components": dict(request.reward_components),
            "closed_windows": [
                window_summary_to_dict(summary)
                for summary in request.closed_windows
            ],
            "experiment_run_index": int(request.experiment_run_index),
            "experiment_seed": int(request.experiment_seed),
            "reward_contract_id": request.reward_contract_id,
            "observation_schema_id": request.obs.schema_id,
        }
