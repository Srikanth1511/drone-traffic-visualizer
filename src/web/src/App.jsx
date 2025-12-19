import React, { useEffect, useMemo, useState } from 'react'
import CesiumViewer from './components/CesiumViewer'
import PlaybackControls from './components/PlaybackControls'
import DroneInspector from './components/DroneInspector'
import ScenarioSelector from './components/ScenarioSelector'
import LayerToggles from './components/LayerToggles'
import './App.css'

const DEFAULT_STATUS = { type: 'info', text: 'Load a scenario to begin.' }

function App() {
  const [scenario, setScenario] = useState(null)
  const [scenarioStatus, setScenarioStatus] = useState(DEFAULT_STATUS)
  const [scenarioLoading, setScenarioLoading] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0)
  const [telemetryData, setTelemetryData] = useState(null)
  const [telemetryLoading, setTelemetryLoading] = useState(false)
  const [selectedDrone, setSelectedDrone] = useState(null)
  const [droneTrails, setDroneTrails] = useState({})
  const [facilityCells, setFacilityCells] = useState([])
  const [focusPosition, setFocusPosition] = useState(null)
  const [layers, setLayers] = useState({
    drones: true,
    corridors: true,
    facilityMap: true,
    trails: true,
    googleTiles: false
  })
  const [lastUpdated, setLastUpdated] = useState(null)
  const googleApiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY

  const isReady = useMemo(() => Boolean(scenario && duration > 0), [scenario, duration])

  const updateStatus = (type, text) => setScenarioStatus({ type, text })
  const handleViewerStatus = (type, text) => setScenarioStatus({ type, text })
  const handleHoverDrone = (drone) => {
    if (drone) {
      setSelectedDrone(drone)
    }
  }

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

      const firstFrame = await fetchTelemetryFrame(0, { showLoader: true, stopOnError: true })
      if (firstFrame?.drones?.length) {
        const avgLat = firstFrame.drones.reduce((sum, d) => sum + d.lat, 0) / firstFrame.drones.length
        const avgLon = firstFrame.drones.reduce((sum, d) => sum + d.lon, 0) / firstFrame.drones.length
        setFocusPosition({ lat: avgLat, lon: avgLon })
      }
    } catch (error) {
      console.error('Error loading scenario:', error)
      setScenario(null)
      setDuration(0)
      updateStatus('error', error.message || 'Failed to load scenario')
    } finally {
      setScenarioLoading(false)
    }
  }

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
      setLastUpdated(new Date())

      setDroneTrails((prevTrails) => {
        const newTrails = { ...prevTrails }
        data.drones.forEach((drone) => {
          if (!newTrails[drone.id]) {
            newTrails[drone.id] = []
          }
          newTrails[drone.id].push({
            lat: drone.lat,
            lon: drone.lon,
            alt: drone.alt_msl,
            time: data.time
          })
          if (newTrails[drone.id].length > 2000) {
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

  useEffect(() => {
    if (!isPlaying || !scenario) return

    const interval = setInterval(() => {
      setCurrentTime((prevTime) => {
        const nextTime = Number((prevTime + (0.1 * playbackSpeed)).toFixed(2))

        if (nextTime >= duration) {
          setIsPlaying(false)
          updateStatus('info', 'Reached end of playback')
          return duration
        }

        fetchTelemetryFrame(nextTime, { stopOnError: true })
        return nextTime
      })
    }, 100)

    return () => clearInterval(interval)
  }, [isPlaying, playbackSpeed, duration, scenario])

  const clampTime = (value) => {
    if (!duration) return 0
    return Math.min(Math.max(value, 0), duration)
  }

  const handleTimeChange = (newTime) => {
    const clampedTime = clampTime(newTime)
    setCurrentTime(clampedTime)
    fetchTelemetryFrame(clampedTime, { showLoader: true, stopOnError: true })
  }

  const handlePlayPause = () => {
    if (!isReady) {
      updateStatus('info', 'Load a scenario before playing back')
      return
    }
    setIsPlaying((prev) => !prev)
  }

  const handleReset = () => {
    setCurrentTime(0)
    setIsPlaying(false)
    setDroneTrails({})
    if (isReady) {
      fetchTelemetryFrame(0, { showLoader: true, stopOnError: true })
    }
  }

  const handleSpeedChange = (speed) => {
    setPlaybackSpeed(speed)
    updateStatus('info', `Playback speed set to ${speed}x`)
  }

  const stepPlayback = (delta) => {
    if (!isReady) return
    const nextTime = clampTime(currentTime + delta)
    setCurrentTime(nextTime)
    fetchTelemetryFrame(nextTime, { showLoader: true, stopOnError: true })
  }

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
      <header className="app-header">
        <div className="brand">Drone Traffic Visualizer</div>
        <div className="header-actions">
          <ScenarioSelector onLoadScenario={loadScenario} loading={scenarioLoading} />
        </div>
      </header>

      <div className="app-body">
        <aside className="sidebar">
          <LayerToggles layers={layers} onToggle={toggleLayer} hasGoogleKey={Boolean(googleApiKey)} />
          <PlaybackControls
            currentTime={currentTime}
            duration={duration}
            isPlaying={isPlaying}
            playbackSpeed={playbackSpeed}
            onTimeChange={handleTimeChange}
            onPlayPause={handlePlayPause}
            onReset={handleReset}
            onSpeedChange={handleSpeedChange}
            onStepBackward={() => stepPlayback(-2)}
            onStepForward={() => stepPlayback(2)}
            isLoading={telemetryLoading || scenarioLoading}
            isReady={isReady}
          />
          <div className="status-textual">
            <div>Drones: {telemetryData?.drones?.length ?? 0}</div>
            <div>Time: {telemetryData?.time?.toFixed ? `${telemetryData.time.toFixed(1)}s` : '—'}</div>
            <div>Status: {scenarioStatus.text}</div>
          </div>
        </aside>

        <main className="viewer-shell">
          <CesiumViewer
            scenario={scenario}
            telemetryData={telemetryData}
            droneTrails={droneTrails}
            layers={layers}
            onDroneSelect={setSelectedDrone}
            onDroneHover={handleHoverDrone}
            isLoading={telemetryLoading || scenarioLoading}
            statusMessage={scenarioStatus}
            facilityCells={facilityCells}
            onStatus={handleViewerStatus}
            googleApiKey={googleApiKey}
            focusPosition={focusPosition}
          />
        </main>

        <aside className="inspector-panel">
          <DroneInspector drone={selectedDrone} />
        </aside>
      </div>
    </div>
  )
}

export default App
