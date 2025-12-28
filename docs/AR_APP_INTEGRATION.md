# AR App Integration Guide

**Version**: 1.0
**Date**: 2025-12-27
**Purpose**: Guide for integrating external AR apps with the drone visualization backend

---

## Overview

This document describes how to integrate an Android AR application with the drone visualization backend. The AR app is maintained in a **separate repository** but connects to the same proven backend endpoints.

**AR App Repository**: `drone-ar-viewer` (separate repo)
**Backend Repository**: This repo (`drone-traffic-visualizer`)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      DJI Drone Ecosystem                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐          ┌──────────────────┐            │
│  │  DJI Mini 3  │─────────>│ DJI Android App  │            │
│  │   (Drone)    │  OcuSync │ (Telemetry Send) │            │
│  └──────────────┘          └────────┬─────────┘            │
│                                     │                        │
│                                     │ WebSocket/HTTP         │
│                                     ↓                        │
│                          ┌──────────────────────┐           │
│                          │  FastAPI Backend     │           │
│                          │  (This Repo)         │           │
│                          │  - Live Telemetry    │           │
│                          │  - Video Streaming   │           │
│                          │  - State Management  │           │
│                          └──────────┬───────────┘           │
│                                     │                        │
│                     ┌───────────────┴───────────┐           │
│                     │                           │           │
│                     ↓                           ↓           │
│          ┌──────────────────┐        ┌──────────────────┐  │
│          │   Web UI         │        │   AR Viewer App  │  │
│          │   (CesiumJS)     │        │   (Separate Repo)│  │
│          │   Desktop/Mobile │        │   Android/Glass  │  │
│          └──────────────────┘        └──────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Insight**: The AR app is a **consumer** of backend data, just like the web UI. No backend changes needed!

---

## Backend Endpoints for AR Integration

### Base URL

**Development (Local)**:
```
http://localhost:8000
```

**Production (Cloud)**:
```
https://your-backend.render.com  (or your cloud provider)
```

---

### 1. Health Check

**Endpoint**: `GET /api/health`

**Purpose**: Verify backend is running

**Request**:
```bash
curl http://localhost:8000/api/health
```

**Response**:
```json
{
  "status": "healthy",
  "playback_loaded": false,
  "scenario_loaded": false
}
```

**Use in AR App**: Check connectivity before showing AR view

---

### 2. Get Current Drone Positions (HTTP Polling)

**Endpoint**: `GET /api/telemetry/live/current`

**Purpose**: Get current state of all active drones

**Request**:
```bash
curl http://localhost:8000/api/telemetry/live/current
```

**Response**:
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
        "gimbalPitch": -45.0,
        "thermalEnabled": false
      }
    }
  ]
}
```

**Polling Strategy** (Simple, but not ideal):
```kotlin
// Poll every 100ms (10 Hz)
val handler = Handler(Looper.getMainLooper())
val pollingRunnable = object : Runnable {
    override fun run() {
        fetchCurrentDrones() // HTTP GET request
        handler.postDelayed(this, 100)
    }
}
handler.post(pollingRunnable)
```

**⚠️ Limitation**: 100ms delay + network latency = ~200-400ms total lag

---

### 3. WebSocket Live Stream (Recommended)

**Endpoint**: `WS /api/telemetry/live`

**Purpose**: Real-time telemetry updates (10 Hz, low latency)

**Connection**:
```kotlin
import okhttp3.WebSocket
import okhttp3.WebSocketListener

val client = OkHttpClient()
val request = Request.Builder()
    .url("ws://localhost:8000/api/telemetry/live")
    .build()

val webSocket = client.newWebSocket(request, object : WebSocketListener() {
    override fun onMessage(webSocket: WebSocket, text: String) {
        val telemetryFrame = Json.decodeFromString<TelemetryFrame>(text)

        // Update AR view with new drone positions
        telemetryFrame.data.drones.forEach { drone ->
            updateDroneInAR(drone)
        }
    }

    override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
        Log.e("WebSocket", "Connection failed", t)
        // Fallback to HTTP polling
    }
})
```

**Message Format** (Received every 100ms):
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
        "payload": {
          "battery": 0.85
        }
      }
    ]
  }
}
```

**Advantages**:
- ✅ Real-time updates (100ms)
- ✅ Lower latency than polling
- ✅ Lower battery usage (no constant HTTP requests)
- ✅ Automatic reconnection support

---

### 4. Get Drone Video Frame (Optional)

**Endpoint**: `GET /api/video/{drone_id}/frame`

**Purpose**: Get latest JPEG frame from drone camera

**Request**:
```bash
curl http://localhost:8000/api/video/dji_mini3_001/frame > frame.jpg
```

