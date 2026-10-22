import json

import numpy as np
import pytest

from python.evaluate import _evaluate_episode, _load_seed_manifest, _summary
from python.compare_heldout import compare


class FakeModel:
    def predict(self, observation, deterministic=True):
        assert deterministic
        mask = observation[19:23]
        return np.asarray([int(np.flatnonzero(mask)[0])]), None


class FakeEnv:
    def __init__(self):
        self.steps = 0

    def reset(self):
        observation = np.zeros(1519, dtype=np.float32)
        observation[19] = 1
        return observation, {
            "episode_id": "holdout-1",
            "experiment_run_index": 21,
            "experiment_seed": 202610160031,
            "action_mask": [1, 0, 0, 0],
        }

    def step(self, action):
        assert action == [0, 1][self.steps]
        self.steps += 1
        terminal = self.steps == 2
        observation = np.zeros(1519, dtype=np.float32)
        if not terminal:
            observation[20] = 1
        info = {
            "episode_id": "holdout-1",
            "action_mask": [0, 0, 0, 0] if terminal else [0, 1, 0, 0],
            "reward_components": {
                "delta_wait_vehicle_seconds": 10.0,
                "ore_tons_shift": 100.0 if terminal else 0.0,
                "shift_grade": 0.27 if terminal else 0.0,
            },
            "closed_windows": [],
        }
        return observation, 1.0, terminal, False, info


def test_load_seed_manifest_rejects_duplicates(tmp_path):
    path = tmp_path / "seeds.json"
    path.write_text(
        json.dumps(
            [
                {"run_index": 21, "experiment_seed": 31},
                {"run_index": 21, "experiment_seed": 32},
            ]
        )
    )
    with pytest.raises(SystemExit, match="run_index values must be unique"):
        _load_seed_manifest(path, 2)


def test_evaluate_episode_collects_metrics_and_mask_counts():
    record = _evaluate_episode(FakeEnv(), FakeModel(), deterministic=True)
    assert record["length"] == 2
    assert record["episode_return"] == 2.0
    assert record["action_counts"] == [1, 1, 0, 0]
    assert record["decision_mask_counts"] == {"1000": 1, "0100": 1}
    assert record["terminal_reward_components"]["ore_tons_shift"] == 100.0
    assert _summary([record])["wait_vehicle_seconds"]["mean"] == 20.0


def test_compare_heldout_pairs_by_seed(tmp_path):
    ppo = tmp_path / "ppo.jsonl"
    ppo.write_text(
        json.dumps(
            {
                "run_index": 21,
                "experiment_seed": 202610160031,
                "episode_return": -2.0,
                "wait_vehicle_seconds": 90.0,
                "terminal_reward_components": {
                    "ore_tons_shift": 1200.0,
                    "shift_grade": 0.27,
                },
            }
        )
        + "\n"
    )
    baseline_dir = tmp_path / "baseline"
    baseline_dir.mkdir()
    (baseline_dir / "policy2_run21_seed202610160031.jsonl").write_text(
        json.dumps(
            {
                "type": "terminal",
                "policy": 2,
                "run_index": 21,
                "experiment_seed": 202610160031,
                "ore_tons_shift": 1000.0,
                "shift_grade": 0.26,
                "wait_vehicle_seconds": 110.0,
            }
        )
        + "\n"
    )
    result = compare(ppo, baseline_dir)
    assert result["metric_summary"]["ore_tons_shift"]["mean_ppo_minus_baseline"] == 200.0
    assert result["metric_summary"]["wait_vehicle_seconds"]["mean_ppo_minus_baseline"] == -20.0
