# Multi-engine configuration integration

The dropdown is built into the original AEROTWIN GCS header. There is one telemetry view, with the same dark glass panels, cyan controls, Orbitron headings, Inter text, JetBrains Mono values, six tabs and Three.js viewer.

## Start on Windows

1. Extract the ZIP into a fresh folder. Node.js/npm and Python 3.10+ must be installed and available on PATH.
2. Run `start_system.bat`. Keep both service windows open while dependencies install and the app starts.
3. Open http://localhost:3000.
4. Choose an engine in **MULTI-ENGINE CONFIGURATION**. Use **YAML** to inspect its configuration and the included files it references.

The existing launcher remains unchanged. Dependencies and compiled Python caches are excluded from the download; the launcher installs the dependencies for your own operating system. The latest frontend build is included in `frontend/dist`.

If profiles cannot load, check the backend window and select **Retry**. Vite forwards `/api` and `/ws` to FastAPI on port 8000. For a separate deployed frontend, set `VITE_API_BASE_URL` to the backend origin before building and configure WebSocket support on that origin. No deployment was performed in this integration.

## Included profiles and data status

The earlier `universal_modularity/profiles/` folder was absent from the supplied archive. These five files were created for this integration; they are editable DEMO configurations, not copies of unseen earlier YAML files.

| YAML file | Requested platform / engine | Demo temperature maximum |
| --- | --- | --- |
| `austro_ae300_tapas.yaml` | TAPAS-BH-201 / Austro AE300 | 220 °C |
| `rotax_915is_archer.yaml` | Archer-NG / Rotax 915 iS | 135 °C |
| `rotax_914_heron.yaml` | IAI Heron 1 / Rotax 914 | 135 °C |
| `csir_nal_wankel55.yaml` | CSIR-NAL Indigenous Wankel / Wankel 55 | 200 °C housing proxy |
| `vrde_jayem_aero_diesel.yaml` | DRDO VRDE-Jayem / Aero Diesel | 210 °C |

Engine/platform names, associations, power and supplied displacement follow the user brief and have not been independently verified. All operating bands are illustrative UI settings, including the requested AE300/Rotax examples. Missing boost, compression ratio and engine-specific CAN details remain explicitly unspecified. Do not treat these settings as approved engine operating limits.

## What switching changes

- Active name, platform, version and the seven specification cards.
- All eight gauge labels, scales, warning colours and progress bars, using a single YAML sensor map. Zero RPM/voltage/pressure remains zero; absent telemetry displays a dash.
- Engine labels and limit-driven component colours in the original 3D viewer. The Wankel profile uses thermal-zone labels on the clearly identified reference geometry; no Wankel CAD model is claimed.
- Comparison-table limits, sensor labels, residual warning bands and chart labels.
- Engine/model context in AI Analytics & RUL, selected limits in Mission Simulator, profile alerts in Advisory, and the active sensor/source map in CAN Monitor.
- Report engine identity, profile version, limits, alert list and reference-model scope.
- A brief cyan pulse on profile changes, with reduced-motion support.

The YAML inspector supports Escape, a close button, backdrop click and keyboard focus containment. It displays the exact active YAML and a checked list of required files. Markup inside YAML is displayed as plain text.

## Reference simulation and model boundary

The original telemetry, CAN listener, simulation, physics, processing, ML and mission modules are byte-for-byte preserved. A separate profile layer evaluates configurable limits against their reference telemetry. It does not rescale live eKart readings, invent engine ECU frames, train a model, change the simulator's physical parameters, or load engine-specific calibrated model weights. The original four-cylinder 3D mesh is retained.

AI/RUL remains the original reference-model output. Each named engine still needs verified configuration data, compatible sensors, matching models and calibration before an engine-specific estimator can be enabled. The UI explicitly identifies this boundary. Merely selecting a diesel or rotary name does not make the reference model a validated digital twin of that engine.

## Files and extension points

