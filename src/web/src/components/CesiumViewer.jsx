import React, { useEffect, useRef, useState } from 'react'
import { Viewer, Entity, PolylineGraphics, PolygonGraphics } from 'resium'
import {
  Cartesian3,
  Color,
  HeadingPitchRoll,
  Transforms,
  PolylineOutlineMaterialProperty,
  Math as CesiumMath
} from 'cesium'
import './CesiumViewer.css'

const CesiumViewer = ({ scenario, telemetryData, layers, onDroneSelect }) => {
  const viewerRef = useRef(null)
  const [selectedDroneId, setSelectedDroneId] = useState(null)

  // Initialize camera position when scenario loads
  useEffect(() => {
    if (scenario && viewerRef.current && viewerRef.current.cesiumElement) {
      const viewer = viewerRef.current.cesiumElement
      const { originLat, originLon } = scenario.scenario

      // Set camera to look at scenario origin
      viewer.camera.flyTo({
        destination: Cartesian3.fromDegrees(originLon, originLat, 1500),
        orientation: {
          heading: CesiumMath.toRadians(0),
          pitch: CesiumMath.toRadians(-45),
          roll: 0.0
        },
        duration: 2.0
      })
    }
  }, [scenario])

  // Handle drone click
  const handleDroneClick = (drone) => {
    setSelectedDroneId(drone.id)
    onDroneSelect(drone)
  }

  // Render drones
  const renderDrones = () => {
    if (!telemetryData || !layers.drones) return null

    return telemetryData.drones.map((drone) => {
      const position = Cartesian3.fromDegrees(
        drone.lon,
        drone.lat,
        drone.alt_msl
      )

      // Calculate orientation from heading
      const heading = CesiumMath.toRadians(drone.heading)
      const pitch = 0
      const roll = 0
      const hpr = new HeadingPitchRoll(heading, pitch, roll)
      const orientation = Transforms.headingPitchRollQuaternion(position, hpr)

      // Color based on health
      let color = Color.LIME
      if (drone.health === 'WARNING') color = Color.YELLOW
      if (drone.health === 'ERROR') color = Color.RED
      if (drone.health === 'OFFLINE') color = Color.GRAY

      const isSelected = drone.id === selectedDroneId

      return (
        <Entity
          key={drone.id}
          position={position}
          orientation={orientation}
          onClick={() => handleDroneClick(drone)}
          name={drone.id}
          description={`Altitude: ${drone.alt_agl.toFixed(1)}m AGL<br/>Speed: ${drone.speed.toFixed(1)} m/s`}
        >
          {/* Cone representing drone */}
          <Entity.cylinder
            length={isSelected ? 8 : 6}
            topRadius={0}
            bottomRadius={isSelected ? 4 : 3}
            material={color}
            outline={isSelected}
            outlineColor={Color.WHITE}
          />

          {/* Label */}
          <Entity.label
            text={drone.id}
            font="12px sans-serif"
            fillColor={Color.WHITE}
            outlineColor={Color.BLACK}
            outlineWidth={2}
            style={1}
            pixelOffset={new Cartesian3(0, -20, 0)}
            show={isSelected}
          />

          {/* Vertical line to ground */}
          {isSelected && (
            <Entity.polyline
              positions={[
                position,
                Cartesian3.fromDegrees(drone.lon, drone.lat, 0)
              ]}
              width={1}
              material={Color.WHITE.withAlpha(0.5)}
            />
          )}
        </Entity>
      )
    })
  }

  // Render corridors
  const renderCorridors = () => {
    if (!scenario || !layers.corridors) return null

    return scenario.corridors.map((corridor) => {
      // Convert centerline to Cartesian3 positions
      const positions = corridor.centerline.map((point) =>
        Cartesian3.fromDegrees(point[1], point[0], point[2])
      )

      // Color by corridor type
      let color = Color.CYAN
      if (corridor.type === 'parallel') color = Color.BLUE
      if (corridor.type === 'switching') color = Color.MAGENTA

      return (
        <Entity key={corridor.id} name={corridor.id}>
          <PolylineGraphics
            positions={positions}
            width={3}
            material={new PolylineOutlineMaterialProperty({
              color: color.withAlpha(0.6),
              outlineWidth: 1,
              outlineColor: Color.WHITE.withAlpha(0.3)
            })}
            clampToGround={false}
          />
        </Entity>
      )
    })
  }

  // Render facility map grid (simplified for MVP)
  const renderFacilityMap = () => {
    if (!scenario || !layers.facilityMap) return null

    // For MVP, render a simple grid overlay
    // Phase 2 will fetch actual FAA facility map data
    return null
  }

  return (
    <div className="cesium-viewer-container">
      <Viewer
        ref={viewerRef}
        full
        timeline={false}
        animation={false}
        baseLayerPicker={false}
        geocoder={false}
        homeButton={false}
        infoBox={true}
        sceneModePicker={false}
        selectionIndicator={true}
        navigationHelpButton={false}
      >
        {renderDrones()}
        {renderCorridors()}
        {renderFacilityMap()}
      </Viewer>

      {/* Status overlay */}
      <div className="viewer-overlay">
        {telemetryData && (
          <div className="status-bar">
            <div>Drones: {telemetryData.drones.length}</div>
            <div>Time: {telemetryData.time.toFixed(1)}s</div>
          </div>
        )}
      </div>
    </div>
  )
}

export default CesiumViewer
