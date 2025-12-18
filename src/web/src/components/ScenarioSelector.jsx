import React, { useState } from 'react'
import './ScenarioSelector.css'

const SCENARIOS = {
  mercedes_benz: {
    name: 'Mercedes-Benz Stadium',
    simulation_file: '/data/simulation_exports/benz_perimeter_patrol.json',
    origin_lat: 33.755489,
    origin_lon: -84.401993,
    facility_map_file: '/data/facility_maps/benz_grid.json'
  },
  georgia_tech: {
    name: 'Georgia Tech Campus',
    simulation_file: '/data/simulation_exports/gt_campus_patrol.json',
    origin_lat: 33.7736,
    origin_lon: -84.4022,
    facility_map_file: '/data/facility_maps/gt_grid.json'
  }
}

const ScenarioSelector = ({ onLoadScenario }) => {
  const [selectedScenario, setSelectedScenario] = useState('mercedes_benz')
  const [loading, setLoading] = useState(false)

  const handleLoad = async () => {
    setLoading(true)
    const config = SCENARIOS[selectedScenario]
    try {
      await onLoadScenario(config)
    } catch (error) {
      console.error('Failed to load scenario:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="scenario-selector">
      <select
        value={selectedScenario}
        onChange={(e) => setSelectedScenario(e.target.value)}
        className="scenario-select"
        disabled={loading}
      >
        {Object.entries(SCENARIOS).map(([key, scenario]) => (
          <option key={key} value={key}>
            {scenario.name}
          </option>
        ))}
      </select>

      <button
        onClick={handleLoad}
        className="load-btn"
        disabled={loading}
      >
        {loading ? 'Loading...' : 'Load Scenario'}
      </button>
    </div>
  )
}

export default ScenarioSelector
