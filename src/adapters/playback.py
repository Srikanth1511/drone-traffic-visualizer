"""Playback adapter for simulator export files.

The adapter consumes the JSON output produced by `export_simulation_data` in
`drone-traffic-simulator` and emits a normalized telemetry schema used by the
visualizer. A lightweight ENU-to-geodetic conversion is applied based on the
scenario origin.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple
import json

from ..services.altitude_service import AltitudeService
from ..services.geo import enu_to_geodetic


@dataclass
class DronePayload:
    cameraStreams: List[str] | None = None
    gimbalYaw: float | None = None
    gimbalPitch: float | None = None
    battery: float | None = None


@dataclass
class DroneState:
    id: str
    lat: float
    lon: float
    alt_msl: float
    alt_agl: float
    heading: float
    speed: float
    health: str | None = None
    linkQuality: float | None = None
    payload: DronePayload | None = None


@dataclass
class TelemetrySnapshot:
    time: float
    drones: List[DroneState]


@dataclass
class CorridorPoint:
    lat: float
    lon: float
    alt_msl: float
    alt_agl: float


@dataclass
class Corridor:
    id: str
    type: str
    width_m: float
    path: List[CorridorPoint]


@dataclass
class PlaybackBundle:
    metadata: Dict
    snapshots: List[TelemetrySnapshot]
    corridors: List[Corridor]


def _normalize_payload(raw: Dict) -> DronePayload:
    if raw is None:
        return DronePayload(cameraStreams=[])
    return DronePayload(
        cameraStreams=raw.get("cameraStreams"),
        gimbalYaw=raw.get("gimbalYaw"),
        gimbalPitch=raw.get("gimbalPitch"),
        battery=raw.get("battery"),
    )


def _normalize_drone(drone_id: str, raw: Dict, origin: Tuple[float, float], altitude: AltitudeService) -> DroneState:
    lat, lon = enu_to_geodetic(raw["x"], raw["y"], origin[0], origin[1])
    alt_msl = float(raw.get("z", 0.0))
    alt_agl = altitude.msl_to_agl(lat, lon, alt_msl)
    return DroneState(
        id=drone_id,
        lat=lat,
        lon=lon,
        alt_msl=alt_msl,
        alt_agl=alt_agl,
        heading=float(raw.get("heading", 0.0)),
        speed=float(raw.get("speed", 0.0)),
        health=raw.get("health"),
        linkQuality=raw.get("linkQuality"),
        payload=_normalize_payload(raw.get("payload")),
    )


def _normalize_corridor(raw: Dict, origin: Tuple[float, float], altitude: AltitudeService) -> Corridor:
    points = []
    for point in raw.get("points", []):
        x, y, *rest = point
        z = rest[0] if rest else 0.0
        lat, lon = enu_to_geodetic(x, y, origin[0], origin[1])
        alt_msl = float(z)
        alt_agl = altitude.msl_to_agl(lat, lon, alt_msl)
        points.append(CorridorPoint(lat=lat, lon=lon, alt_msl=alt_msl, alt_agl=alt_agl))

    return Corridor(
        id=raw.get("id", "corridor"),
        type=raw.get("type", "standard"),
        width_m=float(raw.get("width", 0.0)),
        path=points,
    )


def load_playback_bundle(
    path: str, altitude: AltitudeService, origin_lat: float | None = None, origin_lon: float | None = None
) -> PlaybackBundle:
    """Load a simulation export and return snapshots plus corridor overlays."""
    with open(path, "r", encoding="utf-8") as fp:
        data = json.load(fp)

    metadata = data.get("metadata", {})
    origin = (
        float(origin_lat if origin_lat is not None else metadata.get("originLat", 0.0)),
        float(origin_lon if origin_lon is not None else metadata.get("originLon", 0.0)),
    )

    corridor_source = data.get("corridors") or metadata.get("corridors", [])
    corridors = [_normalize_corridor(corridor, origin, altitude) for corridor in corridor_source]

    snapshots: List[TelemetrySnapshot] = []
    timesteps = data.get("timesteps", [])
    for step in sorted(timesteps, key=lambda ts: ts.get("time", 0.0)):
        time = float(step.get("time", 0.0))
        drones_raw: Dict[str, Dict] = step.get("drones", {})
        drones = [_normalize_drone(drone_id, payload, origin, altitude) for drone_id, payload in drones_raw.items()]
        snapshots.append(TelemetrySnapshot(time=time, drones=drones))

    return PlaybackBundle(metadata=metadata, snapshots=snapshots, corridors=corridors)


def load_playback(path: str, altitude: AltitudeService, origin_lat: float | None = None, origin_lon: float | None = None) -> Iterable[TelemetrySnapshot]:
    """Backwards-compatible snapshot generator wrapper."""
    bundle = load_playback_bundle(path, altitude, origin_lat, origin_lon)
    for snapshot in bundle.snapshots:
        yield snapshot


def snapshot_stream_to_list(snapshot_stream: Iterable[TelemetrySnapshot]) -> List[TelemetrySnapshot]:
    """Materialize a snapshot stream for deterministic testing."""
    return list(snapshot_stream)
