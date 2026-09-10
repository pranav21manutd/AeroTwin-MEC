Act as a senior full-stack engineer specializing in React, FastAPI, telemetry dashboards and configuration-driven digital twins.

Implement the changes below directly in the attached `AeroPiston-master.zip`. Deliver the complete runnable updated project. Start by inspecting the actual files; do not stop at a plan or return disconnected snippets.

OBJECTIVE

Integrate “Multi-Engine Configuration” into the mother dashboard as a native dropdown. Selecting an engine must activate its configuration package and update the relevant interface across the existing dashboard: specifications, labels, gauge ranges, warning thresholds, sensor mappings, 3D inspection context, diagnostics context and reports.

The experience must feel like one application. Preserve the original theme, navigation, single-engine telemetry layout and Three.js viewer. Do not create a separate dashboard, iframe, microfrontend or extra “ME Configuration” tab. “Whole UI changes” means engine-dependent configuration changes throughout the interface; it does not mean replacing the page layout or changing the colour theme for each engine.

1. INSPECT AND PRESERVE THE EXISTING PROJECT

The expected stack is React 18 + Vite + Recharts + Three.js + lucide-react, with FastAPI/WebSocket on port 8000 and Vite on port 3000. Confirm the actual structure and reuse its dependencies, lockfile, components and CSS classes.

Inspect App.jsx, Header.jsx, TelemetryGauges.jsx, DigitalTwinView.jsx, Engine3DViewer.jsx, the remaining tab components, index.css, vite.config.js, backend/main.py and start_system.bat. If an earlier integration already exists, extend or repair it without duplicating selectors, APIs, state or styles.

Preserve Cockpit View, Digital Twin, AI Analytics & RUL, Mission Simulator, Advisory Checklist, CAN Monitor and Report. Keep existing scenario controls, fault injection and viewer interactions working. Make a recoverable working copy and proceed with routine implementation decisions without asking unnecessary design-confirmation questions.

2. MATCH THE MOTHER DASHBOARD THEME

Reuse these existing design tokens and classes:

- Backgrounds: #07090e and #0d121d.
- Cards: rgba(17, 24, 39, 0.75), glassmorphism, blur(12px).
- Cyan #00f0ff; blue #3b82f6; emerald #10b981; amber #f59e0b; rose #f43f5e; purple #a855f7.
- Orbitron headings/labels, Inter body text, JetBrains Mono data/YAML.
- `.glass-panel`, `.font-orbitron`, `.font-mono`, `.btn-gcs`, `.btn-gcs-active` and existing badge classes.

Keep the existing spacing, rounded corners, borders, shadows and hover behaviour. Cyan indicates primary configuration/data, amber thermal warnings, emerald healthy status, rose critical states and purple model-related information. Do not add a PINN label unless a PINN is actually implemented.

3. ADD FIVE ENGINE CONFIGURATION PACKAGES

Use these requested entries, with filename stems as engine IDs:

- `austro_ae300_tapas.yaml` — TAPAS-BH-201 / Austro AE300.
- `rotax_915is_archer.yaml` — Archer-NG / Rotax 915 iS.
- `rotax_914_heron.yaml` — IAI Heron 1 / Rotax 914.
- `csir_nal_wankel55.yaml` — CSIR-NAL Indigenous Wankel / Wankel 55.
- `vrde_jayem_aero_diesel.yaml` — DRDO VRDE-Jayem / Aero Diesel.

First look for the supplied original YAML packages, including `universal_modularity/profiles/`. Reuse real supplied files and their associated assets when available. If absent, create clearly labelled editable DEMO profiles and state that the originals were missing. Do not claim to have copied unseen files or independently verified the requested engine/platform associations.

Keep profiles in `backend/app/engine_profiles/`. Each package must define its ID, schema version, profile version, display name, platform, specifications, sensor map, UI labels, ranges, warning rules, viewer context, model compatibility and a manifest of required files. Verify each referenced file exists; do not invent assets, ECU protocols, calibration files or trained model weights.

Use YAML as the configuration source of truth. Avoid separate hardcoded engine tables in each React component. A new compatible profile should be discoverable after backend restart without editing the frontend dropdown.

Missing specifications such as boost, compression ratio or engine CAN details should display “Not supplied”. Illustrative limits must be explicitly marked as demo settings. The requested example of AE300 CHT maximum 220 °C versus Rotax 914 maximum 135 °C may demonstrate switching; do not present those values as verified operating limits.

4. BUILD THE NATIVE HEADER DROPDOWN

Create or update `EngineProfileSelector.jsx`. Place the selector between the header brand/status area and tab navigation. It must list engine/platform names, display the confirmed active profile/version and include a YAML button beside it.

Style the select with the existing glass panel, dark surface, cyan border/focus glow and matching typography. Provide loading, switching, unavailable and retry states. Prevent overlapping switch requests. If selection fails, retain the last server-confirmed profile and show a useful error.

Under the selector, add seven compact specification cards: Active Powerplant, Thermodynamic Cycle, Displacement / Compression Ratio, Max Boost, Fuel Type, CAN Protocol and Profile Switch Latency. Update them from active metadata. Keep a horizontal desktop strip that wraps neatly on smaller screens.

5. ADD THE YAML INSPECTOR AND MORPH ANIMATION

The YAML button must open a full-screen glass overlay displaying the exact active YAML source in JetBrains Mono with cyan syntax highlighting. Include the filename, version, configuration status and manifest of required files with their availability.

Render YAML as text, never executable code or unescaped HTML. Support scrolling, Escape, a visible Close button and clicking the backdrop. Trap keyboard focus, restore it on close, label the dialog accessibly and prevent background scrolling.

