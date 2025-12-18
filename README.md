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
   ./run.sh        # installs deps into .venv and runs pytest
   ./run.sh --serve  # installs deps and starts uvicorn with reload
   ```
   The first run downloads dependencies (internet required). Subsequent runs reuse `.venv`.
2. Manual commands (if you prefer):
   ```bash
   pip install -e .[dev]
   pytest
   uvicorn src.server.main:app --reload
   ```

The server exposes a health check (`/health`), a simple facility ceiling probe (`/facility-ceiling`), and a telemetry playback endpoint that reads simulation JSON files. See `docs/PHASE1_WEB_MVP.md` for MVP details and `docs/FAA_RULES.md` for a quick reference on FAA constraints.

## Relation to `drone-traffic-simulator`
The simulator remains the source of truth for generating state logs and corridor networks. Use its `export_simulation_data` helper to produce a JSON bundle, then point this visualizer to the resulting file via the playback adapter. No changes to the simulator are required.

## Front-end placeholder
The `src/web` directory contains a lightweight Vite/React starter configuration stub to mirror the final layout. It can be replaced or expanded without touching back-end adapters.