**Response**: JPEG image (binary)

**Headers**:
```
Content-Type: image/jpeg
Cache-Control: no-cache
```

**Use in AR App**:
```kotlin
fun fetchDroneVideo(droneId: String): Bitmap? {
    val url = "http://localhost:8000/api/video/$droneId/frame"
    val request = Request.Builder().url(url).build()

    client.newCall(request).execute().use { response ->
        if (response.isSuccessful) {
            val bytes = response.body?.bytes()
            return BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
        }
    }
    return null
}

// Update every 100ms (10 FPS)
handler.postDelayed({
    val frame = fetchDroneVideo("dji_mini3_001")
    videoImageView.setImageBitmap(frame)
}, 100)
```

**⚠️ Note**: Video is optional. Main AR feature (drone finder) works without video.

---

### 5. MJPEG Video Stream (Alternative)

**Endpoint**: `GET /api/video/{drone_id}/stream.mjpeg`

**Purpose**: Continuous MJPEG stream (motion JPEG)

**Request**:
```bash
curl http://localhost:8000/api/video/dji_mini3_001/stream.mjpeg
```

**Response**: Multipart MJPEG stream

**Use in AR App** (using library):
```kotlin
// Add dependency: implementation 'com.github.niqdev:mjpeg-view:2.0.0'

val mjpegView = findViewById<MjpegView>(R.id.drone_video)
mjpegView.setSource("http://localhost:8000/api/video/dji_mini3_001/stream.mjpeg")
mjpegView.setMode(MjpegView.MODE_FIT_WIDTH)
mjpegView.isAdjustHeight = true
```

---

## AR-Specific Calculations

### GPS to AR Coordinates

The AR app needs to convert drone GPS position to AR scene coordinates.

**Required Inputs**:
- Drone position: `(droneLat, droneLon, droneAlt)`
- User position: `(userLat, userLon, userAlt)` - from phone GPS
- Phone orientation: `(heading, pitch, roll)` - from phone sensors

**Calculation Steps**:

#### 1. Calculate Distance (Haversine Formula)

```kotlin
import kotlin.math.*

fun calculateDistance(
    lat1: Double, lon1: Double,
    lat2: Double, lon2: Double
): Double {
    val R = 6371000.0 // Earth radius in meters

    val dLat = (lat2 - lat1) * PI / 180.0
    val dLon = (lon2 - lon1) * PI / 180.0

    val a = sin(dLat / 2).pow(2) +
            cos(lat1 * PI / 180.0) * cos(lat2 * PI / 180.0) *
            sin(dLon / 2).pow(2)

    val c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c // Distance in meters
}
```

#### 2. Calculate Bearing (Direction to Drone)

```kotlin
fun calculateBearing(
    lat1: Double, lon1: Double,
    lat2: Double, lon2: Double
): Double {
    val dLon = (lon2 - lon1) * PI / 180.0

    val y = sin(dLon) * cos(lat2 * PI / 180.0)
    val x = cos(lat1 * PI / 180.0) * sin(lat2 * PI / 180.0) -
            sin(lat1 * PI / 180.0) * cos(lat2 * PI / 180.0) * cos(dLon)

    val bearing = atan2(y, x) * 180.0 / PI

    return (bearing + 360.0) % 360.0 // Normalize to 0-360°
}
```

#### 3. Convert to AR Scene Position

```kotlin
data class ARPosition(val x: Float, val y: Float, val z: Float)

fun droneToARPosition(
    droneLat: Double, droneLon: Double, droneAlt: Double,
    userLat: Double, userLon: Double, userAlt: Double,
    phoneHeading: Float
): ARPosition {
    // 1. Calculate horizontal distance
    val horizontalDistance = calculateDistance(userLat, userLon, droneLat, droneLon)

    // 2. Calculate bearing from user to drone
    val bearing = calculateBearing(userLat, userLon, droneLat, droneLon)

    // 3. Calculate relative bearing (adjust for phone orientation)
    val relativeBearing = (bearing - phoneHeading + 360.0) % 360.0

    // 4. Calculate vertical difference
    val verticalDistance = droneAlt - userAlt

    // 5. Convert to AR coordinates
    // ARCore: X = right, Y = up, Z = forward (into screen)
    val arX = (horizontalDistance * sin(relativeBearing * PI / 180.0)).toFloat()
    val arZ = -(horizontalDistance * cos(relativeBearing * PI / 180.0)).toFloat()
    val arY = verticalDistance.toFloat()

    return ARPosition(arX, arY, arZ)
}
```

