"""
Playback adapter for simulation data.

Reads JSON exported by drone-traffic-simulator's SimulationDataExporter
and converts it to the unified telemetry schema.
"""

import json
import math
from pathlib import Path
from typing import List, Iterator, Dict, Any, Optional

from src.models import DroneState, TelemetryFrame, DroneHealth, CameraPayload, Corridor
from src.utils.coordinates import enu_to_latlon, calculate_heading


class PlaybackAdapter:
    """
    Adapter for replaying simulation data.

    Loads exported simulation JSON and yields TelemetryFrames chronologically.
    """

    def __init__(self, simulation_file: Path, origin_lat: float, origin_lon: float):
        """
        Initialize playback adapter.

        Args:
            simulation_file: Path to simulation JSON export
            origin_lat: Scenario origin latitude
            origin_lon: Scenario origin longitude
        """
        self.simulation_file = simulation_file
        self.origin_lat = origin_lat
        self.origin_lon = origin_lon
        self.data: Optional[Dict[str, Any]] = None
        self.corridors: List[Corridor] = []
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self._load_data()

    def _load_data(self) -> None:
        """Load simulation data from JSON file."""
        try:
            with open(self.simulation_file, 'r') as f:
                self.data = json.load(f)
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"Simulation file not found at {self.simulation_file}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Simulation file at {self.simulation_file} is not valid JSON"
            ) from exc

        if not self.data or 'timesteps' not in self.data:
            raise ValueError("Simulation data missing required 'timesteps' entries")

        if not self.data['timesteps']:
            raise ValueError("Simulation data contains no timesteps to play back")

        self.start_time = self.data['timesteps'][0]['time']
        self.end_time = self.data['timesteps'][-1]['time']

        # Load corridors if present
        if 'corridors' in self.data:
            for corridor_data in self.data['corridors']:
                corridor = self._parse_corridor(corridor_data)
                self.corridors.append(corridor)

    def _parse_corridor(self, data: Dict[str, Any]) -> Corridor:
        """Parse corridor from JSON data."""
        # Convert centerline from ENU to lat/lon if needed
        centerline = []
        for point in data.get('centerline', []):
            if len(point) == 3:
                # ENU coordinates
                x, y, z = point
                lat, lon = enu_to_latlon(x, y, self.origin_lat, self.origin_lon)
                centerline.append([lat, lon, z])
            else:
                # Already lat/lon
                centerline.append(point)

        return Corridor(
            id=data['id'],
            centerline=centerline,
            width=data.get('width', 30.0),
            altitude_range=data.get('altitude_range', data.get('altitudeRange', [40, 60])),
            capacity=data.get('capacity', 4),
            type=data.get('type', 'specific'),
            risk_score=data.get('risk_score', data.get('riskScore', 0.0)),
            rf_quality=data.get('rf_quality', data.get('rfQuality', 1.0)),
            connections=data.get('connections', [])
        )

    def get_corridors(self) -> List[Corridor]:
        """Get corridor network."""
        return self.corridors

    def get_metadata(self) -> Dict[str, Any]:
        """Get simulation metadata."""
        if self.data:
            return self.data.get('metadata', {})
        return {}

    def get_duration(self) -> float:
        """Get total simulation duration in seconds."""
        if not self.data or 'timesteps' not in self.data:
            return 0.0

        timesteps = self.data['timesteps']
        if not timesteps:
            return 0.0

        return timesteps[-1]['time']

    def get_frame_at_time(self, time: float) -> Optional[TelemetryFrame]:
        """
        Get telemetry frame at specific time.

        Args:
            time: Simulation time in seconds

        Returns:
            TelemetryFrame or None if time is out of bounds
        """
        if not self.data or 'timesteps' not in self.data:
            return None

        timesteps = self.data['timesteps']

        if time < self.start_time or time > self.end_time:
            return None

        # Find closest timestep
        closest_idx = 0
        min_diff = float('inf')

        for idx, ts in enumerate(timesteps):
            diff = abs(ts['time'] - time)
            if diff < min_diff:
                min_diff = diff
                closest_idx = idx

        return self._parse_timestep(timesteps[closest_idx])

    def iter_frames(self) -> Iterator[TelemetryFrame]:
        """
        Iterate through all telemetry frames chronologically.

        Yields:
            TelemetryFrame for each timestep
        """
        if not self.data or 'timesteps' not in self.data:
            return

        for timestep_data in self.data['timesteps']:
            yield self._parse_timestep(timestep_data)

    def _parse_timestep(self, timestep_data: Dict[str, Any]) -> TelemetryFrame:
        """Parse a single timestep into TelemetryFrame."""
        time = timestep_data['time']
        drones = []

        uavs_data = timestep_data.get('uavs', {})

        for uav_id, uav_state in uavs_data.items():
            drone = self._parse_drone_state(uav_id, uav_state)
            drones.append(drone)

        return TelemetryFrame(time=time, drones=drones)

    def _parse_drone_state(self, uav_id: str, state: Dict[str, Any]) -> DroneState:
        """
        Parse drone state from simulation data.

        Args:
            uav_id: UAV identifier
            state: State dictionary from simulation

        Returns:
            DroneState object
        """
        # Extract position (can be ENU or lat/lon)
        position = state.get('position', [0, 0, 0])

        if 'lat' in state:
            # Already in lat/lon format
            lat = state['lat']
            lon = state['lon']
            alt_agl = position[2] if len(position) > 2 else 0.0
        else:
            # ENU format - convert to lat/lon
            x, y, z = position
            lat, lon = enu_to_latlon(x, y, self.origin_lat, self.origin_lon)
            alt_agl = z

        # Extract velocity for heading calculation
        velocity = state.get('velocity', [0, 0, 0])
        vx, vy, vz = velocity

        # Calculate heading from velocity
        if abs(vx) > 0.01 or abs(vy) > 0.01:
            heading = (math.degrees(math.atan2(vx, vy)) + 360) % 360
        else:
            heading = 0.0

        # Calculate speed
        speed = math.sqrt(vx**2 + vy**2)

        # For now, assume ground elevation is 0 (will be improved with altitude service)
        alt_msl = alt_agl

        # Slightly stagger altitudes per-drone for clearer 3D separation
        hash_offset = sum(ord(c) for c in uav_id) % 6  # 0-5
        alt_agl += hash_offset * 3.0
        alt_msl += hash_offset * 3.0

        # Parse battery (normalize to 0-1 if needed)
        battery = state.get('battery', 1.0)
        if battery > 1.0:
            battery = battery / 100.0

        # Determine health status
        operational_state = state.get('operational_state', 'active')
        if operational_state == 'active':
            health = DroneHealth.OK
        else:
            health = DroneHealth.WARNING

        # Create payload
        payload = CameraPayload(
            battery=battery,
            camera_streams=[]
        )

        return DroneState(
            id=uav_id,
            lat=lat,
            lon=lon,
            alt_msl=alt_msl,
            alt_agl=alt_agl,
            heading=heading,
            speed=speed,
            health=health,
            link_quality=1.0,
            payload=payload,
            vertical_speed=vz,
            corridor_id=state.get('corridor_id'),
            route_index=state.get('route_index')
        )
