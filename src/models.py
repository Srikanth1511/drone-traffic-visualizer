"""
Core data models for drone visualization system.

Defines the common telemetry schema that all adapters must output.
Follows the spec: lat, lon, alt_msl, alt_agl, heading, speed, health, etc.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class DroneHealth(str, Enum):
    """Drone operational health status."""
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"
    OFFLINE = "OFFLINE"


@dataclass
class CameraPayload:
    """Camera and gimbal payload information."""
    camera_streams: List[str] = field(default_factory=list)
    gimbal_yaw: float = 0.0  # degrees
    gimbal_pitch: float = 0.0  # degrees
    battery: float = 1.0  # 0.0 to 1.0
    thermal_enabled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cameraStreams": self.camera_streams,
            "gimbalYaw": self.gimbal_yaw,
            "gimbalPitch": self.gimbal_pitch,
            "battery": self.battery,
            "thermalEnabled": self.thermal_enabled
        }


@dataclass
class DroneState:
    """
    Unified drone state representation.

    All adapters (playback, MAVLink, DJI, Remote ID) output this format.
    """
    id: str
    lat: float  # degrees
    lon: float  # degrees
    alt_msl: float  # meters (mean sea level)
    alt_agl: float  # meters (above ground level)
    heading: float  # degrees (0-360, 0=north, clockwise)
    speed: float  # m/s
    health: DroneHealth = DroneHealth.OK
    link_quality: float = 1.0  # 0.0 to 1.0
    payload: Optional[CameraPayload] = None

    # Optional fields for enhanced telemetry
    vertical_speed: float = 0.0  # m/s
    corridor_id: Optional[str] = None
    route_index: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "id": self.id,
            "lat": self.lat,
            "lon": self.lon,
            "alt_msl": self.alt_msl,
            "alt_agl": self.alt_agl,
            "heading": self.heading,
            "speed": self.speed,
            "health": self.health.value,
            "linkQuality": self.link_quality,
            "verticalSpeed": self.vertical_speed
        }

        if self.payload:
            result["payload"] = self.payload.to_dict()

        if self.corridor_id:
            result["corridorId"] = self.corridor_id
        if self.route_index is not None:
            result["routeIndex"] = self.route_index

        return result


@dataclass
class TelemetryFrame:
    """
    A single timestep containing states for all drones.

    This is the primary data structure sent to the frontend.
    """
    time: float  # simulation or real time in seconds
    drones: List[DroneState]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "time": self.time,
            "drones": [drone.to_dict() for drone in self.drones]
        }


@dataclass
class Corridor:
    """Corridor representation from simulation data."""
    id: str
    centerline: List[List[float]]  # List of [x, y, z] or [lat, lon, alt]
    width: float  # meters
    altitude_range: List[float]  # [min, max] in meters AGL
    capacity: int = 4
    type: str = "specific"
    risk_score: float = 0.0
    rf_quality: float = 1.0
    connections: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "centerline": self.centerline,
            "width": self.width,
            "altitudeRange": self.altitude_range,
            "capacity": self.capacity,
            "type": self.type,
            "riskScore": self.risk_score,
            "rfQuality": self.rf_quality,
            "connections": self.connections
        }


@dataclass
class Scenario:
    """Scenario configuration for visualization."""
    name: str
    origin_lat: float
    origin_lon: float
    bounds: Dict[str, List[float]]  # {"min": [x, y, z], "max": [x, y, z]}
    corridors: List[Corridor] = field(default_factory=list)
    facility_map_cache: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "originLat": self.origin_lat,
            "originLon": self.origin_lon,
            "bounds": self.bounds,
            "corridors": [c.to_dict() for c in self.corridors],
            "facilityMapCache": self.facility_map_cache
        }


@dataclass
class FacilityMapCell:
    """FAA UAS Facility Map grid cell with altitude ceiling."""
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    max_altitude_agl: float  # meters AGL

    def contains(self, lat: float, lon: float) -> bool:
        """Check if lat/lon is within this cell."""
        return (self.lat_min <= lat <= self.lat_max and
                self.lon_min <= lon <= self.lon_max)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "latMin": self.lat_min,
            "latMax": self.lat_max,
            "lonMin": self.lon_min,
            "lonMax": self.lon_max,
            "maxAltitudeAgl": self.max_altitude_agl
        }
