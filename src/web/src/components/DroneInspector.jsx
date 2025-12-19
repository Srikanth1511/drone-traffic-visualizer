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

  const formatNumber = (value, digits = 1, fallback = '—') =>
    Number.isFinite(value) ? value.toFixed(digits) : fallback

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

  const batteryLevel = Number.isFinite(drone?.payload?.battery)
    ? Math.round(drone.payload.battery * 100)
    : null

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
          <span className="value">{formatNumber(drone.lat, 6)}°</span>
        </div>
        <div className="data-row">
          <span className="label">Longitude:</span>
          <span className="value">{formatNumber(drone.lon, 6)}°</span>
        </div>
        <div className="data-row">
          <span className="label">Alt (MSL):</span>
          <span className="value">{formatNumber(drone.alt_msl)} m</span>
        </div>
        <div className="data-row">
          <span className="label">Alt (AGL):</span>
          <span className="value">{formatNumber(drone.alt_agl)} m</span>
        </div>
      </div>

      <div className="inspector-section">
        <h3>Flight Data</h3>
        <div className="data-row">
          <span className="label">Heading:</span>
          <span className="value">{formatNumber(drone.heading)}°</span>
        </div>
        <div className="data-row">
          <span className="label">Speed:</span>
          <span className="value">{formatNumber(drone.speed)} m/s</span>
        </div>
        <div className="data-row">
          <span className="label">V-Speed:</span>
          <span className="value">{formatNumber(drone.verticalSpeed)} m/s</span>
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
            {formatNumber(drone.linkQuality * 100, 0)}%
          </span>
        </div>
        {batteryLevel !== null && (
          <div className="data-row battery-row">
            <span className="label">Battery:</span>
            <div className="battery-meter">
              <div className="battery-fill" style={{ width: `${batteryLevel}%` }} />
              <span className="battery-text">{batteryLevel}%</span>
            </div>
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
