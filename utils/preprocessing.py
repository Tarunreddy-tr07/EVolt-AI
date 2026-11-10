"""
utils/preprocessing.py
-----------------------
Phase 1: Data Preprocessing for EV-Charging-RL-System

Reads raw data/ev_dataset.csv (ACN-Data, Caltech 2020) and outputs:
  - data/processed_data.csv       : cleaned, feature-enriched session data
  - data/arrival_distributions.json : empirical distributions for the RL environment

Usage (standalone):
    python -m utils.preprocessing
    python utils/preprocessing.py
"""

import json
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from dateutil import parser as dateutil_parser
from scipy import stats

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# Paths (relative to project root)
# ─────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_CSV      = PROJECT_ROOT / "data" / "ev_dataset.csv"
PROCESSED_CSV = PROJECT_ROOT / "data" / "processed_data.csv"
DIST_JSON    = PROJECT_ROOT / "data" / "arrival_distributions.json"


# ─────────────────────────────────────────────
# 1. Parsing helpers
# ─────────────────────────────────────────────

def _parse_rfc1123(series: pd.Series) -> pd.Series:
    """
    Parse a Series of RFC 1123 strings like 'Wed, 01 Jan 2020 02:12:11 GMT'
    into tz-naive UTC datetimes.  Handles NaN gracefully.
    """
    def _parse_one(val):
        if pd.isna(val) or str(val).strip() == "":
            return pd.NaT
        try:
            return dateutil_parser.parse(str(val)).replace(tzinfo=None)
        except Exception:
            return pd.NaT

    return series.map(_parse_one)


# ─────────────────────────────────────────────
# 2. Main preprocessing function
# ─────────────────────────────────────────────

def preprocess(raw_path: Path = RAW_CSV,
               out_csv: Path = PROCESSED_CSV,
               out_json: Path = DIST_JSON,
               verbose: bool = True) -> pd.DataFrame:
    """
    Full preprocessing pipeline.

    Returns
    -------
    pd.DataFrame
        Cleaned, feature-enriched DataFrame (also saved to out_csv).
    """
    if verbose:
        print(f"[preprocessing] Reading {raw_path} ...")

    df = pd.read_csv(raw_path, low_memory=False)
    n_raw = len(df)
    if verbose:
        print(f"  Raw rows: {n_raw}")

    # ── 2a. Parse datetime columns ──────────────────────────────────────
    datetime_cols = ["connectionTime", "disconnectTime",
                     "doneChargingTime", "requestedDeparture"]
    for col in datetime_cols:
        if col in df.columns:
            df[col] = _parse_rfc1123(df[col])

    # ── 2b. Drop rows with missing/invalid connection or disconnect time ──
    required = ["connectionTime", "disconnectTime"]
    before = len(df)
    df = df.dropna(subset=required)
    if verbose:
        dropped = before - len(df)
        print(f"  Dropped {dropped} rows with null connectionTime/disconnectTime")

    # ── 2c. Derived columns ──────────────────────────────────────────────
    # Dwell duration
    df["dwell_hours"] = (
        df["disconnectTime"] - df["connectionTime"]
    ).dt.total_seconds() / 3600.0

    # Drop sessions with non-positive dwell time (data errors)
    before = len(df)
    df = df[df["dwell_hours"] > 0].copy()
    if verbose:
        dropped = before - len(df)
        print(f"  Dropped {dropped} rows with dwell_hours <= 0")

    # Cap unrealistically long sessions (> 72 hours = data error)
    before = len(df)
    df = df[df["dwell_hours"] <= 72].copy()
    if verbose:
        dropped = before - len(df)
        print(f"  Dropped {dropped} rows with dwell_hours > 72")

    # Arrival features
    df["arrival_hour"]      = df["connectionTime"].dt.hour
    df["arrival_dayofweek"] = df["connectionTime"].dt.dayofweek  # 0=Mon

    # Weekend flag
    df["is_weekend"] = (df["arrival_dayofweek"] >= 5).astype(int)

    # Energy requested — fall back to delivered when missing
    df["energy_requested_kwh"] = df["kWhRequested"].fillna(df["kWhDelivered"])

    # Guard: energy_requested must be positive
    df["energy_requested_kwh"] = df["energy_requested_kwh"].clip(lower=0.01)

    # Implied minimum charge rate needed to fulfil demand within dwell window
    df["required_charge_rate_kw"] = df["energy_requested_kwh"] / df["dwell_hours"]

    # Efficiency (Wh/mile), fill missing with dataset median
    median_wh_per_mile = df["WhPerMile"].median()
    df["WhPerMile"] = df["WhPerMile"].fillna(median_wh_per_mile)

    # Estimated battery capacity (kWh) — proxy from energy requested + 20% buffer
    # Real capacity unknown; this is just for ML model features
    df["estimated_battery_capacity_kwh"] = (df["energy_requested_kwh"] * 1.2).clip(upper=100)

    # kWhDelivered fill (should always be present, but just in case)
    df["kWhDelivered"] = df["kWhDelivered"].fillna(0)

    # Departure — time from connection to requested departure (hours)
    df["requested_dwell_hours"] = None
    mask = df["requestedDeparture"].notna()
    df.loc[mask, "requested_dwell_hours"] = (
        df.loc[mask, "requestedDeparture"] - df.loc[mask, "connectionTime"]
    ).dt.total_seconds() / 3600.0
    # Fall back to actual dwell if no requestedDeparture
    df["requested_dwell_hours"] = (
        pd.to_numeric(df["requested_dwell_hours"], errors="coerce")
          .fillna(df["dwell_hours"])
    )
    # Clip nonsensical values
    df["requested_dwell_hours"] = df["requested_dwell_hours"].clip(lower=0.1)

    # Session date (for grouping)
    df["session_date"] = df["connectionTime"].dt.date

    if verbose:
        print(f"  Final clean rows: {len(df)}")
        null_check_cols = [
            "arrival_hour", "arrival_dayofweek", "dwell_hours",
            "energy_requested_kwh", "required_charge_rate_kw"
        ]
        nulls = df[null_check_cols].isnull().sum()
        print(f"  Null counts in RL-required columns:\n{nulls}")

    # ── 2d. Save processed CSV ───────────────────────────────────────────
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    if verbose:
        print(f"  Saved -> {out_csv}")

    # ── 2e. Build and save distributions ────────────────────────────────
    dist = _build_distributions(df, verbose=verbose)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w") as f:
        json.dump(dist, f, indent=2)
    if verbose:
        print(f"  Saved -> {out_json}")

    return df


