"""
reinforcement_learning/reward_function.py
------------------------------------------
Reward function for the EV charging RL environment.

reward = + w1 * energy_delivered_step          (progress toward satisfying demand)
         - w2 * electricity_cost_step          (TOU price × power drawn)
         - w3 * grid_overload_penalty          (if total draw > capacity)
         - w4 * unmet_demand_penalty           (at departure, if SoC < 1)
         + w5 * load_balance_bonus             (smooth / flat power curve)

Default weights from the implementation plan:
    w1=1.0, w2=0.5, w3=10.0, w4=20.0, w5=0.1
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np

from reinforcement_learning.state_space import (
    GRID_CAPACITY_KW, get_tou_price
)


# ─────────────────────────────────────────────
# Weight configuration
# ─────────────────────────────────────────────

@dataclass
class RewardWeights:
    """Tunable reward weights — adjust after initial training."""
    w_energy:    float = 1.0    # per kWh delivered (positive)
    w_cost:      float = 0.5    # per $ electricity cost (negative)
    w_overload:  float = 10.0   # per kW over capacity (negative)
    w_unmet:     float = 20.0   # per kWh unmet at departure (negative)
    w_balance:   float = 0.1    # load-balance smoothness bonus

DEFAULT_WEIGHTS = RewardWeights()


# ─────────────────────────────────────────────
# Step reward  (called every 15-min timestep)
# ─────────────────────────────────────────────

def compute_step_reward(
    energy_delivered_kwh: float,
    total_power_kw: float,
    current_hour: int,
    dt_hours: float = 0.25,
    weights: RewardWeights = DEFAULT_WEIGHTS,
    power_history: List[float] = None,
) -> tuple[float, dict]:
    """
    Compute the per-step reward component (excludes departure penalties).

    Parameters
    ----------
    energy_delivered_kwh : float  Total kWh delivered this step across all slots.
    total_power_kw        : float  Total power draw this step (kW).
    current_hour          : int    Current simulated hour (0–23).
    dt_hours              : float  Timestep length in hours (default 0.25 = 15 min).
    weights               : RewardWeights
    power_history         : list  Recent power levels for load-balance bonus.

    Returns
    -------
    (reward: float, info: dict)   Scalar reward + breakdown dict.
    """
    # Energy delivery reward
    r_energy = weights.w_energy * energy_delivered_kwh

    # Electricity cost penalty
    price_per_kwh = get_tou_price(current_hour)
    cost = price_per_kwh * energy_delivered_kwh
    r_cost = -weights.w_cost * cost

    # Grid overload penalty (per-kW over limit, per step)
    overload_kw = max(0.0, total_power_kw - GRID_CAPACITY_KW)
    r_overload = -weights.w_overload * overload_kw * dt_hours

    # Load-balance bonus — penalise large variance in recent power levels
    r_balance = 0.0
    if power_history and len(power_history) >= 2:
        recent = np.array(power_history[-8:])  # last 2 hours
        variance = float(np.var(recent))
        # Bonus is higher when variance is low
        r_balance = weights.w_balance * max(0.0, 1.0 - variance / (GRID_CAPACITY_KW ** 2))

    reward = r_energy + r_cost + r_overload + r_balance

    info = {
        "r_energy":    r_energy,
        "r_cost":      r_cost,
        "r_overload":  r_overload,
        "r_balance":   r_balance,
        "electricity_cost_usd": cost,
        "overload_kw":  overload_kw,
    }

    return float(reward), info


# ─────────────────────────────────────────────
# Departure penalty  (called when a slot is freed)
# ─────────────────────────────────────────────

def compute_departure_penalty(
    energy_target: float,
    energy_delivered: float,
    weights: RewardWeights = DEFAULT_WEIGHTS,
) -> tuple[float, dict]:
    """
    Sparse penalty applied once when an EV departs.

    Parameters
    ----------
    energy_target     : float  kWh the driver wanted.
    energy_delivered  : float  kWh actually delivered.
    weights           : RewardWeights

    Returns
    -------
    (penalty: float, info: dict)  Negative scalar + breakdown dict.
    """
    unmet_kwh = max(0.0, energy_target - energy_delivered)
    penalty   = -weights.w_unmet * unmet_kwh

    info = {
        "unmet_kwh":     unmet_kwh,
        "r_unmet":       penalty,
        "soc_satisfied": energy_delivered / max(energy_target, 1e-6),
    }

    return float(penalty), info
