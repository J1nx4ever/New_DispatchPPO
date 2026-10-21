"""Manual AnyLogic communication check; no PPO updates or checkpoint loading.

Run this server, then manually start ONE RL_Training run in AnyLogic.
Action rules are first-legal or a fresh untrained masked policy, for checking only.
"""
from __future__ import annotations
from contextlib import nullcontext
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from .alp_audit import validate_alp_contract
from .dispatch_bridge import DispatchCallbackBridge
from .dispatch_env import DispatchEnv
from .dispatch_service import create_server
from .episode_runner import ParameterVariationEpisodeRunner
from .protocol_artifacts import verify_protocol_artifacts


def first_legal_action(mask):
    mask = np.asarray(mask)
    if mask.shape != (4,) or not np.isin(mask, [0, 1]).all():
        raise ValueError('expected four binary action mask entries')
    legal = np.flatnonzero(mask)
    if not len(legal):
        raise ValueError('action request has no legal action')
    return int(legal[0])


def run_episode(env, stream=None, *, capture_observations=False, action_selector=None):
    """One actual episode; never reset at a decision/rollout boundary."""
    if capture_observations and stream is None:
        raise ValueError("capturing observations requires an explicit record stream")
    observation, info = env.reset()
    minimum = observation.astype(np.float64).copy()
    maximum = minimum.copy()
    def write(kind, obs, metadata, **extra):
        if stream is None:
            return
        row = dict(record=kind, **metadata, **extra)
        if capture_observations:
            row['observation'] = obs.tolist()
        stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False)+'\n')
        stream.flush()
    write('episode_start', observation, info)
    transitions = 0
    total_reward = 0.0
    action_counts = [0, 0, 0, 0]
    mask_counts = {}
    while True:
        action = (first_legal_action(info['action_mask']) if action_selector is None
                  else action_selector(observation, info))
        if (not isinstance(action, (int, np.integer)) or not 0 <= action < 4
                or not info['action_mask'][action]):
            raise ValueError('action selector returned an illegal dispatch action')
        key = ''.join('1' if legal else '0' for legal in info['action_mask'])
        mask_counts[key] = mask_counts.get(key, 0) + 1
        action_counts[action] += 1
        action_request_id = info['request_id']
        observation, reward, terminated, truncated, info = env.step(action)
        transitions += 1
        total_reward += reward
        np.minimum(minimum, observation, out=minimum)
        np.maximum(maximum, observation, out=maximum)
        write('transition', observation, info, action_request_id=action_request_id,
              action=action, reward=reward, terminated=terminated, truncated=truncated)
        if terminated or truncated:
            return dict(transitions=transitions, total_reward=total_reward,
                        terminated=terminated, truncated=truncated,
                        action_counts=action_counts, decision_mask_counts=mask_counts,
                        episode_id=info['episode_id'], observation_min=minimum.tolist(),
                        observation_max=maximum.tolist())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=50051)
    parser.add_argument('--callback-timeout', type=float, default=3600)
    parser.add_argument('--action-rule', choices=['first-legal', 'masked-untrained'], default='first-legal')
    parser.add_argument('--policy-seed', type=int, default=7)
    parser.add_argument('--record-transitions', action='store_true', help='Opt in to per-transition JSONL logging.')
    parser.add_argument('--capture-observations', action='store_true', help='Record full observations; also enables transition logging.')
    args = parser.parse_args()
    if args.callback_timeout <= 0:
        parser.error('--callback-timeout must be positive')
    contract = validate_alp_contract()
    protocol = verify_protocol_artifacts()
    root = Path(__file__).resolve().parents[1]
    args.output_dir.mkdir(parents=True, exist_ok=False)
    status = dict(status='waiting', source_kind='real_anylogic_smoke',
                  action_rule='first_legal_load_site', ppo_optimization=False,
                  alp_runtime_verified=False, contract=contract,
                  record_transitions=args.record_transitions or args.capture_observations,
                  capture_observations=args.capture_observations,
                  alp_sha256=hashlib.sha256((root/'anylogic/DRL-PPO.alp').read_bytes()).hexdigest(),
                  protocol=protocol)
    status_path = args.output_dir/'status.json'
    def save_status():
        status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2)+'\n')
    save_status()
    bridge = DispatchCallbackBridge()
    env = DispatchEnv(bridge, ParameterVariationEpisodeRunner(1), args.callback_timeout)
    action_selector = None
    server = None
    try:
        if args.action_rule == 'masked-untrained':
            import torch
            from .masked_policy import DispatchMaskedPolicy, POLICY_CONTRACT_ID
            torch.manual_seed(args.policy_seed)
            policy = DispatchMaskedPolicy(env.observation_space, env.action_space,
                                          lambda _: 3e-4,
                                          net_arch=dict(pi=[128,128], vf=[128,128]))
            policy.set_training_mode(False)
            action_selector = lambda obs, info: int(policy.predict(obs, deterministic=False)[0])
            status.update(action_rule='masked_untrained', policy_contract_id=POLICY_CONTRACT_ID,
                          policy_seed=args.policy_seed, policy_trained=False)
            save_status()
        server = create_server(bridge, args.host, args.port)
        server.start()
        print(f'Communication check on {args.host}:{args.port}; action rule={args.action_rule}; manually start ONE AnyLogic run. No PPO updates.', flush=True)
        records = ((args.output_dir/'transitions.jsonl').open('x', encoding='utf-8')
                   if args.record_transitions or args.capture_observations else nullcontext(None))
        with records as stream:
            result = run_episode(env, stream, capture_observations=args.capture_observations,
                                 action_selector=action_selector)
        status.update(status='complete', **result)
        status['verification_scope'] = 'Python callback contract and terminal received; GUI schema log and business behavior require separate verification'
        print(f"Received terminal: {result['transitions']} transitions. Results: {args.output_dir}", flush=True)
    except BaseException as exc:
        status.update(status='incomplete', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        env.close()
        if server is not None:
            server.stop(2).wait()
        save_status()

if __name__ == '__main__':
    main()
