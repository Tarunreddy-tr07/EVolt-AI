"""
machine_learning/soc_prediction.py
-------------------------------------
Phase 4a: State-of-Charge (SoC) Prediction Model.

Since ACN-Data doesn't provide continuous SoC readings, we generate
synthetic SoC curves using a piecewise-linear + logistic-tail model
(mimics real lithium-ion charging physics), then train a Random Forest
regressor to predict SoC given observable features.

The trained model is used by battery_manager.py to feed SoC estimates
into the RL environment's state vector.

Features:
    - time_elapsed_frac  : fraction of session elapsed (0–1)
    - charge_rate_kw     : current charging rate (kW)
    - battery_capacity_kwh: estimated battery size (kWh)
    - energy_delivered_kwh: kWh delivered so far

Target:
    - soc : state of charge (0.0–1.0)

Usage:
    python -m machine_learning.soc_prediction
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────

_ROOT         = Path(__file__).resolve().parent.parent
PROCESSED_CSV = _ROOT / "data" / "processed_data.csv"
SAVED_MODELS  = Path(__file__).resolve().parent / "saved_models"
SOC_MODEL_PATH = SAVED_MODELS / "soc_model.joblib"


# ─────────────────────────────────────────────
# Synthetic SoC curve generator
# ─────────────────────────────────────────────

def _soc_curve(time_elapsed_frac: float) -> float:
    """
    Piecewise-linear + logistic tail SoC model.

    Phase 1 (CC): 0 → 80% linearly over first 80% of time.
    Phase 2 (CV): 80% → 100% with exponential tapering over last 20%.

    Parameters
    ----------
    time_elapsed_frac : float  in [0, 1]

    Returns
    -------
    float  SoC in [0, 1]
    """
    t = float(np.clip(time_elapsed_frac, 0.0, 1.0))
    if t <= 0.8:
        # Constant-current phase: linear ramp
        return t / 0.8 * 0.8   # reaches 0.8 at t=0.8
    else:
        # Constant-voltage phase: exponential tapering
        tail_t = (t - 0.8) / 0.2        # 0 → 1 in tail
        extra  = 0.2 * (1 - np.exp(-4 * tail_t)) / (1 - np.exp(-4))
        return min(0.8 + extra, 1.0)


# ─────────────────────────────────────────────
# Dataset generation
# ─────────────────────────────────────────────

def generate_soc_dataset(
    csv_path: Path = PROCESSED_CSV,
    points_per_session: int = 20,
    noise_std: float = 0.01,
    rng_seed: int = 42,
) -> pd.DataFrame:
    """
    Generate a synthetic SoC dataset from processed_data.csv.

    For each real session, sample `points_per_session` time points
    and compute SoC using the piecewise model, adding small Gaussian noise.
    """
    df = pd.read_csv(csv_path)
    rng = np.random.default_rng(rng_seed)

    rows = []
    for _, session in df.iterrows():
        capacity    = float(session.get("estimated_battery_capacity_kwh", 40.0))
        energy_tgt  = float(session.get("energy_requested_kwh", 20.0))
        dwell_h     = float(session.get("dwell_hours", 4.0))
        charge_rate = float(session.get("required_charge_rate_kw", 3.3))
        charge_rate = np.clip(charge_rate, 0.5, 6.6)

        # Sample random time points within the session
        t_fracs = np.sort(rng.uniform(0.0, 1.0, points_per_session))
        for t_frac in t_fracs:
            true_soc    = _soc_curve(t_frac)
            noisy_soc   = float(np.clip(true_soc + rng.normal(0, noise_std), 0.0, 1.0))
            energy_deliv = t_frac * energy_tgt

            rows.append({
                "time_elapsed_frac":      t_frac,
                "charge_rate_kw":         charge_rate,
                "battery_capacity_kwh":   capacity,
                "energy_delivered_kwh":   energy_deliv,
                "soc":                    noisy_soc,
            })

    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# Training
# ─────────────────────────────────────────────

FEATURE_COLS = [
    "time_elapsed_frac",
    "charge_rate_kw",
    "battery_capacity_kwh",
    "energy_delivered_kwh",
]
TARGET_COL = "soc"


def train_soc_model(
    data: pd.DataFrame = None,
    save_path: Path = SOC_MODEL_PATH,
    n_estimators: int = 200,
    test_size: float = 0.2,
    seed: int = 42,
) -> tuple:
    """
    Train a Random Forest regressor for SoC prediction.

    Returns (model, metrics_dict).
    """
    if data is None:
        data = generate_soc_dataset()

    X = data[FEATURE_COLS].values
    y = data[TARGET_COL].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed
    )

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=12,
        min_samples_leaf=4,
        n_jobs=-1,
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

    # Save
    save_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, save_path)
    print(f"  SoC model saved -> {save_path}  |  R2={metrics['r2']:.4f}  RMSE={metrics['rmse']:.4f}")

    return model, metrics


# ─────────────────────────────────────────────
# Inference API
# ─────────────────────────────────────────────

class SoCPredictor:
    """Thin wrapper around the trained model for runtime inference."""

    def __init__(self, model_path: Path = SOC_MODEL_PATH):
        if not model_path.exists():
            raise FileNotFoundError(
                f"SoC model not found at {model_path}. "
                "Run: python -m machine_learning.soc_prediction"
            )
        self._model = joblib.load(model_path)

    def predict(
        self,
        time_elapsed_frac: float,
        charge_rate_kw: float,
        battery_capacity_kwh: float,
        energy_delivered_kwh: float,
    ) -> float:
        """Return predicted SoC (0.0–1.0)."""
        x = np.array([[
            time_elapsed_frac,
            charge_rate_kw,
            battery_capacity_kwh,
            energy_delivered_kwh,
        ]])
        return float(np.clip(self._model.predict(x)[0], 0.0, 1.0))


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("Generating synthetic SoC dataset from processed_data.csv ...")
    data = generate_soc_dataset()
    print(f"  Dataset size: {len(data)} rows")

    print("Training SoC model ...")
    model, metrics = train_soc_model(data)

    print(f"\n  R2 score:  {metrics['r2']:.4f}")
    print(f"  RMSE:      {metrics['rmse']:.4f}")
    print("Done.")
