"""
=====================================================================================
 REAL CAN INTEGRATION: VESC MOTOR PYTHON TELEMETRY READER
=====================================================================================
 Extracted for SIH physical motor CAN integration.
 Listens to can0 using python-can / SocketCAN interface and decodes Extended CAN frames:
 - CMD_STATUS1 (9): Motor RPM & Motor Current
 - CMD_STATUS4 (16): MOSFET Temperature & Motor Temperature
 - CMD_STATUS5 (27): Input Voltage
=====================================================================================
"""

import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("VESCCANReader")

class VESCMotorCANReader:
    VESC_ID = 39
    CMD_STATUS1 = 9
    CMD_STATUS4 = 16
    CMD_STATUS5 = 27

    def __init__(self, channel: str = "can0", bustype: str = "socketcan"):
        self.channel = channel
        self.bustype = bustype
        self.bus = None
        self.current_state = {
            "vesc_id": self.VESC_ID,
            "ekart_rpm": 0.0,
            "bus_current": 0.0,
            "bus_voltage": 0.0,
            "motor_temp": 0.0,
            "controller_temp": 0.0,
            "power_kw": 0.0,
            "can_status": "REAL_CAN0_OFFLINE"
        }
        self._init_bus()

    def _init_bus(self):
        try:
            import can
            # Filter extended frames for VESC_ID
            self.bus = can.interface.Bus(channel=self.channel, bustype=self.bustype)
            self.current_state["can_status"] = f"REAL_CAN0_CONNECTED ({self.channel})"
            logger.info(f"[+] Connected to physical VESC CAN interface on {self.channel}")
        except Exception as e:
            logger.warning(f"[-] Could not connect to real CAN interface {self.channel}: {e}")
            self.current_state["can_status"] = "REAL_CAN0_DISCONNECTED"

    def read_telemetry(self, timeout: float = 0.05) -> Dict[str, Any]:
        """Polls and decodes extended VESC CAN frames."""
        if not self.bus:
            return self.current_state

        try:
            msg = self.bus.recv(timeout=timeout)
            if msg and msg.is_extended_id:
                can_id = msg.arbitration_id
                controller_id = can_id & 0xFF
                command = (can_id >> 8) & 0xFF

                if controller_id == self.VESC_ID:
                    data = msg.data
                    if command == self.CMD_STATUS1 and len(data) >= 6:
                        # Bytes 0-3: RPM (int32_t big-endian)
                        rpm = int.from_bytes(data[0:4], byteorder='big', signed=True)
                        # Bytes 4-5: Current (int16_t big-endian, 0.1A)
                        current_raw = int.from_bytes(data[4:6], byteorder='big', signed=True)
                        self.current_state["ekart_rpm"] = float(rpm)
                        self.current_state["bus_current"] = round(current_raw / 10.0, 2)

                    elif command == self.CMD_STATUS4 and len(data) >= 4:
                        # Bytes 0-1: MOSFET Temp (int16_t, 0.1°C)
                        mosfet_raw = int.from_bytes(data[0:2], byteorder='big', signed=True)
                        # Bytes 2-3: Motor Temp (int16_t, 0.1°C)
                        motor_raw = int.from_bytes(data[2:4], byteorder='big', signed=True)
                        self.current_state["controller_temp"] = round(mosfet_raw / 10.0, 1)
                        self.current_state["motor_temp"] = round(motor_raw / 10.0, 1)

                    elif command == self.CMD_STATUS5 and len(data) >= 6:
                        # Bytes 4-5: Input Voltage (uint16_t, 0.1V)
                        voltage_raw = int.from_bytes(data[4:6], byteorder='big', signed=False)
                        self.current_state["bus_voltage"] = round(voltage_raw / 10.0, 2)

                    # Compute instant electric power (kW)
                    p_kw = (self.current_state["bus_voltage"] * self.current_state["bus_current"]) / 1000.0
                    self.current_state["power_kw"] = round(p_kw, 3)

        except Exception as e:
            logger.error(f"Error reading VESC CAN frame: {e}")

        return self.current_state

if __name__ == "__main__":
    print("=" * 65)
    print(" REAL VESC MOTOR CAN READER TEST BENCH (can0)")
    print("=" * 65)
    reader = VESCMotorCANReader(channel="can0")
    print(f"Status: {reader.current_state['can_status']}")
    print("Polling real VESC CAN bus... Press Ctrl+C to exit.")
    
    try:
        while True:
            state = reader.read_telemetry(timeout=0.1)
            print(f"\r[CAN Telemetry] RPM: {state['ekart_rpm']} | Volt: {state['bus_voltage']}V | Curr: {state['bus_current']}A | Motor Temp: {state['motor_temp']}°C | Power: {state['power_kw']} kW", end="")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting VESC CAN test bench.")
