"""
machine_learning/soh_prediction.py
-------------------------------------
Phase 4b: State-of-Health (SoH) Prediction Model.

ACN-Data contains no battery degradation information.  We therefore
generate realistic synthetic degradation data based on published
lithium-ion battery models (Capacity fade vs. cycle count).

Reference model (simplified Arrhenius / power-law):
    SoH = 1 - A * cycle_count^0.5 * exp(B * depth_of_discharge)

Features:
    - cycle_count          : number of full charge/discharge cycles
    - avg_discharge_rate_c : average C-rate during discharge (0.2–2.0)
    - depth_of_discharge   : fraction of capacity used per cycle (0–1)
    - avg_temperature_c    : average temperature in Celsius (15–40)

Target:
    - soh : remaining capacity fraction (0.6–1.0)

Usage:
    python -m machine_learning.soh_prediction
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────

SAVED_MODELS  = Path(__file__).resolve().parent / "saved_models"
SOH_MODEL_PATH = SAVED_MODELS / "soh_model.joblib"

# ─────────────────────────────────────────────
# Synthetic SoH data generator
# ─────────────────────────────────────────────

# Degradation constants (calibrated to match published Li-ion fade curves)
_A = 0.02        # overall fade magnitude
_B = 0.15        # DoD sensitivity
_C = 0.002       # C-rate sensitivity
_D = 0.001       # temperature sensitivity (above 25°C baseline)

def _true_soh(
    cycle_count: float,
    avg_discharge_rate_c: float,
    depth_of_discharge: float,
    avg_temperature_c: float = 25.0,
) -> float:
    """
    Physics-informed SoH model.

    Returns remaining capacity fraction (0–1), capped at [0.6, 1.0]
    to match realistic end-of-life thresholds.
    """
    temp_excess = max(0.0, avg_temperature_c - 25.0)
    fade = (
        _A * (cycle_count ** 0.5)
        * np.exp(_B * depth_of_discharge)
        * np.exp(_C * avg_discharge_rate_c)
        * np.exp(_D * temp_excess)
    )
    return float(np.clip(1.0 - fade, 0.6, 1.0))


def generate_soh_dataset(
    n_samples: int = 10_000,
    noise_std: float = 0.005,
    rng_seed: int = 42,
) -> pd.DataFrame:
    """
    Generate a synthetic SoH dataset.

    Samples random battery histories and computes degradation using
    the simplified Arrhenius/power-law model with Gaussian noise.
    """
    rng = np.random.default_rng(rng_seed)

    cycle_count           = rng.integers(1, 1500, n_samples).astype(float)
    avg_discharge_rate_c  = rng.uniform(0.2, 2.0, n_samples)
    depth_of_discharge    = rng.uniform(0.3, 1.0, n_samples)
    avg_temperature_c     = rng.uniform(15.0, 40.0, n_samples)

    soh = np.array([
        _true_soh(c, r, d, t)
        for c, r, d, t in zip(
            cycle_count, avg_discharge_rate_c,
            depth_of_discharge, avg_temperature_c
        )
    ])
    soh += rng.normal(0, noise_std, n_samples)
    soh  = np.clip(soh, 0.6, 1.0)

    return pd.DataFrame({
        "cycle_count":          cycle_count,
        "avg_discharge_rate_c": avg_discharge_rate_c,
        "depth_of_discharge":   depth_of_discharge,
        "avg_temperature_c":    avg_temperature_c,
        "soh":                  soh,
    })


# ─────────────────────────────────────────────
# Training
# ─────────────────────────────────────────────

FEATURE_COLS = [
    "cycle_count",
    "avg_discharge_rate_c",
    "depth_of_discharge",
    "avg_temperature_c",
]
TARGET_COL = "soh"


def train_soh_model(
    data: pd.DataFrame = None,
    save_path: Path = SOH_MODEL_PATH,
    n_estimators: int = 300,
    test_size: float = 0.2,
    seed: int = 42,
) -> tuple:
    """Train a GradientBoosting regressor for SoH prediction."""
    if data is None:
        data = generate_soh_dataset()

    X = data[FEATURE_COLS].values
    y = data[TARGET_COL].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed
    )

    model = GradientBoostingRegressor(
        n_estimators=n_estimators,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        random_state=seed,
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    metrics = {
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
        "r2":   float(r2_score(y_test, y_pred)),
        "n_train": len(X_train),
        "n_test":  len(X_test),
    }

    save_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, save_path)
    print(f"  SoH model saved -> {save_path}  |  R2={metrics['r2']:.4f}  RMSE={metrics['rmse']:.4f}")

    return model, metrics


# ─────────────────────────────────────────────
# Inference API
# ─────────────────────────────────────────────

class SoHPredictor:
    """Runtime SoH prediction wrapper."""

    def __init__(self, model_path: Path = SOH_MODEL_PATH):
        if not model_path.exists():
            raise FileNotFoundError(
                f"SoH model not found at {model_path}. "
                "Run: python -m machine_learning.soh_prediction"
            )
        self._model = joblib.load(model_path)

    def predict(
        self,
        cycle_count: float,
        avg_discharge_rate_c: float = 0.5,
        depth_of_discharge: float = 0.8,
        avg_temperature_c: float = 25.0,
    ) -> float:
        """Return predicted SoH fraction (0.6–1.0)."""
        x = np.array([[
            cycle_count,
            avg_discharge_rate_c,
            depth_of_discharge,
            avg_temperature_c,
        ]])
        return float(np.clip(self._model.predict(x)[0], 0.6, 1.0))

    def health_label(self, soh: float) -> str:
        """Convert SoH fraction to a human-readable health category."""
        if soh >= 0.90:
            return "Excellent"
        elif soh >= 0.80:
            return "Good"
        elif soh >= 0.70:
            return "Fair"
        else:
            return "Poor (consider replacement)"


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("Generating synthetic SoH dataset ...")
    data = generate_soh_dataset(n_samples=10_000)
    print(f"  Dataset size: {len(data)} rows")
    print(f"  SoH range:   [{data['soh'].min():.3f}, {data['soh'].max():.3f}]")

    print("Training SoH model ...")
    model, metrics = train_soh_model(data)

    print(f"\n  R2 score:  {metrics['r2']:.4f}")
    print(f"  RMSE:      {metrics['rmse']:.4f}")
    print("Done.")
