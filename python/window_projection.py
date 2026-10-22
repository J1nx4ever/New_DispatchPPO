"""V4 / dispatch.physical.v3: FIFO-only (P0) time-window projection.

Only uses the *current* 1519-D public observation and fixed, audited V4
constants. No AnyLogic future-state access, no simulation-state mutation.

IMPORTANT: P0 projects the material *already in crusher FIFO*, not all
committed material. P1--P3 are NOT implemented here. Do not describe the
result as the final F1 committed-material projection in a research paper.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
from .observation_contract import FIELD_NAMES

PARAMETERS = json.loads(Path(__file__).with_name('window_projection_parameters.json').read_text())
PROJECTION_CONTRACT_ID = PARAMETERS['projection_contract_id']
RAW_DIM = PARAMETERS['raw_dimension']
SHIFT_SECONDS = PARAMETERS['shift_seconds']
WINDOW_SECONDS = PARAMETERS['window_seconds']
WINDOW_COUNT = PARAMETERS['window_count']
PROJECTION_SCALE_TONS = PARAMETERS['feature_scale_tons']
FIFO_SLOTS = PARAMETERS['fifo_slots']
FIFO_BASE = PARAMETERS['fifo_base']
FIFO_STRIDE = PARAMETERS['fifo_stride']
FIFO_TONS_SCALE = PARAMETERS['fifo_tons_scale']
CRUSHER_RATE_SCALE_TPH = PARAMETERS['crusher_rate_scale_tph']
BUFFER_TONS_INDEX = 1300
CRUSHER_RATE_INDEX = 1304
SHIFT_ELAPSED_INDEX = 0
SHIFT_REMAINING_INDEX = 1
WINDOW_INDEX = 2
WINDOW_REMAINING_INDEX = 3
TERMINAL_INDEX = 17

# Every P0 offset is cross-checked against the audited local observation schema.
EXPECTED_FIELDS = {
    0: "global.shiftElapsed",
    1: "global.shiftRemaining",
    2: "global.windowIndex",
    3: "global.windowRemaining",
    17: "global.terminal",
    1300: "dump.0.bufferTons",
    1304: "dump.0.crusherRate",
    1391: "fifo.0.valid",
    1392: "fifo.0.tons",
    1393: "fifo.0.grade",
    1436: "fifo.15.valid",
    1437: "fifo.15.tons",
    1438: "fifo.15.grade",
}
for _slot in range(FIFO_SLOTS):
    for _offset, _suffix in enumerate(('valid', 'tons', 'grade')):
        EXPECTED_FIELDS[FIFO_BASE + _slot * FIFO_STRIDE + _offset] = f'fifo.{_slot}.{_suffix}'


def assert_schema_fields(field_names: Iterable[str]) -> None:
    names = tuple(field_names)
    if len(names) != RAW_DIM:
        raise ValueError(f"expected {RAW_DIM} schema names, got {len(names)}")
    for i, wanted in EXPECTED_FIELDS.items():
        if names[i] != wanted:
            raise ValueError(f"index {i}: expected {wanted!r}, got {names[i]!r}")


assert_schema_fields(FIELD_NAMES)


@dataclass(frozen=True)
class Batch:
    remaining_tons: float
    grade_fraction: float


@dataclass(frozen=True)
class Projection:
    current_window: int
    produced_tons_by_window: tuple[float, float, float, float]
    produced_metal_by_window: tuple[float, float, float, float]
    remaining_after_shift_tons: float
    initial_fifo_tons: float
    initial_fifo_metal_tons: float
    remaining_after_shift_metal_tons: float
    observation_time_seconds: float
    observation_time_error_seconds: float
    # Six fields in exact V1.0 order, normalized before returning.
    features: np.ndarray


def _checked_raw(raw: np.ndarray) -> np.ndarray:
    a = np.asarray(raw, dtype=np.float64)
    if a.shape != (RAW_DIM,):
        raise ValueError(f"expected shape ({RAW_DIM},), got {a.shape}")
    if not np.all(np.isfinite(a)) or np.any(np.abs(a) > np.finfo(np.float32).max):
        raise ValueError("non-finite raw observation")
    # Reproduce the wire precision also for lists/float64 offline fixtures.
    return a.astype(np.float32).astype(np.float64)


def _half_ulp(value: float) -> float:
    """Conservative float32 round-to-nearest error, in normalized units."""
    x = np.float32(value)
    maximum = np.finfo(np.float32).max
    up = float(np.nextafter(x, np.float32(np.inf))) - float(x) if x < maximum else 0.0
    down = float(x) - float(np.nextafter(x, np.float32(-np.inf))) if x > -maximum else 0.0
    return max(up, down) / 2.0


def _decode_clock(a: np.ndarray) -> tuple[float, int, bool, float]:
    """Cross-check all three public clocks; never repair a stale window index.

    Select the clock with the smallest transport error (typically remaining
    window time), preserving near-cutoff instants when shiftElapsed rounds to 1.
    No RPC double time or hidden crusher clock is an extra predictor input.
    """
    if a[TERMINAL_INDEX] not in (0.0, 1.0):
        raise ValueError('global.terminal must be binary')
    terminal = bool(a[TERMINAL_INDEX])
    raw_index = float(a[WINDOW_INDEX]) * WINDOW_COUNT
    current = int(round(raw_index))
    if raw_index != current or not 0 <= current <= WINDOW_COUNT:
        raise ValueError('invalid normalized window index')
    if terminal != (current == WINDOW_COUNT):
        raise ValueError('terminal/windowIndex inconsistency')
    for index in (SHIFT_ELAPSED_INDEX, SHIFT_REMAINING_INDEX, WINDOW_REMAINING_INDEX):
        if not 0.0 <= a[index] <= 1.0:
            raise ValueError('invalid elapsed/remaining time')
    if terminal:
        if a[0] != 1.0 or a[1] != 0.0 or a[3] != 0.0:
            raise ValueError('terminal/time inconsistency')
        return SHIFT_SECONDS, current, True, 0.0
    if a[1] <= 0 or a[3] <= 0:
        raise ValueError('nonterminal remaining time must be positive')

    end = (current + 1) * WINDOW_SECONDS
    candidates = (
        (float(a[0]) * SHIFT_SECONDS, _half_ulp(a[0]) * SHIFT_SECONDS),
        (SHIFT_SECONDS - float(a[1]) * SHIFT_SECONDS, _half_ulp(a[1]) * SHIFT_SECONDS),
        (end - float(a[3]) * WINDOW_SECONDS, _half_ulp(a[3]) * WINDOW_SECONDS),
    )
    slack = PARAMETERS['clock_arithmetic_atol_seconds']
    lower = max(t - error for t, error in candidates)
    upper = min(t + error for t, error in candidates)
    if lower > upper + slack:
        raise ValueError('observation time/windowIndex/remaining clocks disagree')
    now, error = min(candidates, key=lambda pair: pair[1])
    if now < current * WINDOW_SECONDS - error - slack or now >= end + slack:
        raise ValueError('observation time lies outside current window')
    # Roundoff can only move the chosen estimate within its audited error bound.
    now = max(current * WINDOW_SECONDS, min(now, end))
    return now, current, False, error + slack


def decode_fifo(raw: np.ndarray, *, check_buffer: bool = True) -> tuple[Batch, ...]:
    """Read contiguous V4 FIFO slots; never double-count reserved/dumping ore.

    dump.0.bufferTons represents crusherStoredTons and includes the FIFO.
    The consistency check is at float32 transport precision, not Java double.
    """
    a = _checked_raw(raw)
    result = []
    seen_empty = False
    for k in range(FIFO_SLOTS):
        base = FIFO_BASE + k * FIFO_STRIDE
        valid, tons_norm, grade = (float(x) for x in a[base:base+3])
        if valid not in (0.0, 1.0):
            raise ValueError(f"fifo.{k}.valid must be binary, got {valid}")
        if valid == 0.0:
            seen_empty = True
            if tons_norm != 0.0 or grade != 0.0:
                raise ValueError(f"fifo.{k} invalid but nonzero data")
            continue
        if seen_empty:
            raise ValueError(f"fifo.{k} valid after empty slot: invalid FIFO order")
        tons = tons_norm * FIFO_TONS_SCALE
        if tons <= 0.0 or not 0.0 <= grade <= 1.0:
            raise ValueError(f"fifo.{k} invalid remaining tons or grade")
        result.append(Batch(remaining_tons=tons, grade_fraction=grade))

    if check_buffer:
        stored = float(a[BUFFER_TONS_INDEX]) * FIFO_TONS_SCALE
        in_fifo = math.fsum(batch.remaining_tons for batch in result)
        tolerance = PARAMETERS['alp_fifo_balance_atol_tons'] + FIFO_TONS_SCALE * (
            _half_ulp(a[BUFFER_TONS_INDEX])
            + math.fsum(_half_ulp(a[FIFO_BASE + k * FIFO_STRIDE + 1]) for k in range(len(result))))
        if stored < 0 or not math.isclose(stored, in_fifo, abs_tol=tolerance, rel_tol=0):
            raise ValueError(
                f"crusher stored mass != FIFO mass: stored={stored}, "
                f"sum_fifo={in_fifo}; check observation/version"
            )
    return tuple(result)


def project_fifo_only(raw: np.ndarray) -> Projection:
    """Exact fluid FIFO integration for existing batches under V4 fixed rate.

    Starts *after* the current observation time. No new batches are admitted.
    Cross-window portions are split by actual processed tonnage; neither
    truck arrival time nor whole-truck window assignment is used.
    """
    a = _checked_raw(raw)
    batches = decode_fifo(a)
    now, current, terminal, time_error = _decode_clock(a)
    rate = float(a[CRUSHER_RATE_INDEX]) * CRUSHER_RATE_SCALE_TPH / 3600.0
    if not math.isfinite(rate) or rate <= 0.0:
        raise ValueError(f"invalid crusher rate t/s: {rate}")

    left = [b.remaining_tons for b in batches]
    grade = [b.grade_fraction for b in batches]
    cursor = 0
    q = [0.0] * WINDOW_COUNT
    m = [0.0] * WINDOW_COUNT
    if not terminal:
        # V4 uses windowIndex and current time; never credit prior output here.
        for w in range(current, WINDOW_COUNT):
            start_sec = max(now, w * WINDOW_SECONDS)
            end_sec = (w+1) * WINDOW_SECONDS
            available = max(0.0, (end_sec - start_sec) * rate)
            while available > 0.0 and cursor < len(left):
                used = min(available, left[cursor])
                q[w] += used
                m[w] += used * grade[cursor]
                left[cursor] -= used
                available -= used
                if left[cursor] <= 0.0:
                    cursor += 1

    pending = math.fsum(left)
    initial = math.fsum(b.remaining_tons for b in batches)
    initial_metal = math.fsum(b.remaining_tons * b.grade_fraction for b in batches)
    pending_metal = math.fsum(x * g for x, g in zip(left, grade))
    if not math.isclose(math.fsum(q) + pending, initial,
                        abs_tol=PARAMETERS['conservation_atol_tons'], rel_tol=PARAMETERS['conservation_rtol']):
        raise AssertionError("FIFO mass conservation violated")
    if not math.isclose(
        math.fsum(m) + pending_metal, initial_metal,
        abs_tol=PARAMETERS['conservation_atol_tons'], rel_tol=PARAMETERS['conservation_rtol'],
    ):
        raise AssertionError("FIFO metal conservation violated")

    feat = np.zeros(6, dtype=np.float32)
    if not terminal:
        feat[0] = q[current] / PROJECTION_SCALE_TONS
        feat[1] = m[current] / PROJECTION_SCALE_TONS
        feat[2] = 1.0
        if current + 1 < WINDOW_COUNT:
            feat[3] = q[current+1] / PROJECTION_SCALE_TONS
            feat[4] = m[current+1] / PROJECTION_SCALE_TONS
            feat[5] = 1.0
    if not np.isfinite(feat).all():
        raise ValueError('projected features overflow float32')
    return Projection(
        current_window=current,
        produced_tons_by_window=tuple(q),
        produced_metal_by_window=tuple(m),
        remaining_after_shift_tons=pending,
        initial_fifo_tons=initial,
        initial_fifo_metal_tons=initial_metal,
        remaining_after_shift_metal_tons=pending_metal,
        observation_time_seconds=now,
        observation_time_error_seconds=time_error,
        features=feat,
    )
