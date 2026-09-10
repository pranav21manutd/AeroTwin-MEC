import time
import math
import random
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("CANListener")

class CANFrameDecoder:
    """
    Decodes J1939 / eKart custom CAN bus frames into engineering units.
    Standard CAN IDs:
    - 0x0CF00400: Motor Speed (RPM) and Motor Torque (% / Nm)
    - 0x1804E0F4: DC Bus Voltage (V) and Battery Current (A)
    - 0x1805E0F4: Controller Temp (°C) and Motor Temp (°C)
    """

    @staticmethod
    def decode(can_id: int, data: bytes) -> Dict[str, Any]:
        result = {}
        if can_id == 0x0CF00400 and len(data) >= 8:
            # Bytes 1-2: Torque (-125 to +125%, 0.5%/bit, offset -125)
            raw_torque = data[2]
            result['torque_pct'] = round(raw_torque * 0.5 - 125.0, 2)
            
            # Bytes 3-4: Engine/Motor RPM (0.125 rpm/bit)
            raw_rpm = (data[4] << 8) | data[3]
            result['ekart_rpm'] = round(raw_rpm * 0.125, 1)

        elif can_id == 0x1804E0F4 and len(data) >= 8:
            # Bytes 0-1: DC Bus Voltage (0.1V/bit)
            raw_volt = (data[1] << 8) | data[0]
            result['bus_voltage'] = round(raw_volt * 0.1, 2)
            
            # Bytes 2-3: Motor Current (0.1A/bit, offset -1000)
            raw_curr = (data[3] << 8) | data[2]
            result['bus_current'] = round(raw_curr * 0.1 - 500.0, 2)

        elif can_id == 0x1805E0F4 and len(data) >= 8:
            # Byte 0: Controller Temp (offset -40)
            result['controller_temp'] = data[0] - 40
            # Byte 1: Motor Temp (offset -40)
            result['motor_temp'] = data[1] - 40

        return result

class CANListener:
    """
    Acquires real CAN telemetry via SocketCAN/python-can if available,
    or smoothly generates eKart CAN frames via virtual loopback.
    """
    def __init__(self, channel: str = "vcan0", bustype: str = "socketcan", mock: bool = True):
        self.channel = channel
        self.bustype = bustype
        self.mock = mock
        self.bus = None
        self._init_bus()
        self.current_state = {
            "ekart_rpm": 3200.0,
            "bus_voltage": 48.2,
            "bus_current": 45.0,
            "torque_pct": 55.0,
            "controller_temp": 42.0,
            "motor_temp": 58.0
        }
        self.t = 0.0

    def _init_bus(self):
        if not self.mock:
            try:
                import can
                self.bus = can.interface.Bus(channel=self.channel, bustype=self.bustype)
                logger.info(f"Connected to real CAN bus on {self.channel}")
            except Exception as e:
                logger.warning(f"Could not connect to CAN bus {self.channel}: {e}. Falling back to virtual CAN simulator.")
                self.mock = True

    def read_frame(self, target_rpm: Optional[float] = None) -> Dict[str, Any]:
        """Reads or synthesizes eKart CAN frame data."""
        self.t += 0.1
        if self.mock or self.bus is None:
            # Synthesize realistic eKart motor behavior responding to target throttle/rpm
            base_rpm = target_rpm if target_rpm is not None else 3200.0 + 800.0 * math.sin(self.t * 0.5)
            noise_rpm = random.gauss(0, 15.0)
            rpm = max(800.0, min(6500.0, base_rpm + noise_rpm))
            
            # Voltage & Current follow load (RPM & Torque)
            load = min(100.0, max(10.0, (rpm / 6500.0) * 100.0 + random.gauss(0, 2.0)))
            voltage = 52.0 - (load / 100.0) * 6.5 + random.gauss(0, 0.1)
            current = (load / 100.0) * 120.0 + random.gauss(0, 1.5)
            
            # Temps accumulate under load
            ctrl_temp = 35.0 + (load / 100.0) * 25.0 + 3.0 * math.sin(self.t * 0.05)
            motor_temp = 40.0 + (load / 100.0) * 40.0 + 5.0 * math.sin(self.t * 0.03)

            # Build synthetic raw CAN frames & decode
            # Frame 1: RPM & Torque
            raw_rpm_int = int(rpm / 0.125)
            raw_torque_int = int((load + 125.0) / 0.5)
            f1_bytes = bytes([0x00, 0x00, min(255, raw_torque_int), raw_rpm_int & 0xFF, (raw_rpm_int >> 8) & 0xFF, 0, 0, 0])
            
            # Frame 2: Volt & Curr
            raw_v_int = int(voltage / 0.1)
            raw_c_int = int((current + 500.0) / 0.1)
            f2_bytes = bytes([raw_v_int & 0xFF, (raw_v_int >> 8) & 0xFF, raw_c_int & 0xFF, (raw_c_int >> 8) & 0xFF, 0, 0, 0, 0])

            d1 = CANFrameDecoder.decode(0x0CF00400, f1_bytes)
            d2 = CANFrameDecoder.decode(0x1804E0F4, f2_bytes)
            
            self.current_state.update(d1)
            self.current_state.update(d2)
            self.current_state["controller_temp"] = round(ctrl_temp, 1)
            self.current_state["motor_temp"] = round(motor_temp, 1)
            self.current_state["can_status"] = "VIRTUAL_CAN_ACTIVE"
            return self.current_state
        else:
            try:
                msg = self.bus.recv(timeout=0.05)
                if msg:
                    decoded = CANFrameDecoder.decode(msg.arbitration_id, msg.data)
                    self.current_state.update(decoded)
                    self.current_state["can_status"] = "SOCKETCAN_LIVE"
            except Exception as e:
                logger.error(f"Error receiving CAN frame: {e}")
            return self.current_state
