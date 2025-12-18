"""
Unit tests for altitude service.

Tests MSL/AGL conversions and facility map ceiling queries.
"""

import unittest
import json
import tempfile
from pathlib import Path

from src.services.altitude_service import AltitudeService


class TestAltitudeService(unittest.TestCase):
    """Test cases for AltitudeService."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary facility map file
        self.temp_dir = tempfile.mkdtemp()
        self.facility_map_file = Path(self.temp_dir) / "test_facility_map.json"

        test_facility_data = {
            "cells": [
                {
                    "latMin": 33.750,
                    "latMax": 33.760,
                    "lonMin": -84.410,
                    "lonMax": -84.395,
                    "maxAltitudeAgl": 121.92
                },
                {
                    "latMin": 33.760,
                    "latMax": 33.770,
                    "lonMin": -84.410,
                    "lonMax": -84.395,
                    "maxAltitudeAgl": 60.96
                }
            ]
        }

        with open(self.facility_map_file, 'w') as f:
            json.dump(test_facility_data, f)

    def test_facility_map_loading(self):
        """Test loading facility map from file."""
        service = AltitudeService(facility_map_file=self.facility_map_file)
        self.assertEqual(len(service.facility_map_cells), 2)

    def test_facility_map_ceiling_query(self):
        """Test querying facility map ceiling at known point."""
        service = AltitudeService(facility_map_file=self.facility_map_file)

        # Point inside first cell
        ceiling = service.get_facility_ceiling(33.755, -84.402)
        self.assertIsNotNone(ceiling)
        self.assertEqual(ceiling, 121.92)

    def test_default_ceiling_outside_cells(self):
        """Test default ceiling when point is outside all cells."""
        service = AltitudeService(facility_map_file=self.facility_map_file)

        # Point outside all cells
        ceiling = service.get_facility_ceiling(40.0, -74.0)
        self.assertEqual(ceiling, 121.92)  # Default 400ft AGL

    def test_msl_to_agl_conversion(self):
        """Test MSL to AGL conversion."""
        service = AltitudeService()

        # Mercedes-Benz Stadium area (~300m MSL ground elevation)
        lat, lon = 33.755489, -84.401993
        alt_msl = 400.0

        alt_agl = service.msl_to_agl(lat, lon, alt_msl)

        # Should be positive and less than MSL
        self.assertGreater(alt_agl, 0)
        self.assertLess(alt_agl, alt_msl)

    def test_agl_to_msl_conversion(self):
        """Test AGL to MSL conversion."""
        service = AltitudeService()

        lat, lon = 33.755489, -84.401993
        alt_agl = 100.0

        alt_msl = service.agl_to_msl(lat, lon, alt_agl)

        # Should be greater than AGL
        self.assertGreater(alt_msl, alt_agl)

    def test_altitude_violation_check(self):
        """Test altitude violation detection."""
        service = AltitudeService(facility_map_file=self.facility_map_file)

        # Point in first cell with 121.92m ceiling
        lat, lon = 33.755, -84.402

        # Test within limits
        result = service.check_altitude_violation(lat, lon, 100.0)
        self.assertFalse(result['violation'])
        self.assertGreater(result['margin'], 0)

        # Test exceeding limits
        result = service.check_altitude_violation(lat, lon, 150.0)
        self.assertTrue(result['violation'])
        self.assertLess(result['margin'], 0)

    def test_ground_elevation_caching(self):
        """Test that ground elevation queries are cached."""
        service = AltitudeService()

        lat, lon = 33.755489, -84.401993

        # First query
        elev1 = service.get_ground_elevation(lat, lon)

        # Second query (should be cached)
        elev2 = service.get_ground_elevation(lat, lon)

        self.assertEqual(elev1, elev2)
        self.assertGreater(len(service.terrain_cache), 0)

    def test_add_facility_map_cell(self):
        """Test adding facility map cell dynamically."""
        service = AltitudeService()

        initial_count = len(service.facility_map_cells)

        service.add_facility_map_cell(
            lat_min=33.0,
            lat_max=34.0,
            lon_min=-85.0,
            lon_max=-84.0,
            max_altitude_agl=100.0
        )

        self.assertEqual(len(service.facility_map_cells), initial_count + 1)


if __name__ == '__main__':
    unittest.main()
