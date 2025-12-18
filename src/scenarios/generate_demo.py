"""
Generate demo scenario for Mercedes-Benz Stadium.

Creates a simulation export with 3 drones patrolling the stadium perimeter.
This serves as the MVP demo and test scenario.
"""

import json
import math
from pathlib import Path
from typing import List, Tuple


def generate_patrol_path(
    center_lat: float,
    center_lon: float,
    radius_meters: float,
    altitude_agl: float,
    num_points: int = 20
) -> List[List[float]]:
    """
    Generate circular patrol path around a center point.

    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        radius_meters: Patrol radius in meters
        altitude_agl: Altitude AGL in meters
        num_points: Number of waypoints in circle

    Returns:
        List of [lon, lat, alt] waypoints
    """
    # Convert radius to degrees (approximate)
    meters_per_deg_lat = 111320.0
    meters_per_deg_lon = 111320.0 * math.cos(math.radians(center_lat))

    radius_lat = radius_meters / meters_per_deg_lat
    radius_lon = radius_meters / meters_per_deg_lon

    waypoints = []
    for i in range(num_points + 1):  # +1 to close the loop
        angle = 2 * math.pi * i / num_points
        lat = center_lat + radius_lat * math.sin(angle)
        lon = center_lon + radius_lon * math.cos(angle)
        waypoints.append([lon, lat, altitude_agl])

    return waypoints


def generate_corridor(
    corridor_id: str,
    centerline: List[List[float]],
    corridor_type: str = "specific"
) -> dict:
    """Generate corridor dictionary."""
    return {
        "id": corridor_id,
        "centerline": centerline,
        "width": 30.0,
        "altitudeRange": [40, 100],
        "capacity": 4,
        "type": corridor_type,
        "riskScore": 0.1,
        "rfQuality": 0.95,
        "connections": []
    }


def generate_drone_trajectory(
    drone_id: str,
    path: List[List[float]],
    speed_mps: float,
    start_time: float,
    time_step: float = 0.1
) -> Tuple[List[dict], float]:
    """
    Generate drone trajectory along a path.

    Args:
        drone_id: Drone identifier
        path: List of [lon, lat, alt] waypoints
        speed_mps: Speed in m/s
        start_time: Start time in seconds
        time_step: Time between samples

    Returns:
        Tuple of (timesteps, duration)
    """
    timesteps = []
    current_time = start_time

    for i in range(len(path) - 1):
        wp1 = path[i]
        wp2 = path[i + 1]

        # Calculate distance between waypoints
        lat1, lon1 = wp1[1], wp1[0]
        lat2, lon2 = wp2[1], wp2[0]

        dlat = lat2 - lat1
        dlon = lon2 - lon1
        distance = math.sqrt(
            (dlat * 111320.0) ** 2 +
            (dlon * 111320.0 * math.cos(math.radians(lat1))) ** 2
        )

        # Calculate number of steps
        travel_time = distance / speed_mps
        num_steps = max(1, int(travel_time / time_step))

        # Generate interpolated positions
        for step in range(num_steps):
            t = step / num_steps
            lon = wp1[0] + t * (wp2[0] - wp1[0])
            lat = wp1[1] + t * (wp2[1] - wp1[1])
            alt = wp1[2] + t * (wp2[2] - wp1[2])

            # Calculate velocity
            vx = (wp2[0] - wp1[0]) * 111320.0 * math.cos(math.radians(lat1)) / travel_time
            vy = (wp2[1] - wp1[1]) * 111320.0 / travel_time
            vz = (wp2[2] - wp1[2]) / travel_time

            # Battery decreases over time (simple linear model)
            battery = max(0.1, 1.0 - (current_time / 3600.0))

            timesteps.append({
                "time": round(current_time, 1),
                "drone_id": drone_id,
                "lat": lat,
                "lon": lon,
                "alt_agl": alt,
                "velocity": [vx, vy, vz],
                "battery": battery,
                "operational_state": "active"
            })

            current_time += time_step

    return timesteps, current_time - start_time


def generate_benz_stadium_demo():
    """Generate Mercedes-Benz Stadium demo scenario."""
    # Mercedes-Benz Stadium coordinates
    origin_lat = 33.755489
    origin_lon = -84.401993

    # Generate 3 drone patrol paths
    drone_configs = [
        {
            "id": "PATROL_001",
            "radius": 500,  # meters
            "altitude": 60,
            "speed": 12.0
        },
        {
            "id": "PATROL_002",
            "radius": 700,
            "altitude": 80,
            "speed": 14.0
        },
        {
            "id": "PATROL_003",
            "radius": 400,
            "altitude": 50,
            "speed": 10.0
        }
    ]

    # Generate corridors and trajectories
    corridors = []
    all_timesteps = []

    for config in drone_configs:
        path = generate_patrol_path(
            origin_lat,
            origin_lon,
            config["radius"],
            config["altitude"],
            num_points=24
        )

        # Create corridor
        corridor = generate_corridor(
            corridor_id=f"corridor_{config['id']}",
            centerline=path,
            corridor_type="specific"
        )
        corridors.append(corridor)

        # Generate trajectory
        trajectory, _ = generate_drone_trajectory(
            config["id"],
            path,
            config["speed"],
            start_time=0.0
        )
        all_timesteps.extend(trajectory)

    # Group by timestep
    timestep_dict = {}
    for step in all_timesteps:
        time = step["time"]
        if time not in timestep_dict:
            timestep_dict[time] = {"time": time, "uavs": {}}

        drone_id = step["drone_id"]
        timestep_dict[time]["uavs"][drone_id] = {
            "position": [0, 0, step["alt_agl"]],  # Local ENU not used, using lat/lon
            "lat": step["lat"],
            "lon": step["lon"],
            "velocity": step["velocity"],
            "battery": step["battery"],
            "operational_state": step["operational_state"]
        }

    # Create final data structure
    simulation_data = {
        "metadata": {
            "region": "Mercedes-Benz Stadium",
            "spatial_bounds": {
                "x": [-1000, 1000],
                "y": [-1000, 1000],
                "z": [0, 150]
            },
            "uav_count": len(drone_configs),
            "timesteps": len(timestep_dict)
        },
        "corridors": corridors,
        "uav_ids": [config["id"] for config in drone_configs],
        "timesteps": sorted(timestep_dict.values(), key=lambda x: x["time"])
    }

    return simulation_data


if __name__ == "__main__":
    # Generate demo data
    print("Generating Mercedes-Benz Stadium demo scenario...")
    demo_data = generate_benz_stadium_demo()

    # Save to file
    output_dir = Path(__file__).parent.parent.parent / "data" / "simulation_exports"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "benz_perimeter_patrol.json"
    with open(output_file, 'w') as f:
        json.dump(demo_data, f, indent=2)

    print(f"Demo scenario saved to: {output_file}")
    print(f"Duration: {demo_data['timesteps'][-1]['time']:.1f}s")
    print(f"Drones: {demo_data['metadata']['uav_count']}")
    print(f"Timesteps: {demo_data['metadata']['timesteps']}")