**Usage in AR App**:
```kotlin
val droneARPosition = droneToARPosition(
    droneLat = 33.7736,
    droneLon = -84.4022,
    droneAlt = 50.0,
    userLat = 33.7746,
    userLon = -84.4032,
    userAlt = 0.0,
    phoneHeading = deviceHeading
)

// Place AR object at calculated position
droneNode.worldPosition = Vector3(
    droneARPosition.x,
    droneARPosition.y,
    droneARPosition.z
)
```

---

## Data Models

### Kotlin Data Classes (for AR App)

```kotlin
import kotlinx.serialization.Serializable

@Serializable
data class TelemetryFrame(
    val time: Double,
    val drones: List<DroneState>
)

@Serializable
data class DroneState(
    val id: String,
    val lat: Double,
    val lon: Double,
    val alt_msl: Double,
    val alt_agl: Double,
    val heading: Double,
    val speed: Double,
    val health: String,
    val linkQuality: Double,
    val verticalSpeed: Double = 0.0,
    val payload: DronePayload? = null
)

@Serializable
data class DronePayload(
    val battery: Double,
    val cameraStreams: List<String> = emptyList(),
    val gimbalYaw: Double = 0.0,
    val gimbalPitch: Double = 0.0,
    val thermalEnabled: Boolean = false
)

@Serializable
data class WebSocketMessage(
    val type: String,
    val data: TelemetryFrame
)
```

---

## Connection Flow

### Startup Sequence

```
1. AR App Launches
   ↓
2. Check Backend Health
   GET /api/health
   ↓
3. Establish WebSocket Connection
   WS /api/telemetry/live
   ↓
4. Start Phone Sensors
   - GPS (user location)
   - Compass (phone heading)
   - Gyroscope (orientation)
   ↓
5. Initialize ARCore Session
   - Camera pass-through
   - Plane detection
   ↓
6. Receive Telemetry Updates
   (10 Hz via WebSocket)
   ↓
7. Calculate AR Positions
   (GPS to AR coordinates)
   ↓
8. Render AR Overlays
   - Arrow pointing to drone
   - Distance/altitude text
   - Battery indicator
   - Optional video feed
```

### Error Handling

```kotlin
class BackendConnection(private val baseUrl: String) {
    private var webSocket: WebSocket? = null
    private var isPolling = false

    fun connect(onDroneUpdate: (List<DroneState>) -> Unit) {
        // Try WebSocket first
        connectWebSocket(onDroneUpdate) { error ->
            Log.w("Backend", "WebSocket failed, falling back to polling", error)
            // Fallback to HTTP polling
            startPolling(onDroneUpdate)
        }
    }

    private fun connectWebSocket(
        onDroneUpdate: (List<DroneState>) -> Unit,
        onError: (Throwable) -> Unit
    ) {
        val request = Request.Builder()
            .url("$baseUrl/api/telemetry/live".replace("http", "ws"))
            .build()

        webSocket = OkHttpClient().newWebSocket(request, object : WebSocketListener() {
            override fun onMessage(webSocket: WebSocket, text: String) {
                val message = Json.decodeFromString<WebSocketMessage>(text)
                onDroneUpdate(message.data.drones)
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                onError(t)
            }
        })
    }

    private fun startPolling(onDroneUpdate: (List<DroneState>) -> Unit) {
        isPolling = true
        val handler = Handler(Looper.getMainLooper())

        val pollingRunnable = object : Runnable {
            override fun run() {
                if (!isPolling) return

                // HTTP GET request
                val request = Request.Builder()
                    .url("$baseUrl/api/telemetry/live/current")
                    .build()

                OkHttpClient().newCall(request).enqueue(object : Callback {
                    override fun onResponse(call: Call, response: Response) {
                        val frame = Json.decodeFromString<TelemetryFrame>(response.body!!.string())
                        onDroneUpdate(frame.drones)
                    }

                    override fun onFailure(call: Call, e: IOException) {
                        Log.e("Polling", "Failed to fetch drones", e)
                    }
                })

                handler.postDelayed(this, 100) // Poll every 100ms
            }
        }

        handler.post(pollingRunnable)
    }

    fun disconnect() {
        webSocket?.close(1000, "User closed app")
        isPolling = false
    }
}
```

---

## Backend Configuration for AR App

### CORS (Cross-Origin Resource Sharing)

