from typing import Dict, Any, List

class FeatureExtractor:
    """
    Sensor Fusion & Feature Extraction Engine:
    Computes higher-order engine analytics:
    - Electrical Power (kW) = Bus Voltage * Bus Current / 1000
    - Mechanical Power Output (kW) estimate from RPM & Torque
    - BSFC (Brake Specific Fuel Consumption - g/kWh)
    - Thermal Stress Gradient (EGT / CHT ratio & delta)
    - Vibration Energy Index
    - Rolling window statistics
    """
    def __init__(self, history_size: int = 20):
        self.history_size = history_size
        self.history: List[Dict[str, Any]] = []

    def extract_features(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        self.history.append(snapshot)
        if len(self.history) > self.history_size:
            self.history.pop(0)

        # Basic derived metrics
        voltage = snapshot.get("bus_voltage", 48.0)
        current = snapshot.get("bus_current", 45.0)
        elec_power_kw = (voltage * current) / 1000.0

        piston_rpm = snapshot.get("piston_rpm", 3360.0)
        torque_pct = snapshot.get("torque_pct", 50.0)
        # Estimated Mechanical kW
        mech_power_kw = (2 * 3.14159 * piston_rpm * (torque_pct * 0.45)) / 60000.0

        total_hybrid_power_kw = max(0.1, elec_power_kw + mech_power_kw)

        fuel_flow_lph = snapshot.get("fuel_flow_lph", 8.5)
        fuel_density_kg_l = 0.75
        fuel_flow_gph = fuel_flow_lph * fuel_density_kg_l * 1000.0  # g/h
        bsfc = fuel_flow_gph / max(0.5, total_hybrid_power_kw)       # g/kWh

        cht = snapshot.get("cht_deg_c", 135.0)
        egt = snapshot.get("egt_deg_c", 650.0)
        thermal_ratio = egt / max(1.0, cht)

        # Rate of change CHT / Rate of change Oil Temp
        if len(self.history) >= 5:
            cht_prev = self.history[-5].get("cht_deg_c", cht)
            dcht_dt = (cht - cht_prev) / 0.5  # 5 steps * 0.1s = 0.5s
        else:
            dcht_dt = 0.0

        vibration_g = snapshot.get("vibration_g", 0.85)

        features = snapshot.copy()
        features.update({
            "elec_power_kw": round(elec_power_kw, 2),
            "mech_power_kw": round(mech_power_kw, 2),
            "total_power_kw": round(total_hybrid_power_kw, 2),
            "bsfc_g_kwh": round(bsfc, 1),
            "thermal_ratio_egt_cht": round(thermal_ratio, 2),
            "dcht_dt": round(dcht_dt, 2),
            "vibration_energy": round(vibration_g**2, 3)
        })
        return features
