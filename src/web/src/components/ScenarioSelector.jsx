import React, { useMemo, useState } from 'react'
import './ScenarioSelector.css'

const SCENARIOS = [
  {
    key: 'mercedes_benz',
    name: 'Mercedes-Benz Stadium (Demo)',
    description: 'Perimeter patrol with 3 drones (~5 min)',
    simulation_file: 'data/simulation_exports/benz_perimeter_patrol.json',
    origin_lat: 33.755489,
    origin_lon: -84.401993,
    facility_map_file: 'data/facility_maps/benz_grid.json'
  }
]

const ScenarioSelector = ({ onLoadScenario, loading }) => {
  const [selectedScenario, setSelectedScenario] = useState(SCENARIOS[0].key)
  const [simulationPath, setSimulationPath] = useState(SCENARIOS[0].simulation_file)
  const [facilityPath, setFacilityPath] = useState(SCENARIOS[0].facility_map_file || '')

  const activeScenario = useMemo(
    () => SCENARIOS.find((scenario) => scenario.key === selectedScenario) || SCENARIOS[0],
    [selectedScenario]
  )

  const handleLoad = async () => {
    const config = {
      ...activeScenario,
      simulation_file: simulationPath.trim(),
      facility_map_file: facilityPath.trim() || null
    }

    try {
      await onLoadScenario(config)
    } catch (error) {
      console.error('Failed to load scenario:', error)
    }
  }

  const handleScenarioChange = (key) => {
    setSelectedScenario(key)
    const scenario = SCENARIOS.find((item) => item.key === key)
    if (scenario) {
      setSimulationPath(scenario.simulation_file)
      setFacilityPath(scenario.facility_map_file || '')
    }
  }

  return (
    <div className="scenario-selector">
      <div className="selector-row">
        <div className="selector-label">Scenario</div>
        <select
          value={selectedScenario}
          onChange={(e) => handleScenarioChange(e.target.value)}
          className="scenario-select"
          disabled={loading}
        >
          {SCENARIOS.map((scenario) => (
            <option key={scenario.key} value={scenario.key}>
              {scenario.name}
            </option>
          ))}
        </select>
      </div>

      <p className="scenario-description">{activeScenario.description}</p>

      <label className="input-label" htmlFor="simulationPath">Simulation JSON</label>
      <input
        id="simulationPath"
        className="path-input"
        value={simulationPath}
        onChange={(e) => setSimulationPath(e.target.value)}
        placeholder="data/simulation_exports/demo.json"
        disabled={loading}
      />

      <label className="input-label" htmlFor="facilityPath">Facility map (optional)</label>
      <input
        id="facilityPath"
        className="path-input"
        value={facilityPath}
        onChange={(e) => setFacilityPath(e.target.value)}
        placeholder="data/facility_maps/demo.json"
        disabled={loading}
      />

      <div className="selector-actions">
        <div className="path-hint">Paths are resolved relative to the project root on the backend.</div>
        <button
          onClick={handleLoad}
          className="load-btn"
          disabled={loading}
        >
          {loading ? 'Loading...' : 'Load Scenario'}
        </button>
      </div>
    </div>
  )
}

export default ScenarioSelector
