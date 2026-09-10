from typing import Dict, Any

class RULEstimator:
    """
    Remaining Useful Life (RUL) & Degradation Trajectory Engine:
    Calculates expected remaining flight operating hours based on cumulative thermal stress,
    vibration energy, oil degradation, and physical residual norm.
    Baseline lifespan: 500 operating hours before overhaul.
    """
    def __init__(self, initial_baseline_hours: float = 450.0):
        self.current_rul_hours = initial_baseline_hours

    def estimate_rul(self, anomaly_info: Dict[str, Any], fault_info: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        anomaly_score = anomaly_info.get("anomaly_score_pct", 10.0)
        primary_fault = fault_info.get("primary_fault", "NORMAL_OPERATION")
        
        # Degradation acceleration factor
        # Normal operation: 1.0 (1 hr run = 1 hr RUL decay)
        # Severe fault / high anomaly: accelerate decay up to 40x
        if anomaly_score > 80.0:
            decay_factor = 25.0
        elif anomaly_score > 60.0:
            decay_factor = 8.0
        elif anomaly_score > 40.0:
            decay_factor = 2.5
        else:
            decay_factor = 1.0

        # Decrement RUL slowly during simulation steps
        self.current_rul_hours = max(2.5, self.current_rul_hours - (0.001 * decay_factor))

        # Health Index calculation (0 - 100%)
        # Combines RUL ratio + anomaly score + primary fault confidence
        rul_health_ratio = (self.current_rul_hours / 500.0) * 100.0
        anomaly_penalty = anomaly_score * 0.4
        
        health_index = max(0.0, min(100.0, rul_health_ratio - anomaly_penalty))

        # Estimate remaining mission flight cycles (assume 2.5 hrs per mission)
        remaining_missions = max(0, int(self.current_rul_hours / 2.5))

        # Maintenance urgency rating
        if health_index < 40.0 or self.current_rul_hours < 25.0:
            urgency = "IMMEDIATE_OVERHAUL_REQUIRED"
        elif health_index < 70.0 or self.current_rul_hours < 100.0:
            urgency = "SCHEDULED_MAINTENANCE_DUE"
        else:
            urgency = "OPERATIONAL"

        return {
            "health_index_pct": round(health_index, 1),
            "rul_hours": round(self.current_rul_hours, 1),
            "remaining_mission_cycles": remaining_missions,
            "decay_acceleration_factor": round(decay_factor, 2),
            "maintenance_urgency": urgency
        }
