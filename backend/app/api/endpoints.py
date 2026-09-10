from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.engine_profile_store import engine_profiles

router = APIRouter()

# Global state reference injected from main app
system_context: Dict[str, Any] = {}

class EnvironmentUpdate(BaseModel):
    altitude_ft: Optional[float] = 2000.0
    ambient_temp_c: Optional[float] = 25.0
    throttle_pct: Optional[float] = 60.0
    fault_mode: Optional[str] = "NONE"

class ScenarioUpdate(BaseModel):
    scenario: str

@router.post("/api/environment")
def update_environment(data: EnvironmentUpdate):
    telemetry_layer = system_context.get("telemetry_layer")
    if not telemetry_layer:
        raise HTTPException(status_code=500, detail="System not initialized")
    
    telemetry_layer.aero_simulator.set_environment(
        altitude_ft=data.altitude_ft,
        ambient_temp_c=data.ambient_temp_c,
        throttle_pct=data.throttle_pct,
        fault_mode=data.fault_mode
    )
    return {"status": "SUCCESS", "environment": data.dict()}

@router.post("/api/scenario")
def set_scenario(data: ScenarioUpdate):
    mission_runner = system_context.get("mission_runner")
    if not mission_runner:
        raise HTTPException(status_code=500, detail="System not initialized")
    
    res = mission_runner.select_scenario(data.scenario)
    return res

@router.get("/api/health")
def get_system_health():
    return {
        "status": "ONLINE",
        "service": "UAV Propulsion Digital Twin & Maintenance Engine",
        "version": "1.0.0"
    }

@router.get("/api/report")
def generate_report(mission_id: str = "MISSION-ALPHA-01"):
    report_gen = system_context.get("report_generator")
    # Capture one coherent frame, even if a profile changes during report generation.
    frame = system_context.get("report_frame", {})
    current_state = frame.get("state", {})
    fault_info = frame.get("fault", {})
    rul_info = frame.get("rul", {})
    advisories = frame.get("advisories", [])

    if not report_gen:
        raise HTTPException(status_code=500, detail="Report generator not loaded")

    report = report_gen.build_report(
        mission_id=mission_id,
        current_state=current_state,
        fault_info=fault_info,
        rul_info=rul_info,
        advisories=advisories
    )
    snapshot_meta = frame.get("engine_meta")
    if not snapshot_meta or snapshot_meta["revision"] != engine_profiles.active()["revision"]:
        raise HTTPException(status_code=409, detail="Waiting for telemetry for the selected profile; try again")
    report["engine_meta"] = snapshot_meta
    report["profile_alerts"] = frame.get("profile_alerts", [])
    report["assessment_scope"] = "Reference simulator / original model; no engine-specific calibration"
    return report
