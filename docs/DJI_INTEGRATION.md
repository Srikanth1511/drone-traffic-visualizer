# DJI Mini 3 Integration Guide

Complete guide for integrating DJI Mini 3 with the live drone visualization system.

## Overview

The DJI Mini 3 can stream telemetry and video to the visualization system using:
- **DJI Mobile SDK** (iOS/Android app)
- **DJI Onboard SDK** (companion computer)
- **DJI Cloud API** (cloud-based integration)

## Quick Comparison

| Method | Best For | Complexity | Video | Telemetry | Range |
|--------|----------|------------|-------|-----------|-------|
| Mobile SDK | Simple setup, testing | Low | ✅ | ✅ | WiFi/4G |
| Onboard SDK | Autonomous missions | High | ❌ | ✅ | Direct |
| Cloud API | Remote operations | Medium | ✅ | ✅ | Global |

**Recommended: Mobile SDK** for initial testing and development.

---

## Option 1: DJI Mobile SDK (Recommended)

Build an iOS/Android app that connects to the drone via DJI Remote Controller.

### Architecture

```
DJI Mini 3 → RC → Mobile App (DJI SDK) → HTTP/WebSocket → Visualizer Backend
```

### Setup Steps

**1. Install DJI Mobile SDK**

```bash
# iOS (Swift/Objective-C)
pod 'DJI-SDK-iOS', '~> 4.16'

# Android (Java/Kotlin)
implementation 'com.dji:dji-sdk:4.16'
```

**2. Register DJI App**

