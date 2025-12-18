# Drone Traffic Visualizer

A live drone visualization console for monitoring and managing drone traffic in urban environments. This system provides a 3D table-top view of venues with simulated and live drone telemetry, corridor networks, and airspace constraints.

![Status](https://img.shields.io/badge/status-Phase%201%20MVP-green)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![React](https://img.shields.io/badge/react-18.2-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

## Features

### Phase 1 (MVP) - ✅ Complete

- **3D Visualization**: CesiumJS-powered 3D map with OpenStreetMap buildings
- **Google Photorealistic 3D Tiles**: Optional high-fidelity 3D building rendering
- **Drone Rendering**: Real-time drone markers with health status indicators and trails
- **Playback Controls**: Timeline scrubber with variable speed (0.5x - 8x)
- **Corridor Networks**: Visualize pre-planned flight corridors with dual-layer paths
- **Airspace Overlays**: FAA UAS Facility Map ceiling display
- **Inspector Panel**: Detailed telemetry for selected drones
- **Default Venues**: Mercedes-Benz Stadium and Georgia Tech Campus
- **Demo Scenario**: 3 drones on perimeter patrol (~5 minutes)

### Phase 2 (Planned)

- Advanced interaction (multi-select, predictive paths)
- Camera feed integration (RTSP/WebRTC)
- Live FAA facility map integration
- Scenario authoring tools
- Export/import scenarios

### Phase 3 (Future)

- Live telemetry adapters (MAVLink, DJI SDK, Remote ID)
- Venue camera network overlay
- Swarm behaviors and deconfliction
- VR/AR support (WebXR)

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn

### Installation

```bash
# Clone repository
git clone https://github.com/Srikanth1511/drone-traffic-visualizer.git
cd drone-traffic-visualizer

# Backend setup
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Generate demo scenario
python3 src/scenarios/generate_demo.py

# Start backend server
python3 -m uvicorn src.server.app:app --reload --port 8000

# In a new terminal: Frontend setup
cd src/web
npm install
npm run dev
```

### Access

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Optional: Google Photorealistic 3D Tiles

For enhanced 3D building rendering with Google's photorealistic tiles:

1. Get a Google Maps API key:
   - Visit https://console.cloud.google.com/google/maps-apis
   - Create a new project or select existing
   - Enable **Map Tiles API** and **Maps JavaScript API**
   - Create credentials → API Key
   - Copy your API key

2. Configure the application:
   ```bash
   cd src/web
   cp .env.local.template .env.local
   # Edit .env.local and add your API key:
   # VITE_GOOGLE_MAPS_API_KEY=your_api_key_here
   ```

3. Enable Google 3D Tiles in the application:
   - Start the frontend
   - Use the **Layers** panel on the left
   - Toggle **Google 3D Tiles** on

**Note**: `.env.local` is excluded from git to protect your API keys.

## Architecture

### Modular Design

```
┌─────────────────────────────────────────┐
│          React Frontend (3D UI)         │
│        CesiumJS + Playback Controls     │
└─────────────────┬───────────────────────┘
                  │ REST API
┌─────────────────▼───────────────────────┐
│         FastAPI Backend Server          │
│     Telemetry API + Scenario Mgmt       │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
┌───────▼──────┐    ┌───────▼────────┐
│   Adapters   │    │    Services    │
│  (Playback,  │    │  (Altitude,    │
│   MAVLink,   │    │   Facility     │
│   DJI, etc.) │    │     Map)       │
└──────────────┘    └────────────────┘
```

### Data Flow

1. **Simulation Export** → JSON file from drone-traffic-simulator
2. **Playback Adapter** → Converts to unified telemetry schema
3. **FastAPI Server** → Serves telemetry via REST API
4. **React Frontend** → Renders 3D visualization
5. **CesiumJS** → Displays drones, corridors, and terrain

### Unified Telemetry Schema

All adapters output a common format:

```json
{
  "time": 123.45,
  "drones": [
    {
      "id": "drone_001",
      "lat": 33.7555,
      "lon": -84.4020,
      "alt_msl": 100.0,
      "alt_agl": 60.0,
      "heading": 180.0,
      "speed": 12.0,
      "health": "OK",
      "linkQuality": 0.98,
      "payload": {
        "cameraStreams": ["rtsp://..."],
        "battery": 0.95
      }
    }
  ]
}
```

## Project Structure

```
drone-traffic-visualizer/
├── src/
│   ├── models.py                 # Core data models
│   ├── utils/                    # Utilities (coordinates, etc.)
│   ├── adapters/                 # Telemetry adapters
│   │   ├── playback.py          # Simulation playback
│   │   ├── mavlink.py           # MAVLink (Phase 3)
│   │   └── vendor_dji.py        # DJI SDK (Phase 3)
│   ├── services/                 # Business logic
│   │   └── altitude_service.py  # MSL/AGL conversion
│   ├── server/                   # FastAPI backend
│   │   └── app.py               # API server
│   ├── scenarios/                # Scenario generators
│   │   └── generate_demo.py     # Demo scenario
│   └── web/                      # React frontend
│       ├── src/
│       │   ├── App.jsx          # Main app
│       │   └── components/      # React components
│       └── package.json
├── data/
│   ├── simulation_exports/       # Simulation JSON files
│   └── facility_maps/           # FAA facility map cache
├── tests/                        # Unit tests
├── docs/                         # Documentation
│   └── PHASE1_WEB_MVP.md        # Phase 1 spec
└── README.md
```

## Usage

### Loading a Scenario

1. Select venue from dropdown (Mercedes-Benz Stadium or Georgia Tech)
2. Click "Load Scenario"
3. Wait for camera to position

### Playback

- **Play/Pause**: Start/stop simulation
- **Timeline**: Scrub to any point
- **Speed**: Adjust playback rate
- **Reset**: Return to start

### Inspecting Drones

1. Click a drone in the 3D view
2. Inspector panel shows:
   - Position (lat/lon, MSL, AGL)
   - Flight data (heading, speed)
   - Status (health, battery, link quality)
   - Navigation (corridor, route)

### Toggling Layers

Use left panel to show/hide:
- Drones
- Corridors
- Facility map grid
- Trails
- Google 3D Tiles (requires API key)

## Testing

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test
python3 -m pytest tests/test_playback.py -v

# Coverage report
python3 -m pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

- ✅ Playback adapter (deterministic replay, monotonic timestamps)
- ✅ Altitude service (MSL/AGL conversion, facility map queries)
- ✅ Coordinate utilities (ENU to lat/lon conversion)

## Integration with drone-traffic-simulator

This visualization system is designed to work seamlessly with the [drone-traffic-simulator](https://github.com/Srikanth1511/drone-traffic-simulator).

### Data Export

From the simulator:

```python
from src.visualization import SimulationDataExporter

exporter = SimulationDataExporter()
exporter.export(
    state_log_csv="output/state_log.csv",
    corridor_json="data/corridors/network.json",
    output_path="output/visualization_data.json"
)
```

### Import to Visualizer

Copy the exported JSON to `data/simulation_exports/` and load via the UI.

## API Reference

See full API documentation at http://localhost:8000/docs when server is running.

### Key Endpoints

- `GET /api/health` - Server health check
- `POST /api/scenario/load` - Load simulation scenario
- `GET /api/telemetry/frame?time=X` - Get frame at time X
- `GET /api/scenario/corridors` - Get corridor network
- `GET /api/airspace/ceiling?lat=X&lon=Y` - Get facility ceiling

## Performance

- **Playback**: Smooth 10 FPS simulation
- **Rendering**: 60 FPS in 3D viewer
- **Memory**: <200MB typical
- **Startup**: <2s scenario load

## Configuration

### Default Venues

Edit `src/web/src/components/ScenarioSelector.jsx`:

```javascript
const SCENARIOS = {
  custom_venue: {
    name: 'My Custom Venue',
    simulation_file: '/data/simulation_exports/custom.json',
    origin_lat: 40.7128,
    origin_lon: -74.0060,
    facility_map_file: '/data/facility_maps/custom_grid.json'
  }
}
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Keep files under 250 lines
4. Write tests for new features
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Code Style

- **Python**: PEP 8, type hints encouraged
- **JavaScript**: ES6+, functional components
- **Max file length**: 250 lines
- **Modularity**: Single responsibility per file

## Roadmap

- [x] Phase 1: Basic visualization and playback
- [ ] Phase 2: Advanced interaction and camera feeds
- [ ] Phase 3: Live telemetry and VR support
- [ ] Phase 4: Multi-site deployment and cloud integration

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the Airloom visualization system
- Built on CesiumJS for 3D mapping
- Integrates with drone-traffic-simulator
- FAA UAS Facility Map data

## Support

- **Documentation**: See [docs/PHASE1_WEB_MVP.md](docs/PHASE1_WEB_MVP.md)
- **Issues**: https://github.com/Srikanth1511/drone-traffic-visualizer/issues
- **Discussions**: https://github.com/Srikanth1511/drone-traffic-visualizer/discussions

## Authors

- Architecture inspired by drone-traffic-simulator
- UI design inspired by Airloom
- Implementation: Modular, scalable, production-ready

---

**Status**: Phase 1 MVP Complete ✅

**Next**: Phase 2 Advanced Features
