"""
FastAPI server for drone visualization system.

Provides REST API endpoints for telemetry data, scenarios, and airspace info.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.adapters.playback import PlaybackAdapter
from src.services.altitude_service import AltitudeService


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


@app.post("/api/scenario/load")
async def load_scenario(
    simulation_file: str,
    origin_lat: float,
    origin_lon: float,
    facility_map_file: Optional[str] = None
):
    """
    Load a scenario for playback.

    Args:
        simulation_file: Path to simulation JSON export
        origin_lat: Scenario origin latitude
        origin_lon: Scenario origin longitude
        facility_map_file: Optional path to facility map cache
    """
    try:
        sim_path = Path(simulation_file)
        if not sim_path.exists():
            raise HTTPException(status_code=404, detail="Simulation file not found")

        # Load playback adapter
        state.playback_adapter = PlaybackAdapter(
            simulation_file=sim_path,
            origin_lat=origin_lat,
            origin_lon=origin_lon
        )

        # Load facility map if provided
        if facility_map_file:
            fac_path = Path(facility_map_file)
            if fac_path.exists():
                state.altitude_service = AltitudeService(facility_map_file=fac_path)

        # Store scenario info
        state.current_scenario = {
            "originLat": origin_lat,
            "originLon": origin_lon,
            "duration": state.playback_adapter.get_duration(),
            "metadata": state.playback_adapter.get_metadata()
        }

        return {
            "success": True,
            "scenario": state.current_scenario,
            "corridors": [c.to_dict() for c in state.playback_adapter.get_corridors()]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

    frame = state.playback_adapter.get_frame_at_time(time)
    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found")

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

    frames = []
    for frame in state.playback_adapter.iter_frames():
        frames.append(frame.to_dict())

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

    return {
        "corridors": [c.to_dict() for c in state.playback_adapter.get_corridors()]
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

    ceiling = state.altitude_service.get_facility_ceiling(lat, lon)

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

    return {
        "cells": state.altitude_service.get_facility_map_grid()
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

    result = state.altitude_service.check_altitude_violation(lat, lon, alt_agl)

    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
