"""Geospatial helpers for ENU to geodetic conversion."""
from __future__ import annotations
import math


def enu_to_geodetic(x: float, y: float, origin_lat: float, origin_lon: float) -> tuple[float, float]:
    """Convert local ENU meters to latitude and longitude using a simple approximation."""
    meters_per_degree_lat = 111_320.0
    lat = origin_lat + (y / meters_per_degree_lat)
    lon = origin_lon + (x / (meters_per_degree_lat * math.cos(math.radians(origin_lat))))
    return lat, lon
