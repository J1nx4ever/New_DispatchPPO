"""Stage-local reporting only; no policy, optimizer, rollout or RNG changes.

SB3 2.9.0 load() restores checkpoint attributes before _setup_model() and then
restores policy/optimizer state. _setup_learn(reset_num_timesteps=False) retains
existing episode deques. on_training_start runs AFTER that setup, BEFORE steps.
Only ep_info_buffer and ep_success_buffer are episode-statistics deques; do not
clear the PPO rollout buffer, optimizer state, or cumulative counters.
"""
from __future__ import annotations

import csv
import json
import math
from collections import deque
from pathlib import Path

import stable_baselines3
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.logger import CSVOutputFormat
from .reward_contract import ADDITIVE_COMPONENTS


def clear_stage_episode_statistics(model) -> None:
    """Preserve deque identity/maxlen when present; initialize missing deques."""
    if stable_baselines3.__version__ != "2.9.0":
        raise RuntimeError("Stage statistics reset requires audited SB3 2.9.0")
    for name in ("ep_info_buffer", "ep_success_buffer"):
        buffer = getattr(model, name)
        if buffer is None:
            setattr(model, name, deque(maxlen=model._stats_window_size))
        elif isinstance(buffer, deque):
            buffer.clear()
        else:
            raise TypeError(f"{name} must be a deque or None")


