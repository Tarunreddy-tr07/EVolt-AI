"""
reinforcement_learning/environment.py
--------------------------------------
Phase 2: Core Gymnasium RL Environment for EV Charging Scheduling.

Episode: 1 simulated day, 96 timesteps × 15-min resolution.
Slots: N_SLOTS=6 Level-2 AC charging bays.
Arrivals: Sampled from empirical ACN-Data distributions (arrival_distributions.json).

Usage:
    from reinforcement_learning.environment import EVChargingEnv
    env = EVChargingEnv()
    obs, info = env.reset()
    for _ in range(96):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import gymnasium as gym

from reinforcement_learning.state_space import (
    N_SLOTS, OBS_DIM, MAX_RATE_KW, GRID_CAPACITY_KW,
    ChargingSlot, build_observation, get_tou_price,
)
from reinforcement_learning.action_space import (
    make_action_space, decode_action,
)
from reinforcement_learning.reward_function import (
    RewardWeights, DEFAULT_WEIGHTS,
    compute_step_reward, compute_departure_penalty,
)

# ─── Paths ────────────────────────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DIST_JSON    = _PROJECT_ROOT / "data" / "arrival_distributions.json"


# ─────────────────────────────────────────────
# ArrivalSampler  (inline, avoids circular import)
# ─────────────────────────────────────────────

class _ArrivalSampler:
    """Minimal sampler that reads arrival_distributions.json."""

    def __init__(self, dist_path: Path, rng: np.random.Generator):
        with open(dist_path, "r") as f:
            self._d = json.load(f)
        self._rng = rng

    def _label(self, is_weekend: bool) -> str:
        return "weekend" if is_weekend else "weekday"

    def sample_energy_kwh(self, is_weekend: bool) -> float:
        p = self._d["energy_demand"][self._label(is_weekend)]
        v = self._rng.lognormal(p["mu"], p["sigma"])
        return float(np.clip(v, p["min"], p["max"]))

    def sample_dwell_hours(self, is_weekend: bool) -> float:
        p = self._d["dwell_time"][self._label(is_weekend)]
        v = self._rng.lognormal(p["mu"], p["sigma"])
        return float(np.clip(v, 0.25, p["max"]))

    def arrivals_this_step(self, hour: int, is_weekend: bool) -> int:
        label = self._label(is_weekend)
        hourly_prob = self._d["arrival_rate"][label].get(str(hour), 0.0)
        avg_per_day = self._d["summary_stats"]["avg_sessions_per_day"]
        expected_per_step = avg_per_day * hourly_prob * 0.25  # 15-min fraction
        return int(self._rng.poisson(max(expected_per_step, 0.0)))


# ─────────────────────────────────────────────
# Main Environment
# ─────────────────────────────────────────────

class EVChargingEnv(gym.Env):
    """
    EV Charging Scheduling Environment.

    Parameters
    ----------
    n_slots           : int   Number of charging bays (default 6).
    dist_json         : Path  Path to arrival_distributions.json.
    reward_weights    : RewardWeights  Tunable reward weights.
    seed              : int   RNG seed (None for random).
    fixed_day_of_week : int or None
        If set, always simulate this weekday (0=Mon..6=Sun).
        None means random per episode.
    """

    metadata = {"render_modes": ["human", "ansi"]}

    def __init__(
        self,
        n_slots: int = N_SLOTS,
        dist_json: Path = _DIST_JSON,
        reward_weights: RewardWeights = DEFAULT_WEIGHTS,
        seed: int = None,
        fixed_day_of_week: Optional[int] = None,
        render_mode: str = None,
    ):
        super().__init__()

        self.n_slots            = n_slots
        self.reward_weights     = reward_weights
        self.fixed_day_of_week  = fixed_day_of_week
        self.render_mode        = render_mode
        self._dist_json         = dist_json

        # Gymnasium spaces
        self.observation_space = gym.spaces.Box(
            low=0.0, high=1.0,
            shape=(OBS_DIM,),
            dtype=np.float32,
        )
        self.action_space = make_action_space(n_slots)

        # Internal state (initialised in reset)
        self._slots:        List[ChargingSlot] = []
        self._step_idx:     int = 0
        self._current_hour: int = 0
        self._is_weekend:   bool = False
        self._power_history: List[float] = []
        self._sampler:      _ArrivalSampler = None
        self._vehicle_counter: int = 0
        self._rng:          np.random.Generator = None

        # Episode-level accumulators (for info dict)
        self._ep_reward:       float = 0.0
        self._ep_energy_kwh:   float = 0.0
        self._ep_cost_usd:     float = 0.0
        self._ep_unmet_kwh:    float = 0.0
        self._ep_overload_kwh: float = 0.0
        self._ep_rejected:     int   = 0   # arrivals rejected (all slots full)
        self._ep_departures:   int   = 0

        # Pre-initialise RNG so action_space.sample() works before reset()
        self._init_rng(seed)

    # ──────────────────────────────────────────
    # RNG helpers
    # ──────────────────────────────────────────

    def _init_rng(self, seed: Optional[int]) -> None:
        self._rng = np.random.default_rng(seed)
        if self._dist_json.exists():
            self._sampler = _ArrivalSampler(self._dist_json, self._rng)

    # ──────────────────────────────────────────
    # reset()
    # ──────────────────────────────────────────

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict] = None,
    ) -> Tuple[np.ndarray, Dict]:
        super().reset(seed=seed)

        if seed is not None:
            self._init_rng(seed)

        # Reload sampler if not yet initialised (first call after __init__)
        if self._sampler is None and self._dist_json.exists():
            self._sampler = _ArrivalSampler(self._dist_json, self._rng)

        # Episode metadata
        if self.fixed_day_of_week is not None:
            dow = self.fixed_day_of_week
        else:
            dow = int(self._rng.integers(0, 7))
        self._is_weekend = dow >= 5

        # Simulation clock: start at midnight (step 0 = 00:00–00:15)
        self._step_idx      = 0
        self._current_hour  = 0
        self._power_history = []
        self._vehicle_counter = 0

        # Fresh slots
        self._slots = [ChargingSlot(i) for i in range(self.n_slots)]

        # Reset accumulators
        self._ep_reward       = 0.0
        self._ep_energy_kwh   = 0.0
        self._ep_cost_usd     = 0.0
        self._ep_unmet_kwh    = 0.0
        self._ep_overload_kwh = 0.0
        self._ep_rejected     = 0
        self._ep_departures   = 0

        obs = self._get_obs()
        info = self._get_info()
        return obs, info

    # ──────────────────────────────────────────
    # step()
    # ──────────────────────────────────────────

    def step(
        self, action: np.ndarray
    ) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Advance the simulation by one 15-minute timestep.

        Parameters
        ----------
        action : np.ndarray  Shape (n_slots,), values in {0..4}.

        Returns
        -------
        obs, reward, terminated, truncated, info
        """
        DT = 0.25  # hours per step

        # 1. Decode action → per-slot kW rates
        rates_kw = decode_action(action)

        # 2. Apply charging & accumulate energy
        step_energy_kwh = 0.0
        for slot, rate in zip(self._slots, rates_kw):
            delivered = slot.charge(rate_kw=rate, dt_hours=DT)
            step_energy_kwh += delivered

        total_power_kw = float(np.sum(rates_kw))
        self._power_history.append(total_power_kw)

        # 3. Step reward
        step_reward, step_info = compute_step_reward(
            energy_delivered_kwh=step_energy_kwh,
            total_power_kw=total_power_kw,
            current_hour=self._current_hour,
            dt_hours=DT,
            weights=self.reward_weights,
            power_history=self._power_history,
        )

        # 4. Advance simulated clock
        self._step_idx     += 1
        self._current_hour  = (self._step_idx * DT) % 24  # fractional → floor for TOU
        self._current_hour  = int(self._current_hour)

        # 5. Process departures (time_remaining decremented after charging)
        departure_reward = 0.0
        for slot in self._slots:
            if slot.occupied:
                slot.time_remaining = max(0.0, slot.time_remaining - DT)
                if slot.time_remaining <= 0.0:
                    session = slot.free()
                    pen, dep_info = compute_departure_penalty(
                        energy_target=session["energy_target"],
                        energy_delivered=session["energy_delivered"],
                        weights=self.reward_weights,
                    )
                    departure_reward        += pen
                    self._ep_unmet_kwh      += dep_info["unmet_kwh"]
                    self._ep_departures     += 1

        # 6. Sample new arrivals (for the current new hour)
        arrivals = 0
        if self._sampler is not None:
            arrivals = self._sampler.arrivals_this_step(
                self._current_hour, self._is_weekend
            )

        for _ in range(arrivals):
            free_slots = [s for s in self._slots if not s.occupied]
            if free_slots:
                slot = free_slots[0]
                energy = self._sampler.sample_energy_kwh(self._is_weekend)
                dwell  = self._sampler.sample_dwell_hours(self._is_weekend)
                self._vehicle_counter += 1
                slot.assign_vehicle(
                    energy_target=energy,
                    dwell_hours=dwell,
                    vehicle_id=self._vehicle_counter,
                )
            else:
                self._ep_rejected += 1

        # 7. Aggregate reward
        reward = step_reward + departure_reward

        # 8. Accumulate episode metrics
        self._ep_reward       += reward
        self._ep_energy_kwh   += step_energy_kwh
        self._ep_cost_usd     += step_info["electricity_cost_usd"]
        self._ep_overload_kwh += step_info["overload_kw"] * DT

        # 9. Termination: episode ends after 96 steps (1 simulated day)
        terminated = self._step_idx >= 96
        truncated  = False

        obs  = self._get_obs()
        info = self._get_info(step_info=step_info, arrivals=arrivals)

        if self.render_mode == "human":
            self.render()

        return obs, reward, terminated, truncated, info

    # ──────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────

    def _get_obs(self) -> np.ndarray:
        total_power = sum(
            s.energy_remaining / max(s.time_remaining, 1e-6)
            if s.occupied else 0.0
            for s in self._slots
        )
        # Use actual power history for the obs builder
        current_total = self._power_history[-1] if self._power_history else 0.0
        return build_observation(self._slots, self._current_hour, current_total)

    def _get_info(self, step_info: dict = None, arrivals: int = 0) -> Dict:
        occupied = sum(1 for s in self._slots if s.occupied)
        return {
            "step":            self._step_idx,
            "hour":            self._current_hour,
            "is_weekend":      self._is_weekend,
            "occupied_slots":  occupied,
            "free_slots":      self.n_slots - occupied,
            "arrivals":        arrivals,
            "ep_reward":       self._ep_reward,
            "ep_energy_kwh":   self._ep_energy_kwh,
            "ep_cost_usd":     self._ep_cost_usd,
            "ep_unmet_kwh":    self._ep_unmet_kwh,
            "ep_overload_kwh": self._ep_overload_kwh,
            "ep_rejected":     self._ep_rejected,
            "ep_departures":   self._ep_departures,
            **(step_info or {}),
        }

    # ──────────────────────────────────────────
    # render()
    # ──────────────────────────────────────────

    def render(self) -> str | None:
        lines = [
            f"Step {self._step_idx:02d}/96  |  "
            f"Hour {self._current_hour:02d}:{'00' if self._step_idx % 4 == 0 else ('15' if self._step_idx % 4 == 1 else ('30' if self._step_idx % 4 == 2 else '45'))}  |  "
            f"{'Weekend' if self._is_weekend else 'Weekday'}"
        ]
        for s in self._slots:
            if s.occupied:
                bar = "█" * int(s.soc * 10) + "░" * (10 - int(s.soc * 10))
                lines.append(
                    f"  Slot {s.slot_id}: [OCCUPIED] SoC={s.soc:.2f} [{bar}] "
                    f"energy_rem={s.energy_remaining:.1f} kWh  "
                    f"time_rem={s.time_remaining:.2f} h"
                )
            else:
                lines.append(f"  Slot {s.slot_id}: [FREE]")
        lines.append(
            f"  Ep reward={self._ep_reward:.2f}  "
            f"cost=${self._ep_cost_usd:.3f}  "
            f"unmet={self._ep_unmet_kwh:.2f} kWh  "
            f"rejected={self._ep_rejected}"
        )
        output = "\n".join(lines)
        if self.render_mode == "human":
            print(output)
        return output

    def close(self):
        pass
