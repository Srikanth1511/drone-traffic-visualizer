import React, { useEffect, useMemo, useState } from 'react'
import ReactDOM from 'react-dom/client'
import L from 'leaflet'
import { MapContainer, Marker, Rectangle, TileLayer, Tooltip } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import './styles.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const facilityColor = (maxAltitudeAgl) => {
  if (maxAltitudeAgl >= 120) return '#10b981'
  if (maxAltitudeAgl >= 80) return '#f59e0b'
  return '#ef4444'
}

const lookupFacilityCell = (cells, lat, lon) =>
  cells.find((cell) =>
    cell.latRange &&
    cell.lonRange &&
    lat >= cell.latRange[0] &&
    lat <= cell.latRange[1] &&
    lon >= cell.lonRange[0] &&
    lon <= cell.lonRange[1]
  )

const droneIcon = (heading, active) =>
  L.divIcon({
    className: `drone-icon ${active ? 'active' : ''}`,
    html: `<div class="chevron" style="transform: rotate(${heading}deg);"></div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  })

const formatMeters = (value) => `${value.toFixed(1)} m`

function ScenarioPicker({ scenarios, selectedId, onSelect }) {
  return (
    <div className="panel soft">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Preset</p>
          <h2>Venue selector</h2>
        </div>
        <div className="pill">powered by FastAPI</div>
      </div>
      <select className="primary-select" value={selectedId ?? ''} onChange={(e) => onSelect(e.target.value)}>
        {scenarios.map((scenario) => (
          <option key={scenario.id} value={scenario.id}>
            {scenario.label}
          </option>
        ))}
      </select>
      <p className="hint">Each preset bundles a playback export and cached FAA ceiling grid for quick demos.</p>
    </div>
  )
}

function LayerToggles({ showFacility, setShowFacility, showDrones, setShowDrones, showCorridors, setShowCorridors }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Layers</p>
          <h3>Overlay stack</h3>
        </div>
      </div>
      <div className="toggle-row">
        <label>
          <input type="checkbox" checked={showDrones} onChange={(e) => setShowDrones(e.target.checked)} />
          Drones + headings
        </label>
      </div>
      <div className="toggle-row">
        <label>
          <input type="checkbox" checked={showCorridors} onChange={(e) => setShowCorridors(e.target.checked)} />
          Corridors
        </label>
      </div>
      <div className="toggle-row">
        <label>
          <input type="checkbox" checked={showFacility} onChange={(e) => setShowFacility(e.target.checked)} />
          FAA facility grid (AGL ceilings)
        </label>
      </div>
      <div className="hint">Matches the Phase 1 MVP UI: left stack for layers, right-side inspector, bottom timeline.</div>
    </div>
  )
}

function PlaybackControls({ timeline, onScrub, playing, setPlaying, speed, setSpeed }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Playback</p>
          <h3>Transport bar</h3>
        </div>
      </div>
      <div className="transport">
        <button className="primary" onClick={() => setPlaying((p) => !p)}>
          {playing ? 'Pause' : 'Play'}
        </button>
        <label>
          Speed
          <input
            type="range"
            min="0.5"
            max="3"
            step="0.25"
            value={speed}
            onChange={(e) => setSpeed(Number(e.target.value))}
          />
          <span className="chip">{speed.toFixed(2)}x</span>
        </label>
      </div>
      <div className="timeline">
        <input
          type="range"
          min={0}
          max={Math.max(timeline.total - 1, 0)}
          step={1}
          value={timeline.index}
          onChange={(e) => onScrub(Number(e.target.value))}
        />
        <div className="timeline-meta">
          <span>t={timeline.currentTime.toFixed(1)}s</span>
          <span>
            {timeline.index + 1}/{timeline.total} frames
          </span>
        </div>
      </div>
    </div>
  )
}

function Inspector({ selectedDrone, facilityCell }) {
  if (!selectedDrone) {
    return (
      <div className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Inspector</p>
            <h3>Pick a drone</h3>
          </div>
        </div>
        <p className="hint">Click a drone marker to mirror the AirLoom-style right-hand status card.</p>
      </div>
    )
  }

  const overCeiling = facilityCell && facilityCell.maxAltitudeAgl !== undefined && selectedDrone.alt_agl > facilityCell.maxAltitudeAgl

  return (
    <div className="panel accent">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Inspector</p>
          <h3>{selectedDrone.id}</h3>
        </div>
        {overCeiling && <div className="pill warning">Above ceiling</div>}
      </div>
      <div className="stat-grid">
        <div>
          <p className="label">Lat / Lon</p>
          <p className="value">{selectedDrone.lat.toFixed(5)}, {selectedDrone.lon.toFixed(5)}</p>
        </div>
        <div>
          <p className="label">Alt MSL</p>
          <p className="value">{formatMeters(selectedDrone.alt_msl)}</p>
        </div>
        <div>
          <p className="label">Alt AGL</p>
          <p className="value">{formatMeters(selectedDrone.alt_agl)}</p>
        </div>
        <div>
          <p className="label">Heading</p>
          <p className="value">{selectedDrone.heading.toFixed(0)}°</p>
        </div>
        <div>
          <p className="label">Speed</p>
          <p className="value">{selectedDrone.speed.toFixed(1)} m/s</p>
        </div>
        <div>
          <p className="label">Battery</p>
          <p className="value">{selectedDrone.payload?.battery ? `${(selectedDrone.payload.battery * 100).toFixed(0)}%` : 'n/a'}</p>
        </div>
      </div>
      {facilityCell && (
        <div className="ceiling">
          <p className="label">Facility ceiling</p>
          <p className="value">{facilityCell.maxAltitudeAgl ? formatMeters(facilityCell.maxAltitudeAgl) : 'n/a'}</p>
        </div>
      )}
    </div>
  )
}

function MapView({ scenario, snapshot, facilityGrid, corridors, showFacility, showCorridors, showDrones, selectedDroneId, onSelectDrone }) {
  const center = [scenario.originLat, scenario.originLon]

  return (
    <div className="panel map-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Live map</p>
          <h3>Interactive corridor view</h3>
        </div>
        <div className="pill">OSM + Leaflet</div>
      </div>
      <MapContainer center={center} zoom={14} scrollWheelZoom className="map-root">
        <TileLayer
          attribution='&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {showCorridors &&
          corridors.map((corridor) => (
            <Polyline
              key={corridor.id}
              positions={corridor.path.map((p) => [p.lat, p.lon])}
              pathOptions={{ color: '#5ac8fa', weight: Math.max(2, Math.min(8, corridor.width_m / 10)), opacity: 0.8 }}
            >
              <Tooltip sticky>
                <div className="tooltip">
                  <div className="label">{corridor.id}</div>
                  <div className="value">{corridor.type}</div>
                </div>
              </Tooltip>
            </Polyline>
          ))}
        {showFacility &&
          facilityGrid.map((cell, idx) => (
            <Rectangle
              key={`${idx}-${cell.latRange?.[0]}-${cell.lonRange?.[0]}`}
              bounds={[
                [cell.latRange[0], cell.lonRange[0]],
                [cell.latRange[1], cell.lonRange[1]],
              ]}
              pathOptions={{ color: facilityColor(cell.maxAltitudeAgl), weight: 1, fillOpacity: 0.25 }}
            >
              <Tooltip sticky>
                <div className="tooltip">
                  <div className="label">Max AGL</div>
                  <div className="value">{formatMeters(cell.maxAltitudeAgl ?? 0)}</div>
                </div>
              </Tooltip>
            </Rectangle>
          ))}
        {showDrones &&
          snapshot?.drones?.map((drone) => (
            <Marker
              key={drone.id}
              position={[drone.lat, drone.lon]}
              icon={droneIcon(drone.heading, drone.id === selectedDroneId)}
              eventHandlers={{
                click: () => onSelectDrone(drone.id),
              }}
            >
              <Tooltip direction="top" offset={[0, -6]}>
                <div className="tooltip">
                  <div className="label">{drone.id}</div>
                  <div className="value">{formatMeters(drone.alt_agl)} AGL</div>
                </div>
              </Tooltip>
            </Marker>
          ))}
      </MapContainer>
    </div>
  )
}

function App() {
  const [scenarios, setScenarios] = useState([])
  const [scenarioId, setScenarioId] = useState(null)
  const [snapshots, setSnapshots] = useState([])
  const [corridors, setCorridors] = useState([])
  const [facilityGrid, setFacilityGrid] = useState([])
  const [loading, setLoading] = useState(false)
  const [playing, setPlaying] = useState(true)
  const [speed, setSpeed] = useState(1)
  const [frameIndex, setFrameIndex] = useState(0)
  const [selectedDroneId, setSelectedDroneId] = useState(null)
  const [showFacility, setShowFacility] = useState(true)
  const [showCorridors, setShowCorridors] = useState(true)
  const [showDrones, setShowDrones] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch(`${API_BASE}/scenarios`)
      .then((res) => {
        if (!res.ok) throw new Error('Scenario request failed')
        return res.json()
      })
      .then((payload) => {
        const list = payload.scenarios || []
        setScenarios(list)
        if (list.length) {
          setScenarioId(list[0].id)
        }
      })
      .catch(() => setError('Failed to load scenario presets'))
  }, [])

  const scenario = useMemo(() => scenarios.find((s) => s.id === scenarioId), [scenarioId, scenarios])
  const currentSnapshot = snapshots[frameIndex]

  useEffect(() => {
    if (!scenario) return
    setLoading(true)
    setError('')
    const load = async () => {
      const telemetryUrl = `${API_BASE}/telemetry?path=${encodeURIComponent(scenario.playbackPath)}&facility_cache=${encodeURIComponent(
        scenario.facilityMapCache
      )}`
      const facilityUrl = `${API_BASE}/facility-grid?path=${encodeURIComponent(scenario.facilityMapCache)}`

      try {
        const [telemetryRes, facilityRes] = await Promise.all([fetch(telemetryUrl), fetch(facilityUrl)])
        if (!telemetryRes.ok || !facilityRes.ok) {
          throw new Error('API request failed')
        }
        const telemetryJson = await telemetryRes.json()
        const facilityJson = await facilityRes.json()
        setCorridors(telemetryJson.corridors || [])
        setSnapshots(telemetryJson.snapshots || [])
        setFacilityGrid(facilityJson.cells || [])
        setFrameIndex(0)
        setSelectedDroneId(null)
      } catch (err) {
        console.error(err)
        setError('Unable to load telemetry or facility grid for this scenario')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [scenario])

  useEffect(() => {
    if (!playing || snapshots.length === 0) return
    const id = setInterval(() => {
      setFrameIndex((idx) => (idx + 1) % snapshots.length)
    }, 1000 / speed)
    return () => clearInterval(id)
  }, [playing, speed, snapshots.length])

  const selectedDrone = useMemo(() => currentSnapshot?.drones?.find((d) => d.id === selectedDroneId), [currentSnapshot, selectedDroneId])
  const ceilingCell = selectedDrone ? lookupFacilityCell(facilityGrid, selectedDrone.lat, selectedDrone.lon) : null

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <p className="eyebrow">Phase 1 web console</p>
          <h1>Drone Traffic Visualizer</h1>
          <p className="subhead">Interactive map, FAA ceiling overlay, playback timeline, and AirLoom-inspired UI chrome.</p>
        </div>
        <div className="top-actions">
          <div className="pill muted">API base {API_BASE}</div>
        </div>
      </header>

      {error && <div className="alert">{error}</div>}

      <div className="layout">
        <div className="column">
          <ScenarioPicker scenarios={scenarios} selectedId={scenarioId} onSelect={setScenarioId} />
          <LayerToggles
            showFacility={showFacility}
            showCorridors={showCorridors}
            showDrones={showDrones}
            setShowFacility={setShowFacility}
            setShowCorridors={setShowCorridors}
            setShowDrones={setShowDrones}
          />
          <PlaybackControls
            timeline={{ index: frameIndex, total: snapshots.length, currentTime: currentSnapshot?.time ?? 0 }}
            onScrub={(idx) => {
              setFrameIndex(idx)
              setPlaying(false)
            }}
            playing={playing}
            setPlaying={setPlaying}
            speed={speed}
            setSpeed={setSpeed}
          />
        </div>
        <div className="column wide">
          {scenario && (
            <MapView
              scenario={scenario}
              snapshot={currentSnapshot}
              facilityGrid={facilityGrid}
              corridors={corridors}
              showFacility={showFacility}
              showCorridors={showCorridors}
              showDrones={showDrones}
              selectedDroneId={selectedDroneId}
              onSelectDrone={setSelectedDroneId}
            />
          )}
          <div className="legend">
            <div className="chip" style={{ background: '#10b981' }}>120m+ ceiling</div>
            <div className="chip" style={{ background: '#f59e0b' }}>80-119m ceiling</div>
            <div className="chip" style={{ background: '#ef4444' }}>Below 80m ceiling</div>
            <div className="chip outline">Heading arrows = drone markers</div>
          </div>
        </div>
        <div className="column">
          <Inspector selectedDrone={selectedDrone} facilityCell={ceilingCell} />
        </div>
      </div>

      {loading && <div className="loading">Loading preset telemetry…</div>}
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />)