The backend already has CORS enabled for web UI. No changes needed for AR app (Android native doesn't require CORS).

### Network Configuration

**Local Testing**:
- Backend: `http://192.168.1.x:8000` (your computer's local IP)
- AR App: Connect to same WiFi network

**Production**:
- Deploy backend to cloud (Render, Railway, etc.)
- Update AR app's `BASE_URL` to cloud URL

---

## Testing the Integration

### 1. Test Backend Health

```bash
# From AR app's Android device
curl http://192.168.1.100:8000/api/health
```

**Expected**:
```json
{"status":"healthy","playback_loaded":false,"scenario_loaded":false}
```

### 2. Test Telemetry Endpoint

```bash
curl http://192.168.1.100:8000/api/telemetry/live/current
```

**Expected**:
```json
{
  "time": 0.0,
  "drones": []
}
```

### 3. Send Test Telemetry

```bash
curl -X POST http://192.168.1.100:8000/api/telemetry/live/update \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test_drone",
    "lat": 33.7736,
    "lon": -84.4022,
    "alt_msl": 350.0,
    "alt_agl": 50.0,
    "heading": 180.0,
    "speed": 5.0,
    "health": "OK"
  }'
```

### 4. Verify AR App Receives Data

- AR app should show drone at calculated AR position
- Arrow should point toward GPS coordinates (33.7736, -84.4022)

---

## Performance Considerations

### Latency Budget

```
DJI Drone → Android App → Backend → AR App
  (OcuSync)    (Parse)     (Store)    (Render)
   ~50ms        ~10ms       ~5ms       ~30ms

Total Latency: ~95ms (acceptable for AR)
```

### Battery Optimization

**AR App Battery Usage**:
- ARCore: ~15% per hour
- GPS: ~5% per hour
- WebSocket: ~3% per hour
- Camera: ~20% per hour

**Total**: ~43% per hour (2.3 hours battery life)

**Optimizations**:
1. Reduce ARCore update rate (60 FPS → 30 FPS)
2. Use GPS "balanced" mode instead of "high accuracy"
3. Pause AR when app in background
4. Show low-power mode warning at 20% battery

---

## Security Considerations

### Authentication (Future)

Currently, backend has no authentication. For production:

**Recommended**: API Key authentication

```kotlin
// AR app sends API key in header
val request = Request.Builder()
    .url("$baseUrl/api/telemetry/live/current")
    .header("X-API-Key", "your-api-key-here")
    .build()
```

**Backend changes needed**:
```python
# src/server/app.py
@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    api_key = request.headers.get("X-API-Key")
    if api_key != os.getenv("API_KEY"):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return await call_next(request)
```

### HTTPS/WSS (Production)

**Development**: HTTP/WS is fine
**Production**: MUST use HTTPS/WSS

```kotlin
// Production URL
const val BACKEND_URL = "https://your-backend.render.com"
const val WEBSOCKET_URL = "wss://your-backend.render.com/api/telemetry/live"
```

---

## Troubleshooting

### Issue 1: "Connection Refused"

**Cause**: Backend not running or wrong IP address

**Solution**:
1. Check backend is running: `curl http://localhost:8000/api/health`
2. Use correct local IP (not `localhost` from Android)
3. Ensure phone and computer on same WiFi network

---

### Issue 2: AR Position Drifts

**Cause**: GPS accuracy (±5m) + compass calibration

**Solution**:
1. Calibrate phone compass (move in figure-8 pattern)
2. Use sensor fusion (GPS + IMU + visual odometry)
3. Apply Kalman filtering to smooth GPS jitter

---

### Issue 3: High Latency

**Cause**: Network congestion or backend overload

**Solution**:
1. Use WebSocket instead of HTTP polling
2. Reduce telemetry update rate (10 Hz → 5 Hz)
3. Deploy backend closer to user (regional cloud deployment)

---

### Issue 4: Battery Drains Quickly

**Cause**: ARCore + GPS + Camera = high power usage

**Solution**:
1. Reduce ARCore update rate (60 FPS → 30 FPS)
2. Pause AR when not actively viewing
3. Show battery warning at 20%
4. Implement low-power mode (disable video, reduce update rate)

---

## Next Steps

1. ✅ Backend is ready (no changes needed)
2. 📱 Set up AR app repository (see separate repo: `drone-ar-viewer`)
3. 🔌 Implement WebSocket connection in AR app
4. 📍 Add GPS and compass services
5. 🎯 Implement "Drone Finder" AR view
6. 🧪 Test with simulated drone data
7. 🚁 Test with real DJI Mini 3

---

## Resources

**Backend Repository**: This repo
**AR App Repository**: `drone-ar-viewer` (separate)
**API Reference**: `docs/LIVE_TELEMETRY_API.md`
**DJI Integration**: `docs/DJI_ANDROID_APP_README.md`

**Questions?** See `docs/FAQ.md` or open an issue.

---

**Backend Status**: ✅ Ready for AR integration (no changes required)
**Next**: Build AR app using this integration guide
