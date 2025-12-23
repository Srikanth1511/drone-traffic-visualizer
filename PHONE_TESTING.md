# Testing Live Telemetry from Your Phone

This guide shows how to test the live telemetry system using your phone without needing ngrok or external services.

## Quick Start (Same WiFi Network)

### Step 1: Start Backend with Network Access

**Option A: Use the startup script (recommended)**
```bash
cd /path/to/drone-traffic-visualizer
./start_backend.sh
```

**Option B: Manual command**
```bash
python3 -m uvicorn src.server.app:app --reload --host 0.0.0.0 --port 8000
```

**⚠️ IMPORTANT:** Do NOT use `--host 127.0.0.1` or omit `--host` entirely!

### Step 2: Find Your Computer's IP Address

**Linux/Mac:**
```bash
hostname -I | awk '{print $1}'
# or
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Windows:**
```cmd
ipconfig
```

Look for something like: `192.168.1.100` or `10.0.0.5`

### Step 3: Test from Phone Browser

1. Make sure your phone is on the **same WiFi network** as your computer
2. Open a browser on your phone
3. Go to: `http://YOUR_IP:8000` (replace YOUR_IP with your computer's IP)
4. You should see:
   ```json
   {
     "name": "Drone Visualization API",
     "version": "0.1.0",
     "status": "operational"
   }
   ```

### Step 4: Test Sending Telemetry from Phone

**Using phone browser console (for testing):**

1. Go to: `http://YOUR_IP:8000/docs` (FastAPI Swagger UI)
2. Try the `/api/drones/register` endpoint
3. Try the `/api/telemetry/live/update` endpoint

**Using a test app (JavaScript/HTML):**

