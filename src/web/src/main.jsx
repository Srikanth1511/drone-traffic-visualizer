import React from 'react'
import ReactDOM from 'react-dom/client'
import './styles.css'

const presets = [
  { label: 'Mercedes-Benz Stadium', coords: [33.755489, -84.401993], radiusKm: 3 },
  { label: 'Georgia Tech', coords: [33.7736, -84.4022], radiusKm: 3 },
]

function App() {
  return (
    <div className="app">
      <header>
        <h1>Drone Traffic Visualizer</h1>
        <p>Simulation playback console with facility ceiling awareness.</p>
        <div className="controls">
          <label htmlFor="location">Location preset</label>
          <select id="location">
            {presets.map((preset) => (
              <option key={preset.label} value={preset.label}>
                {preset.label}
              </option>
            ))}
          </select>
        </div>
      </header>
      <main>
        <section className="panel">
          <h2>Layer toggles</h2>
          <ul>
            <li><input type="checkbox" defaultChecked /> Drones</li>
            <li><input type="checkbox" defaultChecked /> Facility grid</li>
            <li><input type="checkbox" /> Corridors</li>
          </ul>
        </section>
        <section className="panel">
          <h2>Playback</h2>
          <p>Hook this UI to the FastAPI telemetry endpoint for live data.</p>
          <div className="controls">
            <button>Play/Pause</button>
            <label>Speed <input type="range" min="0.5" max="8" step="0.5" defaultValue="1" /></label>
          </div>
        </section>
        <section className="panel">
          <h2>Inspector</h2>
          <p>Select a drone to view ID, altitude (MSL/AGL), heading, speed, and battery.</p>
        </section>
      </main>
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />)
