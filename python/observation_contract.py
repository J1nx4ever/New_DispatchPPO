"""Physical observation contract extracted from DRL-PPO.alp, never clipped.

observation_schema.json records all 1519 indices and Java scaling expressions.
Only proven categorical/unit bounds are enforced. Scaled physical quantities
are finite float32, not necessarily in [0, 1]. Runtime schema CSV comparison
is still required to verify the loaded AnyLogic model.
"""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import numpy as np

OBSERVATION_SCHEMA_ID = "dispatch.physical.v3"
OBSERVATION_SIZE = 1519
OBSERVATION_ALP_PATH = "anylogic/DRL-PPO.alp"
SCHEMA = tuple(json.loads(Path(__file__).with_name("observation_schema.json").read_text()))
FIELD_NAMES = tuple(field["name"] for field in SCHEMA)
ACTION_MASK_SLICE = slice(19, 23)
TRUCK_OFFSET = 27
TRUCK_STRIDE = 120
EGO_INDICES = tuple(TRUCK_OFFSET + i * TRUCK_STRIDE for i in range(9))
FLOAT32_MAX = float(np.finfo(np.float32).max)
OBSERVATION_LOW = tuple(0.0 if f['kind'] in ('binary', 'unit', 'truck_slot') else -FLOAT32_MAX for f in SCHEMA)
OBSERVATION_HIGH = tuple(1.0 if f['kind'] in ('binary', 'unit', 'truck_slot') else FLOAT32_MAX for f in SCHEMA)


def validate_observation(schema_id, values, *, terminal=None, truck_id=None):
    if schema_id != OBSERVATION_SCHEMA_ID:
        raise ValueError(f"schema_id must be {OBSERVATION_SCHEMA_ID!r}, got {schema_id!r}")
    raw = np.asarray(values, dtype=np.float64)
    if raw.shape != (OBSERVATION_SIZE,):
        raise ValueError(f"observation must have shape ({OBSERVATION_SIZE},), got {raw.shape}")
    if not np.isfinite(raw).all() or np.any(np.abs(raw) > FLOAT32_MAX):
        raise ValueError("observation contains non-finite values or float32 overflow")
    obs = raw.astype(np.float32)
    bad = (obs < OBSERVATION_LOW) | (obs > OBSERVATION_HIGH)
    if bad.any():
        i = int(np.flatnonzero(bad)[0])
        raise ValueError(f"observation field {i} ({FIELD_NAMES[i]}) outside declared bounds")
    for f in SCHEMA:
        if f['kind'] == 'binary' and obs[f['index']] not in (0.0, 1.0):
            raise ValueError(f"{f['name']} must be binary")
        if f['kind'] == 'truck_slot' and not np.isclose(obs[f['index']]*9, round(float(obs[f['index']]*9)), atol=1e-6):
            raise ValueError(f"{f['name']} must encode (truckId+1)/9 or zero")
    for i in range(9):
        for suffix, count in [('type.',3), ('phase.',12), ('loadTarget.',4), ('dumpTarget.',2), ('node.',9), ('segment.',16)]:
            start = FIELD_NAMES.index(f'truck.{i}.{suffix}0')
            if obs[start:start+count].sum() > 1:
                raise ValueError(f"truck.{i}.{suffix} is not one-hot or all-zero")
    if terminal is not None:
        if bool(obs[17]) != terminal:
            raise ValueError("global.terminal disagrees with callback kind")
        egos = obs[list(EGO_INDICES)]
        if terminal:
            if egos.any() or obs[19:27].any():
                raise ValueError("terminal observation must have zero ego, action mask and action tons")
        else:
            if truck_id is None or not 0 <= truck_id < 9 or egos.sum() != 1 or egos[truck_id] != 1:
                raise ValueError("decision observation must identify exactly the requesting truck")
            if not obs[ACTION_MASK_SLICE].any():
                raise ValueError("action request must have at least one available load site")
    return obs


def action_mask(values):
    return np.asarray(values)[ACTION_MASK_SLICE].astype(bool, copy=True)


def validate_schema_output(output: str):
    """Compare actual [OBS_SCHEMA_BEGIN] CSV from obsCheckDecision with disk contract."""
    try:
        block = output.split('[OBS_SCHEMA_BEGIN]', 1)[1].split('[OBS_SCHEMA_END]', 1)[0].strip()
    except IndexError as exc:
        raise ValueError("missing OBS_SCHEMA markers") from exc
    if '[OBS_SCHEMA_END]' not in output:
        raise ValueError("missing OBS_SCHEMA_END")
    rows = list(csv.DictReader(io.StringIO(block)))
    actual = [(int(row['index']), row['name']) for row in rows]
    expected = list(enumerate(FIELD_NAMES))
    if actual != expected:
        raise ValueError("runtime observation schema differs from audited ALP field order")
    return True
