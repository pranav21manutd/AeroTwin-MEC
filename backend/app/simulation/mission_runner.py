import time
import math
import random
from typing import Dict, Any, List, Optional

class MissionRunner:
    """
    Mission Simulation & Replay Engine:
    Manages mission scenario states (High Altitude, Hot Weather, Endurance, Rapid Throttle)
    and playback control of pre-recorded mission datasets.
    """
    def __init__(self):
        self.active_scenario = "NOMINAL_FLIGHT"
        self.replay_mode = False
        self.replay_index = 0
        self.replay_data: List[Dict[str, Any]] = []
        self.playback_speed = 1.0
        self.is_paused = False

    def select_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """
        Scenarios:
        - NOMINAL_FLIGHT
        - HIGH_ALTITUDE (15,000 ft altitude)
        - HOT_WEATHER (45°C ambient, cooling stress)
        - ENDURANCE_MISSION (Long duration thermal soak)
        - RAPID_THROTTLE (Aggressive transient step inputs)
        """
        self.active_scenario = scenario_name
        self.replay_mode = False
        return {"scenario": scenario_name, "status": "ACTIVATED"}

    def get_scenario_inputs(self, t: float) -> Dict[str, Any]:
        if self.active_scenario == "HIGH_ALTITUDE":
            return {
                "altitude_ft": 15000.0,
                "ambient_temp_c": -5.0,
                "throttle_pct": 75.0,
                "target_rpm": 4800.0,
                "fault_mode": "NONE"
            }
        elif self.active_scenario == "HOT_WEATHER":
            return {
                "altitude_ft": 1500.0,
                "ambient_temp_c": 48.0,
                "throttle_pct": 80.0,
                "target_rpm": 5200.0,
                "fault_mode": "OVERHEATING"
            }
        elif self.active_scenario == "ENDURANCE_MISSION":
            return {
                "altitude_ft": 5000.0,
                "ambient_temp_c": 22.0,
                "throttle_pct": 55.0,
                "target_rpm": 3800.0,
                "fault_mode": "NONE"
            }
        elif self.active_scenario == "RAPID_THROTTLE":
            # Oscillating throttle every 4 seconds between 25% and 95%
            step = math.sin(t * 1.5)
            throttle = 90.0 if step > 0 else 25.0
            rpm = 5800.0 if step > 0 else 2200.0
            return {
                "altitude_ft": 3000.0,
                "ambient_temp_c": 28.0,
                "throttle_pct": throttle,
                "target_rpm": rpm,
                "fault_mode": "COMBUSTION_INSTABILITY" if step > 0.8 else "NONE"
            }
        else: # NOMINAL_FLIGHT
            return {
                "altitude_ft": 2500.0,
                "ambient_temp_c": 25.0,
                "throttle_pct": 60.0 + 15.0 * math.sin(t * 0.2),
                "target_rpm": 3500.0 + 800.0 * math.sin(t * 0.2),
                "fault_mode": "NONE"
            }

    def load_replay_dataset(self, dataset: List[Dict[str, Any]]):
        self.replay_data = dataset
        self.replay_index = 0
        self.replay_mode = True

    def get_next_replay_frame(self) -> Optional[Dict[str, Any]]:
        if not self.replay_mode or not self.replay_data:
            return None
        
        if self.replay_index >= len(self.replay_data):
            self.replay_index = 0  # Loop back
            
        frame = self.replay_data[self.replay_index]
        if not self.is_paused:
            self.replay_index = (self.replay_index + 1) % len(self.replay_data)
            
        return frame
