# Live Telemetry Examples

This directory contains example scripts demonstrating how to send live telemetry data to the drone visualization system.

## Prerequisites

1. **Backend server running:**
   ```bash
   cd /path/to/drone-traffic-visualizer
   python3 -m uvicorn src.server.app:app --reload --port 8000
   ```

2. **Frontend running:**
   ```bash
   cd src/web
   npm run dev
   ```

3. **Python dependencies:**
   ```bash
   pip install requests websockets
   ```

## Examples

### 1. HTTP Telemetry Test (`test_live_telemetry.py`)

Demonstrates sending telemetry via HTTP POST requests.

**Usage:**
```bash
python3 examples/test_live_telemetry.py
```

**Features:**
- Registers drone via HTTP
- Sends telemetry at 1 Hz (once per second)
- Simulates circular flight pattern around Atlanta
- Shows battery drain simulation
- Unregisters drone on exit

**Flight Pattern:** Circular (radius ~111m, 10-second period)

---

### 2. WebSocket Telemetry Test (`test_live_websocket.py`)

Demonstrates bidirectional WebSocket communication for lower latency.

**Usage:**
```bash
python3 examples/test_live_websocket.py
```

**Features:**
- Connects via WebSocket
- Registers drone through WebSocket
- Sends telemetry at 10 Hz (10 times per second)
- Simulates figure-8 flight pattern
- Receives broadcast messages from server

**Flight Pattern:** Figure-8 (radius ~222m, 15-second period)

---

## Viewing Live Telemetry

1. Open the frontend at http://localhost:3000
2. Click the **"Live"** button in the header to switch to Live mode
3. Wait for the green **"● Live"** indicator
4. Run one of the test scripts
5. Watch the drone appear and move on the map in real-time

## Understanding the Output

### HTTP Test Output
```
[    10.0s] Position: (33.773600, -84.402200) Alt: 50.0m Heading: 90° Speed: 5.0m/s Battery: 100%
```

### WebSocket Test Output
```
[    15.0s] Position: (33.773600, -84.402200) Alt: 60.0m Heading: 135° Speed: 7.5m/s Battery: 99%
```

## Customization

### Modify Flight Pattern

Edit the position calculation in `send_telemetry()` or the WebSocket loop:

```python
# Circular pattern
angle = (time_elapsed / 10.0) * 2 * math.pi
lat = START_LAT + radius * math.cos(angle)
lon = START_LON + radius * math.sin(angle)

# Straight line
lat = START_LAT + (time_elapsed / 1000.0)
lon = START_LON
```

### Change Update Rate

```python
# HTTP: Change sleep duration
time.sleep(0.5)  # 2 Hz instead of 1 Hz

# WebSocket: Change sleep duration
await asyncio.sleep(0.05)  # 20 Hz instead of 10 Hz
```

### Add Multiple Drones

Run multiple instances with different `DRONE_ID`:

```bash
# Terminal 1
DRONE_ID=drone_001 python3 examples/test_live_telemetry.py

# Terminal 2
DRONE_ID=drone_002 python3 examples/test_live_telemetry.py
```

Or modify the script to send multiple drones from one script.

## Integration with Phone App

The phone app will use the same API endpoints demonstrated here:

- **Register:** `POST /api/drones/register`
- **Update:** `POST /api/telemetry/live/update` or WebSocket
- **Disconnect:** `DELETE /api/drones/{drone_id}`

See [../docs/LIVE_TELEMETRY_API.md](../docs/LIVE_TELEMETRY_API.md) for complete API documentation.

## Troubleshooting

### Connection Refused

**Problem:** `ConnectionRefusedError: [Errno 111] Connection refused`

**Solution:** Ensure backend server is running on port 8000:
```bash
python3 -m uvicorn src.server.app:app --reload --port 8000
```

### Drone Not Appearing

**Problem:** Drone registered but not visible on map

**Solutions:**
1. Verify you've switched to "Live" mode (green indicator)
2. Check that telemetry includes valid coordinates
3. Ensure Google 3D Tiles is enabled if using terrain
4. Verify altitude values are reasonable (alt_agl > 0)

### WebSocket Error

**Problem:** `websockets.exceptions.InvalidURI`

**Solution:** Check WebSocket URL format:
- HTTP backend → `ws://localhost:8000/ws/telemetry/live`
- HTTPS backend → `wss://localhost:8000/ws/telemetry/live`

### High CPU Usage

**Problem:** Frontend using 100% CPU in live mode

**Solutions:**
1. Reduce update rate (increase sleep duration)
2. Reduce trail buffer size in frontend
3. Disable trails layer temporarily
4. Use HTTP instead of WebSocket for testing

## Next Steps

1. **Phone App Integration:** Use these examples as reference for implementing telemetry streaming from the phone app
2. **ESP32 Integration:** Adapt HTTP example for microcontroller use
3. **MAVLink Integration:** Wrap MAVLink messages in the same telemetry format
4. **Custom Adapters:** Create adapters for other drone platforms

## References

- [Live Telemetry API Documentation](../docs/LIVE_TELEMETRY_API.md)
- [FastAPI WebSocket Documentation](https://fastapi.tiangolo.com/advanced/websockets/)
- [Python websockets Library](https://websockets.readthedocs.io/)
