"""
Coordinate conversion utilities.

Converts between local ENU (East-North-Up) coordinates and geodetic (lat/lon).
Based on the drone-traffic-simulator coordinate system.
"""

import math
from typing import Tuple


# Earth radius in meters (WGS84 equatorial radius)
EARTH_RADIUS = 6378137.0


def enu_to_latlon(
    x: float,
    y: float,
    origin_lat: float,
    origin_lon: float
) -> Tuple[float, float]:
    """
    Convert local ENU coordinates to latitude/longitude.

    Args:
        x: East offset in meters
        y: North offset in meters
        origin_lat: Origin latitude in degrees
        origin_lon: Origin longitude in degrees

    Returns:
        Tuple of (latitude, longitude) in degrees
    """
    # Convert origin to radians
    origin_lat_rad = math.radians(origin_lat)

    # Meters per degree at this latitude
    # 1 degree of latitude ≈ 111,320 meters (constant)
    # 1 degree of longitude varies by latitude
    meters_per_deg_lat = 111320.0
    meters_per_deg_lon = 111320.0 * math.cos(origin_lat_rad)

    # Convert offsets to degrees
    lat = origin_lat + (y / meters_per_deg_lat)
    lon = origin_lon + (x / meters_per_deg_lon)

    return lat, lon


def latlon_to_enu(
    lat: float,
    lon: float,
    origin_lat: float,
    origin_lon: float
) -> Tuple[float, float]:
    """
    Convert latitude/longitude to local ENU coordinates.

    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        origin_lat: Origin latitude in degrees
        origin_lon: Origin longitude in degrees

    Returns:
        Tuple of (x, y) in meters (East, North)
    """
    # Convert to radians
    origin_lat_rad = math.radians(origin_lat)

    # Meters per degree
    meters_per_deg_lat = 111320.0
    meters_per_deg_lon = 111320.0 * math.cos(origin_lat_rad)

    # Convert to ENU offsets
    x = (lon - origin_lon) * meters_per_deg_lon
    y = (lat - origin_lat) * meters_per_deg_lat

    return x, y


def calculate_heading(
    from_lat: float,
    from_lon: float,
    to_lat: float,
    to_lon: float
) -> float:
    """
    Calculate heading between two points.

    Args:
        from_lat: Starting latitude
        from_lon: Starting longitude
        to_lat: Ending latitude
        to_lon: Ending longitude

    Returns:
        Heading in degrees (0-360, 0=north, clockwise)
    """
    # Convert to radians
    lat1 = math.radians(from_lat)
    lat2 = math.radians(to_lat)
    dlon = math.radians(to_lon - from_lon)

    # Calculate bearing
    x = math.sin(dlon) * math.cos(lat2)
    y = (math.cos(lat1) * math.sin(lat2) -
         math.sin(lat1) * math.cos(lat2) * math.cos(dlon))

    bearing = math.atan2(x, y)

    # Convert to degrees and normalize to 0-360
    heading = (math.degrees(bearing) + 360) % 360

    return heading


def calculate_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculate great-circle distance between two points using Haversine formula.

    Args:
        lat1: First point latitude
        lon1: First point longitude
        lat2: Second point latitude
        lon2: Second point longitude

    Returns:
        Distance in meters
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    # Haversine formula
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = EARTH_RADIUS * c

    return distance
