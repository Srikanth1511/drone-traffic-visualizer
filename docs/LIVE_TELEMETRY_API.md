# Live Telemetry API Documentation

This document describes the real-time telemetry API for streaming drone data to the visualization system.

## Overview

The Live Telemetry API allows external sources (DJI drones, MAVLink adapters, custom telemetry systems, etc.) to send real-time drone telemetry data to the visualization system via HTTP or WebSocket.

## Base URL

```
http://localhost:8000
```

For WebSocket connections:
```
ws://localhost:8000
```

---

## HTTP Endpoints

### 1. Register Drone

Register a new drone for tracking.

**Endpoint:** `POST /api/drones/register`

**Request Body:**
```json
{
  "drone_id": "dji_mini3_001",
  "metadata": {
    "type": "dji",
    "model": "Mini 3",
    "operator": "John Doe"
  }
}
```

**Response:**
```json
{
  "drone_id": "dji_mini3_001",
  "registered_at": "2025-01-15T10:30:00.000Z",
  "status": "registered"
}
```

---

### 2. Update Telemetry (HTTP)

Send telemetry update via HTTP POST (alternative to WebSocket).

**Endpoint:** `POST /api/telemetry/live/update`

**Request Body:**
```json
{
  "id": "dji_mini3_001",
  "lat": 33.7736,
  "lon": -84.4022,
  "alt_msl": 350.0,
  "alt_agl": 50.0,
  "heading": 180.0,
  "speed": 5.5,
  "health": "OK",
  "link_quality": 0.95,
  "vertical_speed": 0.0,
  "payload": {
    "battery": 0.85,
    "cameraStreams": ["rtsp://example.com/stream"],
    "gimbalYaw": 0.0,
    "gimbalPitch": -45.0
  }
}
```

**Response:**
```json
{
  "id": "dji_mini3_001",
  "lat": 33.7736,
  "lon": -84.4022,
  "alt_msl": 350.0,
  "alt_agl": 50.0,
  "heading": 180.0,
  "speed": 5.5,
  "health": "OK",
  "linkQuality": 0.95,
  "verticalSpeed": 0.0,
  "payload": {
    "battery": 0.85,
    "cameraStreams": ["rtsp://example.com/stream"],
    "gimbalYaw": 0.0,
    "gimbalPitch": -45.0,
    "thermalEnabled": false
  }
}
```

---

### 3. Get Current Live Telemetry

Retrieve the current state of all active drones.

**Endpoint:** `GET /api/telemetry/live/current`

**Response:**
```json
{
  "time": 123.45,
  "drones": [
    {
      "id": "dji_mini3_001",
      "lat": 33.7736,
      "lon": -84.4022,
      "alt_msl": 350.0,
      "alt_agl": 50.0,
      "heading": 180.0,
      "speed": 5.5,
      "health": "OK",
      "linkQuality": 0.95,
      "verticalSpeed": 0.0,
      "payload": {
        "battery": 0.85,
        "cameraStreams": [],
        "gimbalYaw": 0.0,
        "gimbalPitch": 0.0,
        "thermalEnabled": false
      }
    }
  ]
}
```

---

### 4. Unregister Drone

Remove a drone from tracking.

**Endpoint:** `DELETE /api/drones/{drone_id}`

**Response:**
```json
{
  "success": true,
  "drone_id": "dji_mini3_001"
}
```

---

## WebSocket Endpoint

### Real-Time Telemetry Streaming

Connect to the WebSocket endpoint for bidirectional real-time telemetry.

**Endpoint:** `ws://localhost:8000/ws/telemetry/live`

#### Client → Server Messages

**1. Register Drone:**
```json
{
  "type": "register",
  "drone_id": "dji_mini3_001",
  "metadata": {
    "type": "dji",
    "model": "Samsung Galaxy S23"
  }
}
```

**2. Update Telemetry:**
```json
{
  "type": "update",
  "data": {
    "id": "dji_mini3_001",
    "lat": 33.7736,
    "lon": -84.4022,
    "alt_msl": 350.0,
    "alt_agl": 50.0,
    "heading": 180.0,
    "speed": 5.5,
    "health": "OK",
    "link_quality": 0.95,
    "vertical_speed": 0.0,
    "payload": {
      "battery": 0.85,
      "cameraStreams": []
    }
  }
}
```

**3. Ping (Keep-Alive):**
```json
{
  "type": "ping"
}
```

#### Server → Client Messages

**1. Registration Response:**
```json
{
  "type": "register_response",
  "data": {
    "drone_id": "dji_mini3_001",
    "registered_at": "2025-01-15T10:30:00.000Z",
    "status": "registered"
  }
}
```

**2. Telemetry Update (Broadcast):**
```json
{
  "type": "telemetry_update",
  "data": {
    "time": 123.45,
    "drones": [
      {
        "id": "dji_mini3_001",
        "lat": 33.7736,
        "lon": -84.4022,
        "alt_msl": 350.0,
        "alt_agl": 50.0,
        "heading": 180.0,
        "speed": 5.5,
        "health": "OK",
        "linkQuality": 0.95,
        "verticalSpeed": 0.0,
        "payload": {
          "battery": 0.85,
          "cameraStreams": [],
          "gimbalYaw": 0.0,
          "gimbalPitch": 0.0,
          "thermalEnabled": false
        }
      }
    ]
  }
}
```

**3. Pong Response:**
```json
{
  "type": "pong"
}
```

---

## Data Schema

