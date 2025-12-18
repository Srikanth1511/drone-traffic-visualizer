# Phase 1 Web MVP

This document summarizes the initial milestone for the Drone Traffic Visualizer. It focuses on simulation playback, facility ceiling awareness, and a developer-friendly skeleton that mirrors the simulator repository.

## Goals
- Render 3D venue basemaps (Google 3D tiles or CesiumJS fallback) centered on Mercedes-Benz Stadium or Georgia Tech.
- Play back simulation exports produced by `drone-traffic-simulator` using the `/telemetry` endpoint.
- Show drone markers with heading, ID, speed, and battery; clicking opens an inspector with MSL/AGL altitudes.
- Overlay FAA UAS Facility Map ceilings and warn when a drone exceeds the permitted AGL ceiling.
- Provide layer toggles for drones, trails (placeholder), corridors, and facility grids (corridor toggle wired in the React viewer).
- Include a scrubber with play/pause and speed controls (front-end stub provided).

## Directory alignment
- `src/adapters/playback.py`: Reads simulator JSON, converts ENU to lat/lon, normalizes telemetry.
- `src/services/altitude_service.py`: Handles MSL→AGL conversion and facility ceiling lookup.
- `src/server/main.py`: FastAPI surface for status/health, facility ceiling probe, telemetry playback, and corridor overlays.
- `src/web`: Vite/React scaffold to wire into the API.
- `scenarios/`: Venue presets with bounds, facility map cache references, and deterministic patrols.

## Running locally
```bash
pip install -e .[dev]
uvicorn src.server.main:app --reload
# (optional) cd src/web && npm install && npm run dev
pytest
```

## Acceptance tests
The following tests in `tests/` provide guardrails for the MVP:
- `TelemetryPlayback_ProducesMonotonicTimestamps`: snapshots stream is chronological.
- `FacilityMap_QueryReturnsCeilingForKnownPoint`: altitude service returns a finite ceiling for a cached grid.
- `ScenarioLoader_SpawnsExpectedDroneCount`: scenario JSONs load with the intended drone totals.
- `DeterministicPlayback_SameSeedSamePositions`: repeated playback of the same file yields the same positions.

## Notes
- Keep API keys (e.g., Google Maps) server-side to avoid exposing credentials in the front end.
- The UI avoids global omniscient terms and instead focuses on an overhead operations view.
- Future phases introduce live telemetry adapters (MAVLink, DJI/FlightHub, Remote ID) and VR/AR readiness.