# ─────────────────────────────────────────────
# 3. Distribution builder
# ─────────────────────────────────────────────

def _build_distributions(df: pd.DataFrame, verbose: bool = True) -> dict:
    """
    Build empirical arrival, energy, and dwell distributions from clean data.

    Returns a dict suitable for JSON serialisation that the RL environment
    uses to sample new EV arrivals at reset/step time.
    """
    dist = {
        "arrival_rate": {},   # hour -> probability (weekday / weekend)
        "energy_demand": {},  # weekday / weekend KDE params
        "dwell_time": {},     # weekday / weekend KDE params
        "summary_stats": {}
    }

    for day_type, label in [(0, "weekday"), (1, "weekend")]:
        subset = df[df["is_weekend"] == day_type]
        if len(subset) < 10:
            if verbose:
                print(f"  Warning: too few {label} samples ({len(subset)}), using full dataset")
            subset = df

        # ── Arrival rate: sessions per hour, normalised to probabilities ──
        hour_counts = subset["arrival_hour"].value_counts().sort_index()
        # Ensure all 24 hours exist
        hour_counts = hour_counts.reindex(range(24), fill_value=0)
        total = hour_counts.sum()
        hour_probs = (hour_counts / total).to_dict()

        dist["arrival_rate"][label] = {
            str(h): float(p) for h, p in hour_probs.items()
        }

        # ── Energy demand distribution ────────────────────────────────────
        energy = subset["energy_requested_kwh"].dropna()
        energy_stats = _fit_lognormal(energy, name=f"{label}_energy")
        dist["energy_demand"][label] = energy_stats

        # ── Dwell time distribution ───────────────────────────────────────
        dwell = subset["dwell_hours"].dropna()
        dwell_stats = _fit_lognormal(dwell, name=f"{label}_dwell")
        dist["dwell_time"][label] = dwell_stats

    # ── Summary statistics ────────────────────────────────────────────────
    dist["summary_stats"] = {
        "total_sessions": int(len(df)),
        "weekday_sessions": int((df["is_weekend"] == 0).sum()),
        "weekend_sessions": int((df["is_weekend"] == 1).sum()),
        "median_energy_kwh": float(df["energy_requested_kwh"].median()),
        "median_dwell_hours": float(df["dwell_hours"].median()),
        "p95_energy_kwh": float(df["energy_requested_kwh"].quantile(0.95)),
        "p95_dwell_hours": float(df["dwell_hours"].quantile(0.95)),
        "max_required_rate_kw": float(df["required_charge_rate_kw"].quantile(0.99)),
        "avg_sessions_per_day": float(
            df.groupby("session_date").size().mean()
        ),
    }

    if verbose:
        print(f"  Distribution summary: {dist['summary_stats']}")

    return dist


