import sys
import site
import os

user_site = site.USER_SITE
if os.path.exists(user_site) and user_site not in sys.path:
    sys.path.insert(0, user_site)

import asyncio
import json
import logging
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect


from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

from app.telemetry.telemetry_layer import TelemetryLayer
from app.processing.noise_filter import KalmanNoiseFilter
from app.processing.feature_extractor import FeatureExtractor
from app.digital_twin.physics_model import PhysicsEngineDigitalTwin
from app.digital_twin.residual_engine import ResidualEngine
from app.ml_layer.anomaly_detector import AnomalyDetector
from app.ml_layer.fault_classifier import FaultClassifier
from app.ml_layer.rul_estimator import RULEstimator
from app.ml_layer.xai_explainer import XAIAdvisor
from app.simulation.mission_runner import MissionRunner
from app.reports.health_report import MissionHealthReportGenerator
from app.api.endpoints import router as api_router, system_context
from app.api.engine_profile_api import router as engine_profile_router
from app.engine_profile_store import engine_profiles, profile_alerts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DigitalTwinBackend")

app = FastAPI(title="UAV Propulsion Digital Twin & Predictive Maintenance Backend")

# Enable CORS for GCS Dashboard Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(engine_profile_router)

# Core Engine Components Initialization
telemetry_layer = TelemetryLayer(mock_can=True)
noise_filter = KalmanNoiseFilter(alpha=0.3)
feature_extractor = FeatureExtractor(history_size=30)
physics_twin = PhysicsEngineDigitalTwin()
residual_engine = ResidualEngine()
anomaly_detector = AnomalyDetector()
fault_classifier = FaultClassifier()
rul_estimator = RULEstimator(initial_baseline_hours=435.0)
xai_advisor = XAIAdvisor()
mission_runner = MissionRunner()
report_generator = MissionHealthReportGenerator()

# Populate system_context for API endpoints
system_context["telemetry_layer"] = telemetry_layer
system_context["mission_runner"] = mission_runner
system_context["report_generator"] = report_generator

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"GCS Dashboard Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"GCS Dashboard Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive & receive incoming command frames if any
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("command") == "SET_SCENARIO":
                    mission_runner.select_scenario(msg.get("scenario", "NOMINAL_FLIGHT"))
                elif msg.get("command") == "SET_FAULT":
                    telemetry_layer.aero_simulator.fault_mode = msg.get("fault_mode", "NONE")
            except Exception as e:
                logger.warning(f"Error handling WS command: {e}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background Telemetry & Digital Twin Processing Loop (10 Hz)
async def background_digital_twin_loop():
    logger.info("Starting Digital Twin & AI/ML Real-Time Loop at 10Hz...")
    t = 0.0
    while True:
        try:
            t += 0.1

            # 1. Acquire scenario parameters if dynamic scenario active
            scen_inputs = mission_runner.get_scenario_inputs(t)
            if mission_runner.active_scenario != "NOMINAL_FLIGHT":
                telemetry_layer.aero_simulator.set_environment(
                    altitude_ft=scen_inputs["altitude_ft"],
                    ambient_temp_c=scen_inputs["ambient_temp_c"],
                    throttle_pct=scen_inputs["throttle_pct"],
                    fault_mode=scen_inputs["fault_mode"]
                )

            # 2. Acquire unified raw snapshot from eKart CAN + Aero Simulator
            target_rpm = scen_inputs.get("target_rpm", 3500.0)
            raw_snapshot = telemetry_layer.get_unified_snapshot(target_rpm=target_rpm)

            # 3. Filter noise
            filtered_snapshot = noise_filter.filter_snapshot(raw_snapshot)

            # 4. Extract higher-order features & sensor fusion
            features = feature_extractor.extract_features(filtered_snapshot)

            # 5. Compute Physics Digital Twin expected state prediction
            expected_twin_state = physics_twin.predict_expected_state(features)

            # 6. Compute Actual vs Twin Residuals
            residuals = residual_engine.compute_residuals(features, expected_twin_state)

            # 7. AI/ML Layer Execution
            anomaly_info = anomaly_detector.detect_anomaly(residuals, features)
            fault_info = fault_classifier.classify_faults(features, residuals, features)
            rul_info = rul_estimator.estimate_rul(anomaly_info, fault_info, features)
            xai_info = xai_advisor.generate_explanation_and_advisory(residuals, fault_info, rul_info)

            # Additive UI configuration. Original reference models and inputs are preserved.
            engine_meta = engine_profiles.active()
            engine_alerts = profile_alerts(features, engine_meta)

            # Update context cache for report export API
            system_context["last_snapshot"] = features
            system_context["last_fault_info"] = fault_info
            system_context["last_rul_info"] = rul_info
            system_context["last_advisories"] = xai_info.get("maintenance_advisories", [])
            system_context["last_engine_meta"] = engine_meta
            system_context["last_profile_alerts"] = engine_alerts
            system_context["report_frame"] = {
                "state": features, "fault": fault_info, "rul": rul_info,
                "advisories": xai_info.get("maintenance_advisories", []),
                "engine_meta": engine_meta, "profile_alerts": engine_alerts,
            }

            # 8. Synthesize Master GCS Telemetry Packet
            packet = {
                "timestamp": round(time.time(), 3),
                "active_engine_id": engine_meta["engine_id"],
                "engine_meta": engine_meta,
                "profile_alerts": engine_alerts,
                "data_scope": "REFERENCE_SIMULATOR_WITH_EKART_BRIDGE",
                "actual_telemetry": features,
                "physics_twin_expected": expected_twin_state,
                "residuals": residuals,
                "anomaly_detection": anomaly_info,
                "fault_classification": fault_info,
                "rul_estimation": rul_info,
                "xai_explanation": xai_info,
                "active_scenario": mission_runner.active_scenario
            }

            # 9. Broadcast to all active GCS Dashboard WebSockets
            if manager.active_connections:
                await manager.broadcast(json.dumps(packet))

        except Exception as e:
            logger.error(f"Error in Digital Twin Loop: {e}", exc_info=True)

        await asyncio.sleep(0.1)  # 10 Hz loop rate

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_digital_twin_loop())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
