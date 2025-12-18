"""Scenario helpers for loading venue presets."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class DronePath:
    id: str
    path: List[List[float]]
    speed: float
    payload: dict | None = None


@dataclass
class Scenario:
    name: str
    originLat: float
    originLon: float
    bounds: dict
    drones: List[DronePath]
    facilityMapCache: str | None = None
    timeline: dict | None = None


def load_scenario(path: str | Path) -> Scenario:
    with open(path, "r", encoding="utf-8") as fp:
        payload = json.load(fp)

    drones = [
        DronePath(
            id=drone.get("id"),
            path=drone.get("path", []),
            speed=float(drone.get("speed", 0.0)),
            payload=drone.get("payload"),
        )
        for drone in payload.get("drones", [])
    ]
    return Scenario(
        name=payload.get("name", Path(path).stem),
        originLat=float(payload["originLat"]),
        originLon=float(payload["originLon"]),
        bounds=payload.get("bounds", {}),
        drones=drones,
        facilityMapCache=payload.get("facilityMapCache"),
        timeline=payload.get("timeline"),
    )
