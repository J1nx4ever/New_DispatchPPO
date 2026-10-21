from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Optional

import numpy as np
import stable_baselines3
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor

from .dispatch_bridge import DispatchCallbackBridge
from .dispatch_env import DispatchEnv
from .dispatch_service import create_server
from .episode_runner import ParameterVariationEpisodeRunner
from .episode_budget_ppo import EpisodeBudgetPPO
from .masked_policy import DispatchMaskedPolicy, POLICY_CONTRACT_ID
from .stage_statistics import StageStatisticsCallback
from .rollout_debug import RolloutDebug
from .reward_contract import (
    FROZEN_REWARD_PARAMETERS,
    REWARD_CONTRACT_ID,
    WINDOWS_PER_EPISODE,
)


from .observation_contract import OBSERVATION_SCHEMA_ID, OBSERVATION_SIZE, OBSERVATION_ALP_PATH
from .protocol_artifacts import verify_protocol_artifacts

class TrainingProgressCallback(BaseCallback):
    def __init__(
        self,
        target_episodes: int,
        transitions_path: Optional[Path],
        *,
        ppo_seed: int,
    ) -> None:
        super().__init__()
        self.target_episodes = target_episodes
        self.transitions_path = transitions_path
        self.completed_episodes = 0
        self.ppo_seed = int(ppo_seed)
        self._transitions_file: Optional[Any] = None
        self._stage_start_timesteps = 0

    def _on_training_start(self) -> None:
        self._stage_start_timesteps = self.num_timesteps
        if self.transitions_path is not None:
            self.transitions_path.parent.mkdir(parents=True, exist_ok=True)
            self._transitions_file = self.transitions_path.open(
                "x", encoding="utf-8", buffering=1
            )

    def _on_step(self) -> bool:
        infos = self.locals.get("infos", [])
        actions = np.asarray(self.locals.get("actions", [])).reshape(-1)
        rewards = np.asarray(self.locals.get("rewards", [])).reshape(-1)
        dones = np.asarray(self.locals.get("dones", [])).reshape(-1)

        for index, info in enumerate(infos):
            action = int(actions[index]) if index < len(actions) else None
            reward = float(rewards[index]) if index < len(rewards) else None
            done = bool(dones[index]) if index < len(dones) else False
            record = {
                "timesteps": self.num_timesteps,
                "stage_timesteps": self.num_timesteps - self._stage_start_timesteps,
                "stage_episode_index": self.completed_episodes + 1,
                "episode_id": info.get("episode_id"),
                "request_id": info.get("request_id"),
                "decision_sequence": info.get("decision_sequence"),
                "sim_time_seconds": info.get("sim_time_seconds"),
                "sim_time_delta_seconds": info.get("sim_time_delta_seconds"),
                "action": action,
                "previous_action_reported": info.get("previous_action"),
                "reward": reward,
                "transition_reward_raw": info.get("transition_reward_raw"),
                "reward_components": info.get("reward_components", {}),
                "done": done,
                "ppo_seed": self.ppo_seed,
                "experiment_run_index": info.get("experiment_run_index"),
                "experiment_seed": info.get("experiment_seed"),
                "reward_contract_id": info.get("reward_contract_id"),
                "observation_schema_id": info.get("observation_schema_id"),
                "closed_windows": info.get("closed_windows", []),
            }
            audit = getattr(self.model, "_rollout_debug", None)
            if audit is not None:
                record.update(audit.event(
                    "training_transition", info,
                    transition_index=self.num_timesteps,
                    action=action,
                    reward=reward,
                    done=done,
                ))
            if self._transitions_file is not None:
                self._transitions_file.write(
                    json.dumps(record, ensure_ascii=False) + "\n"
                )

            if done:
                self.completed_episodes += 1
                episode = info.get("episode", {})
                print(
                    "Completed episode "
                    f"{self.completed_episodes}/{self.target_episodes}: "
                    f"reward={episode.get('r', 'n/a')}, "
                    f"length={episode.get('l', 'n/a')}, "
                    f"episode_id={info.get('episode_id', 'n/a')}",
                    flush=True,
                )

        if self.completed_episodes >= self.target_episodes:
            self.model.request_episode_budget_stop()
        return True

    def _on_training_end(self) -> None:
        if self._transitions_file is not None:
            self._transitions_file.close()
            self._transitions_file = None



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ordinary PPO with serial AnyLogic Parameter Variation callbacks.")
    parser.add_argument('--episodes', type=int, required=True)
    parser.add_argument('--anylogic-seed-manifest', type=Path, required=True)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=50051)
    parser.add_argument('--seed', type=int, default=123)
    parser.add_argument('--callback-timeout', type=float, default=3600.0)
    parser.add_argument('--rpc-workers', type=int, default=8)
    parser.add_argument('--n-steps', type=int, choices=[128], default=128)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--learning-rate', type=float, default=3e-4)
    parser.add_argument('--ent-coef', type=float, default=0.01)
    parser.add_argument('--resume-model', type=Path, help='Completed physical-v3 masked-policy run only; legacy/unmasked models rejected.')
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--alp-path', type=Path, default=Path(__file__).resolve().parents[1] / OBSERVATION_ALP_PATH)
    parser.add_argument('--audit-rollouts', action='store_true', help='Opt in to per-request events and detailed rollout snapshots.')
    parser.add_argument('--record-transitions', action='store_true', help='Opt in to per-transition JSONL logging.')
    return parser.parse_args()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _git_value(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"
    return result.stdout.strip()

def _prepare_output_dir(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(
            f"--output-dir must be absent or empty; refusing to mix logs: {output_dir}"
        )
    output_dir.mkdir(parents=True, exist_ok=True)

def _load_seed_manifest(path: Path, episodes: int) -> list[tuple[int, int]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"seed manifest does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"seed manifest is not valid JSON: {path}") from exc
    if not isinstance(payload, list) or len(payload) != episodes:
        raise SystemExit(
            f"seed manifest must contain exactly {episodes} rows: {path}"
        )
    rows: list[tuple[int, int]] = []
    for position, item in enumerate(payload, 1):
        if not isinstance(item, dict):
            raise SystemExit(f"seed manifest row {position} must be an object")
        try:
            run_index_raw = item["run_index"]
            experiment_seed_raw = item["experiment_seed"]
        except KeyError as exc:
            raise SystemExit(
                f"seed manifest row {position} requires integer "
                "run_index and experiment_seed"
            ) from exc
        if (
            not isinstance(run_index_raw, int)
            or isinstance(run_index_raw, bool)
            or not isinstance(experiment_seed_raw, int)
            or isinstance(experiment_seed_raw, bool)
        ):
            raise SystemExit(
                f"seed manifest row {position} requires integer "
                "run_index and experiment_seed"
            )
        run_index = run_index_raw
        experiment_seed = experiment_seed_raw
        if run_index <= 0 or experiment_seed <= 0:
            raise SystemExit(
                f"seed manifest row {position} values must be positive"
            )
        rows.append((run_index, experiment_seed))
    if len({row[0] for row in rows}) != len(rows):
        raise SystemExit("seed manifest run_index values must be unique")
    if len({row[1] for row in rows}) != len(rows):
        raise SystemExit("seed manifest experiment_seed values must be unique")
    return rows

def _validate_resume_contract(resume_model: Path) -> None:
    parent = resume_model.resolve().parent
    manifest_path = parent / "run_manifest.json"
    success_path = parent / "SUCCESS.json"
    if not manifest_path.is_file() or not success_path.is_file():
        raise SystemExit(
            "--resume-model must come from a completed P0 run containing "
            "run_manifest.json and SUCCESS.json"
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        success = json.loads(success_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit("resume run metadata is not valid JSON") from exc
    for label, payload in (("run_manifest", manifest), ("SUCCESS", success)):
        if payload.get("reward_contract_id") != REWARD_CONTRACT_ID:
            raise SystemExit(f"resume {label} has an incompatible reward contract")
        if payload.get("policy_contract_id") != POLICY_CONTRACT_ID:
            raise SystemExit(f"resume {label} lacks the compatible masked policy contract")
    if manifest.get("observation_schema_id") != OBSERVATION_SCHEMA_ID:
        raise SystemExit("resume run has an incompatible observation schema")
    if success.get("model_sha256") != _sha256(resume_model.resolve()):
        raise SystemExit("resume model hash does not match SUCCESS.json")

def _manifest(args: argparse.Namespace, output_dir: Path) -> dict[str, Any]:
    repository_root = Path(__file__).resolve().parents[1]
    alp_path = args.alp_path.resolve()
    proto_path = repository_root / "proto-src/src/main/proto/dispatch.proto"
    proto_jar_path = repository_root / "dist/DRL-Dispatching-1.2.0.jar"
    seed_manifest_path = args.anylogic_seed_manifest.resolve()
    resume_model = args.resume_model.resolve() if args.resume_model else None
    return {
        "audit_run_id": str(uuid.uuid4()),
        "status": "running",
        "created_unix_seconds": time.time(),
        "command": [sys.executable, *sys.argv],
        "output_dir": str(output_dir.resolve()),
        "git_commit": _git_value("rev-parse", "HEAD"),
        "git_status_porcelain": _git_value("status", "--porcelain"),
        "python_version": platform.python_version(),
        "stable_baselines3_version": stable_baselines3.__version__,
        "reward_contract_id": REWARD_CONTRACT_ID,
        "observation_schema_id": OBSERVATION_SCHEMA_ID,
        "observation_dimension": OBSERVATION_SIZE,
        "alp_path": str(alp_path.resolve()),
        # A disk hash identifies the audited source, not the GUI's loaded model.
        "alp_runtime_verified": False,
        "windows_per_episode": WINDOWS_PER_EPISODE,
        "frozen_reward_parameters": FROZEN_REWARD_PARAMETERS,
        "alp_sha256": _sha256(alp_path),
        "proto_sha256": _sha256(proto_path),
        "proto_jar_sha256": _sha256(proto_jar_path),
        "anylogic_seed_manifest": str(seed_manifest_path),
        "anylogic_seed_manifest_sha256": _sha256(seed_manifest_path),
        "anylogic_episode_metadata": [
            {
                "run_index": run_index,
                "experiment_seed": experiment_seed,
            }
            for run_index, experiment_seed in _load_seed_manifest(
                seed_manifest_path, args.episodes
            )
        ],
        "episodes_requested": args.episodes,
        "ppo_seed": args.seed,
        "learning_rate": args.learning_rate,
        "ent_coef": args.ent_coef,
        "n_steps": args.n_steps,
        "batch_size": args.batch_size,
        "audit_rollouts": args.audit_rollouts,
        "record_transitions": args.record_transitions,
        "process_pid": os.getpid(),
        "algorithm": "PPO",
        "policy_class": "python.masked_policy.DispatchMaskedPolicy",
        "policy_contract_id": POLICY_CONTRACT_ID,
        "action_mask_indices": [19, 20, 21, 22],
        "ppo_configuration": dict(n_epochs=10, gamma=.995, gae_lambda=.95,
            clip_range=.2, clip_range_vf=None, max_grad_norm=.5,
            normalize_advantage=True, net_arch=dict(pi=[128,128], vf=[128,128]), target_kl=None),
        "protected_core_sha256": _sha256(repository_root / "python/episode_budget_ppo.py"),
        "resume_model": str(resume_model) if resume_model else None,
        "resume_model_sha256": _sha256(resume_model) if resume_model else None,
    }

def main() -> None:
    args = parse_args()
    if args.episodes <= 0:
        raise SystemExit("--episodes must be positive")
    if args.n_steps < 2 or args.batch_size <= 1 or args.batch_size > args.n_steps:
        raise SystemExit("require n_steps >= 2 and 1 < batch_size <= n_steps")
    if args.callback_timeout <= 0:
        raise SystemExit("--callback-timeout must be positive")
    if args.learning_rate <= 0:
        raise SystemExit("--learning-rate must be positive")
    if args.ent_coef < 0:
        raise SystemExit("--ent-coef must be non-negative")
    if args.resume_model is not None and not args.resume_model.is_file():
        raise SystemExit(
            f"--resume-model does not exist or is not a file: "
            f"{args.resume_model}"
        )
    if args.resume_model is not None:
        _validate_resume_contract(args.resume_model)
    expected_episode_metadata = _load_seed_manifest(
        args.anylogic_seed_manifest, args.episodes
    )

    repository_root = Path(__file__).resolve().parents[1]
    verify_protocol_artifacts(repository_root)
    from .alp_audit import validate_alp_contract
    validate_alp_contract(args.alp_path)

    run_stamp = time.strftime("%Y%m%d-%H%M%S")
    output_dir = args.output_dir or Path("runs") / f"ppo-{run_stamp}"
    _prepare_output_dir(output_dir)
    manifest = _manifest(args, output_dir)
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "tensorboard").mkdir(exist_ok=True)

    rollout_debug = RolloutDebug(output_dir / "rollout_audit", source_kind="real_anylogic",
                     audit_run_id=manifest["audit_run_id"],
                     seed_manifest_path=args.anylogic_seed_manifest,
                     capture_rollouts=args.audit_rollouts,
                     expected_episode_identities=[
                         {"run_index": i, "experiment_seed": s,
                          "episode_id": f"{REWARD_CONTRACT_ID}-run-{i}-seed-{s}"}
                         for i, s in expected_episode_metadata]) if args.audit_rollouts else None
    run_completed = False
    bridge = DispatchCallbackBridge(
        expected_episode_metadata=expected_episode_metadata,
        rollout_audit=rollout_debug,
        window_grade_bounds=True,
    )
    server = create_server(
        bridge,
        host=args.host,
        port=args.port,
        max_workers=args.rpc_workers,
    )
    server.start()

    base_env = DispatchEnv(
        bridge,
        runner=ParameterVariationEpisodeRunner(total_episodes=args.episodes),
        callback_timeout=args.callback_timeout,
    )
    env = Monitor(base_env, filename=str(output_dir / "monitor.csv"))

    progress = TrainingProgressCallback(
        target_episodes=args.episodes,
        transitions_path=output_dir / "transitions.jsonl" if args.record_transitions else None,
        ppo_seed=args.seed,
    )
    callbacks: list[BaseCallback] = [StageStatisticsCallback(output_dir), progress]
    model: Optional[EpisodeBudgetPPO] = None
    try:
        if args.resume_model is not None:
            print(f"Loading PPO model from {args.resume_model}", flush=True)
            model = EpisodeBudgetPPO.load(
                args.resume_model,
                env=env,
                learning_rate=args.learning_rate,
                n_steps=128,
                batch_size=args.batch_size,
                ent_coef=args.ent_coef,
                seed=args.seed,
                tensorboard_log=str(output_dir / "tensorboard"),
                device="auto",
            )
            if type(model.policy) is not DispatchMaskedPolicy:
                raise RuntimeError('Checkpoint does not contain DispatchMaskedPolicy')
        else:
            model = EpisodeBudgetPPO(
                DispatchMaskedPolicy,
                env,
                learning_rate=args.learning_rate,
                n_steps=args.n_steps,
                batch_size=args.batch_size,
                n_epochs=10,
                gamma=0.995,
                gae_lambda=0.95,
                clip_range=0.2,
                ent_coef=args.ent_coef,
                policy_kwargs={
                    "net_arch": {"pi": [128, 128], "vf": [128, 128]}
                },
                tensorboard_log=str(output_dir / "tensorboard"),
                seed=args.seed,
                verbose=1,
            )

        model._rollout_debug = rollout_debug
        print(
            f"Dispatch gRPC listening on {args.host}:{args.port}. "
            f"Start AnyLogic RL_Training with {args.episodes} replications; "
            f"outputs: {output_dir}",
            flush=True,
        )
        model.learn(
            total_timesteps=2**62,
            callback=callbacks,
            tb_log_name="dispatch_ppo",
            reset_num_timesteps=args.resume_model is None,
        )
        if progress.completed_episodes != args.episodes:
            raise RuntimeError(
                f"training stopped with {progress.completed_episodes} completed episodes; "
                f"expected {args.episodes}"
            )
        model.save(output_dir / "dispatch_ppo")
        finish_audit = model.finish_audit()
        manifest.update(status="complete", training_finish=finish_audit)
        (output_dir / "run_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (output_dir / "training_finish.json").write_text(
            json.dumps(finish_audit, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        model_path = output_dir / "dispatch_ppo.zip"
        success = {
            "policy_contract_id": POLICY_CONTRACT_ID,
            "status": "complete",
            "audit_run_id": manifest["audit_run_id"],
            "process_pid": os.getpid(),
            "completed_episodes": progress.completed_episodes,
            "model_sha256": _sha256(model_path),
            "final_num_timesteps": model.num_timesteps,
            "training_finish": finish_audit,
            "reward_contract_id": REWARD_CONTRACT_ID,
            "observation_schema_id": OBSERVATION_SCHEMA_ID,
            "anylogic_seed_manifest_sha256": _sha256(
                args.anylogic_seed_manifest.resolve()
            ),
        }
        (output_dir / "SUCCESS.json").write_text(
            json.dumps(success, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        run_completed = True
        print(f"Saved PPO model to {output_dir / 'dispatch_ppo.zip'}", flush=True)
    finally:
        env.close()
        server.stop(grace=2).wait()
        if rollout_debug is not None:
            rollout_debug.close(status="complete" if run_completed else "incomplete")

if __name__ == "__main__":
    main()
