"""
Altitude service for MSL to AGL conversion and terrain queries.

Converts mean sea level (MSL) altitudes to above ground level (AGL)
using terrain data and provides FAA UAS Facility Map ceiling lookups.
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from src.models import FacilityMapCell


@dataclass
class TerrainElevation:
    """Terrain elevation at a specific location."""
    lat: float
    lon: float
    elevation_msl: float  # meters


class AltitudeService:
    """
    Service for altitude conversions and airspace ceiling lookups.

    Provides MSL to AGL conversion and FAA facility map queries.
    """

    def __init__(self, facility_map_file: Optional[Path] = None):
        """
        Initialize altitude service.

        Args:
            facility_map_file: Optional path to cached facility map data
        """
        self.facility_map_cells: List[FacilityMapCell] = []
        self.terrain_cache: Dict[tuple, float] = {}

        if facility_map_file and facility_map_file.exists():
            self._load_facility_map(facility_map_file)

    def _load_facility_map(self, file_path: Path) -> None:
        """
        Load facility map from cached JSON file.

        Args:
            file_path: Path to facility map JSON
        """
        with open(file_path, 'r') as f:
            data = json.load(f)

        if 'cells' in data:
            for cell_data in data['cells']:
                cell = FacilityMapCell(
                    lat_min=cell_data['latMin'],
                    lat_max=cell_data['latMax'],
                    lon_min=cell_data['lonMin'],
                    lon_max=cell_data['lonMax'],
                    max_altitude_agl=cell_data['maxAltitudeAgl']
                )
                self.facility_map_cells.append(cell)

    def get_ground_elevation(self, lat: float, lon: float) -> float:
        """
        Get ground elevation at a specific lat/lon.

        For MVP, returns simple elevation estimate.
        Phase 2+ will integrate USGS elevation API.

        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees

        Returns:
            Ground elevation in meters MSL
        """
        # Check cache first
        cache_key = (round(lat, 6), round(lon, 6))
        if cache_key in self.terrain_cache:
            return self.terrain_cache[cache_key]

        # For MVP: Use simple elevation model
        # Mercedes-Benz Stadium is at ~300m MSL
        # Georgia Tech is at ~320m MSL
        elevation = self._estimate_elevation(lat, lon)

        # Cache result
        self.terrain_cache[cache_key] = elevation

        return elevation

    def _estimate_elevation(self, lat: float, lon: float) -> float:
        """
        Estimate ground elevation.

        Simple interpolation for Atlanta area.
        Will be replaced with terrain API in Phase 2.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Estimated elevation in meters MSL
        """
        # Mercedes-Benz Stadium: (33.755489, -84.401993) ~300m
        # Georgia Tech: (33.7736, -84.4022) ~320m
        # Atlanta elevation range: ~250-350m MSL

        # Simple linear interpolation based on latitude
        # Higher latitude (north) = higher elevation
        base_lat = 33.755489
        base_elevation = 300.0
        elevation_per_degree = 1000.0  # meters per degree latitude

        elevation = base_elevation + (lat - base_lat) * elevation_per_degree

        # Clamp to reasonable Atlanta range
        return max(250.0, min(350.0, elevation))

    def msl_to_agl(self, lat: float, lon: float, alt_msl: float) -> float:
        """
        Convert MSL altitude to AGL.

        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            alt_msl: Altitude in meters MSL

        Returns:
            Altitude in meters AGL
        """
        ground_elevation = self.get_ground_elevation(lat, lon)
        return alt_msl - ground_elevation

    def agl_to_msl(self, lat: float, lon: float, alt_agl: float) -> float:
        """
        Convert AGL altitude to MSL.

        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            alt_agl: Altitude in meters AGL

        Returns:
            Altitude in meters MSL
        """
        ground_elevation = self.get_ground_elevation(lat, lon)
        return alt_agl + ground_elevation

    def get_facility_ceiling(self, lat: float, lon: float) -> Optional[float]:
        """
        Get FAA UAS Facility Map ceiling at location.

        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees

        Returns:
            Maximum authorized altitude in meters AGL, or None if not found
        """
        for cell in self.facility_map_cells:
            if cell.contains(lat, lon):
                return cell.max_altitude_agl

        # Default: 400 feet AGL (~122m) per FAA Part 107
        return 121.92

    def check_altitude_violation(
        self,
        lat: float,
        lon: float,
        alt_agl: float
    ) -> Dict[str, Any]:
        """
        Check if altitude violates facility map ceiling.

        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            alt_agl: Current altitude in meters AGL

        Returns:
            Dictionary with violation status and details
        """
        ceiling = self.get_facility_ceiling(lat, lon)

        violation = alt_agl > ceiling if ceiling is not None else False

        return {
            "violation": violation,
            "currentAltAgl": alt_agl,
            "ceilingAgl": ceiling,
            "margin": ceiling - alt_agl if ceiling is not None else None
        }

    def get_facility_map_grid(self) -> List[Dict[str, Any]]:
        """
        Get all facility map cells for visualization.

        Returns:
            List of cell dictionaries
        """
        return [cell.to_dict() for cell in self.facility_map_cells]

    def add_facility_map_cell(
        self,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        max_altitude_agl: float
    ) -> None:
        """
        Add a facility map cell.

        Args:
            lat_min: Minimum latitude
            lat_max: Maximum latitude
            lon_min: Minimum longitude
            lon_max: Maximum longitude
            max_altitude_agl: Maximum altitude in meters AGL
        """
        cell = FacilityMapCell(
            lat_min=lat_min,
            lat_max=lat_max,
            lon_min=lon_min,
            lon_max=lon_max,
            max_altitude_agl=max_altitude_agl
        )
        self.facility_map_cells.append(cell)
