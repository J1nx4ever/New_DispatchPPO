"""ALP physical-v4 reward and time-window contract shared by training code/tests."""

from __future__ import annotations

from math import isclose, isfinite
from typing import Any, Mapping
from .reward_config import RewardConfiguration

ADDITIVE_COMPONENTS = ("wait", "grade_action", "grade_2h", "grade_shift", "production", "waste")


REWARD_CONTRACT_ID = "dispatch-reward-physical-v4"
SHIFT_SECONDS = 28_800.0
WINDOW_SECONDS = 7_200.0
WINDOWS_PER_EPISODE = 4

GRADE_GAP_MIN = -0.01
GRADE_GAP_MAX = 0.01

FROZEN_REWARD_PARAMETERS: dict[str, float] = {
    "num_trucks": 9.0,
    "target_grade": 0.27,
    "grade_lower": 0.26,
    "grade_upper": 0.28,
    "target_waste_tons_shift": 4000.0,
    "wait_ref_seconds": 200.0,
    "target_ore_tons_2h": 4_000.0,
    "target_ore_tons_shift": 16_000.0,
    "w_wait": 1.0,
    "w_grade_2h": 1.0,
    "w_grade_shift": 6.0,
    "w_production": 4.0,
    "w_grade_action": 0.15,
    "grade_prior_tons": 20_000.0,
    "grade_action_delta_clip": 0.10,
}


def grade_reward(grade_gap: float) -> float:
    """ALP gradeDeviation/gradeReward; symmetric 0.01 allowance at current settings."""
    target = FROZEN_REWARD_PARAMETERS["target_grade"]
    allowance = (FROZEN_REWARD_PARAMETERS["grade_upper"] - target if grade_gap < 0
                 else target - FROZEN_REWARD_PARAMETERS["grade_lower"])
    deviation = min(3.0, abs(grade_gap) / allowance)
    return max(-1.0, min(1.0, 1.0 - deviation))


def violation_upper(grade_gap: float) -> bool:
    return grade_gap < GRADE_GAP_MIN


def violation_lower(grade_gap: float) -> bool:
    return grade_gap > GRADE_GAP_MAX


def window_violated(grade_gap: float) -> bool:
    return violation_upper(grade_gap) or violation_lower(grade_gap)


def window_summary_to_dict(summary: Any) -> dict[str, Any]:
    return {
        "window_index": int(summary.window_index),
        "window_start_seconds": float(summary.window_start_seconds),
        "window_end_seconds": float(summary.window_end_seconds),
        "ore_tons": float(summary.ore_tons),
        "metal_tons": float(summary.metal_tons),
        "grade": float(summary.grade),
        "grade_gap": float(summary.grade_gap),
        "grade_reward_raw": float(summary.grade_reward_raw),
        "grade_reward_weighted": float(summary.grade_reward_weighted),
        "violation_upper": bool(summary.violation_upper),
        "violation_lower": bool(summary.violation_lower),
    }


def validate_window_summary(summary: Mapping[str, Any], *, grade_bounds: bool = True) -> None:
    numeric_fields = (
        "window_start_seconds",
        "window_end_seconds",
        "ore_tons",
        "metal_tons",
        "grade",
        "grade_gap",
        "grade_reward_raw",
        "grade_reward_weighted",
    )
    if not all(isfinite(float(summary[field])) for field in numeric_fields):
        raise ValueError("window summary contains NaN or infinity")

    index = int(summary["window_index"])
    if not 0 <= index < WINDOWS_PER_EPISODE:
        raise ValueError(f"window_index must be in [0, 3], got {index}")

    expected_start = index * WINDOW_SECONDS
    expected_end = (index + 1) * WINDOW_SECONDS
    if not isclose(float(summary["window_start_seconds"]), expected_start, abs_tol=1e-6):
        raise ValueError("window_start_seconds does not match window_index")
    if not isclose(float(summary["window_end_seconds"]), expected_end, abs_tol=1e-6):
        raise ValueError("window_end_seconds does not match window_index")

    gap = float(summary["grade_gap"])
    ore_tons = float(summary["ore_tons"])
    metal_tons = float(summary["metal_tons"])
    grade = float(summary["grade"])
    if ore_tons < 0.0 or metal_tons < 0.0 or metal_tons > ore_tons + 1e-6:
        raise ValueError("window tonnages must be non-negative")
    expected_grade = metal_tons / ore_tons if ore_tons > 0.0 else 0.0
    expected_gap = FROZEN_REWARD_PARAMETERS["target_grade"] - expected_grade
    if not isclose(grade, expected_grade, abs_tol=1e-9):
        raise ValueError("grade disagrees with ore_tons and metal_tons")
    if not isclose(gap, expected_gap, abs_tol=1e-9):
        raise ValueError("grade_gap disagrees with grade")
    expected_upper = ore_tons > 0.0 and grade > 0.28 + 1e-12
    expected_lower = ore_tons <= 0.0 or grade < 0.26 - 1e-12
    if bool(summary["violation_upper"]) != expected_upper:
        raise ValueError("violation_upper disagrees with grade_gap")
    if bool(summary["violation_lower"]) != expected_lower:
        raise ValueError("violation_lower disagrees with grade_gap")
    if not isclose(float(summary["grade_reward_raw"]), grade_reward(gap), abs_tol=1e-9):
        raise ValueError("grade_reward_raw disagrees with frozen reward contract")
    expected_weighted = grade_reward(gap) * FROZEN_REWARD_PARAMETERS["w_grade_2h"]
    if not isclose(
        float(summary["grade_reward_weighted"]), expected_weighted, abs_tol=1e-9
    ):
        raise ValueError("grade_reward_weighted disagrees with frozen reward contract")


