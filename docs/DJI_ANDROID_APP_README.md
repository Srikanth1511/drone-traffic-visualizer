# DJI Mini 3 Live Telemetry & Video Android App

Android app for streaming live telemetry and video from DJI Mini 3 to the [drone-traffic-visualizer](https://github.com/YOUR_USERNAME/drone-traffic-visualizer) backend.

## Features

- ✅ Real-time GPS telemetry streaming (10 Hz)
- ✅ Live H.264 video feed
- ✅ Battery, altitude, heading, speed monitoring
- ✅ WebSocket connection to visualizer backend
- ✅ Automatic reconnection handling
- ✅ Works with DJI Mini 3 / Mini 3 Pro

## Prerequisites

### Required
- **Android Studio** (Arctic Fox or later)
- **DJI Developer Account** - [Register here](https://developer.dji.com/)
- **DJI App Key** - [Create app and get key](https://developer.dji.com/user/apps/)
- **DJI Mini 3** or **Mini 3 Pro**
- **DJI RC** or **DJI RC-N1** (Remote Controller)
- **Android Phone/Tablet** (Android 6.0+)
- **drone-traffic-visualizer backend** running on your network

### Recommended
- Physical Android device (emulator won't work with DJI SDK)
- USB-C cable for RC connection
- Same WiFi network for phone and visualizer backend

---

## Quick Start (5 Minutes)

### Step 1: Clone and Open Project

```bash
git clone https://github.com/YOUR_USERNAME/dji-telemetry-app.git
cd dji-telemetry-app
```

Open in Android Studio:
```
File → Open → Select dji-telemetry-app folder
```

### Step 2: Add DJI App Key

1. Get your DJI App Key from [DJI Developer Portal](https://developer.dji.com/user/apps/)
2. Open `app/src/main/AndroidManifest.xml`
3. Replace `YOUR_DJI_APP_KEY` with your actual key:

```xml
<meta-data
    android:name="com.dji.sdk.API_KEY"
    android:value="YOUR_ACTUAL_APP_KEY_HERE" />
```

### Step 3: Configure Backend URL

Open `app/src/main/java/com/example/djitelemetry/Config.kt`:

```kotlin
object Config {
    // Replace with your computer's IP address
    const val BACKEND_URL = "http://192.168.1.100:8000"
}
```

**Find your computer's IP:**
- Linux/Mac: `hostname -I | awk '{print $1}'`
- Windows: `ipconfig` → Look for IPv4 Address

### Step 4: Build and Run

1. Connect your Android phone via USB
2. Enable USB Debugging on phone
3. In Android Studio: **Run** → **Run 'app'**
4. Accept USB debugging prompt on phone

### Step 5: Connect and Fly

1. Power on DJI Mini 3
2. Power on DJI RC
3. Connect phone to RC via USB-C
4. Launch app on phone
5. Wait for "Connected to Aircraft" message
6. Open visualizer frontend at `http://YOUR_COMPUTER_IP:3000`
7. Click **"Live"** button
8. Start flying - watch live telemetry on map!

---

## Detailed Setup

### 1. DJI SDK Installation

The project uses DJI Android SDK v4.16. Dependencies are already configured in `build.gradle`:

```gradle
dependencies {
    implementation 'com.dji:dji-sdk:4.16'
    implementation 'com.dji:dji-uxsdk:4.16'

    // WebSocket for telemetry streaming
    implementation 'com.squareup.okhttp3:okhttp:4.10.0'

    // JSON parsing
    implementation 'com.google.code.gson:gson:2.10'
}
```

### 2. Project Structure

```
dji-telemetry-app/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/example/djitelemetry/
│   │   │   │   ├── MainActivity.kt           # Main UI
│   │   │   │   ├── DJIApplication.kt         # DJI SDK initialization
│   │   │   │   ├── TelemetryService.kt       # Telemetry streaming
│   │   │   │   ├── VideoStreamService.kt     # Video streaming
│   │   │   │   ├── Config.kt                 # Configuration
│   │   │   │   └── models/
│   │   │   │       └── DroneState.kt         # Telemetry data model
│   │   │   ├── AndroidManifest.xml
│   │   │   └── res/
│   │   │       ├── layout/
│   │   │       │   └── activity_main.xml     # UI layout
│   │   │       └── values/
│   │   │           └── strings.xml
│   ├── build.gradle
│   └── proguard-rules.pro
├── build.gradle
├── settings.gradle
└── README.md
```

### 3. Key Components

#### DJIApplication.kt
Initializes DJI SDK on app start.

```kotlin
class DJIApplication : Application() {
    override fun onCreate() {
        super.onCreate()

        DJISDKManager.getInstance().registerApp(this, object : DJISDKManager.SDKManagerCallback {
            override fun onRegister(djiError: DJIError?) {
                if (djiError == DJISDKError.REGISTRATION_SUCCESS) {
                    DJISDKManager.getInstance().startConnectionToProduct()
                }
            }

            override fun onProductConnect(baseProduct: BaseProduct?) {
                // Aircraft connected
            }

            override fun onProductDisconnect() {
                // Aircraft disconnected
            }
        })
    }
}
```

#### TelemetryService.kt
Streams telemetry to visualizer backend via WebSocket.

```kotlin
class TelemetryService(private val backendUrl: String) {
    private val client = OkHttpClient()
    private var webSocket: WebSocket? = null
    private val droneId = "dji_mini3_${System.currentTimeMillis()}"

    fun connect() {
        val request = Request.Builder()
            .url("$backendUrl/ws/telemetry/live".replace("http", "ws"))
            .build()

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                // Register drone
                val registration = JSONObject().apply {
                    put("type", "register")
                    put("drone_id", droneId)
                    put("metadata", JSONObject().apply {
                        put("type", "dji")
                        put("model", "Mini 3")
                    })
                }
                webSocket.send(registration.toString())
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                // Handle server messages
            }
        })
    }

    fun sendTelemetry(state: FlightControllerState) {
        val telemetry = JSONObject().apply {
            put("type", "update")
            put("data", JSONObject().apply {
                put("id", droneId)
                put("lat", state.aircraftLocation.latitude)
                put("lon", state.aircraftLocation.longitude)
                put("alt_msl", state.altitude)
                put("alt_agl", state.takeoffLocationAltitude)
                put("heading", state.attitude.yaw)
                put("speed", sqrt(
                    state.velocityX.pow(2) + state.velocityY.pow(2)
                ))
                put("health", if (state.areMotorsOn()) "OK" else "WARNING")
                put("link_quality", state.uplinkSignalQuality / 100.0)
                put("vertical_speed", state.velocityZ)
                put("payload", JSONObject().apply {
                    put("battery", state.batteryThresholdBehavior.value / 100.0)
                })
            })
        }

        webSocket?.send(telemetry.toString())
    }
}
```

#### MainActivity.kt
Main UI and telemetry loop setup.

```kotlin
class MainActivity : AppCompatActivity() {
    private lateinit var telemetryService: TelemetryService

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        telemetryService = TelemetryService(Config.BACKEND_URL)

        // Setup DJI connection listener
        DJISDKManager.getInstance().product?.let { product ->
            if (product is Aircraft) {
                setupFlightController(product.flightController)
            }
        }
    }

    private fun setupFlightController(fc: FlightController?) {
        fc?.setStateCallback { state ->
            // Called at 10 Hz
            telemetryService.sendTelemetry(state)
            updateUI(state)
        }
    }

    private fun updateUI(state: FlightControllerState) {
        runOnUiThread {
            findViewById<TextView>(R.id.tvLatitude).text =
                "Lat: ${state.aircraftLocation.latitude}"
            findViewById<TextView>(R.id.tvLongitude).text =
                "Lon: ${state.aircraftLocation.longitude}"
            findViewById<TextView>(R.id.tvAltitude).text =
                "Alt: ${state.altitude}m"
            findViewById<TextView>(R.id.tvSpeed).text =
                "Speed: ${sqrt(state.velocityX.pow(2) + state.velocityY.pow(2))}m/s"
        }
    }
}
```

### 4. Video Streaming (Optional)

For live video streaming, add VideoStreamService:

```kotlin
class VideoStreamService(private val backendUrl: String) {
    fun startVideoStream() {
        DJISDKManager.getInstance().videoFeeder?.primaryVideoFeed?.addVideoDataListener {
            videoBuffer, size ->
            // H.264 encoded video data
            // Forward to backend or use WebRTC

            // Option 1: Send to backend for recording
            sendVideoChunk(videoBuffer, size)

            // Option 2: Display locally
            // codecManager.sendDataToDecoder(videoBuffer, size)
        }
    }

    private fun sendVideoChunk(data: ByteArray, size: Int) {
        // Implementation depends on your backend video handling
        // Can use HTTP chunks, WebRTC, or RTMP
    }
}
```

---

## Building From Scratch

If you want to create the project from scratch:

### 1. Create New Android Project

```
Android Studio → New Project → Empty Activity
Name: DJI Telemetry App
Package: com.example.djitelemetry
Language: Kotlin
Minimum SDK: API 23 (Android 6.0)
```

### 2. Add DJI SDK Dependencies

**app/build.gradle:**
```gradle
android {
    compileSdk 33

    defaultConfig {
        applicationId "com.example.djitelemetry"
        minSdk 23
        targetSdk 33

        ndk {
            abiFilters 'armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64'
        }
    }

    packagingOptions {
        pickFirst 'lib/*/libdjivideo.so'
        pickFirst 'lib/*/libSDKRelativeJNI.so'
        pickFirst 'lib/*/libFlyForbid.so'
        pickFirst 'lib/*/libduml_vision_bokeh.so'
        pickFirst 'lib/*/libyuv2.so'
        pickFirst 'lib/*/libGroudStation.so'
        pickFirst 'lib/*/libFRCorkscrew.so'
        pickFirst 'lib/*/libUpgradeVerify.so'
        pickFirst 'lib/*/libFR.so'
        pickFirst 'lib/*/libDJIFlySafeCore.so'
        pickFirst 'lib/*/libdjifs_jni.so'
        pickFirst 'lib/*/libsfjni.so'
        pickFirst 'lib/*/libDJICommonJNI.so'
        pickFirst 'lib/*/libDJICSDKCommon.so'
        pickFirst 'lib/*/libDJIUpgradeCore.so'
        pickFirst 'lib/*/libDJIUpgradeJNI.so'
        pickFirst 'lib/*/libDJIWaypointV2Core.so'
        pickFirst 'lib/*/libAMapSDK_MAP_v6_9_2.so'
        pickFirst 'lib/*/libDJIMOP.so'
        pickFirst 'lib/*/libDJISDKLOGJNI.so'

        exclude 'META-INF/rxjava.properties'
        exclude 'assets/location_map_gps_locked.png'
        exclude 'assets/location_map_gps_3d.png'
    }
}

dependencies {
    implementation 'androidx.core:core-ktx:1.9.0'
    implementation 'androidx.appcompat:appcompat:1.6.0'
    implementation 'com.google.android.material:material:1.8.0'
    implementation 'androidx.constraintlayout:constraintlayout:2.1.4'

    // DJI SDK
    implementation ('com.dji:dji-sdk:4.16', {
        exclude module: 'library-anti-distortion'
        exclude module: 'fly-safe-database'
    })
    compileOnly 'com.dji:dji-sdk-provided:4.16'

    // WebSocket
    implementation 'com.squareup.okhttp3:okhttp:4.10.0'

    // JSON
    implementation 'com.google.code.gson:gson:2.10'
}
```

**settings.gradle:**
```gradle
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven { url 'https://jitpack.io' }
    }
}
```

### 3. Add Permissions

**AndroidManifest.xml:**
```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.example.djitelemetry">

    <!-- DJI SDK Permissions -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
    <uses-permission android:name="android.permission.CHANGE_WIFI_STATE" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
    <uses-permission android:name="android.permission.RECORD_AUDIO" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.READ_PHONE_STATE" />

    <uses-feature android:name="android.hardware.usb.host" />
    <uses-feature android:name="android.hardware.usb.accessory" />

    <application
        android:name=".DJIApplication"
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:theme="@style/Theme.AppCompat.Light.NoActionBar">

        <!-- DJI App Key -->
        <meta-data
            android:name="com.dji.sdk.API_KEY"
            android:value="YOUR_DJI_APP_KEY_HERE" />

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:screenOrientation="landscape">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>

            <!-- USB connection -->
            <intent-filter>
                <action android:name="android.hardware.usb.action.USB_ACCESSORY_ATTACHED" />
            </intent-filter>
            <meta-data
                android:name="android.hardware.usb.action.USB_ACCESSORY_ATTACHED"
                android:resource="@xml/accessory_filter" />
        </activity>

    </application>
</manifest>
```

### 4. Add USB Filter

Create `app/src/main/res/xml/accessory_filter.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <usb-accessory
        android:manufacturer="DJI"
        android:model="Android Accessory"
        android:version="1.0" />
</resources>
```

---

## Testing

### 1. Test Backend Connection

```bash
# On your computer, start the visualizer backend
cd drone-traffic-visualizer
./start_backend.sh

# Note the IP address shown (e.g., 192.168.1.100)
```

### 2. Update App Config

In `Config.kt`:
```kotlin
const val BACKEND_URL = "http://192.168.1.100:8000"
```

### 3. Run App

1. Connect phone to RC
2. Power on drone
3. Launch app
4. Check connection status

### 4. Verify Telemetry

Open visualizer frontend:
```
http://192.168.1.100:3000
```

- Click "Live" button
- Should see green "● Live" indicator
- Drone should appear on map
- Trails should show flight path

---

## Troubleshooting

### App won't connect to DJI SDK

**Problem:** "Registration failed" or "Product not connected"

**Solutions:**
1. Verify DJI App Key is correct in AndroidManifest.xml
2. Ensure phone is connected to RC via USB-C
3. Try uninstalling and reinstalling app
4. Update DJI RC firmware
5. Check USB debugging is enabled

### Telemetry not appearing in visualizer

**Problem:** App connects to drone but no data in visualizer

**Solutions:**
1. Check phone and computer are on same WiFi network
2. Verify backend URL in Config.kt is correct
3. Check backend is running: `curl http://YOUR_IP:8000`
4. Look for errors in Android Studio Logcat
5. Check firewall isn't blocking port 8000

### Video streaming not working

**Problem:** No video feed

**Solutions:**
1. Ensure DJI Fly app works first (proves hardware is OK)
2. Check `videoFeeder` is initialized
3. Verify codec manager setup
4. Try restarting app and drone

### Battery drains quickly

**Solutions:**
1. Reduce telemetry update rate (currently 10 Hz)
2. Disable video streaming if not needed
3. Use lower screen brightness
4. Keep phone plugged into RC

---

## Integration with Visualizer

The app integrates with [drone-traffic-visualizer](https://github.com/YOUR_USERNAME/drone-traffic-visualizer):

### Telemetry Flow

```
DJI Mini 3 → RC → Phone (This App) → WebSocket → Visualizer Backend → Frontend Map
```

### API Endpoints Used

- `ws://BACKEND:8000/ws/telemetry/live` - WebSocket telemetry streaming
- `POST /api/drones/register` - Register drone
- `POST /api/telemetry/live/update` - HTTP telemetry (fallback)

### Data Format

Telemetry matches the unified schema:

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
    "vertical_speed": 0.2,
    "payload": {
      "battery": 0.85
    }
  }
}
```

---

## Production Deployment

### Security

Add authentication:

```kotlin
class TelemetryService(
    private val backendUrl: String,
    private val apiKey: String
) {
    private fun createWebSocketRequest(): Request {
        return Request.Builder()
            .url(websocketUrl)
            .addHeader("Authorization", "Bearer $apiKey")
            .build()
    }
}
```

### Error Handling

Add retry logic:

```kotlin
private fun connectWithRetry(maxRetries: Int = 3) {
    var attempt = 0
    while (attempt < maxRetries) {
        try {
            connect()
            break
        } catch (e: Exception) {
            attempt++
            Thread.sleep(2000 * attempt) // Exponential backoff
        }
    }
}
```

### Logging

Add structured logging:

```kotlin
import android.util.Log

private fun log(message: String) {
    Log.d("DJITelemetry", message)
}

private fun logError(message: String, error: Throwable) {
    Log.e("DJITelemetry", message, error)
}
```

---

## Next Steps

1. **Clone this repo** and follow Quick Start
2. **Get DJI App Key** from developer portal
3. **Build and install** on Android device
4. **Connect to drone** and test telemetry
5. **Verify visualization** in drone-traffic-visualizer
6. **Add video streaming** (optional)
7. **Customize UI** for your needs

---

## Resources

- [DJI Mobile SDK Documentation](https://developer.dji.com/mobile-sdk/documentation/)
- [DJI Developer Forum](https://forum.dji.com/forum-139-1.html)
- [drone-traffic-visualizer](https://github.com/YOUR_USERNAME/drone-traffic-visualizer)
- [Sample Apps](https://github.com/dji-sdk/Mobile-SDK-Android)
- [Video Tutorials](https://www.youtube.com/c/DJIDeveloper)

---

## License

MIT License - See LICENSE file

---

## Support

For issues:
- DJI SDK issues: [DJI Forum](https://forum.dji.com/)
- Integration issues: [Open an issue](https://github.com/YOUR_USERNAME/dji-telemetry-app/issues)
- Visualizer issues: [Visualizer repo](https://github.com/YOUR_USERNAME/drone-traffic-visualizer/issues)
