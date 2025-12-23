#!/usr/bin/env python3
"""
Test script for live telemetry integration.

This script simulates a drone sending real-time telemetry data to the
visualization system via HTTP POST requests.

Usage:
    python3 examples/test_live_telemetry.py
"""

import requests
import time
import math
import random

BASE_URL = 'http://localhost:8000'
DRONE_ID = 'test_drone_001'

# Starting position (Atlanta, GA)
START_LAT = 33.7736
START_LON = -84.4022
START_ALT_AGL = 50.0  # meters

def register_drone():
    """Register the test drone."""
    print("Registering drone...")
    response = requests.post(f'{BASE_URL}/api/drones/register', json={
        'drone_id': DRONE_ID,
        'metadata': {
            'type': 'test',
            'description': 'Test drone for live telemetry integration',
            'operator': 'System Test'
        }
    })

    if response.status_code == 200:
        print(f"✓ Drone registered: {response.json()}")
        return True
    else:
        print(f"✗ Registration failed: {response.status_code} - {response.text}")
        return False

def send_telemetry(time_elapsed, position_offset):
    """Send telemetry update."""
    # Simulate circular flight pattern
    angle = (time_elapsed / 10.0) * 2 * math.pi  # Complete circle every 10 seconds
    radius = 0.001  # ~111 meters

    lat = START_LAT + radius * math.cos(angle)
    lon = START_LON + radius * math.sin(angle)

    # Calculate heading (direction of movement)
    heading = (math.degrees(angle) + 90) % 360

    # Simulate slight altitude variation
    alt_agl = START_ALT_AGL + 5 * math.sin(angle * 2)

    # Simulate speed variation
    speed = 5.0 + 2.0 * math.sin(angle)

    # Simulate battery drain
    battery = max(0.0, 1.0 - (time_elapsed / 3600.0))  # 1 hour flight time

    telemetry = {
        'id': DRONE_ID,
        'lat': lat,
        'lon': lon,
        'alt_msl': 300.0 + alt_agl,  # Approximate MSL altitude for Atlanta
        'alt_agl': alt_agl,
        'heading': heading,
        'speed': speed,
        'health': 'OK' if battery > 0.2 else 'WARNING',
        'link_quality': 0.90 + 0.10 * random.random(),
        'vertical_speed': 5 * math.cos(angle * 2) * 2 / 10,
        'payload': {
            'battery': battery,
            'cameraStreams': [],
            'gimbalYaw': 0.0,
            'gimbalPitch': -45.0
        }
    }

    response = requests.post(f'{BASE_URL}/api/telemetry/live/update', json=telemetry)

    if response.status_code == 200:
        data = response.json()
        print(f"[{time_elapsed:6.1f}s] Position: ({lat:.6f}, {lon:.6f}) "
              f"Alt: {alt_agl:.1f}m Heading: {heading:.0f}° "
              f"Speed: {speed:.1f}m/s Battery: {battery*100:.0f}%")
        return True
    else:
        print(f"✗ Telemetry update failed: {response.status_code}")
        return False

def check_current_telemetry():
    """Check current live telemetry state."""
    response = requests.get(f'{BASE_URL}/api/telemetry/live/current')

    if response.status_code == 200:
        data = response.json()
        print(f"\nCurrent telemetry state:")
        print(f"  Time: {data.get('time', 0):.1f}s")
        print(f"  Active drones: {len(data.get('drones', []))}")
        for drone in data.get('drones', []):
            print(f"    - {drone['id']}: {drone.get('health', 'UNKNOWN')}")
        return True
    else:
        print(f"✗ Failed to get current telemetry: {response.status_code}")
        return False

def unregister_drone():
    """Unregister the test drone."""
    print("\nUnregistering drone...")
    response = requests.delete(f'{BASE_URL}/api/drones/{DRONE_ID}')

    if response.status_code == 200:
        print(f"✓ Drone unregistered: {response.json()}")
        return True
    else:
        print(f"✗ Unregistration failed: {response.status_code}")
        return False

def main():
    """Main test loop."""
    print("=" * 60)
    print("Live Telemetry Integration Test")
    print("=" * 60)
    print(f"Backend URL: {BASE_URL}")
    print(f"Drone ID: {DRONE_ID}")
    print()
    print("Instructions:")
    print("1. Ensure backend server is running (python3 -m uvicorn src.server.app:app --reload)")
    print("2. Open http://localhost:3000 in browser")
    print("3. Click 'Live' button to switch to live mode")
    print("4. Watch the drone appear and move in a circular pattern")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    # Register drone
    if not register_drone():
        return

    print("\nStarting telemetry stream (1 Hz)...")
    print()

    time_elapsed = 0.0
    position_offset = 0

    try:
        while True:
            # Send telemetry update
            if not send_telemetry(time_elapsed, position_offset):
                break

            # Every 10 seconds, check current state
            if int(time_elapsed) % 10 == 0 and time_elapsed > 0:
                check_current_telemetry()

            time.sleep(1.0)  # 1 Hz update rate
            time_elapsed += 1.0

    except KeyboardInterrupt:
        print("\n\nStopping telemetry stream...")

    finally:
        # Clean up
        unregister_drone()
        print("\nTest completed.")

if __name__ == '__main__':
    main()
