import React, { useState, useEffect, useRef } from 'react'
import CesiumViewer from './components/CesiumViewer'
import PlaybackControls from './components/PlaybackControls'
import DroneInspector from './components/DroneInspector'
import ScenarioSelector from './components/ScenarioSelector'
import LayerToggles from './components/LayerToggles'
import './App.css'

function App() {
  const [mode, setMode] = useState('playback') // 'playback' or 'live'
  const [scenario, setScenario] = useState(null)
  const [scenarioStatus, setScenarioStatus] = useState({ type: 'info', text: 'Load a scenario or switch to live mode.' })
  const [scenarioLoading, setScenarioLoading] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0)
  const [telemetryData, setTelemetryData] = useState(null)
  const [telemetryLoading, setTelemetryLoading] = useState(false)
  const [selectedDrone, setSelectedDrone] = useState(null)
  const [droneTrails, setDroneTrails] = useState({}) // Track position history
  const [facilityCells, setFacilityCells] = useState([])
  const [layers, setLayers] = useState({
    drones: true,
    corridors: true,
    facilityMap: true,
    trails: true, // Enable trails by default
    googleTiles: false // Google 3D tiles disabled by default (requires API key)
  })

  // WebSocket for live mode
  const wsRef = useRef(null)
  const [wsConnected, setWsConnected] = useState(false)

  // Check if Google Maps API key is available
  const googleApiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY
  const hasGoogleKey = Boolean(googleApiKey && googleApiKey !== 'your_google_maps_api_key_here')

  // Status update helpers
  const updateStatus = (type, text) => setScenarioStatus({ type, text })
  const handleViewerStatus = (type, text) => setScenarioStatus({ type, text })

  // Load scenario
  const loadScenario = async (scenarioConfig) => {
    setScenarioLoading(true)
    setScenarioStatus({ type: 'info', text: 'Loading scenario...' })
    setIsPlaying(false)
    setDroneTrails({})
    setSelectedDrone(null)

    try {
      const response = await fetch('/api/scenario/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(scenarioConfig)
      })

      let payload
      try {
        payload = await response.json()
      } catch (parseError) {
        throw new Error('Server response was not valid JSON while loading scenario')
      }

      if (!response.ok) {
        throw new Error(payload?.detail || 'Failed to load scenario')
      }

      const loadedScenario = {
        ...payload.scenario,
        name: scenarioConfig.name,
        metadata: payload.scenario?.metadata || scenarioConfig.metadata || {},
        corridors: payload.corridors || []
      }

      setScenario(loadedScenario)
      setDuration(payload.scenario.duration || 0)
      setCurrentTime(0)
      updateStatus('success', `Loaded ${scenarioConfig.name || 'scenario'} successfully.`)

      // Load facility map
      try {
        const facilityResponse = await fetch('/api/airspace/facility-map')
        if (facilityResponse.ok) {
          const facilityPayload = await facilityResponse.json()
          setFacilityCells(facilityPayload?.cells || [])
        } else {
          setFacilityCells([])
        }
      } catch (facilityError) {
        console.warn('Unable to load facility map grid', facilityError)
        setFacilityCells([])
      }

      // Load initial telemetry
      await fetchTelemetryFrame(0, { showLoader: true, stopOnError: true })
    } catch (error) {
      console.error('Error loading scenario:', error)
      setScenario(null)
      setDuration(0)
      updateStatus('error', error.message || 'Failed to load scenario')
    } finally {
      setScenarioLoading(false)
    }
  }

  // Fetch telemetry frame at specific time
  const fetchTelemetryFrame = async (time, { showLoader = false, stopOnError = false } = {}) => {
    if (showLoader) setTelemetryLoading(true)

    try {
      const response = await fetch(`/api/telemetry/frame?time=${time}`)
      let data
      try {
        data = await response.json()
      } catch (parseError) {
        throw new Error('Telemetry response was not valid JSON')
      }

      if (!response.ok) {
        throw new Error(data?.detail || 'Failed to fetch telemetry')
      }

      setTelemetryData(data)

      // Update drone trails
      setDroneTrails((prevTrails) => {
        const newTrails = { ...prevTrails }
        data.drones.forEach((drone) => {
          if (!newTrails[drone.id]) {
            newTrails[drone.id] = []
          }
          newTrails[drone.id].push({
            lat: drone.lat,
            lon: drone.lon,
            alt: drone.alt_agl, // Use AGL for proper terrain-relative positioning
            time: data.time
          })
          // Keep last 300 positions for better performance
          if (newTrails[drone.id].length > 300) {
            newTrails[drone.id].shift()
          }
        })
        return newTrails
      })

      return data
    } catch (error) {
      console.error('Error fetching telemetry:', error)
      updateStatus('error', error.message || 'Telemetry fetch failed')
      if (stopOnError) {
        setIsPlaying(false)
      }
    } finally {
      if (showLoader) setTelemetryLoading(false)
    }
  }

  // Playback loop
  useEffect(() => {
    if (!isPlaying || !scenario) return

    const interval = setInterval(() => {
      setCurrentTime((prevTime) => {
        const nextTime = prevTime + (0.1 * playbackSpeed)

        if (nextTime >= duration) {
          setIsPlaying(false)
          return duration
        }

        // Fetch telemetry for next time
        fetchTelemetryFrame(nextTime)

        return nextTime
      })
    }, 100)

    return () => clearInterval(interval)
  }, [isPlaying, playbackSpeed, duration, scenario])

  // Handle time scrub
  const handleTimeChange = (newTime) => {
    setCurrentTime(newTime)
    fetchTelemetryFrame(newTime)
  }

  // Handle play/pause
  const handlePlayPause = () => {
    setIsPlaying(!isPlaying)
  }

  // Handle reset
  const handleReset = () => {
    setCurrentTime(0)
    setIsPlaying(false)
    setDroneTrails({}) // Clear trails on reset
    fetchTelemetryFrame(0)
  }

  // Toggle layer visibility
  const toggleLayer = (layerName) => {
    if (layerName === 'googleTiles' && !googleApiKey) {
      updateStatus('info', 'Set VITE_GOOGLE_MAPS_API_KEY to enable Google 3D Tiles')
      return
    }

    setLayers((prev) => ({
      ...prev,
      [layerName]: !prev[layerName]
    }))
  }

  // ============================================================================
  // LIVE MODE FUNCTIONALITY
  // ============================================================================

  // Connect to WebSocket for live telemetry
  const connectLiveMode = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      updateStatus('info', 'Already connected to live telemetry')
      return
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/telemetry/live`

      updateStatus('info', 'Connecting to live telemetry...')
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('WebSocket connected')
        setWsConnected(true)
        updateStatus('success', 'Connected to live telemetry stream')

        // Create a default scenario for live mode
        setScenario({
          name: 'Live Telemetry',
          originLat: 33.7736, // Default to Atlanta
          originLon: -84.4022,
          corridors: []
        })
        setIsPlaying(false)
        setDroneTrails({})
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)

          if (message.type === 'telemetry_update') {
            const data = message.data
            setTelemetryData(data)

            // Update drone trails
            setDroneTrails((prevTrails) => {
              const newTrails = { ...prevTrails }
              data.drones.forEach((drone) => {
                if (!newTrails[drone.id]) {
                  newTrails[drone.id] = []
                }
                newTrails[drone.id].push({
                  lat: drone.lat,
                  lon: drone.lon,
                  alt: drone.alt_agl,
                  time: data.time
                })
                // Keep last 300 positions
                if (newTrails[drone.id].length > 300) {
                  newTrails[drone.id].shift()
                }
              })
              return newTrails
            })
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        updateStatus('error', 'WebSocket connection error')
        setWsConnected(false)
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setWsConnected(false)
        updateStatus('info', 'Disconnected from live telemetry')
      }

      wsRef.current = ws
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
      updateStatus('error', 'Failed to connect to live telemetry')
    }
  }

  // Disconnect from live mode
  const disconnectLiveMode = () => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
      setWsConnected(false)
      setTelemetryData(null)
      setDroneTrails({})
      updateStatus('info', 'Disconnected from live mode')
    }
  }

  // Switch between playback and live mode
  const switchMode = (newMode) => {
    if (newMode === mode) return

    if (newMode === 'live') {
      // Switching to live mode
      setIsPlaying(false)
      setScenario(null)
      setDroneTrails({})
      setSelectedDrone(null)
      setMode('live')
      connectLiveMode()
    } else {
      // Switching to playback mode
      disconnectLiveMode()
      setMode('playback')
      setScenario(null)
      setTelemetryData(null)
      updateStatus('info', 'Load a scenario to begin.')
    }
  }

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  return (
    <div className="app">
      <div className="app-header">
        <h1>Drone Traffic Visualizer</h1>

        {/* Mode Switcher */}
        <div className="mode-switcher">
          <button
            className={`mode-btn ${mode === 'playback' ? 'active' : ''}`}
            onClick={() => switchMode('playback')}
          >
            Playback
          </button>
          <button
            className={`mode-btn ${mode === 'live' ? 'active' : ''}`}
            onClick={() => switchMode('live')}
          >
            Live {wsConnected && '●'}
          </button>
        </div>

        {/* Scenario selector (only in playback mode) */}
        {mode === 'playback' && <ScenarioSelector onLoadScenario={loadScenario} />}

        {/* Live mode controls */}
        {mode === 'live' && (
          <div className="live-controls">
            {wsConnected ? (
              <button className="disconnect-btn" onClick={disconnectLiveMode}>
                Disconnect
              </button>
            ) : (
              <button className="connect-btn" onClick={connectLiveMode}>
                Reconnect
              </button>
            )}
          </div>
        )}
      </div>

      <div className="app-main">
        <div className="left-panel">
          <LayerToggles layers={layers} onToggle={toggleLayer} hasGoogleKey={hasGoogleKey} />
        </div>

        <div className="viewer-container">
          <CesiumViewer
            scenario={scenario}
            telemetryData={telemetryData}
            droneTrails={droneTrails}
            layers={layers}
            onDroneSelect={setSelectedDrone}
            isLoading={telemetryLoading || scenarioLoading}
            statusMessage={scenarioStatus}
            facilityCells={facilityCells}
            onStatus={handleViewerStatus}
            googleApiKey={googleApiKey}
          />
        </div>

        <div className="right-panel">
          <DroneInspector drone={selectedDrone} />
        </div>
      </div>

      <div className="app-footer">
        {/* Only show playback controls in playback mode */}
        {mode === 'playback' && (
          <PlaybackControls
            currentTime={currentTime}
            duration={duration}
            isPlaying={isPlaying}
            playbackSpeed={playbackSpeed}
            onTimeChange={handleTimeChange}
            onPlayPause={handlePlayPause}
            onReset={handleReset}
            onSpeedChange={setPlaybackSpeed}
          />
        )}

        {/* Live mode indicator */}
        {mode === 'live' && (
          <div className="live-footer">
            <span className={`live-indicator ${wsConnected ? 'connected' : 'disconnected'}`}>
              {wsConnected ? '● Live' : '○ Disconnected'}
            </span>
            <span className="live-info">
              {telemetryData ? `${telemetryData.drones?.length || 0} drone(s) active` : 'Waiting for telemetry...'}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
