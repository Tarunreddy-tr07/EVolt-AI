import os
from pathlib import Path
import joblib
import numpy as np

# Resolve model paths
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SOC_MODEL_PATH = _ROOT / "machine_learning" / "saved_models" / "soc_model.joblib"
SOH_MODEL_PATH = _ROOT / "machine_learning" / "saved_models" / "soh_model.joblib"

class MLModelService:
    def __init__(self):
        self.soc_model = None
        self.soh_model = None
        self._load_models()

    def _load_models(self):
        try:
            if SOC_MODEL_PATH.exists():
                self.soc_model = joblib.load(SOC_MODEL_PATH)
                print(f"SoC model loaded from {SOC_MODEL_PATH}")
            else:
                print(f"Warning: SoC model not found at {SOC_MODEL_PATH}")

            if SOH_MODEL_PATH.exists():
                self.soh_model = joblib.load(SOH_MODEL_PATH)
                print(f"SoH model loaded from {SOH_MODEL_PATH}")
            else:
                print(f"Warning: SoH model not found at {SOH_MODEL_PATH}")
        except Exception as e:
            print(f"Error loading ML models: {e}")

    def predict_soc(
        self,
        time_elapsed_frac: float,
        charge_rate_kw: float,
        battery_capacity_kwh: float,
        energy_delivered_kwh: float
    ) -> float:
        """Predict battery state of charge (0.0 - 1.0)"""
        if self.soc_model is None:
            # Simple linear fallback if model is missing
            return min(1.0, max(0.0, time_elapsed_frac))
        
        X = np.array([[
            time_elapsed_frac,
            charge_rate_kw,
            battery_capacity_kwh,
            energy_delivered_kwh
        ]])
        pred = self.soc_model.predict(X)[0]
        return float(np.clip(pred, 0.0, 1.0))

    def predict_soh(
        self,
        cycle_count: float,
        avg_discharge_rate_c: float = 0.5,
        depth_of_discharge: float = 0.8,
        avg_temperature_c: float = 25.0
    ) -> float:
        """Predict battery state of health (0.6 - 1.0)"""
        if self.soh_model is None:
            # Fallback capacity fade formula if model is missing
            fade = 0.02 * (cycle_count ** 0.5) * np.exp(0.15 * depth_of_discharge)
            return float(np.clip(1.0 - fade, 0.6, 1.0))
        
        X = np.array([[
            cycle_count,
            avg_discharge_rate_c,
            depth_of_discharge,
            avg_temperature_c
        ]])
        pred = self.soh_model.predict(X)[0]
        return float(np.clip(pred, 0.6, 1.0))

    def get_health_label(self, soh: float) -> str:
        if soh >= 0.90:
            return "Excellent"
        elif soh >= 0.80:
            return "Good"
        elif soh >= 0.70:
            return "Fair"
        else:
            return "Poor (consider replacement)"

# Instantiate global service
ml_service = MLModelService()
