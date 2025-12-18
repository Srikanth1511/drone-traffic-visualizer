import React from 'react'
import './LayerToggles.css'

const LayerToggles = ({ layers, onToggle }) => {
  const layerConfig = [
    { key: 'drones', label: 'Drones', icon: '🚁' },
    { key: 'corridors', label: 'Corridors', icon: '🛣️' },
    { key: 'facilityMap', label: 'Facility Map', icon: '🗺️' },
    { key: 'trails', label: 'Trails', icon: '📍' },
    { key: 'googleTiles', label: 'Google 3D Tiles', icon: '🌎' }
  ]

  return (
    <div className="layer-toggles">
      <h3>Layers</h3>

      {layerConfig.map(({ key, label, icon }) => (
        <div key={key} className="layer-toggle-item">
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={layers[key]}
              onChange={() => onToggle(key)}
              className="toggle-checkbox"
            />
            <span className="toggle-slider"></span>
            <span className="layer-name">
              <span className="layer-icon">{icon}</span>
              {label}
            </span>
          </label>
        </div>
      ))}

      <div className="layer-info">
        <p className="info-text">
          Toggle layers to show/hide elements on the map.
        </p>
      </div>
    </div>
  )
}

export default LayerToggles