Create a simple HTML file and open it on your phone:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Drone Telemetry Test</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; padding: 20px; }
        button { padding: 15px; font-size: 16px; margin: 10px 0; width: 100%; }
        .success { background: #4CAF50; color: white; }
        .error { background: #f44336; color: white; }
        #status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        input { width: 100%; padding: 10px; margin: 5px 0; font-size: 16px; }
    </style>
</head>
<body>
    <h1>Live Telemetry Test</h1>

    <label>Backend URL:</label>
    <input type="text" id="backendUrl" value="http://YOUR_IP:8000" placeholder="http://192.168.1.100:8000">

    <button onclick="registerDrone()">1. Register Drone</button>
    <button onclick="sendTelemetry()">2. Send Telemetry</button>
    <button onclick="getStatus()">3. Check Status</button>
    <button onclick="startStream()">4. Start Streaming (1 Hz)</button>
    <button onclick="stopStream()">5. Stop Streaming</button>

    <div id="status"></div>

    <script>
        let streamInterval = null;
        let lat = 33.7736;
        let lon = -84.4022;
        let heading = 0;

        function getBackendUrl() {
            return document.getElementById('backendUrl').value;
        }

        function setStatus(message, isError = false) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = isError ? 'error' : 'success';
        }

        async function registerDrone() {
            try {
                const response = await fetch(`${getBackendUrl()}/api/drones/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        drone_id: 'phone_test_001',
                        metadata: { type: 'phone_browser' }
                    })
                });

                const data = await response.json();
                setStatus('✓ Registered: ' + JSON.stringify(data));
            } catch (error) {
                setStatus('✗ Error: ' + error.message, true);
            }
        }

        async function sendTelemetry() {
            try {
                // Simulate movement
                heading = (heading + 10) % 360;
                const radius = 0.001;
                const angle = (heading * Math.PI / 180);
                lat = 33.7736 + radius * Math.cos(angle);
                lon = -84.4022 + radius * Math.sin(angle);

                const response = await fetch(`${getBackendUrl()}/api/telemetry/live/update`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        id: 'phone_test_001',
                        lat: lat,
                        lon: lon,
                        alt_msl: 350.0,
                        alt_agl: 50.0,
                        heading: heading,
                        speed: 5.0,
                        health: 'OK',
                        link_quality: 0.9,
                        payload: { battery: 0.85 }
                    })
                });

                const data = await response.json();
                setStatus(`✓ Telemetry sent: Heading ${heading}°`);
            } catch (error) {
                setStatus('✗ Error: ' + error.message, true);
            }
        }

        async function getStatus() {
            try {
                const response = await fetch(`${getBackendUrl()}/api/telemetry/live/current`);
                const data = await response.json();
                setStatus(`✓ Active drones: ${data.drones.length}`);
            } catch (error) {
                setStatus('✗ Error: ' + error.message, true);
            }
        }

        function startStream() {
            if (streamInterval) {
                setStatus('Already streaming!', true);
                return;
            }

            streamInterval = setInterval(sendTelemetry, 1000);
            setStatus('✓ Streaming started (1 Hz)');
        }

        function stopStream() {
            if (streamInterval) {
                clearInterval(streamInterval);
                streamInterval = null;
                setStatus('✓ Streaming stopped');
            } else {
                setStatus('Not streaming!', true);
            }
        }
    </script>
</body>
</html>
```

Save this as `test_telemetry.html` and open it on your phone!

### Step 5: View Live Telemetry on Desktop

1. On your computer, open: `http://localhost:3000`
2. Click the **"Live"** button in the header
3. Watch for the green **"● Live"** indicator
4. You should see the drone from your phone appear on the map!

## Using Your Phone's GPS

To send your phone's actual GPS location, you'll need a simple web app that accesses the phone's location:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Phone GPS → Drone Viz</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; padding: 20px; max-width: 500px; }
        button { padding: 15px; font-size: 16px; margin: 10px 0; width: 100%; }
        .active { background: #4CAF50; color: white; }
        .inactive { background: #666; color: white; }
        input { width: 100%; padding: 10px; margin: 5px 0; font-size: 16px; }
        #info { padding: 10px; background: #f0f0f0; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>Phone GPS Telemetry</h1>

    <label>Backend URL:</label>
    <input type="text" id="backendUrl" value="http://YOUR_IP:8000">

    <button id="toggleBtn" onclick="toggleTracking()" class="inactive">
        Start Tracking
    </button>

    <div id="info">
        <strong>Status:</strong> <span id="status">Not started</span><br>
        <strong>Position:</strong> <span id="position">-</span><br>
        <strong>Altitude:</strong> <span id="altitude">-</span><br>
        <strong>Speed:</strong> <span id="speed">-</span><br>
        <strong>Heading:</strong> <span id="heading">-</span>
    </div>

    <script>
        let watchId = null;
        let isTracking = false;

        function updateDisplay(text, field) {
            document.getElementById(field).textContent = text;
        }

        async function sendPosition(position) {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            const alt = position.coords.altitude || 0;
            const speed = position.coords.speed || 0;
            const heading = position.coords.heading || 0;

            updateDisplay(`${lat.toFixed(6)}, ${lon.toFixed(6)}`, 'position');
            updateDisplay(`${alt.toFixed(1)}m`, 'altitude');
            updateDisplay(`${speed.toFixed(1)} m/s`, 'speed');
            updateDisplay(`${heading.toFixed(0)}°`, 'heading');

            try {
                const backendUrl = document.getElementById('backendUrl').value;
                const response = await fetch(`${backendUrl}/api/telemetry/live/update`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        id: 'phone_gps_' + Date.now().toString(36),
                        lat: lat,
                        lon: lon,
                        alt_msl: alt,
                        alt_agl: alt,
                        heading: heading,
                        speed: speed,
                        health: 'OK',
                        link_quality: 1.0,
                        payload: {
                            battery: (navigator.getBattery ?
                                     (await navigator.getBattery()).level : 1.0)
                        }
                    })
                });

                if (response.ok) {
                    updateDisplay('✓ Sending GPS data', 'status');
                } else {
                    updateDisplay('✗ Failed to send', 'status');
                }
            } catch (error) {
                updateDisplay('✗ Error: ' + error.message, 'status');
            }
        }

        function toggleTracking() {
            const btn = document.getElementById('toggleBtn');

            if (isTracking) {
                // Stop tracking
                if (watchId !== null) {
                    navigator.geolocation.clearWatch(watchId);
                    watchId = null;
                }
                isTracking = false;
                btn.textContent = 'Start Tracking';
                btn.className = 'inactive';
                updateDisplay('Stopped', 'status');
            } else {
                // Start tracking
                if (!navigator.geolocation) {
                    alert('Geolocation is not supported by your browser');
                    return;
                }

                updateDisplay('Starting...', 'status');

                watchId = navigator.geolocation.watchPosition(
                    sendPosition,
                    (error) => {
                        updateDisplay('✗ GPS Error: ' + error.message, 'status');
                    },
                    {
                        enableHighAccuracy: true,
                        maximumAge: 0,
                        timeout: 5000
                    }
                );

                isTracking = true;
                btn.textContent = 'Stop Tracking';
                btn.className = 'active';
            }
        }
    </script>
</body>
</html>
```

## Troubleshooting

### "Connection refused" on phone

**Problem:** Phone can't connect to `http://YOUR_IP:8000`

**Solutions:**
1. ✅ Verify backend is running with `--host 0.0.0.0`
2. ✅ Ensure phone and computer are on the **same WiFi network**
3. ✅ Check firewall isn't blocking port 8000
4. ✅ Try accessing `http://YOUR_IP:8000` from your computer's browser first

### Firewall blocking connections

**Linux:**
```bash
sudo ufw allow 8000
```

**Windows:**
```cmd
netsh advfirewall firewall add rule name="Drone Viz Backend" dir=in action=allow protocol=TCP localport=8000
```

**Mac:**
System Preferences → Security & Privacy → Firewall → Firewall Options → Allow port 8000

### GPS not working

**Problem:** Phone GPS not sending position

**Solutions:**
1. ✅ Use HTTPS (required for geolocation on some browsers)
2. ✅ Grant location permissions when prompted
3. ✅ Try outdoors for better GPS signal
4. ✅ Use Chrome or Safari (better GPS support)

### Mixed content errors (HTTP vs HTTPS)

If you need HTTPS for GPS to work, you'll need to set up SSL or use ngrok.

**Quick ngrok setup:**
```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8000
```

This gives you a public HTTPS URL like: `https://abc123.ngrok.io`

Use this URL in the phone app instead of `http://YOUR_IP:8000`.

## Next Steps

Once you confirm the backend is reachable from your phone:

1. Build the actual phone app with React/PWA
2. Integrate camera and audio streaming
3. Add offline support and caching
4. Deploy to a public server for remote testing

## Security Notes

**⚠️ WARNING:** This setup exposes your backend to your local network!

**For production:**
- Add authentication (API keys, OAuth)
- Use HTTPS with valid SSL certificates
- Implement rate limiting
- Add CORS restrictions
- Use environment variables for sensitive config
- Deploy behind a reverse proxy (nginx, Caddy)

**For now (testing):**
- Only use on trusted WiFi networks
- Don't expose port 8000 to the internet
- Don't store sensitive data
- Use for testing only
