import math
import random
import time
from typing import Dict, Any, Optional

class AeroEngineSimulator:
    """
    Simulates physical thermodynamic parameters for a high-performance 2-stroke/4-stroke
    UAV Piston Engine (e.g. 210cc Twin Cylinder IC Aero Engine).
    Generates CHT, EGT, Oil P, Oil T, Fuel Flow, Injection Timing, Vibration.
    Supports mission injection: High Altitude, Hot Weather, Rapid Throttle, Fault Modes.
    """

    def __init__(self):
        self.t = 0.0
        # Environmental state defaults
        self.altitude_ft = 2000.0  # MSL Altitude in feet
        self.ambient_temp_c = 25.0  # Ambient °C
        self.throttle_pct = 60.0    # 0 - 100 %
        self.fault_mode = "NONE"    # NONE, LUBRICATION_ISSUE, COMBUSTION_INSTABILITY, SENSOR_DRIFT, OVERHEATING, VIBRATION_SPIKE, ECU_DEGRADATION

    def set_environment(self, altitude_ft: float, ambient_temp_c: float, throttle_pct: float, fault_mode: str = "NONE"):
        self.altitude_ft = altitude_ft
        self.ambient_temp_c = ambient_temp_c
        self.throttle_pct = max(0.0, min(100.0, throttle_pct))
        self.fault_mode = fault_mode

    def step(self, ekart_rpm: float) -> Dict[str, Any]:
        self.t += 0.1
        
        # RPM is coupled with eKart electric drive or throttle input
        rpm = max(1000.0, min(7500.0, ekart_rpm * 1.05 + random.gauss(0, 10.0)))

        # Standard Air Density lapse rate with altitude
        # Air density ratio relative to Sea Level
        p_ratio = math.exp(-self.altitude_ft / 27000.0)

        # Baseline Thermodynamic Physics Equations:
        # CHT: Baseline ambient + function of throttle, RPM, and air density cooling
        # High altitude means less cooling airflow mass density!
        cooling_factor = p_ratio * 0.85 + 0.15
        steady_cht = self.ambient_temp_c + 110.0 * (self.throttle_pct / 100.0)**1.2 + (rpm / 6000.0) * 45.0
        cht = steady_cht / max(0.5, cooling_factor) + random.gauss(0, 0.8)

        # EGT: Peak combustion temp ~ 600 - 850 °C. Leaner at altitude if uncompensated!
        rich_lean_factor = 1.0 + (1.0 - p_ratio) * 0.25 # leaning effect at altitude
        egt = 450.0 + 320.0 * (self.throttle_pct / 100.0)**0.9 * rich_lean_factor + random.gauss(0, 3.5)

        # Oil Pressure: Proportional to RPM, inversely with Oil Temp
        base_oil_temp = self.ambient_temp_c + 55.0 + (self.throttle_pct / 100.0) * 35.0
        oil_temp = base_oil_temp + random.gauss(0, 0.4)
        
        # Viscosity drop with temp lowers pressure slightly
        oil_viscosity_factor = max(0.6, 1.0 - (oil_temp - 80.0) * 0.005)
        oil_pressure = (25.0 + (rpm / 6000.0) * 45.0) * oil_viscosity_factor + random.gauss(0, 0.5)

        # Fuel Flow (L/h): Proportional to RPM, Throttle, Air Density
        fuel_flow = (1.5 + 18.0 * (self.throttle_pct / 100.0)**1.3 * p_ratio) + random.gauss(0, 0.1)

        # Injection Timing (°BTDC): 22° at idle, up to 34° at max RPM
        injection_timing = 22.0 + (rpm / 7000.0) * 12.0 + random.gauss(0, 0.2)

        # Vibration RMS (g): Base engine imbalance at high RPM + harmonics
        vibration_rms = 0.4 + (rpm / 6000.0)**2 * 1.8 + random.gauss(0, 0.05)

        # INJECT FAULT MODES (For testing ML anomaly detection & diagnostics)
        if self.fault_mode == "LUBRICATION_ISSUE":
            oil_pressure *= 0.45  # Severe pressure drop (e.g. pump cavitation / leak)
            oil_temp += 38.0      # Oil temperature runaway
            vibration_rms += 1.2   # Increased friction vibration

        elif self.fault_mode == "COMBUSTION_INSTABILITY":
            egt += 95.0 * math.sin(self.t * 3.0) + random.gauss(0, 25.0) # High oscillation
            cht += 25.0
            fuel_flow *= 1.3
            vibration_rms += 0.95

        elif self.fault_mode == "SENSOR_DRIFT":
            # CHT sensor drift upward artificially by +35°C without physical changes
            cht += 45.0

        elif self.fault_mode == "OVERHEATING":
            cht += 65.0  # Extreme thermal surge
            oil_temp += 30.0
            egt += 50.0

        elif self.fault_mode == "ABNORMAL_VIBRATION":
            vibration_rms += 3.8 + 1.2 * math.sin(self.t * 12.0) # Bearing damage or prop unbalance

        elif self.fault_mode == "ECU_DEGRADATION":
            injection_timing += 8.5 * math.sin(self.t * 1.5)  # Misfires & timing jitter
            fuel_flow *= 1.25
            egt += 40.0

        return {
            "piston_rpm": round(rpm, 1),
            "cht_deg_c": round(cht, 2),
            "egt_deg_c": round(egt, 2),
            "oil_pressure_psi": round(max(0.0, oil_pressure), 2),
            "oil_temp_deg_c": round(oil_temp, 2),
            "fuel_flow_lph": round(max(0.0, fuel_flow), 2),
            "injection_timing_btdc": round(injection_timing, 2),
            "vibration_g": round(max(0.0, vibration_rms), 3),
            "altitude_ft": self.altitude_ft,
            "ambient_temp_c": self.ambient_temp_c,
            "throttle_pct": self.throttle_pct,
            "sim_fault_active": self.fault_mode
        }
