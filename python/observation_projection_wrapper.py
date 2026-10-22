"""Gymnasium adapter: raw gRPC 1519D remains untouched.

Use P0 mode only for feature-pipeline smoke tests / diagnostics.
Official F1 with *all* committed material requires P1--P3 validation.
"""
from __future__ import annotations

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from .window_projection import (
    RAW_DIM, project_fifo_only, assert_schema_fields, PROJECTION_CONTRACT_ID,
)
from .observation_contract import (
    OBSERVATION_LOW, OBSERVATION_HIGH, FIELD_NAMES,
)

AGENT_DIM = 1525


class FIFOObservationWrapper(gym.ObservationWrapper):
    def __init__(self, env: gym.Env):
        super().__init__(env)
        assert_schema_fields(FIELD_NAMES)
        if env.observation_space.shape != (RAW_DIM,):
            raise ValueError("FIFO wrapper expects V4 1519D observation")
        # Projected tons/metal cannot be negative. Do not clip to [0,1].
        # Only validity bits are unit-valued, at positions 2 and 5.
        maximum = np.finfo(np.float32).max
        lo = np.concatenate((np.asarray(OBSERVATION_LOW, np.float32),
                             np.zeros(6, dtype=np.float32)))
        hi = np.concatenate((np.asarray(OBSERVATION_HIGH, np.float32),
                             np.array([maximum, maximum, 1.0,
                                       maximum, maximum, 1.0], np.float32)))
        self.observation_space = spaces.Box(low=lo, high=hi, dtype=np.float32)

    def observation(self, observation: np.ndarray) -> np.ndarray:
        raw = np.asarray(observation, dtype=np.float32)
        if raw.shape != (RAW_DIM,):
            raise ValueError(f"expected raw observation ({RAW_DIM},)")
        z = project_fifo_only(raw).features
        combined = np.concatenate((raw, z)).astype(np.float32, copy=False)
        if combined.shape != (AGENT_DIM,) or not np.isfinite(combined).all():
            raise ValueError("invalid augmented observation")
        if not np.array_equal(combined[:RAW_DIM], raw):
            raise AssertionError("raw 1519D observation was modified")
        return combined