- Go to [DJI Developer](https://developer.dji.com/)
- Create account and register app
- Get **App Key**
- Download SDK

**3. Minimal Integration Code**

**iOS (Swift):**
```swift
import DJISDK
import Foundation

class DJITelemetryBridge {
    let backendURL = "http://YOUR_COMPUTER_IP:8000"
    var droneID = "dji_mini3_001"

    func initialize() {
        // Register app
        DJISDKManager.registerApp(with: self)

        // Connect to drone
        DJISDKManager.startConnectionToProduct()

        // Setup telemetry listener
        if let aircraft = DJISDKManager.product() as? DJIAircraft {
            aircraft.flightController?.delegate = self
        }
    }

    func sendTelemetry(_ state: DJIFlightControllerState) {
        let telemetry: [String: Any] = [
            "id": droneID,
            "lat": state.aircraftLocation.coordinate.latitude,
            "lon": state.aircraftLocation.coordinate.longitude,
            "alt_msl": state.altitude,  // meters MSL
            "alt_agl": state.takeoffLocationAltitude,  // meters AGL
            "heading": state.attitude.yaw,
            "speed": sqrt(pow(state.velocityX, 2) + pow(state.velocityY, 2)),
            "health": state.areMotorsOn ? "OK" : "WARNING",
            "link_quality": Double(DJISDKManager.product()?.airLink?.downlinkSignalQuality ?? 0) / 100.0,
            "vertical_speed": state.velocityZ,
            "payload": [
                "battery": Double(state.batteryPercentRemaining) / 100.0
            ]
        ]

        // Send to backend
        sendToBackend(telemetry)
    }

    func sendToBackend(_ data: [String: Any]) {
        guard let url = URL(string: "\(backendURL)/api/telemetry/live/update") else { return }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: data)

        URLSession.shared.dataTask(with: request).resume()
    }
}

extension DJITelemetryBridge: DJIFlightControllerDelegate {
    func flightController(_ fc: DJIFlightController, didUpdate state: DJIFlightControllerState) {
        // Called at 10 Hz
        sendTelemetry(state)
    }
}
```

**Android (Kotlin):**
```kotlin
import dji.sdk.sdkmanager.DJISDKManager
import dji.sdk.flightcontroller.FlightController
import dji.sdk.products.Aircraft
import okhttp3.*
import org.json.JSONObject

class DJITelemetryBridge {
    private val backendURL = "http://YOUR_COMPUTER_IP:8000"
    private val droneID = "dji_mini3_001"
    private val client = OkHttpClient()

    fun initialize() {
        // Register app
        DJISDKManager.getInstance().registerApp(context, object : DJISDKManager.SDKManagerCallback {
            override fun onRegister(error: DJIError?) {
                if (error == null) {
                    DJISDKManager.getInstance().startConnectionToProduct()
                }
            }

            override fun onProductConnect(product: BaseProduct?) {
                setupTelemetryListener()
            }

            override fun onProductDisconnect() {}
            override fun onComponentChange(key: ComponentKey?, oldComponent: BaseComponent?, newComponent: BaseComponent?) {}
        })
    }

    private fun setupTelemetryListener() {
        val aircraft = DJISDKManager.getInstance().product as? Aircraft
        aircraft?.flightController?.setStateCallback { state ->
            sendTelemetry(state)
        }
    }

    private fun sendTelemetry(state: FlightControllerState) {
        val telemetry = JSONObject().apply {
            put("id", droneID)
            put("lat", state.aircraftLocation.latitude)
            put("lon", state.aircraftLocation.longitude)
            put("alt_msl", state.altitude)
            put("alt_agl", state.takeoffLocationAltitude)
            put("heading", state.attitude.yaw)
            put("speed", Math.sqrt(Math.pow(state.velocityX.toDouble(), 2.0) + Math.pow(state.velocityY.toDouble(), 2.0)))
            put("health", if (state.areMotorsOn()) "OK" else "WARNING")
            put("link_quality", state.uplinkSignalQuality / 100.0)
            put("vertical_speed", state.velocityZ)
            put("payload", JSONObject().apply {
                put("battery", state.batteryThresholdBehavior.toString())
            })
        }

        sendToBackend(telemetry.toString())
    }

    private fun sendToBackend(json: String) {
        val request = Request.Builder()
            .url("$backendURL/api/telemetry/live/update")
            .post(RequestBody.create(MediaType.parse("application/json"), json))
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onResponse(call: Call, response: Response) {}
            override fun onFailure(call: Call, e: IOException) {}
        })
    }
}
```

### Video Streaming

**Get video feed:**
```swift
// iOS
DJISDKManager.videoFeeder()?.primaryVideoFeed.add(self, with: nil)

func videoFeed(_ videoFeed: DJIVideoFeed, didUpdateVideoData rawData: Data) {
    // H.264 encoded video data
    // Forward to backend or process locally
}
```

```kotlin
// Android
DJISDKManager.getInstance().videoFeeder?.primaryVideoFeed?.addVideoDataListener { videoBuffer, size ->
    // H.264 encoded video data
    // Forward to backend or process locally
}
```

---

## Option 2: DJI Cloud API (Enterprise)

For remote/cloud-based operations without mobile app.

### Prerequisites
- DJI Cloud API account
- DJI Enterprise drone (Mini 3 may have limited support)
- MQTT broker or DJI Cloud Platform

### Integration Steps

**1. Subscribe to telemetry via MQTT**

```python
import paho.mqtt.client as mqtt
import json
import requests

BACKEND_URL = "http://localhost:8000"
DJI_CLOUD_ENDPOINT = "ssl://mqtt.djicloud.com:8883"

def on_message(client, userdata, msg):
    """Receive telemetry from DJI Cloud"""
    data = json.loads(msg.payload)

    # Convert DJI format to our schema
    telemetry = {
        "id": f"dji_{data['sn']}",
        "lat": data['latitude'],
        "lon": data['longitude'],
        "alt_msl": data['elevation'],
        "alt_agl": data['height'],
        "heading": data['attitude_head'],
        "speed": data['horizontal_speed'],
        "health": "OK" if data['in_the_sky'] else "WARNING",
        "vertical_speed": data['vertical_speed'],
        "payload": {
            "battery": data['capacity_percent'] / 100.0
        }
    }

    # Forward to visualizer
    requests.post(f"{BACKEND_URL}/api/telemetry/live/update", json=telemetry)

# Connect to DJI Cloud
client = mqtt.Client()
client.on_message = on_message
client.connect(DJI_CLOUD_ENDPOINT, 8883, 60)
client.subscribe("thing/product/{your-product-sn}/osd")
client.loop_forever()
```

---

## Option 3: MAVLink Bridge (Advanced)

If you have a companion computer (Raspberry Pi, Jetson Nano) connected to the drone.

### Hardware Setup
- DJI Mini 3
- Raspberry Pi 4
- USB-to-UART adapter

### Software

```python
from pymavlink import mavutil
import requests
import time

BACKEND_URL = "http://YOUR_COMPUTER_IP:8000"
DRONE_ID = "dji_mini3_001"

# Connect to flight controller
master = mavutil.mavlink_connection('/dev/ttyUSB0', baud=57600)

def send_telemetry():
    while True:
        msg = master.recv_match(type='GLOBAL_POSITION_INT', blocking=True)

        telemetry = {
            "id": DRONE_ID,
            "lat": msg.lat / 1e7,
            "lon": msg.lon / 1e7,
            "alt_msl": msg.alt / 1000.0,
            "alt_agl": msg.relative_alt / 1000.0,
            "heading": msg.hdg / 100.0,
            "speed": (msg.vx**2 + msg.vy**2)**0.5 / 100.0,
            "vertical_speed": msg.vz / 100.0,
            "health": "OK"
        }

        requests.post(f"{BACKEND_URL}/api/telemetry/live/update", json=telemetry)
        time.sleep(0.1)  # 10 Hz

send_telemetry()
```

---

## Testing

### 1. Start Backend
```bash
./start_backend.sh
```

### 2. Start Frontend
```bash
cd src/web
npm run dev
```

### 3. Run Mobile App
- Connect RC to drone
- Connect phone to RC
- Launch your DJI SDK app
- Watch telemetry appear in visualization

### 4. Verify
- Frontend: Click **"Live"** button
- Should see green **"● Live"** indicator
- Drone appears on map
- Trails show flight path

---

## Troubleshooting

### DJI SDK Connection Failed
- Verify app key is correct
- Check RC is powered on and connected to drone
- Ensure phone has USB debugging enabled (Android)
- Update DJI SDK to latest version

### No Telemetry Appearing
- Check backend is running with `--host 0.0.0.0`
- Verify network connectivity (phone and computer on same network)
- Check backend logs for incoming requests
- Verify drone GPS has lock (outdoor flight)

### Video Streaming Issues
- DJI video is H.264 encoded
- Requires decoding before web display
- Consider using WebRTC for real-time streaming
- Or save to file and process separately

### Rate Limiting
- DJI SDK provides telemetry at 10 Hz
- Backend can handle up to 100 Hz
- Adjust update frequency based on network bandwidth

---

## Production Deployment

### Security
```python
# Add authentication
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
requests.post(url, json=telemetry, headers=headers)
```

### Error Handling
```swift
func sendToBackend(_ data: [String: Any]) {
    // ... setup request ...

    URLSession.shared.dataTask(with: request) { data, response, error in
        if let error = error {
            print("❌ Failed to send telemetry: \(error)")
            // Retry logic here
        } else {
            print("✅ Telemetry sent successfully")
        }
    }.resume()
}
```

### Buffering for Poor Connectivity
```swift
var telemetryQueue: [[String: Any]] = []

func sendTelemetry(_ state: DJIFlightControllerState) {
    let telemetry = createTelemetryDict(state)

    if isNetworkAvailable {
        sendToBackend(telemetry)
        // Send queued data
        telemetryQueue.forEach { sendToBackend($0) }
        telemetryQueue.removeAll()
    } else {
        telemetryQueue.append(telemetry)
    }
}
```

---

## Resources

- [DJI Mobile SDK Docs](https://developer.dji.com/mobile-sdk/)
- [DJI Cloud API Docs](https://developer.dji.com/doc/cloud-api-tutorial/en/)
- [DJI Forum](https://forum.dji.com/forum-139-1.html)
- [Sample Apps](https://github.com/dji-sdk/Mobile-SDK-Android)
- [Live Telemetry API](./LIVE_TELEMETRY_API.md)

---

## Quick Start Checklist

- [ ] DJI Developer account created
- [ ] App registered and App Key obtained
- [ ] Mobile SDK installed (iOS/Android)
- [ ] Backend running with `./start_backend.sh`
- [ ] Frontend running on port 3000
- [ ] Mobile app built and installed
- [ ] Drone powered on and connected to RC
- [ ] RC connected to phone
- [ ] GPS lock obtained (outdoor)
- [ ] Telemetry flowing to visualizer
- [ ] Drone visible on 3D map

---

## Next Steps

1. **Start Simple**: Use DJI Mobile SDK with HTTP POST
2. **Add WebSocket**: Upgrade to WebSocket for lower latency
3. **Add Video**: Integrate camera feed
4. **Go Cloud**: Deploy to cloud for remote access
5. **Scale**: Add multiple drones, authentication, monitoring
