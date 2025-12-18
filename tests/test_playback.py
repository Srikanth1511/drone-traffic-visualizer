"""
Unit tests for playback adapter.

Tests the PlaybackAdapter's ability to load and replay simulation data.
"""

import unittest
from pathlib import Path
import json
import tempfile

from src.adapters.playback import PlaybackAdapter
from src.models import DroneHealth


class TestPlaybackAdapter(unittest.TestCase):
    """Test cases for PlaybackAdapter."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary simulation file
        self.temp_dir = tempfile.mkdtemp()
        self.sim_file = Path(self.temp_dir) / "test_sim.json"

        # Create test simulation data
        test_data = {
            "metadata": {
                "region": "Test",
                "uav_count": 2,
                "timesteps": 3
            },
            "corridors": [
                {
                    "id": "corridor_001",
                    "centerline": [[0, 0, 50], [100, 0, 50], [100, 100, 50]],
                    "width": 30.0,
                    "altitude_range": [40, 60],
                    "capacity": 4,
                    "type": "specific",
                    "risk_score": 0.1,
                    "rf_quality": 0.95,
                    "connections": []
                }
            ],
            "uav_ids": ["drone_001", "drone_002"],
            "timesteps": [
                {
                    "time": 0.0,
                    "uavs": {
                        "drone_001": {
                            "position": [0, 0, 50],
                            "velocity": [10, 0, 0],
                            "battery": 1.0,
                            "operational_state": "active"
                        },
                        "drone_002": {
                            "position": [50, 50, 60],
                            "velocity": [0, 10, 0],
                            "battery": 0.95,
                            "operational_state": "active"
                        }
                    }
                },
                {
                    "time": 1.0,
                    "uavs": {
                        "drone_001": {
                            "position": [10, 0, 50],
                            "velocity": [10, 0, 0],
                            "battery": 0.99,
                            "operational_state": "active"
                        },
                        "drone_002": {
                            "position": [50, 60, 60],
                            "velocity": [0, 10, 0],
                            "battery": 0.94,
                            "operational_state": "active"
                        }
                    }
                },
                {
                    "time": 2.0,
                    "uavs": {
                        "drone_001": {
                            "position": [20, 0, 50],
                            "velocity": [10, 0, 0],
                            "battery": 0.98,
                            "operational_state": "active"
                        },
                        "drone_002": {
                            "position": [50, 70, 60],
                            "velocity": [0, 10, 0],
                            "battery": 0.93,
                            "operational_state": "active"
                        }
                    }
                }
            ]
        }

        with open(self.sim_file, 'w') as f:
            json.dump(test_data, f)

        self.origin_lat = 33.755489
        self.origin_lon = -84.401993

    def test_load_simulation_file(self):
        """Test loading simulation file."""
        adapter = PlaybackAdapter(
            self.sim_file,
            self.origin_lat,
            self.origin_lon
        )

        self.assertIsNotNone(adapter.data)
        self.assertEqual(len(adapter.get_corridors()), 1)

    def test_get_duration(self):
        """Test getting simulation duration."""
        adapter = PlaybackAdapter(
            self.sim_file,
            self.origin_lat,
            self.origin_lon
        )

        duration = adapter.get_duration()
        self.assertEqual(duration, 2.0)

    def test_monotonic_timestamps(self):
        """Test that playback produces monotonically increasing timestamps."""
        adapter = PlaybackAdapter(
            self.sim_file,
            self.origin_lat,
            self.origin_lon
        )

        prev_time = -1
        for frame in adapter.iter_frames():
            self.assertGreater(frame.time, prev_time)
            prev_time = frame.time

    def test_frame_at_time(self):
        """Test getting frame at specific time."""
        adapter = PlaybackAdapter(
            self.sim_file,
            self.origin_lat,
            self.origin_lon
        )

        frame = adapter.get_frame_at_time(1.0)
        self.assertIsNotNone(frame)
        self.assertEqual(len(frame.drones), 2)
        self.assertAlmostEqual(frame.time, 1.0, places=1)

    def test_drone_count(self):
        """Test that expected number of drones are spawned."""
        adapter = PlaybackAdapter(
            self.sim_file,
            self.origin_lat,
            self.origin_lon
        )

        frame = adapter.get_frame_at_time(0.0)
        self.assertEqual(len(frame.drones), 2)

    def test_drone_health_status(self):
        """Test drone health status parsing."""
        adapter = PlaybackAdapter(
            self.sim_file,
            self.origin_lat,
            self.origin_lon
        )

        frame = adapter.get_frame_at_time(0.0)
        for drone in frame.drones:
            self.assertIn(drone.health, [
                DroneHealth.OK,
                DroneHealth.WARNING,
                DroneHealth.ERROR,
                DroneHealth.OFFLINE
            ])

    def test_deterministic_playback(self):
        """Test that same file produces identical positions."""
        adapter1 = PlaybackAdapter(
            self.sim_file,
            self.origin_lat,
            self.origin_lon
        )
        adapter2 = PlaybackAdapter(
            self.sim_file,
            self.origin_lat,
            self.origin_lon
        )

        frames1 = list(adapter1.iter_frames())
        frames2 = list(adapter2.iter_frames())

        self.assertEqual(len(frames1), len(frames2))

        for f1, f2 in zip(frames1, frames2):
            self.assertEqual(f1.time, f2.time)
            self.assertEqual(len(f1.drones), len(f2.drones))

            for d1, d2 in zip(f1.drones, f2.drones):
                self.assertEqual(d1.id, d2.id)
                self.assertAlmostEqual(d1.lat, d2.lat, places=6)
                self.assertAlmostEqual(d1.lon, d2.lon, places=6)


if __name__ == '__main__':
    unittest.main()
