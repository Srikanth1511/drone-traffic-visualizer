from __future__ import annotations

from pathlib import Path
from typing import Optional

from dataclasses import asdict

from fastapi import FastAPI, HTTPException

from ..adapters.playback import TelemetrySnapshot, load_playback, snapshot_stream_to_list
from ..services.altitude_service import AltitudeService

app = FastAPI(title="Drone Traffic Visualizer API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/facility-ceiling")
def facility_ceiling(lat: float, lon: float, cache: Optional[str] = None) -> dict:
    altitude = AltitudeService(cache)
    ceiling = altitude.facility_ceiling(lat, lon)
    if ceiling is None:
        raise HTTPException(status_code=404, detail="Ceiling not found for coordinate")
    return {"lat": lat, "lon": lon, "ceiling_agl_m": ceiling}


@app.get("/telemetry")
def telemetry(path: str, origin_lat: Optional[float] = None, origin_lon: Optional[float] = None, facility_cache: Optional[str] = None) -> dict:
    resolved = Path(path)
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="Playback file not found")

    altitude = AltitudeService(facility_cache)
    snapshots = snapshot_stream_to_list(load_playback(str(resolved), altitude, origin_lat, origin_lon))
    return {"snapshots": [asdict(snapshot) for snapshot in snapshots]}
