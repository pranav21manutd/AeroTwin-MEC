"""Validated, process-wide configuration; the reference simulation is unchanged."""
from copy import deepcopy
from pathlib import Path
from time import perf_counter
from uuid import uuid4
from typing import Dict, List, Literal
import math

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

APP_ROOT = Path(__file__).resolve().parent
PROFILE_ROOT = APP_ROOT / "engine_profiles"
DEFAULT_ENGINE_ID = "austro_ae300_tapas"


class SensorSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    label: str
    unit: str
    source: Literal["REFERENCE_SIMULATOR", "EKART_BRIDGE"]
    expected_key: str
    residual_key: str
    min: float = 0
    max: float = Field(gt=0)
    warning: float
    direction: Literal["high", "low", "range"] = "high"
    low: float | None = None
    residual_warning: float = Field(gt=0)
    accent: Literal["cyan", "amber", "emerald", "purple"]

    @model_validator(mode="after")
    def valid_range(self):
        if not self.min < self.warning < self.max:
            raise ValueError("Expected min < warning < max")
        if self.low is not None and not self.min <= self.low < self.warning:
            raise ValueError("Invalid low-pressure bound")
        if self.direction in ("low", "range") and self.low is None:
            raise ValueError("Low/range sensor requires a low bound")
        return self


class PackageFile(BaseModel):
    role: str
    path: str


class EngineProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    engine_id: str
    profile_version: str
    display_name: str
    platform: str
    engine_name: str
    configuration_status: Literal["DEMO — calibration required"]
    provenance: str
    specs: Dict[str, str]
    viewer: Dict[str, str]
    model_binding: Dict[str, str]
    sensor_map: Dict[str, SensorSpec]
    files: List[PackageFile]

    @model_validator(mode="after")
    def complete_sensors(self):
        required = {"piston_rpm", "cht_deg_c", "egt_deg_c", "oil_pressure_psi",
                    "oil_temp_deg_c", "bus_voltage", "vibration_g", "fuel_flow_lph"}
        if set(self.sensor_map) != required:
            raise ValueError("Profile must define the eight dashboard sensors")
        required_specs = {"powerplant", "cycle", "displacement_cr", "boost", "fuel", "can_protocol"}
        if set(self.specs) != required_specs:
            raise ValueError("Incomplete specification strip")
        return self


class EngineProfileStore:
    def __init__(self, directory=PROFILE_ROOT):
        self.profiles = {}
        self.yaml_sources = {}
        for path in sorted(Path(directory).glob("*.yaml")):
            source = path.read_text(encoding="utf-8")
            profile = EngineProfile.model_validate(yaml.safe_load(source))
            if profile.engine_id != path.stem or profile.engine_id in self.profiles:
                raise ValueError(f"Invalid or duplicate engine id: {path.name}")
            metadata = profile.model_dump()
            metadata["filename"] = path.name
            for entry in metadata["files"]:
                resolved = (APP_ROOT.parent / entry["path"]).resolve()
                if not resolved.is_relative_to(APP_ROOT):
                    raise ValueError("Package file must stay inside backend/app")
                if not resolved.is_file():
                    raise ValueError(f"Missing profile dependency: {entry['path']}")
                entry["available"] = True
            # Explicit limits alias for consumers, derived from the same sensor map.
            metadata["limits"] = {key: value["max"] for key, value in metadata["sensor_map"].items()}
            self.profiles[profile.engine_id] = metadata
            self.yaml_sources[profile.engine_id] = source
        if DEFAULT_ENGINE_ID not in self.profiles:
            raise ValueError("Default engine profile is missing")
        self.session_id = str(uuid4())
        self._active = self._metadata(DEFAULT_ENGINE_ID, 0, None)

    def _metadata(self, engine_id, revision, latency):
        data = deepcopy(self.profiles[engine_id])
        data.update(revision=revision, server_session_id=self.session_id, switch_latency_ms=latency)
        return data

    def active(self):
        return deepcopy(self._active)

    def catalog(self):
        ids = [DEFAULT_ENGINE_ID] + [key for key in self.profiles if key != DEFAULT_ENGINE_ID]
        return {"profiles": [deepcopy(self.profiles[key]) for key in ids], "engine_meta": self.active(),
                "active_engine_id": self._active["engine_id"]}

    def select(self, engine_id):
        started = perf_counter()
        if engine_id not in self.profiles:
            raise KeyError(engine_id)
        if engine_id == self._active["engine_id"]:
            return self.active()
        new_state = self._metadata(engine_id, self._active["revision"] + 1, None)
        new_state["switch_latency_ms"] = round((perf_counter() - started) * 1000, 3)
        # One atomic reference replacement; the broadcast captures a complete revision.
        self._active = new_state
        return self.active()

    def raw_yaml(self, engine_id):
        return self.yaml_sources[engine_id]


def profile_alerts(telemetry, metadata):
    """Evaluate selected demo limits without changing measured values or ML inputs."""
    alerts = []
    for key, spec in metadata["sensor_map"].items():
        value = telemetry.get(key)
        if not isinstance(value, (float, int)) or not math.isfinite(value):
            continue
        severity = None
        if value >= spec["max"] or value < spec["min"]:
            severity = "CRITICAL"
        elif spec["direction"] in ("low", "range") and value <= spec["low"]:
            severity = "CRITICAL"
        elif spec["direction"] == "low" and value <= spec["warning"]:
            severity = "WARNING"
        elif spec["direction"] != "low" and value >= spec["warning"]:
            severity = "WARNING"
        if severity:
            alerts.append({"key": key, "label": spec["label"], "value": value,
                           "unit": spec["unit"], "severity": severity,
                           "message": f"{spec['label']}: {value} {spec['unit']} outside the selected demo band"})
    return alerts


engine_profiles = EngineProfileStore()
