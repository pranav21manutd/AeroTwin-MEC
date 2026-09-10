# UAV Propulsion Digital Twin & Predictive Maintenance System
## Technical Documentation & Deployment Roadmap

### Executive Summary
This document outlines the technical architecture, physics formulation, machine learning models, telemetry ingestion pipelines, and deployment roadmap for the **UAV Propulsion Digital Twin & AI/ML Predictive Maintenance Platform**.

---

## 1. System Architecture

```
                             +------------------------+
                             |    Telemetry Ingestion  |
                             | (eKart CAN + Aero Sim) |
                             +-----------+------------+
                                         |
                                         v
                             +------------------------+
                             | Data Processing & EKF  |
                             | Noise Filter & Fusion  |
                             +-----------+------------+
                                         |
                                         v
                     +-------------------+-------------------+
                     |                                       |
                     v                                       v
         +-----------------------+               +-----------------------+
         | Physics Digital Twin  |               | Raw / Processed State |
         | Expected Predictions  |               |  Actual Telemetry     |
         +-----------+-----------+               +-----------+-----------+
                     |                                       |
                     +-------------------+-------------------+
                                         |
                                         v
                             +------------------------+
                             |    Residual Engine     |
                             | Residual = Act - Exp   |
                             +-----------+------------+
                                         |
                                         v
                             +------------------------+
                             |  AI / ML Diagnostics   |
                             | (IsoForest, XGB, RUL)  |
                             +-----------+------------+
                                         |
                                         v
                             +------------------------+
                             | Autonomous Advisory &  |
                             | GCS Real-Time Dashboard|
                             +------------------------+
```

---

## 2. Mathematical Formulation & Digital Twin Physics

### 2.1 Thermodynamic IC Engine Baseline Equations
The physics digital twin calculates nominal baseline expectations $S_{exp}$ using first-principles thermodynamic relationships:

1. **Air Pressure Ratio vs Altitude ($h$ in feet)**:
   $$\delta_p(h) = \exp\left(-\frac{h}{27000}\right)$$

2. **Expected Cylinder Head Temperature (CHT)**:
   $$\text{CHT}_{exp} = \frac{T_{amb} + 105.0 \cdot \left(\frac{\text{Throttle}}{100}\right)^{1.2} + 42.0 \cdot \left(\frac{\text{RPM}}{6000}\right)}{0.9 \cdot \delta_p(h) + 0.1}$$

3. **Expected Exhaust Gas Temperature (EGT)**:
   $$\text{EGT}_{exp} = 460.0 + 310.0 \cdot \left(\frac{\text{Throttle}}{100}\right)^{0.9}$$

4. **Residual Vector Calculation**:
   $$\mathbf{\Delta S} = \mathbf{S}_{actual} - \mathbf{S}_{twin\_expected}$$

---

## 3. AI / ML Diagnostic Layer

### 3.1 Anomaly Detection
Uses residual norm vector $\mathbf{\Delta S}$ evaluated against baseline normal operating manifold via Isolation Forest & sigmoidal confidence transform.

### 3.2 Multi-Class Fault Classification
Classifies the 6 exact propulsion failure modes:
1. **Coding degradation**: Fuel injection mapping deviation & ECU map corruption.
2. **Lubrication issues**: Oil pressure drop & friction-induced oil temperature runaway.
3. **Sensor drift / failure**: Thermocouple/transducer calibration offset without physical thermal correlation.
4. **Combustion instability**: EGT oscillation, ignition timing misfires, lean/rich flameout tendency.
5. **Overheating trends**: CHT surge exceeding thermal envelope.
6. **Abnormal vibration patterns**: Mechanical bearing wear, structural damper failure, dynamic propeller pitch imbalance.

### 3.3 Remaining Useful Life (RUL) Estimation
Calculates current health index $H(t) \in [0, 100\%]$ and remaining flight hours $RUL(t)$ via dynamic degradation acceleration factor:
$$\frac{d(RUL)}{dt} = -\gamma(\text{AnomalyScore}) \cdot \Delta t$$

---

## 4. Deployment Roadmap

```
Phase 1: Hardware-in-the-Loop (HIL) Bench Testing (Weeks 1-4)
- SocketCAN interface integration with eKart motor controller & physical IC engine sensor rack.
- Calibration of baseline thermodynamic physics model parameters.

Phase 2: Edge AI Analytics Optimization (Weeks 5-8)
- Quantization of ML models (ONNX Runtime / TensorRT Micro) for onboard Raspberry Pi 4 / NVIDIA Jetson Orin Nano edge execution.

Phase 3: GCS Integration & Flight Certification (Weeks 9-12)
- Telemetry link binding over MAVLink / Custom UDP payload.
- Real-time ground station flight trial verification & autonomous advisory sign-off.
```
