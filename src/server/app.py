"""
FastAPI server for drone visualization system.

Provides REST API endpoints for telemetry data, scenarios, and airspace info.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.adapters.playback import PlaybackAdapter
from src.services.altitude_service import AltitudeService

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parents[2]


# Global state for current playback session
class AppState:
    """Application state container."""
    playback_adapter: Optional[PlaybackAdapter] = None
    altitude_service: Optional[AltitudeService] = None
    current_scenario: Optional[Dict[str, Any]] = None


state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup: Initialize default services
    state.altitude_service = AltitudeService()
    yield
    # Shutdown: Cleanup resources
    state.playback_adapter = None
    state.altitude_service = None


# Create FastAPI app
app = FastAPI(
    title="Drone Visualization API",
    description="Live drone visualization and telemetry system",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Drone Visualization API",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "playback_loaded": state.playback_adapter is not None,
        "scenario_loaded": state.current_scenario is not None
    }


from pydantic import BaseModel

class ScenarioLoadRequest(BaseModel):
    simulation_file: str
    origin_lat: float
    origin_lon: float
    facility_map_file: Optional[str] = None


@app.post("/api/scenario/load")
async def load_scenario(request: ScenarioLoadRequest):
    """
    Load a scenario for playback.

    Args:
        simulation_file: Path to simulation JSON export
        origin_lat: Scenario origin latitude
        origin_lon: Scenario origin longitude
        facility_map_file: Optional path to facility map cache
    """
    def resolve_path(path_value: str) -> Path:
        path = Path(path_value)
        if not path.is_absolute():
            path = (BASE_DIR / path).resolve()
        return path

    try:
        sim_path = resolve_path(request.simulation_file)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to resolve simulation path")
        raise HTTPException(status_code=400, detail="Invalid simulation file path") from exc

    if not sim_path.exists():
        raise HTTPException(status_code=404, detail=f"Simulation file not found at {sim_path}")

    try:
        state.playback_adapter = PlaybackAdapter(
            simulation_file=sim_path,
            origin_lat=request.origin_lat,
            origin_lon=request.origin_lon
        )
    except (FileNotFoundError, ValueError) as exc:
        logger.exception("Scenario load failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error creating playback adapter")
        raise HTTPException(status_code=500, detail="Failed to initialize playback adapter") from exc

    # Load facility map if provided
    if request.facility_map_file:
        try:
            fac_path = resolve_path(request.facility_map_file)
            if fac_path.exists():
                state.altitude_service = AltitudeService(facility_map_file=fac_path)
            else:
                logger.warning("Facility map file not found at %s", fac_path)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error loading facility map: %s", exc)
            raise HTTPException(status_code=400, detail="Invalid facility map file") from exc

    # Store scenario info
    state.current_scenario = {
        "originLat": request.origin_lat,
        "originLon": request.origin_lon,
        "duration": state.playback_adapter.get_duration(),
        "metadata": state.playback_adapter.get_metadata()
    }

    return {
        "success": True,
        "scenario": state.current_scenario,
        "corridors": [c.to_dict() for c in state.playback_adapter.get_corridors()]
    }


@app.get("/api/telemetry/frame")
async def get_telemetry_frame(time: float = Query(..., description="Simulation time")):
    """
    Get telemetry frame at specific time.

    Args:
        time: Simulation time in seconds

    Returns:
        TelemetryFrame as JSON
    """
    if not state.playback_adapter:
        raise HTTPException(status_code=400, detail="No scenario loaded")
    try:
        frame = state.playback_adapter.get_frame_at_time(time)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error retrieving telemetry frame")
        raise HTTPException(status_code=500, detail="Failed to retrieve telemetry frame") from exc

    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found for requested time")

    return frame.to_dict()


@app.get("/api/telemetry/all")
async def get_all_telemetry():
    """
    Get all telemetry frames.

    Returns:
        List of all frames
    """
    if not state.playback_adapter:
        raise HTTPException(status_code=400, detail="No scenario loaded")

    try:
        frames = []
        for frame in state.playback_adapter.iter_frames():
            frames.append(frame.to_dict())
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error iterating telemetry frames")
        raise HTTPException(status_code=500, detail="Unable to stream telemetry frames") from exc

    return {
        "frames": frames,
        "count": len(frames)
    }


@app.get("/api/scenario/info")
async def get_scenario_info():
    """Get current scenario information."""
    if not state.current_scenario:
        raise HTTPException(status_code=400, detail="No scenario loaded")

    return state.current_scenario


@app.get("/api/scenario/corridors")
async def get_corridors():
    """Get corridor network."""
    if not state.playback_adapter:
        raise HTTPException(status_code=400, detail="No scenario loaded")

    try:
        corridors = [c.to_dict() for c in state.playback_adapter.get_corridors()]
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to retrieve corridors")
        raise HTTPException(status_code=500, detail="Unable to retrieve corridor network") from exc

    return {
        "corridors": corridors
    }


@app.get("/api/airspace/ceiling")
async def get_airspace_ceiling(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    """
    Get facility map ceiling at location.

    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees

    Returns:
        Ceiling information
    """
    if not state.altitude_service:
        raise HTTPException(status_code=500, detail="Altitude service not initialized")
    try:
        ceiling = state.altitude_service.get_facility_ceiling(lat, lon)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to fetch airspace ceiling")
        raise HTTPException(status_code=500, detail="Failed to fetch airspace ceiling") from exc

    return {
        "lat": lat,
        "lon": lon,
        "ceilingAgl": ceiling
    }


@app.get("/api/airspace/facility-map")
async def get_facility_map():
    """Get all facility map cells."""
    if not state.altitude_service:
        raise HTTPException(status_code=500, detail="Altitude service not initialized")
    try:
        cells = state.altitude_service.get_facility_map_grid()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to fetch facility map grid")
        raise HTTPException(status_code=500, detail="Failed to fetch facility map grid") from exc

    return {
        "cells": cells
    }


@app.post("/api/altitude/check")
async def check_altitude_violation(
    lat: float,
    lon: float,
    alt_agl: float
):
    """
    Check altitude violation.

    Args:
        lat: Latitude
        lon: Longitude
        alt_agl: Altitude AGL in meters
    """
    if not state.altitude_service:
        raise HTTPException(status_code=500, detail="Altitude service not initialized")
    try:
        result = state.altitude_service.check_altitude_violation(lat, lon, alt_agl)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to evaluate altitude violation")
        raise HTTPException(status_code=500, detail="Failed to evaluate altitude violation") from exc

    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
