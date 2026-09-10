import math
from typing import Dict, Any

class PhysicsEngineDigitalTwin:
    """
    First-Principles Thermodynamic Physics Digital Twin:
    Predicts expected nominal physics baseline state of the IC Engine and Electric Drive
    as a function of operational inputs (Throttle %, RPM, Altitude ft, Ambient Temp °C).
    """

    def predict_expected_state(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        rpm = telemetry.get("piston_rpm", 3360.0)
        throttle = telemetry.get("throttle_pct", 60.0)
        altitude = telemetry.get("altitude_ft", 2000.0)
        ambient_temp = telemetry.get("ambient_temp_c", 25.0)

        # Ambient air pressure drop with altitude
        pressure_ratio = math.exp(-altitude / 27000.0)
        cooling_air_density = pressure_ratio

        # 1. Physics Expected CHT (°C)
        # Expected CHT depends on combustion heat generation vs cooling mass flow
        cooling_efficiency = max(0.4, cooling_air_density * 0.9 + 0.1)
        heat_gen = ambient_temp + 105.0 * (throttle / 100.0)**1.2 + (rpm / 6000.0) * 42.0
        exp_cht = heat_gen / cooling_efficiency

        # 2. Physics Expected EGT (°C)
        # Stoichiometric air-fuel ratio baseline calculation
        exp_egt = 460.0 + 310.0 * (throttle / 100.0)**0.9

        # 3. Physics Expected Oil Pressure (PSI)
        # Viscosity model baseline
        exp_oil_temp = ambient_temp + 55.0 + (throttle / 100.0) * 35.0
        viscosity_factor = max(0.6, 1.0 - (exp_oil_temp - 80.0) * 0.005)
        exp_oil_p = (25.0 + (rpm / 6000.0) * 45.0) * viscosity_factor

        # 4. Physics Expected Fuel Flow (L/h)
        exp_fuel_flow = 1.5 + 18.0 * (throttle / 100.0)**1.3 * pressure_ratio

        # 5. Physics Expected Vibration RMS (g)
        exp_vibration = 0.4 + (rpm / 6000.0)**2 * 1.8

        # 6. Electric Drive Expected Voltage & Current
        load_fraction = throttle / 100.0
        exp_bus_voltage = 52.0 - load_fraction * 6.5
        exp_bus_current = load_fraction * 120.0
        exp_motor_temp = 40.0 + load_fraction * 40.0

        return {
            "exp_ekart_rpm": round(rpm / 1.05, 1),
            "exp_piston_rpm": round(rpm, 1),
            "exp_cht_deg_c": round(exp_cht, 2),
            "exp_egt_deg_c": round(exp_egt, 2),
            "exp_oil_pressure_psi": round(exp_oil_p, 2),
            "exp_oil_temp_deg_c": round(exp_oil_temp, 2),
            "exp_fuel_flow_lph": round(exp_fuel_flow, 2),
            "exp_vibration_g": round(exp_vibration, 3),
            "exp_bus_voltage": round(exp_bus_voltage, 2),
            "exp_bus_current": round(exp_bus_current, 2),
            "exp_motor_temp": round(exp_motor_temp, 2)
        }
