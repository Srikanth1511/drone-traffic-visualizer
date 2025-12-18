# Drone Traffic Visualizer

This repository hosts a standalone visualization console for the `drone-traffic-simulator` project. It focuses on playing back simulation exports, rendering 3D venue maps, overlaying FAA facility ceilings, and providing a developer-friendly foundation for future live telemetry adapters.

## Project layout
```
src/
  adapters/          # Data source adapters that normalize telemetry
  server/            # FastAPI server for serving telemetry and assets
  services/          # Shared business logic (altitude, facilities)
  scenarios/         # Scenario loader helpers
  web/               # Front-end source (placeholder scaffold)
scenarios/           # Venue presets (Mercedes-Benz Stadium, Georgia Tech)
docs/                # Specifications and operations guides
tests/               # Unit tests covering adapters and services
data/facility_maps/  # Cached facility grid samples for testing
```

## Getting started
1. Run everything via the one-click helper:
   ```bash
   ./run.sh           # installs deps into .venv and runs pytest
   ./run.sh --serve   # installs deps and starts uvicorn with reload
   ./run.sh --web     # installs npm deps and starts the Vite/React viewer on port 5173
   ```
   The first run downloads dependencies (internet required). Subsequent runs reuse `.venv` and `node_modules/`.
2. Manual commands (if you prefer):
   ```bash
   pip install -e .[dev]
   pytest
   uvicorn src.server.main:app --reload
   cd src/web && npm install && npm run dev
   ```

The server exposes a readiness/status probe (`/status`, with `/health` as an alias), a simple facility ceiling probe (`/facility-ceiling`), a facility grid stream (`/facility-grid`), scenario presets (`/scenarios`), and a telemetry playback endpoint that reads simulation JSON files (including corridor overlays for the Phase 1 map view). See `docs/PHASE1_WEB_MVP.md` for MVP details and `docs/FAA_RULES.md` for a quick reference on FAA constraints.

## Relation to `drone-traffic-simulator`
The simulator remains the source of truth for generating state logs and corridor networks. Use its `export_simulation_data` helper to produce a JSON bundle, then point this visualizer to the resulting file via the playback adapter. No changes to the simulator are required.

## Front-end (AirLoom-inspired map UI)
- Vite + React + React-Leaflet render an interactive OSM map with FAA facility grid overlays, corridor polylines, and heading-aware drone icons.
- Scenario presets are listed from `/scenarios` and include cached facility grid paths plus playback exports stored in `data/playback/`.
- The bottom transport bar supports play/pause, speed control, and scrubbing between telemetry snapshots from `/telemetry`.
- The right-hand inspector mirrors the MVP requirement: per-drone lat/lon, MSL/AGL altitudes, heading, speed, battery, and a violation pill when above the facility ceiling from `/facility-grid`.
- The layout mirrors the requested map experience while keeping the "god view" wording out of the UI; basemap defaults to OSM tiles for out-of-the-box testing.
