# Real CAN Integration - VESC Motor Telemetry

This folder (`real_can_integration/`) contains standalone modules to interface directly with physical VESC Motor Controllers over Linux SocketCAN (`can0`).

It leaves your main project folder (`backend/`) completely untouched so the virtual CAN (`vcan0`) simulator continues operating without disturbance.

---

## 1. Files Included

- **`vesc_motor_can.c`**: Clean C program extracted from your original code. Filters and parses ONLY VESC Extended CAN Frames for **VESC ID 39**:
  - `CMD_STATUS1` (9): RPM & Motor Current
  - `CMD_STATUS4` (16): MOSFET & Motor Temperatures
  - `CMD_STATUS5` (27): Input Voltage
  - Outputs real-time telemetry JSON to `stdout` at 10Hz.
- **`vesc_can_reader.py`**: Standalone Python module using `python-can` / `SocketCAN` to decode VESC motor extended frames directly into Python dictionaries.
- **`Makefile`**: Simple Makefile to compile `vesc_motor_can.c`.

---

## 2. Hardware & SocketCAN Setup (Linux / Raspberry Pi / Jetson)

1. Connect your VESC CAN High (CAN-H) and CAN Low (CAN-L) lines to your CAN transceiver (e.g. MCP2515, Waveshare CAN Hat, or USB-to-CAN adapter).
2. Configure the `can0` interface speed (VESC default bitrate is 500,000 Baud / 500 kbps):
   ```bash
   sudo ip link set can0 type can bitrate 500000
   sudo ip link set can0 up
   ```

---

## 3. How to Compile & Run

### **A. Using Standalone C Executable**
```bash
cd real_can_integration
make
./vesc_motor_can can0
```

### **B. Using Standalone Python Reader Test Bench**
```bash
cd real_can_integration
python3 vesc_can_reader.py
```

---

## 4. How to Connect Real CAN to the SIH Digital Twin Later

When you are ready to switch the backend from virtual CAN (`vcan0`) to real physical VESC CAN (`can0`):
In `backend/app/telemetry/can_listener.py`, change `mock=True` to `mock=False` and `channel="can0"`, or import `VESCMotorCANReader` from `real_can_integration/vesc_can_reader.py`!
