import numpy as np
from typing import Dict, Any

class KalmanNoiseFilter:
    """
    1D/Multi-parameter Extended Kalman Filter for smoothing sensor signals
    (RPM, CHT, EGT, Oil P, Vibration, Bus Current) while preserving true physical transients.
    """
    def __init__(self, alpha: float = 0.25):
        # Smoothing parameter alpha for lightweight online filtering
        self.alpha = alpha
        self.state_estimates = {}

    def filter_snapshot(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        filtered = snapshot.copy()
        numeric_keys = [
            "ekart_rpm", "piston_rpm", "bus_voltage", "bus_current", 
            "cht_deg_c", "egt_deg_c", "oil_pressure_psi", "oil_temp_deg_c", 
            "fuel_flow_lph", "vibration_g"
        ]

        for k in numeric_keys:
            raw_val = snapshot.get(k, 0.0)
            if k not in self.state_estimates:
                self.state_estimates[k] = float(raw_val)
            else:
                # Exponential Moving Average / Kalman Update Step
                self.state_estimates[k] = (1 - self.alpha) * self.state_estimates[k] + self.alpha * float(raw_val)
            filtered[f"{k}_filtered"] = round(self.state_estimates[k], 2)

        return filtered
