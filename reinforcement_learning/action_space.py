

from __future__ import annotations

import numpy as np
import gymnasium as gym

from reinforcement_learning.state_space import N_SLOTS, MAX_RATE_KW

# ─────────────────────────────────────────────
# Rate levels
# ─────────────────────────────────────────────

N_RATE_LEVELS   = 5
RATE_FRACTIONS  = np.array([0.0, 0.25, 0.50, 0.75, 1.0], dtype=np.float32)
RATE_KW_LEVELS  = RATE_FRACTIONS * MAX_RATE_KW  # [0, 1.65, 3.3, 4.95, 6.6]


# ─────────────────────────────────────────────
# Space factory
# ─────────────────────────────────────────────

def make_action_space(n_slots: int = N_SLOTS) -> gym.spaces.MultiDiscrete:
    """
    Return the MultiDiscrete action space for the environment.

    Each element is an integer index into RATE_KW_LEVELS (0–4).
    """
    return gym.spaces.MultiDiscrete([N_RATE_LEVELS] * n_slots)


# ─────────────────────────────────────────────
# Action decoder
# ─────────────────────────────────────────────

def decode_action(action: np.ndarray) -> np.ndarray:
    """
    Convert a raw MultiDiscrete action array to per-slot kW rates.

    Parameters
    ----------
    action : np.ndarray  Shape (N_SLOTS,), values in {0,1,2,3,4}.

    Returns
    -------
    np.ndarray  Shape (N_SLOTS,), per-slot charging rate in kW.
    """
    action = np.asarray(action, dtype=int)
    return RATE_KW_LEVELS[action]


def encode_action(rates_kw: np.ndarray) -> np.ndarray:
    """
    Snap continuous rates to the nearest discrete level.
    Useful for expert baselines or evaluation.

    Parameters
    ----------
    rates_kw : np.ndarray  Shape (N_SLOTS,), rates in kW.

    Returns
    -------
    np.ndarray  Shape (N_SLOTS,), integer indices.
    """
    rates_kw = np.asarray(rates_kw, dtype=np.float32)
    indices = np.argmin(
        np.abs(rates_kw[:, None] - RATE_KW_LEVELS[None, :]), axis=1
    )
    return indices.astype(int)


# ─────────────────────────────────────────────
# Human-readable helper
# ─────────────────────────────────────────────

def action_to_str(action: np.ndarray) -> str:
    """Return a human-readable string for an action vector."""
    rates = decode_action(action)
    parts = [f"Slot{i}: {r:.2f} kW" for i, r in enumerate(rates)]
    return " | ".join(parts)
