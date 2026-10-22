"""Evaluate a completed masked PPO checkpoint on real AnyLogic episodes.

This entry point is inference-only: it never calls learn() or changes weights.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import statistics
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import stable_baselines3
from stable_baselines3 import PPO

from .dispatch_bridge import DispatchCallbackBridge
from .dispatch_env import DispatchEnv
from .dispatch_service import create_server
from .episode_runner import ParameterVariationEpisodeRunner
from .masked_policy import DispatchMaskedPolicy, POLICY_CONTRACT_ID
from .observation_contract import (
    AGENT_OBSERVATION_SIZE, OBSERVATION_SCHEMA_ID, OBSERVATION_SIZE,
)
from .observation_projection_wrapper import (
    FIFOObservationWrapper, PROJECTION_CONTRACT_ID,
)
from .protocol_artifacts import verify_protocol_artifacts
from .reward_contract import (
    REWARD_CONTRACT_ID, FROZEN_REWARD_PARAMETERS, WINDOWS_PER_EPISODE,
    ADDITIVE_COMPONENTS, validate_window_summary,
)
from .reward_config import RewardConfiguration, configuration_to_components


def _validate_reward_identity(payload: dict[str, Any], label: str) -> str:
    if payload.get('reward_contract_id') != REWARD_CONTRACT_ID:
        raise SystemExit(f'{label} uses an incompatible reward contract')
    try:
        config = RewardConfiguration(**payload['reward_configuration'])
    except (KeyError, TypeError, ValueError) as exc:
        raise SystemExit(f'{label} lacks a valid frozen Reward V1.0 configuration') from exc
    if payload.get('reward_configuration_fingerprint') != config.fingerprint:
        raise SystemExit(f'{label} reward configuration fingerprint does not match')
    return config.fingerprint


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_seed_manifest(path: Path, episodes: int) -> list[tuple[int, int]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"cannot read seed manifest: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"seed manifest is not valid JSON: {path}") from exc
    if not isinstance(payload, list) or len(payload) != episodes:
        raise SystemExit(
            f"seed manifest must contain exactly {episodes} rows: {path}"
        )
    result: list[tuple[int, int]] = []
    for row_number, row in enumerate(payload, 1):
        if not isinstance(row, dict):
            raise SystemExit(f"seed manifest row {row_number} must be an object")
        run_index = row.get("run_index")
        seed = row.get("experiment_seed")
        if (
            not isinstance(run_index, int)
            or isinstance(run_index, bool)
            or not isinstance(seed, int)
            or isinstance(seed, bool)
            or run_index <= 0
            or seed <= 0
        ):
            raise SystemExit(
                f"seed manifest row {row_number} requires positive integer "
                "run_index and experiment_seed"
            )
        result.append((run_index, seed))
    if len({row[0] for row in result}) != len(result):
        raise SystemExit("seed manifest run_index values must be unique")
    if len({row[1] for row in result}) != len(result):
        raise SystemExit("seed manifest experiment_seed values must be unique")
    return result


def _validate_checkpoint(model_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved = model_path.resolve()
    if not resolved.is_file():
        raise SystemExit(f"model file does not exist: {resolved}")
    run_dir = resolved.parent
    try:
        run_manifest = json.loads(
            (run_dir / "run_manifest.json").read_text(encoding="utf-8")
        )
        success = json.loads((run_dir / "SUCCESS.json").read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(
            "checkpoint must be from a completed run containing run_manifest.json "
            "and SUCCESS.json"
        ) from exc
    except json.JSONDecodeError as exc:
        raise SystemExit("checkpoint run metadata is invalid JSON") from exc

    if run_manifest.get("status") != "complete" or success.get("status") != "complete":
        raise SystemExit("checkpoint run is not marked complete")
    _validate_reward_identity(run_manifest, 'checkpoint manifest')
    _validate_reward_identity(success, 'checkpoint SUCCESS')
    if run_manifest.get("observation_schema_id") != OBSERVATION_SCHEMA_ID:
        raise SystemExit("checkpoint uses an incompatible observation schema")
    if run_manifest.get("policy_contract_id") != POLICY_CONTRACT_ID:
        raise SystemExit("checkpoint does not declare the masked policy contract")
    if success.get("policy_contract_id") != POLICY_CONTRACT_ID:
        raise SystemExit("SUCCESS.json does not declare the masked policy contract")
    if success.get("model_sha256") != _sha256(resolved):
        raise SystemExit("model hash does not match SUCCESS.json")
    return run_manifest, success


def _evaluate_episode(env: DispatchEnv, model: PPO, *, deterministic: bool) -> dict[str, Any]:
    observation, info = env.reset()
    episode_id = info["episode_id"]
    run_index = int(info["experiment_run_index"])
    experiment_seed = int(info["experiment_seed"])
    action_counts = [0, 0, 0, 0]
    mask_counts: dict[str, int] = {}
    component_sums: dict[str, float] = {}
    episode_return = 0.0
    transitions = 0
    closed_windows: list[dict[str, Any]] = []

    while True:
        mask = np.asarray(info["action_mask"])
        if (
            mask.shape != (4,)
            or not np.isin(mask, [0, 1]).all()
            or not mask.any()
        ):
            raise ValueError("environment supplied an invalid nonterminal action mask")
        action_value, _ = model.predict(observation, deterministic=deterministic)
        action = int(np.asarray(action_value).reshape(-1)[0])
        if action < 0 or action >= 4 or not mask[action]:
            raise ValueError(f"policy selected illegal action {action} for mask {mask}")

        mask_key = "".join(str(int(bit)) for bit in mask)
        mask_counts[mask_key] = mask_counts.get(mask_key, 0) + 1
        action_counts[action] += 1
        observation, reward, terminated, truncated, info = env.step(action)
        if not math.isfinite(float(reward)):
            raise ValueError("environment returned a non-finite reward")
        episode_return += float(reward)
        transitions += 1
        for name, value in info.get("reward_components", {}).items():
            # Config/terminal diagnostics are not additive reward components.
            if name in (*ADDITIVE_COMPONENTS, 'delta_wait_vehicle_seconds'):
                component_sums[name] = component_sums.get(name, 0.0) + float(value)
        for window in info.get('closed_windows', []):
            validate_window_summary(window)
            if window['window_index'] != len(closed_windows):
                raise ValueError('evaluation windows must arrive exactly once in order')
            closed_windows.append(dict(window))

        if terminated or truncated:
            if not terminated or truncated:
                raise RuntimeError(
                    f"episode {episode_id} ended without the expected terminal"
                )
            break

    if len(closed_windows) != WINDOWS_PER_EPISODE:
        raise ValueError('evaluation requires all four window summaries')
    terminal = info['reward_components']
    ore = float(terminal['ore_tons_shift'])
    waste = float(terminal['waste_tons_shift'])
    if not math.isclose(math.fsum(w['ore_tons'] for w in closed_windows), ore, rel_tol=1e-9, abs_tol=1e-5):
        raise ValueError('window ore tons do not match terminal crushed ore')
    if not math.isclose(math.fsum(w['metal_tons'] for w in closed_windows),
                        ore * float(terminal['shift_grade']), rel_tol=1e-9, abs_tol=1e-5):
        raise ValueError('window metal tons do not match terminal crushed metal')
    ore_met = ore >= FROZEN_REWARD_PARAMETERS['target_ore_tons_shift'] - 1e-6
    waste_met = waste >= FROZEN_REWARD_PARAMETERS['target_waste_tons_shift'] - 1e-6
    compliant = sum(not (w['violation_upper'] or w['violation_lower']) for w in closed_windows)
    return {
        "episode_id": episode_id,
        "run_index": run_index,
        "experiment_seed": experiment_seed,
        "length": transitions,
        "episode_return": episode_return,
        "wait_vehicle_seconds": component_sums.get(
            "delta_wait_vehicle_seconds", 0.0
        ),
        "terminal_reward_components": {
            key: float(value)
            for key, value in info["reward_components"].items()
        },
        "reward_component_sums": component_sums,
        "action_counts": action_counts,
        "decision_mask_counts": mask_counts,
        "closed_windows": closed_windows,
        'ore_plan_met': ore_met,
        'waste_plan_met': waste_met,
        'production_joint_met': ore_met and waste_met,
        'compliant_windows': compliant,
        'window_compliance_rate': compliant / WINDOWS_PER_EPISODE,
        'all_windows_compliant': compliant == WINDOWS_PER_EPISODE,
    }


def _summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    returns = [float(record["episode_return"]) for record in records]
    lengths = [int(record["length"]) for record in records]

    def metric_values(name: str) -> list[float]:
        values = []
        for record in records:
            value = record["terminal_reward_components"].get(name)
            if value is not None and math.isfinite(float(value)):
                values.append(float(value))
        return values

    metrics: dict[str, dict[str, float]] = {}
    for name in (
        "ore_tons_shift",
        "shift_grade",
        "grade_gap_shift",
        "production_shortfall",
        "waste_tons_shift",
        "waste_shortfall",
    ):
        values = metric_values(name)
        if values:
            metrics[name] = {
                "mean": statistics.fmean(values),
                "min": min(values),
                "max": max(values),
            }
    wait_values = [
        float(record["reward_component_sums"].get("delta_wait_vehicle_seconds", 0.0))
        for record in records
    ]
    return {
        "episodes": len(records),
        "total_transitions": sum(lengths),
        "episode_return": {
            "mean": statistics.fmean(returns),
            "min": min(returns),
            "max": max(returns),
        },
        "episode_length": {
            "mean": statistics.fmean(lengths),
            "min": min(lengths),
            "max": max(lengths),
        },
        "wait_vehicle_seconds": {
            "mean": statistics.fmean(wait_values),
            "min": min(wait_values),
            "max": max(wait_values),
        },
        "terminal_metrics": metrics,
        'window_compliance_rate': sum(r['compliant_windows'] for r in records) / (len(records) * WINDOWS_PER_EPISODE),
        'all_windows_compliant_rate': statistics.fmean(r['all_windows_compliant'] for r in records),
        'ore_plan_attainment_rate': statistics.fmean(r['ore_plan_met'] for r in records),
        'waste_plan_attainment_rate': statistics.fmean(r['waste_plan_met'] for r in records),
        'production_joint_attainment_rate': statistics.fmean(r['production_joint_met'] for r in records),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inference-only evaluation of a completed masked PPO model."
    )
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--episodes", type=int, required=True)
    parser.add_argument("--anylogic-seed-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=50051)
    parser.add_argument("--callback-timeout", type=float, default=3600.0)
    parser.add_argument("--rpc-workers", type=int, default=8)
    parser.add_argument("--alp-path", type=Path, help='Only used with explicit --audit-alp.')
    parser.add_argument('--audit-alp', action='store_true', help='Optional offline source/parameter audit.')
    parser.add_argument(
        "--stochastic",
        action="store_true",
        help="sample from the policy instead of deterministic prediction",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.episodes <= 0:
        raise SystemExit("--episodes must be positive")
    if args.callback_timeout <= 0:
        raise SystemExit("--callback-timeout must be positive")
    if args.rpc_workers < 2:
        raise SystemExit("--rpc-workers must be at least 2")
    output_dir = args.output_dir
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"--output-dir must be absent or empty: {output_dir}")

    expected = _load_seed_manifest(args.anylogic_seed_manifest, args.episodes)
    run_manifest, success = _validate_checkpoint(args.model)
    verify_protocol_artifacts()
    from .alp_audit import validate_alp_contract

    alp_contract = None
    if args.audit_alp:
        if args.alp_path is None:
            raise SystemExit('--audit-alp requires --alp-path')
        alp_contract = validate_alp_contract(args.alp_path)
    model_path = args.model.resolve()
    model = PPO.load(model_path, device="auto")
    if type(model.policy) is not DispatchMaskedPolicy:
        raise SystemExit("checkpoint does not load as DispatchMaskedPolicy")
    # Runs predating the projection wrapper are raw 1519D F0 runs.
    agent_mode = run_manifest.get("agent_observation_mode", "f0")
    if agent_mode not in ("f0", "p0-smoke"):
        raise SystemExit("checkpoint declares an unknown agent observation mode")
    expected_dimension = (
        OBSERVATION_SIZE if agent_mode == "f0" else AGENT_OBSERVATION_SIZE
    )
    if int(run_manifest.get("agent_observation_dimension", OBSERVATION_SIZE)) != expected_dimension:
        raise SystemExit("training run declares an inconsistent agent observation dimension")
    projection_id = run_manifest.get("projection_contract_id")
    if expected_dimension == OBSERVATION_SIZE:
        if projection_id is not None:
            raise SystemExit("raw observation run declares a projection contract")
    elif projection_id != PROJECTION_CONTRACT_ID:
        raise SystemExit("checkpoint declares an incompatible projection contract")
    if tuple(model.observation_space.shape or ()) != (expected_dimension,):
        raise SystemExit("checkpoint observation space is incompatible with its training manifest")
    if getattr(model.action_space, "n", None) != 4:
        raise SystemExit("checkpoint action space is incompatible")
    model.policy.set_training_mode(False)

    output_dir.mkdir(parents=True, exist_ok=True)
    evaluation_id = str(uuid.uuid4())
    manifest: dict[str, Any] = {
        "evaluation_id": evaluation_id,
        "status": "running",
        "created_unix_seconds": time.time(),
        "command": [sys.executable, *sys.argv],
        "model_path": str(model_path),
        "model_sha256": _sha256(model_path),
        "source_training_run": str(model_path.parent),
        "source_training_success": success,
        "source_training_commit": run_manifest.get("git_commit"),
        "policy_contract_id": POLICY_CONTRACT_ID,
        "reward_contract_id": REWARD_CONTRACT_ID,
        'reward_spec_sha256': _sha256(Path(__file__).with_name('reward_v1_configuration.json')),
        'observation_schema_sha256': _sha256(Path(__file__).with_name('observation_schema.json')),
        "observation_schema_id": OBSERVATION_SCHEMA_ID,
        "agent_observation_mode": agent_mode,
        "agent_observation_dimension": expected_dimension,
        "projection_contract_id": projection_id,
        "episodes_requested": args.episodes,
        "deterministic": not args.stochastic,
        "seed_manifest": str(args.anylogic_seed_manifest.resolve()),
        "seed_manifest_sha256": _sha256(args.anylogic_seed_manifest.resolve()),
        "expected_episode_metadata": [
            {"run_index": run_index, "experiment_seed": seed}
            for run_index, seed in expected
        ],
        "alp_contract": alp_contract,
        'configuration_source': 'anylogic_rpc',
        'local_alp_audit_requested': args.audit_alp,
        'runtime_reward_configuration_received': False,
        "alp_runtime_verified": False,
        "python_version": platform.python_version(),
        "stable_baselines3_version": stable_baselines3.__version__,
    }
    manifest_path = output_dir / "evaluation_manifest.json"
    episodes_path = output_dir / "evaluation_episodes.jsonl"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    bridge = DispatchCallbackBridge(expected_episode_metadata=expected, runtime_configuration=True)
    server = create_server(
        bridge, args.host, args.port, max_workers=args.rpc_workers
    )
    env = DispatchEnv(
        bridge,
        runner=ParameterVariationEpisodeRunner(total_episodes=args.episodes),
        callback_timeout=args.callback_timeout,
    )
    if agent_mode == "p0-smoke":
        env = FIFOObservationWrapper(env)
    completed = False
    records: list[dict[str, Any]] = []
    try:
        server.start()
        print(
            f"Dispatch gRPC listening on {args.host}:{args.port}. "
            f"Start AnyLogic RL_Training with {args.episodes} replications; "
            f"evaluation only, no PPO updates. Outputs: {output_dir}",
            flush=True,
        )
        reward_config = bridge.wait_for_configuration(timeout=args.callback_timeout)
        if reward_config.fingerprint != run_manifest['reward_configuration_fingerprint']:
            raise RuntimeError('AnyLogic runtime reward configuration differs from training checkpoint')
        if alp_contract is not None and alp_contract['reward_configuration_fingerprint'] != reward_config.fingerprint:
            raise RuntimeError('optional local audit disagrees with received runtime configuration')
        manifest.update(
            runtime_reward_configuration_received=True,
            reward_configuration=reward_config.to_dict(),
            reward_configuration_fingerprint=reward_config.fingerprint,
            runtime_reward_parameters=configuration_to_components(reward_config),
        )
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        with episodes_path.open("x", encoding="utf-8") as stream:
            for episode_index in range(args.episodes):
                record = _evaluate_episode(
                    env, model, deterministic=not args.stochastic
                )
                expected_row = expected[episode_index]
                if (record["run_index"], record["experiment_seed"]) != expected_row:
                    raise RuntimeError(
                        f"episode {episode_index + 1} metadata does not match manifest"
                    )
                records.append(record)
                stream.write(
                    json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n"
                )
                stream.flush()
                print(
                    f"Evaluated episode {episode_index + 1}/{args.episodes}: "
                    f"seed={record['experiment_seed']}, "
                    f"return={record['episode_return']:.6f}, "
                    f"length={record['length']}",
                    flush=True,
                )

        summary = _summary(records)
        (output_dir / "evaluation_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        manifest.update(status="complete", evaluation_summary=summary)
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (output_dir / "SUCCESS.json").write_text(
            json.dumps(
                {
                    "status": "complete",
                    "evaluation_id": evaluation_id,
                    "episodes": len(records),
                    "model_sha256": manifest["model_sha256"],
                    "seed_manifest_sha256": manifest["seed_manifest_sha256"],
                    'reward_contract_id': REWARD_CONTRACT_ID,
                    'reward_configuration': reward_config.to_dict(),
                    'reward_configuration_fingerprint': reward_config.fingerprint,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        completed = True
    except BaseException as exc:
        manifest.update(
            status="incomplete",
            error=f"{type(exc).__name__}: {exc}",
            completed_episodes=len(records),
        )
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        raise
    finally:
        env.close()
        server.stop(grace=2).wait()
    if completed:
        print(f"Evaluation complete: {output_dir}", flush=True)


if __name__ == "__main__":
    main()
