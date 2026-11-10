"""
reinforcement_learning/state_space.py
--------------------------------------
Defines the observation (state) vector for the EV charging RL environment.

State vector layout (27 floats, all normalised to [0, 1]):
  Per charging slot (N_SLOTS=6, 4 features each = 24 values):
    [occupied, soc_estimate, energy_remaining_norm, time_remaining_norm]
  Global features (3 values):
    [current_hour_norm, grid_price_norm, total_power_fraction]
"""

from __future__ import annotations

import numpy as np
from typing import List, Dict

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

N_SLOTS          = 6          # number of charging slots simulated
MAX_ENERGY_KWH   = 100.0      # normalisation ceiling for energy
MAX_DWELL_HOURS  = 24.0       # normalisation ceiling for time remaining
MAX_RATE_KW      = 6.6        # Level-2 AC max per slot (kW)
GRID_CAPACITY_KW = N_SLOTS * MAX_RATE_KW  # max total draw (kW)

# Observation vector dimension
OBS_DIM = N_SLOTS * 4 + 3    # 27


# ─────────────────────────────────────────────
# TOU pricing curve  ($/kWh)
# ─────────────────────────────────────────────

TOU_PRICE_SCHEDULE: Dict[int, float] = {
    **{h: 0.07  for h in range(0,  6)},   # 00:00–06:00 off-peak
    **{h: 0.15  for h in range(6, 17)},   # 06:00–17:00 mid-peak
    **{h: 0.35  for h in range(17, 21)},  # 17:00–21:00 on-peak
    **{h: 0.15  for h in range(21, 24)},  # 21:00–24:00 mid-peak
}

TOU_MIN = min(TOU_PRICE_SCHEDULE.values())  # 0.07
TOU_MAX = max(TOU_PRICE_SCHEDULE.values())  # 0.35


def get_tou_price(hour: int) -> float:
    """Return the TOU electricity price ($/kWh) for the given hour (0–23)."""
    return TOU_PRICE_SCHEDULE.get(hour % 24, 0.15)


def get_tou_price_norm(hour: int) -> float:
    """Normalised TOU price in [0, 1]."""
    price = get_tou_price(hour)
    return (price - TOU_MIN) / (TOU_MAX - TOU_MIN)


# ─────────────────────────────────────────────
# Slot data container
# ─────────────────────────────────────────────

class ChargingSlot:
    """Mutable state for a single charging slot."""

    def __init__(self, slot_id: int):
        self.slot_id        = slot_id
        self.occupied       = False
        self.vehicle_id     = None        # arbitrary identifier for the vehicle
        self.soc            = 0.0         # state of charge (0.0–1.0)
        self.energy_target  = 0.0         # kWh the vehicle wants
        self.energy_delivered = 0.0       # kWh delivered so far this session
        self.time_remaining = 0.0         # hours until departure
        self.max_rate_kw    = MAX_RATE_KW

    @property
    def energy_remaining(self) -> float:
        return max(0.0, self.energy_target - self.energy_delivered)

    @property
    def energy_remaining_norm(self) -> float:
        return min(self.energy_remaining / MAX_ENERGY_KWH, 1.0)

    @property
    def time_remaining_norm(self) -> float:
        return min(self.time_remaining / MAX_DWELL_HOURS, 1.0)

    def observe(self) -> np.ndarray:
        """Return a 4-element normalised feature vector for this slot."""
        return np.array([
            float(self.occupied),
            self.soc if self.occupied else 0.0,
            self.energy_remaining_norm if self.occupied else 0.0,
            self.time_remaining_norm   if self.occupied else 0.0,
        ], dtype=np.float32)

    def assign_vehicle(self, energy_target: float, dwell_hours: float,
                       vehicle_id=None) -> None:
        """Assign an arriving EV to this slot."""
        self.occupied         = True
        self.vehicle_id       = vehicle_id
        self.soc              = 0.0        # assume EV arrives nearly empty
        self.energy_target    = max(energy_target, 0.01)
        self.energy_delivered = 0.0
        self.time_remaining   = max(dwell_hours, 0.25)

    def free(self) -> dict:
        """Detach the vehicle; return session summary."""
        summary = {
            "slot_id":          self.slot_id,
            "vehicle_id":       self.vehicle_id,
            "energy_target":    self.energy_target,
            "energy_delivered": self.energy_delivered,
            "soc_final":        self.soc,
        }
        self.occupied         = False
        self.vehicle_id       = None
        self.soc              = 0.0
        self.energy_target    = 0.0
        self.energy_delivered = 0.0
        self.time_remaining   = 0.0
        return summary

    def charge(self, rate_kw: float, dt_hours: float) -> float:
        """
        Apply charging for dt_hours at rate_kw kW.

        Returns
        -------
        float   kWh actually delivered this step (≤ energy_remaining).
        """
        if not self.occupied or rate_kw <= 0:
            return 0.0

        # Clip to what's still needed
        delta_kwh = min(rate_kw * dt_hours, self.energy_remaining)
        delta_kwh = max(delta_kwh, 0.0)

        self.energy_delivered += delta_kwh

        # SoC update — logistic near full to mimic real charging taper
        if self.energy_target > 0:
            raw_soc = self.energy_delivered / self.energy_target
            # Logistic tail: slow down above 80%
            if raw_soc <= 0.8:
                self.soc = raw_soc
            else:
                # Map [0.8, 1.0] through a gentle logistic compression
                x = (raw_soc - 0.8) / 0.2   # 0→1 in the tail
                tail = 0.8 + 0.2 * (1 - np.exp(-4 * x)) / (1 - np.exp(-4))
                self.soc = min(tail, 1.0)

        return delta_kwh


# ─────────────────────────────────────────────
# Station state builder
# ─────────────────────────────────────────────

def build_observation(slots: List[ChargingSlot],
                      current_hour: int,
                      total_power_kw: float) -> np.ndarray:
    """
    Assemble the full observation vector for the environment's step().

    Parameters
    ----------
    slots : list of ChargingSlot
    current_hour : int        Simulated hour (0–23).
    total_power_kw : float    Sum of current charging rates across all slots.

    Returns
    -------
    np.ndarray  Shape (OBS_DIM,) = (27,), dtype float32, values in [0, 1].
    """
    slot_obs = np.concatenate([s.observe() for s in slots])  # 24 values

    global_obs = np.array([
        current_hour / 23.0,                              # hour norm
        get_tou_price_norm(current_hour),                 # price norm
        min(total_power_kw / GRID_CAPACITY_KW, 1.0),     # power fraction
    ], dtype=np.float32)

    return np.concatenate([slot_obs, global_obs]).astype(np.float32)