def _fit_lognormal(series: pd.Series, name: str = "") -> dict:
    """
    Fit a log-normal distribution to a positive-valued series.
    Returns {mu, sigma, min, max, percentiles} for environment sampling.
    """
    vals = series[series > 0].values
    if len(vals) < 5:
        return {"mu": 0.0, "sigma": 1.0, "min": 0.1, "max": 10.0,
                "p5": 0.1, "p25": 1.0, "p50": 2.0, "p75": 5.0, "p95": 10.0}

    log_vals = np.log(vals)
    mu    = float(np.mean(log_vals))
    sigma = float(np.std(log_vals))

    return {
        "distribution": "lognormal",
        "mu":    mu,
        "sigma": sigma,
        "min":   float(np.min(vals)),
        "max":   float(np.max(vals)),
        "p5":    float(np.percentile(vals,  5)),
        "p25":   float(np.percentile(vals, 25)),
        "p50":   float(np.percentile(vals, 50)),
        "p75":   float(np.percentile(vals, 75)),
        "p95":   float(np.percentile(vals, 95)),
    }


# ─────────────────────────────────────────────
# 4. Sampler (used by RL environment at runtime)
# ─────────────────────────────────────────────

class ArrivalSampler:
    """
    Lightweight class that the RL environment instantiates once and calls
    per timestep to stochastically generate new EV arrivals.

    Parameters
    ----------
    dist_json_path : str or Path
        Path to arrival_distributions.json produced by preprocess().
    rng_seed : int, optional
    """

    def __init__(self, dist_json_path: Path = DIST_JSON, rng_seed: int = None):
        with open(dist_json_path, "r") as f:
            self._dist = json.load(f)
        self._rng = np.random.default_rng(rng_seed)

    def sample_energy_kwh(self, is_weekend: bool = False) -> float:
        """Draw an energy demand (kWh) from the fitted log-normal."""
        label = "weekend" if is_weekend else "weekday"
        params = self._dist["energy_demand"][label]
        val = self._rng.lognormal(params["mu"], params["sigma"])
        return float(np.clip(val, params["min"], params["max"]))

    def sample_dwell_hours(self, is_weekend: bool = False) -> float:
        """Draw a dwell duration (hours) from the fitted log-normal."""
        label = "weekend" if is_weekend else "weekday"
        params = self._dist["dwell_time"][label]
        val = self._rng.lognormal(params["mu"], params["sigma"])
        return float(np.clip(val, 0.25, params["max"]))  # min 15 min

    def arrivals_this_step(self, hour: int, is_weekend: bool = False,
                            step_fraction: float = 0.25) -> int:
        """
        Stochastically decide how many EVs arrive in a 15-min window.

        Parameters
        ----------
        hour : int            Current hour of the simulated day (0–23).
        is_weekend : bool     Weekend flag.
        step_fraction : float Fraction of hour in this timestep (0.25 for 15 min).

        Returns
        -------
        int   Number of new arrivals (0, 1, or rarely 2).
        """
        label = "weekend" if is_weekend else "weekday"
        hourly_prob = self._dist["arrival_rate"][label].get(str(hour), 0.0)

        # avg_sessions_per_day × hourly_prob = expected arrivals this hour
        avg_per_day = self._dist["summary_stats"]["avg_sessions_per_day"]
        expected_per_hour = avg_per_day * hourly_prob
        expected_per_step = expected_per_hour * step_fraction

        # Poisson draw for integer count
        return int(self._rng.poisson(expected_per_step))

    @property
    def summary_stats(self) -> dict:
        return self._dist["summary_stats"]


# ─────────────────────────────────────────────
# 5. Entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    # Force UTF-8 output on Windows to avoid cp1252 issues
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    df = preprocess(verbose=True)
    print("\n--- Sample of processed data ---")
    cols = [
        "sessionID", "arrival_hour", "arrival_dayofweek", "is_weekend",
        "dwell_hours", "energy_requested_kwh", "required_charge_rate_kw"
    ]
    print(df[cols].head(10).to_string(index=False))
    print(f"\nShape: {df.shape}")
    print("Done.")
