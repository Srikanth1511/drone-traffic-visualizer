import React from 'react'
import './DroneInspector.css'

const DroneInspector = ({ drone }) => {
  if (!drone) {
    return (
      <div className="drone-inspector">
        <h2>Drone Inspector</h2>
        <p className="no-selection">Select a drone to view details</p>
      </div>
    )
  }

  const getHealthColor = (health) => {
    switch (health) {
      case 'OK':
        return '#4CAF50'
      case 'WARNING':
        return '#FFC107'
      case 'ERROR':
        return '#F44336'
      case 'OFFLINE':
        return '#9E9E9E'
      default:
        return '#666'
    }
  }

  const getHealthIndicator = (health) => {
    return (
      <span
        className="health-indicator"
        style={{ backgroundColor: getHealthColor(health) }}
      />
    )
  }

  return (
    <div className="drone-inspector">
      <h2>Drone Inspector</h2>

      <div className="inspector-section">
        <div className="drone-id">
          {getHealthIndicator(drone.health)}
          <span className="id-text">{drone.id}</span>
        </div>
      </div>

      <div className="inspector-section">
        <h3>Position</h3>
        <div className="data-row">
          <span className="label">Latitude:</span>
          <span className="value">{drone.lat.toFixed(6)}°</span>
        </div>
        <div className="data-row">
          <span className="label">Longitude:</span>
          <span className="value">{drone.lon.toFixed(6)}°</span>
        </div>
        <div className="data-row">
          <span className="label">Alt (MSL):</span>
          <span className="value">{drone.alt_msl.toFixed(1)} m</span>
        </div>
        <div className="data-row">
          <span className="label">Alt (AGL):</span>
          <span className="value">{drone.alt_agl.toFixed(1)} m</span>
        </div>
      </div>

      <div className="inspector-section">
        <h3>Flight Data</h3>
        <div className="data-row">
          <span className="label">Heading:</span>
          <span className="value">{drone.heading.toFixed(1)}°</span>
        </div>
        <div className="data-row">
          <span className="label">Speed:</span>
          <span className="value">{drone.speed.toFixed(1)} m/s</span>
        </div>
        <div className="data-row">
          <span className="label">V-Speed:</span>
          <span className="value">{drone.verticalSpeed?.toFixed(1) || '0.0'} m/s</span>
        </div>
      </div>

      <div className="inspector-section">
        <h3>Status</h3>
        <div className="data-row">
          <span className="label">Health:</span>
          <span className="value" style={{ color: getHealthColor(drone.health) }}>
            {drone.health}
          </span>
        </div>
        <div className="data-row">
          <span className="label">Link Quality:</span>
          <span className="value">
            {(drone.linkQuality * 100).toFixed(0)}%
          </span>
        </div>
        {drone.payload && (
          <div className="data-row">
            <span className="label">Battery:</span>
            <span className="value">
              {(drone.payload.battery * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>

      {drone.corridorId && (
        <div className="inspector-section">
          <h3>Navigation</h3>
          <div className="data-row">
            <span className="label">Corridor:</span>
            <span className="value">{drone.corridorId}</span>
          </div>
          {drone.routeIndex !== undefined && (
            <div className="data-row">
              <span className="label">Route Index:</span>
              <span className="value">{drone.routeIndex}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default DroneInspector
