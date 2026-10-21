"""Run attribution events plus optional SB3 2.9.0 rollout snapshots.

No prediction, sampling, seeding, or optimizer operation is performed here.
Detailed snapshots/hash collection is opt-in and adds wall time when enabled.
RPC reception/release is Python evidence, not proof of AnyLogic clock freezing.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import stable_baselines3


def policy_hash(policy):
    digest = hashlib.sha256()
    for name, tensor in sorted(policy.state_dict().items()):
        array = tensor.detach().cpu().numpy().copy()
        digest.update(name.encode())
        digest.update(str(array.dtype).encode())
        digest.update(str(array.shape).encode())
        digest.update(array.tobytes())
    return digest.hexdigest()


def identity(info):
    return {**{k: info.get(k) for k in ('episode_id', 'request_id', 'decision_sequence', 'sim_time_seconds')},
            'run_index': info.get('run_index', info.get('experiment_run_index')),
            'experiment_seed': info.get('experiment_seed'),
            **{k: info[k] for k in ('dispatch_kind', 'action_required', 'truck_id',
                                     'reward_contract_id', 'observation_schema_id') if k in info}}


class RolloutDebug:
    def __init__(self, directory: Path, *, source_kind: str,
                 expected_episode_identities=(), seed_manifest_path=None, audit_run_id=None,
                 capture_rollouts=True):
        if source_kind not in ('real_anylogic', 'synthetic_test'):
            raise ValueError('Explicit data provenance required')
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        self.source_kind = source_kind
        # OS entropy only: never touch Python/NumPy/Torch sampling RNGs.
        self.audit_run_id = audit_run_id or str(uuid.uuid4())
        self.pid = os.getpid()
        self.capture_rollouts = bool(capture_rollouts)
        expected = copy.deepcopy(list(expected_episode_identities))
        self.seed_manifest_path = Path(seed_manifest_path).resolve() if seed_manifest_path else None
        canonical = json.dumps(expected, sort_keys=True, separators=(',', ':')).encode()
        self.expected_identities_sha256 = hashlib.sha256(canonical).hexdigest()
        self.seed_manifest_sha256 = hashlib.sha256(
            self.seed_manifest_path.read_bytes() if self.seed_manifest_path else canonical).hexdigest()
        self.rollout_id = None  # Initial reset/requests precede rollout 1.
        self._next_id = 1
        self.action_context = {}
        self._rows = []
        self._boundary = {}
        self._meta = None
        self._lock = threading.Lock()
        self._events = (self.directory / 'sync_events.jsonl').open('x', encoding='utf-8', buffering=1)
        self._event_sequence = 0
        self._closed = False
        self.event('run_start', output_dir=str(self.directory.parent.resolve()),
                   source_kind=source_kind, seed_manifest_path=str(self.seed_manifest_path) if self.seed_manifest_path else None,
                   capture_rollouts=self.capture_rollouts,
                   seed_manifest_sha256=self.seed_manifest_sha256,
                   expected_episode_identities=expected,
                   expected_identities_sha256=self.expected_identities_sha256)

    def event(self, name, info=None, **extra):
        with self._lock:
            self._event_sequence += 1
            record = {
                'event': name, 'event_sequence': self._event_sequence,
                'monotonic_ns': time.monotonic_ns(),
                'audit_run_id': self.audit_run_id, 'pid': self.pid,
                'utc_time': datetime.now(timezone.utc).isoformat(timespec='microseconds'),
                'rollout_id': self.rollout_id, **identity(info or self.action_context), **extra,
            }
            self._events.write(json.dumps(record, ensure_ascii=False) + '\n')
            return {key: record[key] for key in (
                'audit_run_id', 'pid', 'utc_time', 'monotonic_ns', 'event_sequence'
            )}

    def begin(self, model):
        self.rollout_id = self._next_id
        self._next_id += 1
        self._rows = []
        self._boundary = {}
        self.event('rollout_start')

    def sampled(self, model, actions):
        if not self.capture_rollouts:
            self.event('action_sampled', actions=np.array(actions, copy=True).tolist(),
                       execution_status='sampled_only; AnyLogic_execution_UNVERIFIED')
            return
        hashed = policy_hash(model.policy)
        self._rows.append({'action_request': copy.deepcopy(identity(self.action_context)),
                           'sampling_policy_hash': hashed})
        self.event('action_sampled', actions=np.array(actions, copy=True).tolist(), policy_hash=hashed,
                   execution_status='sampled_only; AnyLogic_execution_UNVERIFIED')

    def transition(self, infos, dones):
        if not self.capture_rollouts:
            return
        self._rows[-1].update(
            result_request=copy.deepcopy(identity(infos[0])),
            done=bool(dones[0]), timeout_bootstrap=bool(
                dones[0] and infos[0].get('TimeLimit.truncated', False)
                and infos[0].get('terminal_observation') is not None),
        )

    def bootstrap_start(self, model, new_obs, dones, infos):
        if not self.capture_rollouts:
            self.event('bootstrap_start', infos[0])
            return
        self._boundary = {'boundary_new_obs': np.array(new_obs, copy=True),
                          'boundary_dones': np.array(dones, copy=True)}
        self._bootstrap_hash = policy_hash(model.policy)
        self.event('bootstrap_start', infos[0], policy_hash=self._bootstrap_hash,
                   boundary_obs_semantics='VecEnv new_obs; may be next episode reset observation')

    def bootstrap_end(self, values):
        if not self.capture_rollouts:
            self.event('bootstrap_end')
            return
        self._boundary['boundary_last_values'] = values.detach().cpu().numpy().copy().reshape(-1)
        self.event('bootstrap_end', self._rows[-1]['result_request'])

    def before_update(self, model):
        if not self.capture_rollouts:
            self.event('update_start')
            return
        b = model.rollout_buffer
        arrays = {name: np.array(getattr(b, field), copy=True) for name, field in {
            'observations':'observations', 'actions':'actions', 'rewards':'rewards',
            'old_values':'values', 'old_log_probs':'log_probs', 'episode_starts':'episode_starts',
            'advantages':'advantages', 'returns':'returns',
        }.items()}
        arrays.update({k: v.copy() for k, v in self._boundary.items()})
        arrays['transition_dones'] = np.array([[r['done']] for r in self._rows], dtype=bool)
        arrays['timeout_bootstrap_applied'] = np.array([[r['timeout_bootstrap']] for r in self._rows], dtype=bool)
        self._meta = {
            'audit_run_id': self.audit_run_id, 'pid': self.pid,
            'seed_manifest_sha256': self.seed_manifest_sha256,
            'rollout_id': self.rollout_id, 'valid_length': b.buffer_size, 'n_steps': model.n_steps,
            'source_kind': self.source_kind, 'stable_baselines3_version': stable_baselines3.__version__,
            'gamma': model.gamma, 'gae_lambda': model.gae_lambda,
            'final_target_episode': model._episode_budget_reached,
            'transitions': copy.deepcopy(self._rows),
            'bootstrap_policy_hash': self._bootstrap_hash,
            'before_update_policy_hash': policy_hash(model.policy),
            'after_update_policy_hash': None, 'update_completed': False,
            'array_dtypes': {k: str(v.dtype) for k,v in arrays.items()},
            'reward_semantics': 'actual buffer rewards, including any timeout value correction; never correct again',
            'request_semantics': 'action_request identifies observation/action; result_request identifies reward/terminal callback',
            'event_rollout_id_semantics': 'active Python context; an arriving RPC may belong to the next rollout; correlate by request_id',
            'anylogic_whole_clock_frozen': 'UNVERIFIED: no simulation-side evidence',
        }
        np.savez_compressed(self.directory / f'rollout_{self.rollout_id:06d}.npz', **arrays)
        self._write_meta()
        self.event('update_start', self._rows[-1]['result_request'], policy_hash=self._meta['before_update_policy_hash'])

    def after_update(self, model):
        if not self.capture_rollouts:
            self.event('update_end')
            return
        self._meta['after_update_policy_hash'] = policy_hash(model.policy)
        self._meta['update_completed'] = True
        self._write_meta()
        self.event('update_end', self._rows[-1]['result_request'], policy_hash=self._meta['after_update_policy_hash'])

    def _write_meta(self):
        (self.directory / f'rollout_{self.rollout_id:06d}.json').write_text(
            json.dumps(self._meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def close(self, *, status='incomplete'):
        if self._closed:
            return
        self.event('run_end', status=status)
        self._events.close()
        self._closed = True