class StageStatisticsCallback(BaseCallback):
    """Exact transition-based episode returns, separate from rounded Monitor.r.

    raw_return sums info.transition_reward_raw (AnyLogic's reported reward).
    training_return sums callback rewards before SB3 time-limit bootstrap.
    Only the six additive rewards are summed as components; configuration flags,
    terminal physical metrics and closed windows are recorded separately.
    Rolling metrics always use at most the last 100 COMPLETED stage episodes.
    """
    def __init__(self, output_dir: Path, reward_config=None, run_metadata=None):
        super().__init__()
        self.output_dir = output_dir
        self.reward_config = reward_config
        self.run_metadata = dict(run_metadata or {})
        self._windows = []
        self._wait_integral = 0.0
        self._episode_csv = None
        self.start_timesteps = 0
        self.stage_timesteps = 0
        self.episodes = []
        self._raw_rewards = []
        self._training_rewards = []
        self._components = {}
        self._episode_file = None
        self._csv = None

    def _on_training_start(self):
        clear_stage_episode_statistics(self.model)
        self.start_timesteps = self.num_timesteps
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._episode_file = (self.output_dir / "stage_episodes.jsonl").open(
            "x", encoding="utf-8", buffering=1
        )
        csv_path = self.output_dir / "stage_metrics.csv"
        # CSVOutputFormat opens w+: refuse to overwrite previous stage artifacts.
        if csv_path.exists():
            raise FileExistsError(csv_path)
        self._csv = CSVOutputFormat(str(csv_path))
        self.logger.output_formats.append(self._csv)
        self._episode_csv = (self.output_dir / 'episodes.csv').open('x', encoding='utf-8', newline='')
        self._episode_writer = csv.DictWriter(self._episode_csv, fieldnames=[
            'run_id','ppo_seed','ablation_variant','episode','episode_id','length','raw_return','training_return','base_return',
            'grade_action_enabled','wait','grade_action','grade_2h','grade_shift','production','waste',
            'ore_tons_shift','shift_grade','waste_tons_shift','waste_shortfall',
            'wait_vehicle_seconds','window_violation_rate','reward_configuration_fingerprint'])
        self._episode_writer.writeheader()
        self._record_metrics()  # Stage counters start at zero, cumulative stays intact.

    def _on_step(self):
        self.stage_timesteps = self.num_timesteps - self.start_timesteps
        for index, info in enumerate(self.locals["infos"]):
            training_reward = float(self.locals["rewards"][index])
            raw_reward = info.get("transition_reward_raw")
            self._raw_rewards.append(training_reward if raw_reward is None else float(raw_reward))
            self._training_rewards.append(training_reward)
            components = info.get('reward_components', {})
            for key in ADDITIVE_COMPONENTS:
                self._components.setdefault(key, []).append(float(components.get(key,0)))
            self._wait_integral += float(components.get('delta_wait_vehicle_seconds',0))
            self._windows.extend(info.get('closed_windows', []))
            if self.locals["dones"][index]:
                record = {
                    "stage_episode_index": len(self.episodes) + 1,
                    "stage_timesteps": self.stage_timesteps,
                    "timesteps": self.num_timesteps,
                    "episode_id": info.get("episode_id"),
                    "length": len(self._raw_rewards),
                    "raw_return": math.fsum(self._raw_rewards),
                    "training_return": math.fsum(self._training_rewards),
                    "reward_components": {k: math.fsum(v) for k, v in self._components.items()},
                }
                terminal = {k:float(components[k]) for k in (
                    'ore_tons_shift','shift_grade','grade_gap_shift','production_fraction_raw',
                    'production_shortfall','waste_tons_shift','waste_target_tons',
                    'waste_fraction_raw','waste_shortfall') if k in components}
                violations = sum(bool(w['violation_upper'] or w['violation_lower']) for w in self._windows)
                record.update(run_id=self.run_metadata.get('audit_run_id'),
                              ppo_seed=self.run_metadata.get('ppo_seed'),
                              ablation_variant=self.reward_config.variant if self.reward_config else None)
                record.update(
                    base_return=record['raw_return']-record['reward_components']['grade_action'],
                    grade_action_enabled=(self.reward_config.grade_action_enabled if self.reward_config
                                          else components.get('grade_action_enabled')),
                    reward_configuration_fingerprint=self.reward_config.fingerprint if self.reward_config else None,
                    terminal_metrics=terminal,closed_windows=list(self._windows),
                    wait_vehicle_seconds=self._wait_integral,
                    window_violation_rate=violations/len(self._windows) if self._windows else None)
                flat=dict(run_id=record['run_id'],ppo_seed=record['ppo_seed'],ablation_variant=record['ablation_variant'],episode=record['stage_episode_index'],episode_id=record['episode_id'],
                          length=record['length'],raw_return=record['raw_return'],training_return=record['training_return'],
                          base_return=record['base_return'],grade_action_enabled=record['grade_action_enabled'],
                          wait_vehicle_seconds=self._wait_integral,window_violation_rate=record['window_violation_rate'],
                          reward_configuration_fingerprint=record['reward_configuration_fingerprint'],
                          **record['reward_components'])
                flat.update({k:terminal.get(k) for k in ('ore_tons_shift','shift_grade','waste_tons_shift','waste_shortfall')})
                self._episode_writer.writerow(flat)
                self._episode_csv.flush()
                self.episodes.append(record)
                self._episode_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                self._raw_rewards.clear()
                self._training_rewards.clear()
                self._components.clear()
                self._windows.clear()
                self._wait_integral = 0.0
        self._record_counters()
        return True

    def _on_rollout_end(self):
        self._record_metrics()

    def summary(self):
        count = len(self.episodes)
        window = self.episodes[-100:]
        result = {
            "start_num_timesteps": self.start_timesteps,
            "timesteps": self.num_timesteps,
            "stage_timesteps": self.stage_timesteps,
            "stage_episode_index": count,
            "completed_episodes": count,
            "rolling_window_limit": 100,
            "rolling_episode_count": len(window),
            "incomplete_episode_transitions": len(self._raw_rewards),
            "reward_configuration": self.reward_config.to_dict() if self.reward_config else None,
        }
        if count:
            for name in ("raw_return", "training_return"):
                result[f"{name}_mean_all"] = math.fsum(e[name] for e in self.episodes) / count
                result[f"{name}_mean_last_100"] = math.fsum(e[name] for e in window) / len(window)
            result['base_return_mean_all'] = math.fsum(e['base_return'] for e in self.episodes)/count
            rates=[e['window_violation_rate'] for e in self.episodes if e['window_violation_rate'] is not None]
            result['window_violation_rate_mean_all'] = math.fsum(rates)/len(rates) if rates else None
            result['terminal_metrics_mean_all'] = {
                k:math.fsum(e['terminal_metrics'][k] for e in self.episodes if k in e['terminal_metrics']) /
                  sum(k in e['terminal_metrics'] for e in self.episodes)
                for k in sorted({k for e in self.episodes for k in e['terminal_metrics']})}
            keys = sorted({k for e in self.episodes for k in e["reward_components"]})
            result["reward_components_mean_all"] = {
                k: math.fsum(e["reward_components"].get(k, 0.0) for e in self.episodes) / count for k in keys
            }
            result["reward_components_mean_last_100"] = {
                k: math.fsum(e["reward_components"].get(k, 0.0) for e in window) / len(window) for k in keys
            }
        return result

    def _record_counters(self):
        self.logger.record("stage/timesteps", self.stage_timesteps)
        self.logger.record("stage/episode_index", len(self.episodes))
        self.logger.record("stage/rolling_episode_count", min(100, len(self.episodes)))

    def _record_metrics(self):
        summary = self.summary()
        self._record_counters()
        if self.reward_config is not None:
            self.logger.record('config/grade_action_enabled',int(self.reward_config.grade_action_enabled),exclude=('stdout','log'))
            self.logger.record('config/waste_shortfall_weight',self.reward_config.waste_shortfall_weight,exclude=('stdout','log'))
        for key in ("raw_return_mean_all", "raw_return_mean_last_100",
                    "training_return_mean_all", "training_return_mean_last_100", "base_return_mean_all"):
            if key in summary:
                self.logger.record(f"stage/{key}", summary[key])
        for key, value in summary.get('terminal_metrics_mean_all', {}).items():
            self.logger.record(f'physical/{key}', value, exclude=('stdout','log'))
        if summary.get('window_violation_rate_mean_all') is not None:
            self.logger.record('physical/window_violation_rate',summary['window_violation_rate_mean_all'],exclude=('stdout','log'))
        for suffix in ("all", "last_100"):
            for key, value in summary.get(f"reward_components_mean_{suffix}", {}).items():
                # SB3 2.9.0 HumanOutputFormat truncates labels at 36 characters;
                # long component names' all/last_100 suffixes then collide.
                # Keep full, unchanged names in CSV/TensorBoard, and keep the
                # console table focused on stage counters and return means.
                self.logger.record(
                    f"stage/reward_components/{key}_mean_{suffix}", value,
                    exclude=("stdout", "log"),
                )

    def _on_training_end(self):
        # Final episode was aggregated in on_step. Flush stage metrics AFTER
        # the already-accepted final PPO update/logger flush, without altering it.
        try:
            self._record_metrics()
            self.logger.dump(step=self.num_timesteps)
            with (self.output_dir / "stage_statistics.json").open("x", encoding="utf-8") as file:
                file.write(json.dumps(self.summary(), ensure_ascii=False, indent=2) + "\n")
        finally:
            if self._episode_file is not None:
                self._episode_file.close()
            if self._episode_csv is not None:
                self._episode_csv.close()
            if self._csv is not None:
                self._csv.close()
                self.logger.output_formats.remove(self._csv)