def validate_reward_accounting(
    transition_reward: float,
    reward_components: Mapping[str, Any],
    closed_windows: list[Mapping[str, Any]],
    *, config: RewardConfiguration | None = None,
) -> None:
    if not isfinite(float(transition_reward)) or not all(isfinite(float(v)) for v in reward_components.values()):
        raise ValueError("reward or diagnostic component contains NaN or infinity")
    config = config or RewardConfiguration()
    required = set(ADDITIVE_COMPONENTS)
    for window in closed_windows:
        validate_window_summary(window)
    missing = required.difference(reward_components)
    if missing:
        raise ValueError(f"reward_components missing frozen fields: {sorted(missing)}")
    action_reward = float(reward_components["grade_action"])
    enabled = reward_components.get("grade_action_enabled")
    if enabled not in (0.0, 1.0) or bool(enabled) != config.grade_action_enabled:
        raise ValueError("grade_action_enabled disagrees with reward configuration")
    if not config.grade_action_enabled and action_reward != 0.0:
        raise ValueError("grade_action must be exactly zero when disabled")
    if not -0.015000001 <= action_reward <= 0.015000001:
        raise ValueError("grade_action outside ALP clipping bounds")
    component_sum = sum(float(reward_components[field]) for field in required)
    if not isclose(float(transition_reward), component_sum, abs_tol=1e-8):
        raise ValueError("transition_reward disagrees with frozen reward component sum")

    if "delta_wait_vehicle_seconds" in reward_components:
        delta_wait = float(reward_components["delta_wait_vehicle_seconds"])
        if not isfinite(delta_wait) or delta_wait < 0.0:
            raise ValueError("delta_wait_vehicle_seconds must be finite and non-negative")
        mean_wait = delta_wait / FROZEN_REWARD_PARAMETERS["num_trucks"]
        normalized = max(
            0.0,
            min(1.0, mean_wait / FROZEN_REWARD_PARAMETERS["wait_ref_seconds"]),
        )
        expected_wait = -FROZEN_REWARD_PARAMETERS["w_wait"] * normalized
        if not isclose(
            float(reward_components["wait"]), expected_wait, abs_tol=1e-9
        ):
            raise ValueError("wait disagrees with delta_wait_vehicle_seconds")

    expected_window_reward = sum(
        float(window["grade_reward_weighted"]) for window in closed_windows
    )
    if not isclose(
        float(reward_components["grade_2h"]), expected_window_reward, abs_tol=1e-9
    ):
        raise ValueError("grade_2h disagrees with closed_windows weighted rewards")

    if "grade_gap_shift" in reward_components:
        terminal_required = {
            "grade_shift_reward_raw",
            "ore_tons_shift",
            "production_fraction_raw",
            "production_shortfall",
        }
        terminal_missing = terminal_required.difference(reward_components)
        if terminal_missing:
            raise ValueError(
                "terminal reward_components missing frozen fields: "
                f"{sorted(terminal_missing)}"
            )
        if "shift_grade" in reward_components and not isclose(float(reward_components["shift_grade"]), FROZEN_REWARD_PARAMETERS["target_grade"] - float(reward_components["grade_gap_shift"]), abs_tol=1e-9):
            raise ValueError("shift_grade disagrees with grade_gap_shift")
        gap = float(reward_components["grade_gap_shift"])
        raw = float(reward_components["grade_shift_reward_raw"])
        weighted = float(reward_components["grade_shift"])
        if not isclose(raw, grade_reward(gap), abs_tol=1e-9):
            raise ValueError("grade_shift_reward_raw disagrees with frozen reward contract")
        expected = raw * FROZEN_REWARD_PARAMETERS["w_grade_shift"]
        if not isclose(weighted, expected, abs_tol=1e-9):
            raise ValueError("grade_shift disagrees with frozen reward contract")

        ore_tons = float(reward_components["ore_tons_shift"])
        if not isfinite(ore_tons) or ore_tons < 0.0:
            raise ValueError("ore_tons_shift must be finite and non-negative")
        fraction = ore_tons / FROZEN_REWARD_PARAMETERS["target_ore_tons_shift"]
        shortfall = max(0.0, min(1.0, 1.0 - fraction))
        production = -FROZEN_REWARD_PARAMETERS["w_production"] * shortfall
        if not isclose(
            float(reward_components["production_fraction_raw"]), fraction, abs_tol=1e-9
        ):
            raise ValueError("production_fraction_raw disagrees with ore_tons_shift")
        if not isclose(
            float(reward_components["production_shortfall"]), shortfall, abs_tol=1e-9
        ):
            raise ValueError("production_shortfall disagrees with ore_tons_shift")
        if not isclose(float(reward_components["production"]), production, abs_tol=1e-9):
            raise ValueError("production disagrees with frozen reward contract")

    if "grade_gap_shift" in reward_components:
        required_waste = {"waste_tons_shift", "waste_target_tons", "waste_fraction_raw", "waste_shortfall"}
        if required_waste.difference(reward_components):
            raise ValueError("terminal reward missing waste diagnostics")
        tons = float(reward_components["waste_tons_shift"])
        target = float(reward_components["waste_target_tons"])
        if tons < 0 or not isclose(target, config.waste_target_tons, abs_tol=1e-9):
            raise ValueError("waste tonnage/target disagrees with reward configuration")
        fraction = tons / target if target > 0 else 0.0
        shortfall = max(0.0, min(1.0, 1.0-fraction)) if target > 0 else 0.0
        expected = -config.waste_shortfall_weight * shortfall
        for key, value in [("waste_fraction_raw", fraction),("waste_shortfall", shortfall),("waste", expected)]:
            if not isclose(float(reward_components[key]), value, abs_tol=1e-9):
                raise ValueError(f"{key} disagrees with waste shortfall formula")
