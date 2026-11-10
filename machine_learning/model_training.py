"""
machine_learning/model_training.py
-------------------------------------
Phase 4: Shared training harness.

Trains both SoC and SoH models in one command and reports metrics.

Usage:
    python -m machine_learning.model_training
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from machine_learning.soc_prediction import (
    generate_soc_dataset, train_soc_model
)
from machine_learning.soh_prediction import (
    generate_soh_dataset, train_soh_model
)


def train_all(verbose: bool = True) -> dict:
    """Train both ML models and return metrics dict."""
    results = {}

    if verbose:
        print("=" * 50)
        print("Phase 4 — ML Model Training")
        print("=" * 50)

    # ── SoC Model ───────────────────────────────────────────────────────
    if verbose:
        print("\n[1/2] SoC Prediction Model")
        print("  Generating synthetic SoC dataset ...")
    soc_data  = generate_soc_dataset(points_per_session=20)
    if verbose:
        print(f"  Dataset: {len(soc_data)} samples")
        print("  Training RandomForestRegressor ...")
    _, soc_metrics = train_soc_model(soc_data)
    results["soc"] = soc_metrics

    # ── SoH Model ───────────────────────────────────────────────────────
    if verbose:
        print("\n[2/2] SoH Prediction Model")
        print("  Generating synthetic SoH dataset (10,000 battery histories) ...")
    soh_data = generate_soh_dataset(n_samples=10_000)
    if verbose:
        print(f"  Dataset: {len(soh_data)} samples")
        print("  Training GradientBoostingRegressor ...")
    _, soh_metrics = train_soh_model(soh_data)
    results["soh"] = soh_metrics

    # ── Summary ──────────────────────────────────────────────────────────
    if verbose:
        print("\n" + "=" * 50)
        print("Training Complete — Metrics Summary")
        print("=" * 50)
        print(f"  SoC  |  R2={soc_metrics['r2']:.4f}  RMSE={soc_metrics['rmse']:.4f}  "
              f"(train={soc_metrics['n_train']}, test={soc_metrics['n_test']})")
        print(f"  SoH  |  R2={soh_metrics['r2']:.4f}  RMSE={soh_metrics['rmse']:.4f}  "
              f"(train={soh_metrics['n_train']}, test={soh_metrics['n_test']})")

    return results


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    train_all(verbose=True)
