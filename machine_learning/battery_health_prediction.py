"""
machine_learning/battery_health_prediction.py
-----------------------------------------------
Phase 4b (supplementary): Battery health combined module.

Wraps both SoC and SoH predictors into a single BatteryHealthPredictor
class, and provides helper functions for generating SoC curves and SoH
trend projections — used by the Streamlit battery dashboard.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Tuple

import numpy as np

from machine_learning.soc_prediction import SoCPredictor, _soc_curve
from machine_learning.soh_prediction import SoHPredictor, _true_soh


class BatteryHealthPredictor:
    """
    Combined SoC + SoH predictor for runtime use in battery_manager.py.

    Loads pre-trained models and exposes:
      - predict_soc()            : point estimate of current SoC
      - soc_curve()              : full SoC curve over a session
      - predict_soh()            : point estimate of current SoH
      - soh_trend()              : projected SoH degradation over future cycles
    """

    def __init__(
        self,
        soc_model_path: Path = None,
        soh_model_path: Path = None,
    ):
        _base = Path(__file__).resolve().parent / "saved_models"
        self._soc = SoCPredictor(soc_model_path or _base / "soc_model.joblib")
        self._soh = SoHPredictor(soh_model_path or _base / "soh_model.joblib")

    # ── SoC ──────────────────────────────────────────────────────────────

    def predict_soc(
        self,
        time_elapsed_frac: float,
        charge_rate_kw: float,
        battery_capacity_kwh: float,
        energy_delivered_kwh: float,
    ) -> float:
        """Return ML-predicted SoC (0–1)."""
        return self._soc.predict(
            time_elapsed_frac,
            charge_rate_kw,
            battery_capacity_kwh,
            energy_delivered_kwh,
        )

    def soc_curve(
        self,
        dwell_hours: float,
        charge_rate_kw: float,
        battery_capacity_kwh: float,
        n_points: int = 50,
    ) -> Tuple[List[float], List[float]]:
        """
        Generate a full SoC curve over a session for the dashboard.

        Returns
        -------
        (times_hours, soc_values)  both lists of length n_points.
        """
        times = np.linspace(0, dwell_hours, n_points)
        t_fracs = times / dwell_hours
        energy_targets = charge_rate_kw * dwell_hours * t_fracs
        energy_targets = np.clip(energy_targets, 0, battery_capacity_kwh)

        soc_vals = [
            self.predict_soc(
                tf, charge_rate_kw, battery_capacity_kwh, ed
            )
            for tf, ed in zip(t_fracs, energy_targets)
        ]
        return list(times), soc_vals

    # ── SoH ──────────────────────────────────────────────────────────────

    def predict_soh(
        self,
        cycle_count: float,
        avg_discharge_rate_c: float = 0.5,
        depth_of_discharge: float = 0.8,
        avg_temperature_c: float = 25.0,
    ) -> float:
        """Return ML-predicted SoH fraction (0.6–1.0)."""
        return self._soh.predict(
            cycle_count,
            avg_discharge_rate_c,
            depth_of_discharge,
            avg_temperature_c,
        )

    def soh_trend(
        self,
        current_cycles: int,
        future_cycles: int = 500,
        avg_discharge_rate_c: float = 0.5,
        depth_of_discharge: float = 0.8,
        avg_temperature_c: float = 25.0,
        n_points: int = 50,
    ) -> Tuple[List[int], List[float]]:
        """
        Project SoH degradation trend over future cycles.

        Returns
        -------
        (cycle_values, soh_values)
        """
        cycle_range = np.linspace(
            current_cycles,
            current_cycles + future_cycles,
            n_points
        ).astype(int)

        soh_vals = [
            self.predict_soh(c, avg_discharge_rate_c, depth_of_discharge, avg_temperature_c)
            for c in cycle_range
        ]
        return list(map(int, cycle_range)), soh_vals

    def health_label(self, soh: float) -> str:
        return self._soh.health_label(soh)
