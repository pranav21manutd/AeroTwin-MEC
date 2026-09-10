from typing import Dict, Any

class ResidualEngine:
    """
    Residual Engine:
    Residual = Actual Sensor Telemetry - Digital Twin Expected Prediction
    A nonzero residual vector indicates physical degradation, environmental deviation,
    or component failure.
    """
    def compute_residuals(self, actual: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
        residuals = {
            "res_cht": round(actual.get("cht_deg_c", 0) - expected.get("exp_cht_deg_c", 0), 2),
            "res_egt": round(actual.get("egt_deg_c", 0) - expected.get("exp_egt_deg_c", 0), 2),
            "res_oil_pressure": round(actual.get("oil_pressure_psi", 0) - expected.get("exp_oil_pressure_psi", 0), 2),
            "res_oil_temp": round(actual.get("oil_temp_deg_c", 0) - expected.get("exp_oil_temp_deg_c", 0), 2),
            "res_fuel_flow": round(actual.get("fuel_flow_lph", 0) - expected.get("exp_fuel_flow_lph", 0), 2),
            "res_vibration": round(actual.get("vibration_g", 0) - expected.get("exp_vibration_g", 0), 3),
            "res_bus_voltage": round(actual.get("bus_voltage", 0) - expected.get("exp_bus_voltage", 0), 2),
            "res_bus_current": round(actual.get("bus_current", 0) - expected.get("exp_bus_current", 0), 2)
        }

        # Calculate normalized Mahalanobis / Euclidean Norm of Residuals
        # Normalized by typical standard deviation parameters
        norm_cht = abs(residuals["res_cht"]) / 15.0
        norm_egt = abs(residuals["res_egt"]) / 30.0
        norm_oil_p = abs(residuals["res_oil_pressure"]) / 8.0
        norm_vib = abs(residuals["res_vibration"]) / 0.5

        residual_score = float((norm_cht**2 + norm_egt**2 + norm_oil_p**2 + norm_vib**2)**0.5)
        residuals["total_residual_norm"] = round(residual_score, 3)

        return residuals
