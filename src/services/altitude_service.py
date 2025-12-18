"""Altitude helpers for converting MSL to AGL and fetching facility ceilings."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional


class AltitudeService:
    def __init__(self, facility_map_path: str | None = None, default_ground_elevation: float = 0.0):
        self.default_ground_elevation = default_ground_elevation
        self._facility_grid = self._load_facility_grid(facility_map_path) if facility_map_path else []

    @staticmethod
    def _load_facility_grid(path: str | None) -> list[Dict]:
        if path is None:
            return []
        with open(path, "r", encoding="utf-8") as fp:
            return json.load(fp).get("cells", [])

    def ground_elevation(self, lat: float, lon: float) -> float:
        """Return ground elevation in meters using cached facility grid cells."""
        for cell in self._facility_grid:
            lat_range = cell.get("latRange")
            lon_range = cell.get("lonRange")
            if not lat_range or not lon_range:
                continue
            if lat_range[0] <= lat <= lat_range[1] and lon_range[0] <= lon <= lon_range[1]:
                return float(cell.get("ground", self.default_ground_elevation))
        return self.default_ground_elevation

    def msl_to_agl(self, lat: float, lon: float, alt_msl: float) -> float:
        return max(0.0, alt_msl - self.ground_elevation(lat, lon))

    def facility_ceiling(self, lat: float, lon: float) -> Optional[float]:
        for cell in self._facility_grid:
            lat_range = cell.get("latRange")
            lon_range = cell.get("lonRange")
            if not lat_range or not lon_range:
                continue
            if lat_range[0] <= lat <= lat_range[1] and lon_range[0] <= lon <= lon_range[1]:
                ceiling = cell.get("maxAltitudeAgl")
                return float(ceiling) if ceiling is not None else None
        return None
