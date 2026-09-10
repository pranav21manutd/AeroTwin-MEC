import time
from typing import Dict, Any
from app.telemetry.can_listener import CANListener
from app.telemetry.aero_simulator import AeroEngineSimulator

class TelemetryLayer:
    """
    Telemetry Pipeline Layer:
    - Synchronizes eKart SocketCAN/Virtual data & Aero Engine thermodynamic telemetry.
    - Applies timestamping & range validation checks.
    - Yields clean unified real-time snapshot vector.
    """
    def __init__(self, can_channel: str = "vcan0", mock_can: bool = True):
        self.can_listener = CANListener(channel=can_channel, mock=mock_can)
        self.aero_simulator = AeroEngineSimulator()

    def get_unified_snapshot(self, target_rpm: float = 3200.0) -> Dict[str, Any]:
        timestamp = time.time()
        
        # Acquire eKart CAN frame state
        ekart_data = self.can_listener.read_frame(target_rpm=target_rpm)
        
        # Acquire Aero Piston engine simulation state synchronized to eKart RPM
        aero_data = self.aero_simulator.step(ekart_rpm=ekart_data.get("ekart_rpm", 3200.0))

        # Merge telemetry vector
        raw_snapshot = {
            "timestamp": round(timestamp, 3),
            "ekart_rpm": ekart_data.get("ekart_rpm", 3200.0),
            "bus_voltage": ekart_data.get("bus_voltage", 48.0),
            "bus_current": ekart_data.get("bus_current", 45.0),
            "torque_pct": ekart_data.get("torque_pct", 50.0),
            "controller_temp": ekart_data.get("controller_temp", 40.0),
            "motor_temp": ekart_data.get("motor_temp", 55.0),
            "can_status": ekart_data.get("can_status", "VIRTUAL_CAN"),
            "piston_rpm": aero_data.get("piston_rpm", 3360.0),
            "cht_deg_c": aero_data.get("cht_deg_c", 135.0),
            "egt_deg_c": aero_data.get("egt_deg_c", 650.0),
            "oil_pressure_psi": aero_data.get("oil_pressure_psi", 45.0),
            "oil_temp_deg_c": aero_data.get("oil_temp_deg_c", 85.0),
            "fuel_flow_lph": aero_data.get("fuel_flow_lph", 8.5),

            "injection_timing_btdc": aero_data.get("injection_timing_btdc", 28.0),
            "vibration_g": aero_data.get("vibration_g", 0.85),
            "altitude_ft": aero_data.get("altitude_ft", 2000.0),
            "ambient_temp_c": aero_data.get("ambient_temp_c", 25.0),
            "throttle_pct": aero_data.get("throttle_pct", 60.0),
            "sim_fault_active": aero_data.get("sim_fault_active", "NONE")
        }

        # Data Validation & Range Guardrails
        validated_snapshot = self._validate(raw_snapshot)
        return validated_snapshot

    def _validate(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures physical bounds and flags sensor out-of-range sensor dropouts."""
        snapshot["validity_flag"] = True
        if snapshot["bus_voltage"] < 0 or snapshot["bus_voltage"] > 100:
            snapshot["validity_flag"] = False
        if snapshot["cht_deg_c"] < -40 or snapshot["cht_deg_c"] > 450:
            snapshot["validity_flag"] = False
        return snapshot
