"""
Live telemetry adapter for real-time drone data.

Receives live telemetry from external sources (DJI drones, MAVLink, custom systems, etc.)
and converts to the unified telemetry schema.
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.models import DroneState, TelemetryFrame, DroneHealth, CameraPayload


class LiveTelemetryAdapter:
    """
    Adapter for real-time telemetry streaming.

    Maintains current state of all active drones and provides
    real-time telemetry frames.
    """

    def __init__(self):
        """Initialize live telemetry adapter."""
        self.drones: Dict[str, DroneState] = {}
        self.start_time = time.time()
        self.last_update: Dict[str, float] = {}  # Track last update time per drone
        self.timeout_seconds = 30.0  # Mark drone offline after 30s of no data

    def update_drone(self, data: Dict[str, Any]) -> DroneState:
        """
        Update or create a drone state from incoming telemetry.

        Args:
            data: Telemetry data dictionary matching DroneState schema

        Returns:
            Updated DroneState object
        """
        drone_id = data.get('id', data.get('drone_id', 'unknown'))

        # Parse health status
        health_str = data.get('health', 'OK').upper()
        try:
            health = DroneHealth[health_str]
        except KeyError:
            health = DroneHealth.OK

        # Parse payload
        payload_data = data.get('payload') or {}
        payload = CameraPayload(
            camera_streams=payload_data.get('cameraStreams', payload_data.get('camera_streams', [])),
            gimbal_yaw=payload_data.get('gimbalYaw', payload_data.get('gimbal_yaw', 0.0)),
            gimbal_pitch=payload_data.get('gimbalPitch', payload_data.get('gimbal_pitch', 0.0)),
            battery=payload_data.get('battery', 1.0),
            thermal_enabled=payload_data.get('thermalEnabled', payload_data.get('thermal_enabled', False))
        )

        # Create drone state
        drone = DroneState(
            id=drone_id,
            lat=data.get('lat', 0.0),
            lon=data.get('lon', 0.0),
            alt_msl=data.get('alt_msl', data.get('altMsl', 0.0)),
            alt_agl=data.get('alt_agl', data.get('altAgl', 0.0)),
            heading=data.get('heading', 0.0),
            speed=data.get('speed', 0.0),
            health=health,
            link_quality=data.get('link_quality', data.get('linkQuality', 1.0)),
            payload=payload,
            vertical_speed=data.get('vertical_speed', data.get('verticalSpeed', 0.0)),
            corridor_id=data.get('corridor_id', data.get('corridorId')),
            route_index=data.get('route_index', data.get('routeIndex'))
        )

        # Update state
        self.drones[drone_id] = drone
        self.last_update[drone_id] = time.time()

        return drone

    def remove_drone(self, drone_id: str) -> bool:
        """
        Remove a drone from active tracking.

        Args:
            drone_id: Drone identifier

        Returns:
            True if drone was removed, False if not found
        """
        if drone_id in self.drones:
            del self.drones[drone_id]
            if drone_id in self.last_update:
                del self.last_update[drone_id]
            return True
        return False

    def get_current_frame(self) -> TelemetryFrame:
        """
        Get current telemetry frame with all active drones.

        Automatically marks drones as OFFLINE if they haven't sent
        data within timeout period.

        Returns:
            TelemetryFrame with current drone states
        """
        current_time = time.time()
        elapsed = current_time - self.start_time

        # Check for timed-out drones
        for drone_id, last_update in list(self.last_update.items()):
            if current_time - last_update > self.timeout_seconds:
                if drone_id in self.drones:
                    self.drones[drone_id].health = DroneHealth.OFFLINE

        return TelemetryFrame(
            time=elapsed,
            drones=list(self.drones.values())
        )

    def get_drone_state(self, drone_id: str) -> Optional[DroneState]:
        """
        Get current state of a specific drone.

        Args:
            drone_id: Drone identifier

        Returns:
            DroneState or None if not found
        """
        return self.drones.get(drone_id)

    def get_active_drone_ids(self) -> List[str]:
        """
        Get list of all active drone IDs.

        Returns:
            List of drone identifiers
        """
        return list(self.drones.keys())

    def get_drone_count(self) -> int:
        """
        Get count of currently tracked drones.

        Returns:
            Number of active drones
        """
        return len(self.drones)

    def clear_all(self) -> None:
        """Clear all drone states (useful for testing or reset)."""
        self.drones.clear()
        self.last_update.clear()
        self.start_time = time.time()

    def register_drone(self, drone_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Register a new drone for tracking.

        Args:
            drone_id: Unique drone identifier
            metadata: Optional metadata about the drone

        Returns:
            Registration confirmation with drone_id and timestamp
        """
        if drone_id not in self.drones:
            # Create initial state with default values
            self.drones[drone_id] = DroneState(
                id=drone_id,
                lat=0.0,
                lon=0.0,
                alt_msl=0.0,
                alt_agl=0.0,
                heading=0.0,
                speed=0.0,
                health=DroneHealth.OFFLINE,
                link_quality=0.0
            )
            self.last_update[drone_id] = time.time()

        return {
            "drone_id": drone_id,
            "registered_at": datetime.utcnow().isoformat(),
            "status": "registered"
        }
