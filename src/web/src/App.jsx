import React, { useState, useEffect } from 'react'
import CesiumViewer from './components/CesiumViewer'
import PlaybackControls from './components/PlaybackControls'
import DroneInspector from './components/DroneInspector'
import ScenarioSelector from './components/ScenarioSelector'
import LayerToggles from './components/LayerToggles'
import './App.css'

function App() {
  const [scenario, setScenario] = useState(null)
  const [scenarioStatus, setScenarioStatus] = useState({ type: 'info', text: 'Load a scenario to begin.' })
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

  return (
    <div className="app">
      <div className="app-header">
        <h1>Drone Traffic Visualizer</h1>
        <ScenarioSelector onLoadScenario={loadScenario} />
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
      </div>
    </div>
  )
}

export default App
