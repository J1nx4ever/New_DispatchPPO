"""Pair PPO holdout results with AnyLogic policy-2 terminal JSON records."""
from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Any


METRICS = {
    "ore_tons_shift": ("ore_tons_shift", "ore_tons_shift"),
    "grade_shift": ("shift_grade", "shift_grade"),
    "wait_vehicle_seconds": ("wait_vehicle_seconds", "wait_vehicle_seconds"),
}


def load_baseline_record(path: Path) -> dict[str, Any]:
    try:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line]
    except OSError as exc:
        raise SystemExit(f"cannot read baseline record: {path}") from exc
    if len(lines) != 1:
        raise SystemExit(f"expected exactly one terminal JSON record in {path}")
    try:
        record = json.loads(lines[0])
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid baseline JSON record: {path}") from exc
    if record.get("type") != "terminal" or record.get("policy") != 2:
        raise SystemExit(f"baseline record is not terminal output for policy 2: {path}")
    return record


def compare(ppo_path: Path, baseline_dir: Path) -> dict[str, Any]:
    try:
        ppo_records = [
            json.loads(line)
            for line in ppo_path.read_text(encoding="utf-8").splitlines()
            if line
        ]
    except OSError as exc:
        raise SystemExit(f"cannot read PPO evaluation records: {ppo_path}") from exc
    if not ppo_records:
        raise SystemExit("PPO evaluation records are empty")

    paired: list[dict[str, Any]] = []
    for ppo in ppo_records:
        run_index = ppo.get("run_index")
        seed = ppo.get("experiment_seed")
        if not isinstance(run_index, int) or not isinstance(seed, int):
            raise SystemExit("PPO episode record is missing run_index or seed")
        baseline_path = baseline_dir / f"policy2_run{run_index}_seed{seed}.jsonl"
        baseline = load_baseline_record(baseline_path)
        if (
            baseline.get("run_index") != run_index
            or baseline.get("experiment_seed") != seed
        ):
            raise SystemExit(f"baseline metadata does not match {baseline_path.name}")

        deltas: dict[str, float] = {}
        ppo_terminal = ppo.get("terminal_reward_components", {})
        for metric, (ppo_key, baseline_key) in METRICS.items():
            ppo_value = (
                ppo.get(ppo_key)
                if metric == "wait_vehicle_seconds"
                else ppo_terminal.get(ppo_key)
            )
            base_value = baseline.get(baseline_key)
            if ppo_value is None or base_value is None:
                raise SystemExit(f"missing paired metric {metric} for seed {seed}")
            ppo_value = float(ppo_value)
            base_value = float(base_value)
            if not math.isfinite(ppo_value) or not math.isfinite(base_value):
                raise SystemExit(f"non-finite paired metric {metric} for seed {seed}")
            deltas[metric] = ppo_value - base_value
        paired.append(
            {
                "run_index": run_index,
                "experiment_seed": seed,
                "ppo_episode_return": float(ppo["episode_return"]),
                "ppo_metrics": {
                    "ore_tons_shift": float(ppo_terminal["ore_tons_shift"]),
                    "grade_shift": float(ppo_terminal["shift_grade"]),
                    "wait_vehicle_seconds": float(ppo["wait_vehicle_seconds"]),
                },
                "baseline_metrics": {
                    "ore_tons_shift": float(baseline["ore_tons_shift"]),
                    "grade_shift": float(baseline["shift_grade"]),
                    "wait_vehicle_seconds": float(baseline["wait_vehicle_seconds"]),
                },
                "ppo_minus_baseline": deltas,
            }
        )

    metric_summary = {
        metric: {
            "mean_ppo_minus_baseline": statistics.fmean(
                row["ppo_minus_baseline"][metric] for row in paired
            ),
            "paired_deltas": [
                row["ppo_minus_baseline"][metric] for row in paired
            ],
        }
        for metric in METRICS
    }
    return {
        "baseline": "ALP policy 2 (grade-aware)",
        "episodes": len(paired),
        "paired_results": paired,
        "metric_summary": metric_summary,
        "interpretation": (
            "Positive delta means PPO produced a larger raw metric. "
            "Lower wait is preferable; ore throughput and grade must be judged "
            "against the frozen reward/operational targets, not in isolation."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ppo-episodes", type=Path, required=True)
    parser.add_argument("--baseline-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.ppo_episodes, args.baseline_dir)
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite comparison report: {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(f"Paired comparison written to {args.output}")


if __name__ == "__main__":
    main()
