from typing import Dict, Any, List

class XAIAdvisor:
    """
    Explainable AI (XAI) & Autonomous Maintenance Advisory Layer:
    - Provides feature attribution breakdown (which sensor / residual drove the decision).
    - Generates actionable step-by-step maintenance recommendations for UAV technicians.
    """

    def generate_explanation_and_advisory(
        self, 
        residuals: Dict[str, Any], 
        fault_info: Dict[str, Any], 
        rul_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        primary_fault = fault_info.get("primary_fault", "NORMAL_OPERATION")
        conf = fault_info.get("fault_confidence_pct", 98.0)

        # Feature Attribution Breakdown (SHAP-style normalized contributions %)
        r_cht = abs(residuals.get("res_cht", 0)) / 15.0
        r_egt = abs(residuals.get("res_egt", 0)) / 30.0
        r_oil_p = abs(residuals.get("res_oil_pressure", 0)) / 8.0
        r_vib = abs(residuals.get("res_vibration", 0)) / 0.5
        r_fuel = abs(residuals.get("res_fuel_flow", 0)) / 2.0
        r_volt = abs(residuals.get("res_bus_voltage", 0)) / 4.0

        total = max(0.001, r_cht + r_egt + r_oil_p + r_vib + r_fuel + r_volt)
        
        feature_attributions = [
            {"feature": "CHT Thermal Residual", "contribution_pct": round((r_cht / total) * 100, 1)},
            {"feature": "EGT Exhaust Residual", "contribution_pct": round((r_egt / total) * 100, 1)},
            {"feature": "Oil Pressure Residual", "contribution_pct": round((r_oil_p / total) * 100, 1)},
            {"feature": "Vibration RMS Residual", "contribution_pct": round((r_vib / total) * 100, 1)},
            {"feature": "Fuel Flow Residual", "contribution_pct": round((r_fuel / total) * 100, 1)},
            {"feature": "Bus Voltage Residual", "contribution_pct": round((r_volt / total) * 100, 1)}
        ]
        # Sort descending by contribution
        feature_attributions.sort(key=lambda x: x["contribution_pct"], reverse=True)

        # Actionable Maintenance Advisory Generator
        advisories: List[Dict[str, Any]] = []

        if primary_fault == "Lubrication issues":
            advisories.append({
                "id": "ADV-001",
                "priority": "HIGH",
                "subsystem": "Lubrication System",
                "action": "Inspect Oil Pump & Pressure Regulator",
                "details": "Oil pressure residual deviation detected. Check oil filter for particulate contamination, verify pump drive gear mesh, and top up 20W-50 aero oil.",
                "est_downtime_mins": 45
            })
            advisories.append({
                "id": "ADV-002",
                "priority": "MEDIUM",
                "subsystem": "Oil Cooling",
                "action": "Clean Oil Heat Exchanger",
                "details": "Inspect cooling fins on oil radiator for blockage or air duct misalignment.",
                "est_downtime_mins": 30
            })

        elif primary_fault == "Combustion instability":
            advisories.append({
                "id": "ADV-003",
                "priority": "HIGH",
                "subsystem": "Fuel / Injection System",
                "action": "Inspect Fuel Injector Nozzles & Ignition Coil",
                "details": "EGT temperature fluctuation indicates cylinder misfire or partial injector spray pattern clog. Run flow rate calibration.",
                "est_downtime_mins": 60
            })

        elif primary_fault == "Sensor drift / failure":
            advisories.append({
                "id": "ADV-004",
                "priority": "MEDIUM",
                "subsystem": "Avionics & Telemetry Sensors",
                "action": "Calibrate or Replace CHT Thermocouple Sensor",
                "details": "Digital Twin residual reveals sensor readout deviation without thermodynamic correlation in oil temperature. Recalibrate reference cold-junction.",
                "est_downtime_mins": 25
            })

        elif primary_fault == "Overheating trends":
            advisories.append({
                "id": "ADV-005",
                "priority": "CRITICAL",
                "subsystem": "Thermal Management",
                "action": "Check Engine Cowling Air Intake & Reduce Throttle",
                "details": "CHT exceeds physical twin expected envelope. Verify ram-air duct obstruction, inspect baffle seals, and verify fuel mixture enrichment.",
                "est_downtime_mins": 40
            })

        elif primary_fault == "Abnormal vibration patterns":
            advisories.append({
                "id": "ADV-006",
                "priority": "CRITICAL",
                "subsystem": "Mechanical / Structure",
                "action": "Inspect Propeller Balance & Engine Mount Dampers",
                "details": "Vibration RMS magnitude exceeds 3.5g threshold. Inspect engine isolation mounts for elastomeric cracking and dynamic propeller pitch balance.",
                "est_downtime_mins": 90
            })

        elif primary_fault == "Coding degradation":
            advisories.append({
                "id": "ADV-007",
                "priority": "HIGH",
                "subsystem": "ECU / Software",
                "action": "Flash ECU Firmware & Verify Fuel Map",
                "details": "Fuel consumption mismatch with RPM curve indicates corrupt ECU lookup tables or sensor map drift. Reflash ECU flash memory.",
                "est_downtime_mins": 20
            })

        else:
            advisories.append({
                "id": "ADV-000",
                "priority": "INFO",
                "subsystem": "General Engine Maintenance",
                "action": "Perform Pre-Flight Visual Inspection",
                "details": "All propulsion metrics nominal. Verify fuel level, inspect battery connection, and check control surface linkages.",
                "est_downtime_mins": 10
            })

        return {
            "xai_feature_attributions": feature_attributions,
            "maintenance_advisories": advisories,
            "top_contributor": feature_attributions[0]["feature"]
        }
