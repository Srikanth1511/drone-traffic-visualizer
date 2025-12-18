from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ..adapters.playback import PlaybackBundle, load_playback_bundle
from ..services.altitude_service import AltitudeService

ROOT_DIR = Path(__file__).resolve().parents[2]
SCENARIO_CATALOG = ROOT_DIR / "scenarios" / "catalog.json"

app = FastAPI(title="Drone Traffic Visualizer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/status")
def status() -> dict:
    """Lightweight readiness check with available assets enumerated."""

    facility_samples = [
        str(ROOT_DIR / "data" / "facility_maps" / name)
        for name in ("benz_grid.json", "gt_grid.json")
        if (ROOT_DIR / "data" / "facility_maps" / name).exists()
    ]

    return {
        "status": "ok",
        "scenarios_available": SCENARIO_CATALOG.exists(),
        "facility_samples": facility_samples,
    }


@app.get("/health")
def health() -> dict:
    """Alias for /status maintained for backward compatibility."""

    return status()


@app.get("/scenarios")
def scenarios() -> dict:
    if not SCENARIO_CATALOG.exists():
        raise HTTPException(status_code=404, detail="Scenario catalog not found")
    with open(SCENARIO_CATALOG, "r", encoding="utf-8") as fp:
        return {"scenarios": json.load(fp)}


@app.get("/facility-grid")
def facility_grid(path: str) -> dict:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = ROOT_DIR / resolved
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="Facility grid not found")

    altitude = AltitudeService(str(resolved))
    return {"cells": altitude._facility_grid}


@app.get("/facility-ceiling")
def facility_ceiling(lat: float, lon: float, cache: Optional[str] = None) -> dict:
    altitude = AltitudeService(cache)
    ceiling = altitude.facility_ceiling(lat, lon)
    if ceiling is None:
        raise HTTPException(status_code=404, detail="Ceiling not found for coordinate")
    return {"lat": lat, "lon": lon, "ceiling_agl_m": ceiling}


@app.get("/telemetry")
def telemetry(
    path: str, origin_lat: Optional[float] = None, origin_lon: Optional[float] = None, facility_cache: Optional[str] = None
) -> dict:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = ROOT_DIR / resolved
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="Playback file not found")

    facility_path = None
    if facility_cache:
        facility_path = Path(facility_cache)
        if not facility_path.is_absolute():
            facility_path = ROOT_DIR / facility_path

    altitude = AltitudeService(str(facility_path) if facility_path else None)
    bundle: PlaybackBundle = load_playback_bundle(str(resolved), altitude, origin_lat, origin_lon)

    return {
        "metadata": bundle.metadata,
        "corridors": [asdict(corridor) for corridor in bundle.corridors],
        "snapshots": [asdict(snapshot) for snapshot in bundle.snapshots],
    }
