import time
from typing import Dict, Any, List

class MissionHealthReportGenerator:
    """
    Generates downloadable Mission-wise Engine Health & Diagnostics Report.
    """
    @staticmethod
    def build_report(
        mission_id: str, 
        current_state: Dict[str, Any], 
        fault_info: Dict[str, Any], 
        rul_info: Dict[str, Any], 
        advisories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return {
            "report_id": f"RPT-{mission_id}-{int(time.time())}",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "mission_id": mission_id,
            "engine_serial_no": "UAV-PT-210-EKART",
            "operating_summary": {
                "total_flight_duration": "02h 45m 12s",
                "max_rpm": current_state.get("piston_rpm", 3360.0),
                "peak_cht_c": current_state.get("cht_deg_c", 135.0),
                "peak_egt_c": current_state.get("egt_deg_c", 650.0),
                "avg_oil_pressure_psi": current_state.get("oil_pressure_psi", 45.0),
                "fuel_consumed_liters": 22.4,
                "max_vibration_g": current_state.get("vibration_g", 0.85)
            },
            "digital_twin_assessment": {
                "overall_health_index": rul_info.get("health_index_pct", 95.0),
                "remaining_useful_life_hours": rul_info.get("rul_hours", 420.0),
                "primary_fault_detected": fault_info.get("primary_fault", "NORMAL_OPERATION"),
                "confidence_pct": fault_info.get("fault_confidence_pct", 98.0),
                "maintenance_urgency": rul_info.get("maintenance_urgency", "OPERATIONAL")
            },
            "recommended_actions": advisories
        }