- `backend/app/engine_profiles/*.yaml`: names, version, specs, viewer labels, eight sensor definitions and required-file references.
- `backend/app/engine_profile_store.py`: startup validation, immutable profile revisions, measured configuration-switch latency and additive limit evaluation.
- `backend/app/api/engine_profile_api.py`: profile endpoints.
- `frontend/src/components/EngineProfileSelector.jsx`: dropdown, spec strip and YAML inspector.
- `frontend/src/lib/engineMetrics.js`: shared frontend thresholds/formatting.
- `frontend/src/components/EngineContextNotice.jsx`: active profile and data scope across tabs.

To add another demo profile, copy one YAML inside `backend/app/engine_profiles/`, change `engine_id` to match the new filename stem, update the profile's self-reference in `files`, and fill the metadata and sensor map. Restart the backend to reload the catalog. No frontend engine list needs editing. Required files must exist under `backend/app`. Invalid ranges, missing dependencies, unknown fields and mismatched IDs are rejected at startup.

Profiles are loaded and validated at startup. Switching activates a cached package. The displayed latency measures the server metadata switch only; it excludes startup validation, network travel, browser rendering and ML/model loading.

## API contract and synchronization

| Method | Endpoint | Result |
| --- | --- | --- |
| GET | `/api/engine/profiles` | Five metadata entries, active engine ID and active metadata |
| GET | `/api/engine/profile/{engine_id}/yaml` | Raw YAML text for an allowlisted ID |
| POST | `/api/engine/select` | Accepts `{"engine_id":"rotax_914_heron"}`; returns active metadata and switch latency |

IDs are filename stems without `.yaml`. Invalid IDs return 404; malformed bodies return 422. Failed selections leave the active state unchanged. Selecting the already active engine is a no-op.

WebSocket packets include `active_engine_id`, `engine_meta` (server session and revision), `profile_alerts`, and data scope, alongside all existing fields. The frontend rejects older revisions, resets displayed history/report state when the profile changes, and reconnects without orphaned timers. Reports capture one coherent data/profile frame and reject a stale revision.

Selection is process-wide and shared by connected dashboard clients. Refreshing a browser retrieves the current server selection. Restarting the backend returns to AE300. Run one backend worker, as the original launcher does; this is a single active configuration, not simultaneous fleet instances or durable selection storage.

## Verification performed

- Production Vite build: passed.
- Seven backend tests: passed. Covers all five YAML endpoints and required files, malformed/unknown selections, invalid limits, zero-pressure alerts, all five profile switches reaching two WebSocket clients, report identity, catalog refresh, no-op switching and original REST controls.
- Static React rendering: passed for all five profiles, all eight gauges, all six tab components, dropdown entries, missing readings, real zero readings and engine-specific thresholds.
- Original simulation/CAN/physics/processing/ML/mission source preservation: verified by comparison with the supplied ZIP.
- Browser interaction/visual QA: not completed. The supervised preview started, but the browser could not access it in this environment. Static rendering does not verify clicking, WebGL appearance, focus behaviour or animations.
- Windows launcher execution: not performed in this Linux environment; the original batch file is preserved.

The original model weights reported a scikit-learn version mismatch (saved with 1.9.0; test runtime 1.8.0) and feature-name warnings. The existing classifier loaded and produced telemetry, but these checks do not validate prediction accuracy. Match the model's training environment or retrain using your original workflow before relying on its predictions. The original large Three.js/Recharts frontend bundle warning remains; the build succeeded.

Re-run checks:

```bash
cd backend
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
cd ../frontend
npm install
node tests/profile_ui.test.mjs
npm run build
```

Manual review on your machine: switch each engine, check CHT maximum 220 → 135, open/close the YAML inspector with keyboard and mouse, inspect the rotary reference labels, check every original tab, open a report, and verify a second browser follows the selection. Also check your preferred screen size and reduced-motion setting.
