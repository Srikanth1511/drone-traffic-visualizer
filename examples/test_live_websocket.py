#!/usr/bin/env python3
"""
WebSocket test script for live telemetry integration.

This script simulates a drone sending real-time telemetry data via WebSocket
for lower latency bidirectional communication.

Usage:
    pip install websockets
    python3 examples/test_live_websocket.py
"""

import asyncio
import websockets
import json
import math
import random
import time

WS_URL = 'ws://localhost:8000/ws/telemetry/live'
DRONE_ID = 'websocket_drone_001'

# Starting position (Atlanta, GA)
START_LAT = 33.7736
START_LON = -84.4022
START_ALT_AGL = 50.0  # meters

async def send_live_telemetry():
    """Connect to WebSocket and send live telemetry."""
    print("=" * 60)
    print("WebSocket Live Telemetry Test")
    print("=" * 60)
    print(f"WebSocket URL: {WS_URL}")
    print(f"Drone ID: {DRONE_ID}")
    print()
    print("Instructions:")
    print("1. Ensure backend server is running")
    print("2. Open http://localhost:3000 in browser")
    print("3. Click 'Live' button to switch to live mode")
    print("4. Watch the drone move in a figure-8 pattern")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✓ WebSocket connected")

            # Register drone
            print("Registering drone...")
            await websocket.send(json.dumps({
                'type': 'register',
                'drone_id': DRONE_ID,
                'metadata': {
                    'type': 'websocket_test',
                    'description': 'WebSocket test drone',
                    'pattern': 'figure-8'
                }
            }))

            # Wait for registration response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"✓ Registration response: {response_data}")
            print()
            print("Starting telemetry stream (10 Hz)...")
            print()

            # Start telemetry loop
            start_time = time.time()
            time_elapsed = 0.0

            while True:
                time_elapsed = time.time() - start_time

                # Simulate figure-8 flight pattern
                t = time_elapsed / 15.0  # Complete figure-8 every 15 seconds
                angle = 2 * math.pi * t

                # Figure-8 parametric equations
                radius = 0.002  # ~222 meters
                lat = START_LAT + radius * math.sin(angle)
                lon = START_LON + radius * math.sin(2 * angle) / 2

                # Calculate heading based on velocity direction
                dlat = radius * math.cos(angle) * 2 * math.pi / 15.0
                dlon = radius * math.cos(2 * angle) * 2 * math.pi / 15.0
                heading = (math.degrees(math.atan2(dlon, dlat)) + 360) % 360

                # Calculate speed
                speed = math.sqrt(dlat**2 + dlon**2) * 111000  # Convert to m/s

                # Simulate altitude variation
                alt_agl = START_ALT_AGL + 10 * math.sin(angle * 3)

                # Simulate battery drain
                battery = max(0.0, 1.0 - (time_elapsed / 3600.0))

                # Create telemetry message
                telemetry = {
                    'type': 'update',
                    'data': {
                        'id': DRONE_ID,
                        'lat': lat,
                        'lon': lon,
                        'alt_msl': 300.0 + alt_agl,
                        'alt_agl': alt_agl,
                        'heading': heading,
                        'speed': speed,
                        'health': 'OK' if battery > 0.2 else 'WARNING',
                        'link_quality': 0.85 + 0.15 * random.random(),
                        'vertical_speed': 10 * math.cos(angle * 3) * 3 / 15.0,
                        'payload': {
                            'battery': battery,
                            'cameraStreams': [],
                            'gimbalYaw': heading,
                            'gimbalPitch': -30.0
                        }
                    }
                }

                # Send telemetry
                await websocket.send(json.dumps(telemetry))

                # Print status
                if int(time_elapsed * 10) % 10 == 0:  # Print every second
                    print(f"[{time_elapsed:6.1f}s] Position: ({lat:.6f}, {lon:.6f}) "
                          f"Alt: {alt_agl:.1f}m Heading: {heading:.0f}° "
                          f"Speed: {speed:.1f}m/s Battery: {battery*100:.0f}%")

                # Check for incoming messages (non-blocking)
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=0.01)
                    incoming = json.loads(message)
                    if incoming.get('type') != 'telemetry_update':
                        print(f"Received: {incoming.get('type')}")
                except asyncio.TimeoutError:
                    pass

                # 10 Hz update rate
                await asyncio.sleep(0.1)

    except websockets.exceptions.ConnectionClosed:
        print("\n✗ WebSocket connection closed")
    except KeyboardInterrupt:
        print("\n\nStopping telemetry stream...")
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        print("\nTest completed.")

if __name__ == '__main__':
    asyncio.run(send_live_telemetry())
