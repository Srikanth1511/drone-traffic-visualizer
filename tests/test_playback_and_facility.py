from pathlib import Path

from src.adapters.playback import load_playback, snapshot_stream_to_list
from src.scenarios.loader import load_scenario
from src.services.altitude_service import AltitudeService


def test_playback_monotonic_and_deterministic():
    altitude = AltitudeService("data/facility_maps/benz_grid.json")
    snapshots_first = snapshot_stream_to_list(load_playback("tests/data/test_simulation.json", altitude))
    snapshots_second = snapshot_stream_to_list(load_playback("tests/data/test_simulation.json", altitude))

    # Monotonic timestamps
    times = [s.time for s in snapshots_first]
    assert times == sorted(times)

    # Deterministic positions
    first_positions = [(round(s.drones[0].lat, 7), round(s.drones[0].lon, 7)) for s in snapshots_first]
    second_positions = [(round(s.drones[0].lat, 7), round(s.drones[0].lon, 7)) for s in snapshots_second]
    assert first_positions == second_positions


def test_facility_map_ceiling_lookup():
    altitude = AltitudeService("data/facility_maps/benz_grid.json")
    ceiling = altitude.facility_ceiling(33.7555, -84.4019)
    assert ceiling is not None
    assert ceiling > 0


def test_scenario_loader_counts():
    benz = load_scenario(Path("scenarios/mercedes_benz.json"))
    gt = load_scenario(Path("scenarios/georgia_tech.json"))
    assert len(benz.drones) == 2
    assert len(gt.drones) == 2