### DroneState

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique drone identifier |
| `lat` | number | Yes | Latitude in degrees (-90 to 90) |
| `lon` | number | Yes | Longitude in degrees (-180 to 180) |
| `alt_msl` | number | Yes | Altitude MSL in meters |
| `alt_agl` | number | Yes | Altitude AGL in meters |
| `heading` | number | Yes | Heading in degrees (0-360, 0=North) |
| `speed` | number | Yes | Ground speed in m/s |
| `health` | string | No | Health status: "OK", "WARNING", "ERROR", "OFFLINE" |
| `link_quality` | number | No | Link quality 0.0-1.0 (default: 1.0) |
| `vertical_speed` | number | No | Vertical speed in m/s (default: 0.0) |
| `corridor_id` | string | No | Current corridor ID (optional) |
| `route_index` | number | No | Current route index (optional) |
| `payload` | object | No | Camera payload data (see below) |

### CameraPayload

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `battery` | number | No | Battery level 0.0-1.0 (default: 1.0) |
| `cameraStreams` | array | No | Array of camera stream URLs |
| `gimbalYaw` | number | No | Gimbal yaw in degrees (default: 0.0) |
| `gimbalPitch` | number | No | Gimbal pitch in degrees (default: 0.0) |
| `thermalEnabled` | boolean | No | Thermal camera enabled (default: false) |

---

## Example Usage

### JavaScript/TypeScript (WebSocket)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/telemetry/live')

ws.onopen = () => {
  // Register drone
  ws.send(JSON.stringify({
    type: 'register',
    drone_id: 'dji_mini3_001',
    metadata: { type: 'dji' }
  }))

  // Start sending telemetry
  setInterval(() => {
    ws.send(JSON.stringify({
      type: 'update',
      data: {
        id: 'dji_mini3_001',
        lat: 33.7736,
        lon: -84.4022,
        alt_msl: 350.0,
        alt_agl: 50.0,
        heading: 180.0,
        speed: 5.5,
        health: 'OK',
        link_quality: 0.95,
        payload: { battery: 0.85 }
      }
    }))
  }, 1000) // Send every second
}

ws.onmessage = (event) => {
  const message = JSON.parse(event.data)
  console.log('Received:', message)
}
```

### Python (HTTP)

```python
import requests
import time

BASE_URL = 'http://localhost:8000'

# Register drone
response = requests.post(f'{BASE_URL}/api/drones/register', json={
    'drone_id': 'python_drone_001',
    'metadata': {'type': 'mavlink', 'vehicle': 'quadcopter'}
})
print(response.json())

# Send telemetry updates
while True:
    telemetry = {
        'id': 'python_drone_001',
        'lat': 33.7736,
        'lon': -84.4022,
        'alt_msl': 350.0,
        'alt_agl': 50.0,
        'heading': 180.0,
        'speed': 5.5,
        'health': 'OK',
        'link_quality': 0.95,
        'payload': {'battery': 0.85}
    }

    response = requests.post(f'{BASE_URL}/api/telemetry/live/update', json=telemetry)
    print(response.json())

    time.sleep(1)  # Send every second
```

### Python (WebSocket)

```python
import asyncio
import websockets
import json

async def send_telemetry():
    uri = "ws://localhost:8000/ws/telemetry/live"

    async with websockets.connect(uri) as websocket:
        # Register
        await websocket.send(json.dumps({
            'type': 'register',
            'drone_id': 'python_drone_001',
            'metadata': {'type': 'mavlink'}
        }))

        # Listen for response
        response = await websocket.recv()
        print(f"Registered: {response}")

        # Send telemetry loop
        while True:
            telemetry = {
                'type': 'update',
                'data': {
                    'id': 'python_drone_001',
                    'lat': 33.7736,
                    'lon': -84.4022,
                    'alt_msl': 350.0,
                    'alt_agl': 50.0,
                    'heading': 180.0,
                    'speed': 5.5,
                    'health': 'OK',
                    'link_quality': 0.95
                }
            }

            await websocket.send(json.dumps(telemetry))
            await asyncio.sleep(1)

asyncio.run(send_telemetry())
```

---

## Frontend Integration

### Switching to Live Mode

In the web UI:
1. Click the **"Live"** button in the header to switch from Playback mode to Live mode
2. The system will automatically connect to the WebSocket endpoint
3. A green indicator **"● Live"** shows when connected
4. The footer displays the count of active drones
5. Drones will appear on the map as soon as telemetry is received

### Disconnecting

Click the **"Disconnect"** button to close the WebSocket connection and stop receiving live telemetry.

---

## Notes

- **Timeout:** Drones are automatically marked as OFFLINE if they don't send data for 30 seconds
- **Broadcast:** When any drone sends telemetry, all connected WebSocket clients receive the update
- **HTTP vs WebSocket:** Use HTTP for simple integration; use WebSocket for lower latency and bidirectional communication
- **CORS:** The API allows all origins by default (configure in production)
- **Authentication:** Not implemented in this MVP (add in production)

---

## Troubleshooting

### WebSocket Connection Failed

- Check that the backend server is running on port 8000
- Verify the WebSocket URL matches your deployment (ws:// for HTTP, wss:// for HTTPS)
- Check browser console for CORS or network errors

### Drones Not Appearing

- Ensure telemetry data includes valid lat/lon coordinates
- Verify `alt_agl` is provided (required for Google 3D Tiles mode)
- Check that the drone health is not "OFFLINE"
- Confirm the drone is within the camera view

### Telemetry Updates Not Received

- Check that the WebSocket connection is active (green indicator)
- Verify telemetry data format matches the schema
- Check server logs for errors
- Ensure messages are sent with `type: "update"`

---

## Future Enhancements

- Video streaming via WebRTC
- Audio streaming integration
- Multi-site deployment with geographic routing
- Authentication and authorization
- Rate limiting and throttling
- Historical playback of live sessions
- Telemetry recording and export
