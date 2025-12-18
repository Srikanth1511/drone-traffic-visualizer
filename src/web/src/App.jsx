import React, { useState, useEffect } from 'react'
import CesiumViewer from './components/CesiumViewer'
import PlaybackControls from './components/PlaybackControls'
import DroneInspector from './components/DroneInspector'
import ScenarioSelector from './components/ScenarioSelector'
import LayerToggles from './components/LayerToggles'
import './App.css'

function App() {
  const [scenario, setScenario] = useState(null)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0)
  const [telemetryData, setTelemetryData] = useState(null)
  const [selectedDrone, setSelectedDrone] = useState(null)
  const [layers, setLayers] = useState({
    drones: true,
    corridors: true,
    facilityMap: true,
    trails: false
  })

  // Load scenario
  const loadScenario = async (scenarioConfig) => {
    try {
      const response = await fetch('/api/scenario/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(scenarioConfig)
      })

      if (!response.ok) {
        throw new Error('Failed to load scenario')
      }

      const data = await response.json()
      setScenario(data)
      setDuration(data.scenario.duration)
      setCurrentTime(0)

      // Load initial telemetry
      await fetchTelemetryFrame(0)
    } catch (error) {
      console.error('Error loading scenario:', error)
    }
  }

  // Fetch telemetry frame at specific time
  const fetchTelemetryFrame = async (time) => {
    try {
      const response = await fetch(`/api/telemetry/frame?time=${time}`)
      if (!response.ok) {
        throw new Error('Failed to fetch telemetry')
      }

      const data = await response.json()
      setTelemetryData(data)
    } catch (error) {
      console.error('Error fetching telemetry:', error)
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
    fetchTelemetryFrame(0)
  }

  // Toggle layer visibility
  const toggleLayer = (layerName) => {
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
          <LayerToggles layers={layers} onToggle={toggleLayer} />
        </div>

        <div className="viewer-container">
          <CesiumViewer
            scenario={scenario}
            telemetryData={telemetryData}
            layers={layers}
            onDroneSelect={setSelectedDrone}
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
