"""
FastAPI server for drone visualization system.

Provides REST API endpoints for telemetry data, scenarios, and airspace info.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import asyncio
import json

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.adapters.playback import PlaybackAdapter
from src.adapters.live import LiveTelemetryAdapter
from src.services.altitude_service import AltitudeService


# Global state for current playback session
class AppState:
    """Application state container."""
    playback_adapter: Optional[PlaybackAdapter] = None
    live_adapter: Optional[LiveTelemetryAdapter] = None
    altitude_service: Optional[AltitudeService] = None
    current_scenario: Optional[Dict[str, Any]] = None
    # WebSocket connections for broadcasting live telemetry
    active_connections: list[WebSocket] = []
    # Video frame storage: {drone_id: latest_frame_bytes}
    video_frames: Dict[str, bytes] = {}


state = AppState()
state.active_connections = []  # Initialize list
state.video_frames = {}  # Initialize video storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup: Initialize default services
    state.altitude_service = AltitudeService()
    state.live_adapter = LiveTelemetryAdapter()
    yield
    # Shutdown: Cleanup resources
    state.playback_adapter = None
    state.live_adapter = None
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
    try:
        sim_path = Path(request.simulation_file)
        if not sim_path.exists():
            raise HTTPException(status_code=404, detail="Simulation file not found")

        # Load playback adapter
        state.playback_adapter = PlaybackAdapter(
            simulation_file=sim_path,
            origin_lat=request.origin_lat,
            origin_lon=request.origin_lon
        )

        # Load facility map if provided
        if request.facility_map_file:
            fac_path = Path(request.facility_map_file)
            if fac_path.exists():
                state.altitude_service = AltitudeService(facility_map_file=fac_path)

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


# ============================================================================
# LIVE TELEMETRY ENDPOINTS
# ============================================================================

class DroneRegistrationRequest(BaseModel):
    """Request model for drone registration."""
    drone_id: str
    metadata: Optional[Dict[str, Any]] = None


@app.post("/api/drones/register")
async def register_drone(request: DroneRegistrationRequest):
    """
    Register a new drone for live tracking.

    Args:
        drone_id: Unique identifier for the drone
        metadata: Optional metadata about the drone

    Returns:
        Registration confirmation
    """
    if not state.live_adapter:
        raise HTTPException(status_code=500, detail="Live telemetry adapter not initialized")

    result = state.live_adapter.register_drone(request.drone_id, request.metadata)
    return result


class TelemetryUpdateRequest(BaseModel):
    """Request model for telemetry update."""
    id: str
    lat: float
    lon: float
    alt_msl: Optional[float] = 0.0
    alt_agl: Optional[float] = 0.0
    heading: Optional[float] = 0.0
    speed: Optional[float] = 0.0
    health: Optional[str] = "OK"
    link_quality: Optional[float] = 1.0
    vertical_speed: Optional[float] = 0.0
    corridor_id: Optional[str] = None
    route_index: Optional[int] = None
    payload: Optional[Dict[str, Any]] = None


@app.post("/api/telemetry/live/update")
async def update_live_telemetry(request: TelemetryUpdateRequest):
    """
    Update live telemetry for a drone (HTTP POST).

    This is an alternative to WebSocket for simpler integration.

    Args:
        Telemetry data matching DroneState schema

    Returns:
        Updated drone state
    """
    if not state.live_adapter:
        raise HTTPException(status_code=500, detail="Live telemetry adapter not initialized")

    try:
        # Update drone state
        drone = state.live_adapter.update_drone(request.dict())

        # Broadcast to connected WebSocket clients
        if state.active_connections:
            frame = state.live_adapter.get_current_frame()
            message = json.dumps({
                "type": "telemetry_update",
                "data": frame.to_dict()
            })
            # Send to all connected clients
            for connection in state.active_connections:
                try:
                    await connection.send_text(message)
                except Exception:
                    # Remove broken connections
                    state.active_connections.remove(connection)

        return drone.to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/telemetry/live/current")
async def get_live_telemetry():
    """
    Get current live telemetry frame.

    Returns:
        Current TelemetryFrame with all active drones
    """
    if not state.live_adapter:
        raise HTTPException(status_code=500, detail="Live telemetry adapter not initialized")

    frame = state.live_adapter.get_current_frame()
    return frame.to_dict()


@app.delete("/api/drones/{drone_id}")
async def unregister_drone(drone_id: str):
    """
    Unregister a drone from live tracking.

    Args:
        drone_id: Drone identifier

    Returns:
        Success status
    """
    if not state.live_adapter:
        raise HTTPException(status_code=500, detail="Live telemetry adapter not initialized")

    removed = state.live_adapter.remove_drone(drone_id)

    if not removed:
        raise HTTPException(status_code=404, detail="Drone not found")

    return {"success": True, "drone_id": drone_id}


@app.websocket("/ws/telemetry/live")
async def websocket_live_telemetry(websocket: WebSocket):
    """
    WebSocket endpoint for real-time telemetry streaming.

    Clients can:
    1. Send telemetry updates: {"type": "update", "data": {...}}
    2. Register drones: {"type": "register", "drone_id": "...", "metadata": {...}}
    3. Receive broadcasts: {"type": "telemetry_update", "data": {...}}

    The connection will receive broadcasts whenever any drone updates its telemetry.
    """
    await websocket.accept()
    state.active_connections.append(websocket)

    try:
        while True:
            # Wait for incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")

            if msg_type == "register":
                # Register drone
                drone_id = message.get("drone_id")
                metadata = message.get("metadata")
                result = state.live_adapter.register_drone(drone_id, metadata)
                await websocket.send_text(json.dumps({
                    "type": "register_response",
                    "data": result
                }))

            elif msg_type == "update":
                # Update telemetry
                telemetry_data = message.get("data")
                drone = state.live_adapter.update_drone(telemetry_data)

                # Broadcast to all clients
                frame = state.live_adapter.get_current_frame()
                broadcast_msg = json.dumps({
                    "type": "telemetry_update",
                    "data": frame.to_dict()
                })

                for connection in state.active_connections:
                    try:
                        await connection.send_text(broadcast_msg)
                    except Exception:
                        # Remove broken connections
                        if connection in state.active_connections:
                            state.active_connections.remove(connection)

            elif msg_type == "ping":
                # Respond to ping
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        # Remove from active connections
        if websocket in state.active_connections:
            state.active_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in state.active_connections:
            state.active_connections.remove(websocket)


# ============================================================================
# VIDEO STREAMING ENDPOINTS
# ============================================================================

from fastapi import File, UploadFile, Form
from fastapi.responses import StreamingResponse, Response
import io

@app.post("/api/video/{drone_id}/frame")
async def upload_video_frame(drone_id: str, frame: UploadFile = File(...)):
    """
    Upload a single video frame (JPEG or H.264 chunk).

    The latest frame is stored in memory and can be retrieved
    via GET /api/video/{drone_id}/frame

    Args:
        drone_id: Unique drone identifier
        frame: Video frame as JPEG or H.264 encoded data

    Returns:
        Success status
    """
    try:
        # Read frame data
        frame_data = await frame.read()

        # Store latest frame for this drone
        state.video_frames[drone_id] = frame_data

        return {
            "success": True,
            "drone_id": drone_id,
            "frame_size": len(frame_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/video/{drone_id}/frame")
async def get_video_frame(drone_id: str):
    """
    Get the latest video frame for a drone.

    Returns the most recently uploaded frame as JPEG image.

    Args:
        drone_id: Unique drone identifier

    Returns:
        JPEG image
    """
    if drone_id not in state.video_frames:
        raise HTTPException(status_code=404, detail="No video frame available for this drone")

    frame_data = state.video_frames[drone_id]

    return Response(
        content=frame_data,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@app.get("/api/video/{drone_id}/stream.mjpeg")
async def stream_video_mjpeg(drone_id: str):
    """
    Stream video as Motion JPEG (MJPEG).

    Continuously sends the latest frame for display in browser.
    Simple but works everywhere.

    Args:
        drone_id: Unique drone identifier

    Returns:
        MJPEG stream
    """
    async def generate():
        while True:
            if drone_id in state.video_frames:
                frame = state.video_frames[drone_id]

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

            await asyncio.sleep(0.1)  # ~10 FPS

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