After a confirmed profile change, apply a brief cyan glow sweep to specification cards and relevant dashboard panels. Respect reduced-motion preferences. Avoid continuous blinking, full-page reloads and rebuilding the Three.js scene merely to update labels or thresholds.

6. UPDATE THE EXISTING TABS FROM SHARED ENGINE CONTEXT

App.jsx must own or coordinate activeEngineId, engineMeta, catalog, switching/error state and telemetry synchronization. Pass the same confirmed context to relevant child components.

TelemetryGauges: drive all eight cards from the sensor map—engine RPM, CHT/housing temperature, EGT, oil pressure, oil temperature, bus voltage, vibration and fuel flow. Adapt labels, units, ranges, warning colours and progress percentages. Handle both low-limit hazards and high-limit hazards. Clamp progress bars without hiding the actual reading. Preserve legitimate zeros with nullish checks; show missing readings as a dash, never a fabricated healthy value.

DigitalTwinView: update parameter labels, limits, units, residual warning bands, comparison headings and chart labels. Calculate each residual from its matching parameter; RPM must not accidentally display a temperature residual.

Engine3DViewer: retain the original mesh, orbit, explode/assemble and inspection interactions. Change engine labels, inspection text and warning colours using the same thresholds as the gauges. Without engine-specific geometry, clearly identify the original mesh as a reference schematic. For the rotary profile, use appropriate reference-zone labels without pretending a piston mesh is an accurate Wankel CAD model.

AI Analytics & RUL: show the selected engine, model binding and calibration status. If matching calibrated models are unavailable, identify the displayed analytics as reference-model outputs. Do not relabel existing RUL predictions as validated predictions for another engine.

Mission Simulator: show the selected engine and limits while preserving existing scenario/environment controls. Advisory: show active-profile limit alerts separately from existing reference-model diagnostic advice. Reset completed checklist state on profile changes so it does not carry into another engine.

CAN Monitor: show the active profile’s sensor/source mapping. Distinguish eKart bridge data from simulated aero parameters. Do not present illustrative hex bytes as captured engine ECU frames.

Report: include engine ID/name, profile version, applicable limits, alerts and model/data scope. Keep report telemetry and profile metadata from the same snapshot.

7. EXTEND FASTAPI WITH VALIDATED PROFILE ENDPOINTS

Add `backend/app/api/engine_profile_api.py` and include its router in main.py:

- GET `/api/engine/profiles`: return the catalog and current active metadata.
- GET `/api/engine/profile/{engine_id}/yaml`: return the exact raw YAML source.
- POST `/api/engine/select`: accept `{"engine_id":"rotax_914_heron"}` and return confirmed active metadata plus measured switch latency.

Use safe YAML parsing and schema validation. Validate required keys, finite numeric ranges, unique IDs and required-file paths. Resolve engine IDs through a catalog allowlist; reject unknown IDs and path traversal. Invalid selections must not mutate active state. Treat selecting the current engine as a no-op.

Measure latency rather than generating a random number. Label precisely what it measures. A cached configuration activation time is not end-to-end UI latency or model-loading time.

8. KEEP REST, WEBSOCKET AND UI STATE CONSISTENT

Add active_engine_id and coherent engine metadata to every existing WebSocket packet. Include a server-session identifier and monotonically increasing profile revision, plus any additive profile-limit alerts.

REST selection and WebSocket broadcasts must share one authoritative active state. Reject stale revisions in the frontend, handle backend restarts, clear displayed comparison history/report state on profile changes and avoid mixing old-engine readings with new-engine limits. Clean up reconnect timers and subscriptions on unmount.

A second connected browser must follow the active selection. Refreshing must retrieve server state. Document that the configuration is shared by clients and whether it resets at server restart. Keep the current single-engine, single-backend-worker design; do not imply simultaneous fleet support.

Use a central API helper and Vite proxy for `/api` and `/ws`, preserving ports 3000/8000. Support a configurable backend origin when needed. Handle HTTP errors and disconnections visibly without silently inventing data or reports.

9. PRESERVE THE SIMULATION AND ML BOUNDARY

This integration is additive. Preserve the existing CAN acquisition, aero simulator, physics equations, feature extraction, ML algorithms and mission modules.

Changing a profile must genuinely update configuration throughout the UI, but must not secretly rescale physical readings, manufacture engine telemetry or imply that one reference model is calibrated for every engine family. If engine-specific calibration is missing, retain supported monitoring and clearly identify reference/unsupported estimator functions. Do not make unsupported accuracy or novelty claims.

10. VERIFY AND DELIVER

Run the production frontend build and backend startup checks. Test all five catalog/YAML entries, valid and invalid switches, malformed requests, unchanged state after failure, zero/missing readings, dynamic thresholds, report identity and synchronization across two WebSocket clients.

Where browser testing is available, verify the dropdown, specification strip, YAML source/closing/focus, pulse animation, all six tabs, 3D controls, refresh/reconnect and narrow-screen readability. Do not claim browser or Windows launcher tests passed unless actually performed. Report environment limitations honestly.

Deliver the complete updated `AeroPiston-master.zip`, retaining the runnable project and existing launcher. Exclude node_modules, virtual environments, caches and machine-specific temporary files; retain dependency manifests, lockfiles and required assets. Include concise setup instructions, a changed-file summary, profile-extension guidance, test results and any missing calibration/data limitations.

Success means one dropdown activates a real configuration package and consistently updates the original dashboard while preserving its visual identity and accurately describing the capabilities of its underlying models.
