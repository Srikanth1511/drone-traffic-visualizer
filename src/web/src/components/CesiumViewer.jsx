import React, { useEffect, useRef, useState } from 'react'
import {
  Viewer,
  Cartesian3,
  Color,
  HeadingPitchRoll,
  Transforms,
  PolylineOutlineMaterialProperty,
  Math as CesiumMath,
  Cartesian2
} from 'cesium'
import 'cesium/Build/Cesium/Widgets/widgets.css'
import './CesiumViewer.css'

const CesiumViewer = ({ scenario, telemetryData, layers, onDroneSelect }) => {
  const viewerRef = useRef(null)
  const cesiumContainerRef = useRef(null)
  const [selectedDroneId, setSelectedDroneId] = useState(null)
  const entitiesRef = useRef({})

  // Initialize Cesium Viewer
  useEffect(() => {
    if (!cesiumContainerRef.current || viewerRef.current) return

    const viewer = new Viewer(cesiumContainerRef.current, {
      timeline: false,
      animation: false,
      baseLayerPicker: false,
      geocoder: false,
      homeButton: false,
      infoBox: true,
      sceneModePicker: false,
      selectionIndicator: true,
      navigationHelpButton: false,
      shouldAnimate: false
    })

    viewerRef.current = viewer

    // Handle entity selection
    viewer.selectedEntityChanged.addEventListener((entity) => {
      if (entity && entity.droneData) {
        setSelectedDroneId(entity.droneData.id)
        onDroneSelect(entity.droneData)
      }
    })

    return () => {
      if (viewerRef.current) {
        viewerRef.current.destroy()
        viewerRef.current = null
      }
    }
  }, [onDroneSelect])

  // Fly to scenario location
  useEffect(() => {
    if (scenario && viewerRef.current) {
      const { originLat, originLon } = scenario.scenario

      viewerRef.current.camera.flyTo({
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

  // Render corridors
  useEffect(() => {
    if (!scenario || !viewerRef.current) return

    const viewer = viewerRef.current
    const entities = viewer.entities

    // Remove old corridor entities
    Object.keys(entitiesRef.current).forEach((key) => {
      if (key.startsWith('corridor_')) {
        entities.remove(entitiesRef.current[key])
        delete entitiesRef.current[key]
      }
    })

    if (!layers.corridors) return

    // Add new corridor entities
    scenario.corridors.forEach((corridor) => {
      const positions = corridor.centerline.map((point) =>
        Cartesian3.fromDegrees(point[1], point[0], point[2])
      )

      let color = Color.CYAN
      if (corridor.type === 'parallel') color = Color.BLUE
      if (corridor.type === 'switching') color = Color.MAGENTA

      const entity = entities.add({
        id: `corridor_${corridor.id}`,
        name: corridor.id,
        polyline: {
          positions: positions,
          width: 3,
          material: new PolylineOutlineMaterialProperty({
            color: color.withAlpha(0.6),
            outlineWidth: 1,
            outlineColor: Color.WHITE.withAlpha(0.3)
          }),
          clampToGround: false
        }
      })

      entitiesRef.current[`corridor_${corridor.id}`] = entity
    })
  }, [scenario, layers.corridors])

  // Render drones
  useEffect(() => {
    if (!telemetryData || !viewerRef.current) return

    const viewer = viewerRef.current
    const entities = viewer.entities

    // Remove old drone entities
    Object.keys(entitiesRef.current).forEach((key) => {
      if (key.startsWith('drone_')) {
        entities.remove(entitiesRef.current[key])
        delete entitiesRef.current[key]
      }
    })

    if (!layers.drones) return

    // Add new drone entities
    telemetryData.drones.forEach((drone) => {
      const position = Cartesian3.fromDegrees(drone.lon, drone.lat, drone.alt_msl)

      const heading = CesiumMath.toRadians(drone.heading)
      const hpr = new HeadingPitchRoll(heading, 0, 0)
      const orientation = Transforms.headingPitchRollQuaternion(position, hpr)

      let color = Color.LIME
      if (drone.health === 'WARNING') color = Color.YELLOW
      if (drone.health === 'ERROR') color = Color.RED
      if (drone.health === 'OFFLINE') color = Color.GRAY

      const isSelected = drone.id === selectedDroneId

      const entity = entities.add({
        id: `drone_${drone.id}`,
        name: drone.id,
        position: position,
        orientation: orientation,
        droneData: drone,
        cylinder: {
          length: isSelected ? 8 : 6,
          topRadius: 0,
          bottomRadius: isSelected ? 4 : 3,
          material: color,
          outline: isSelected,
          outlineColor: Color.WHITE
        },
        label: isSelected ? {
          text: drone.id,
          font: '12px sans-serif',
          fillColor: Color.WHITE,
          outlineColor: Color.BLACK,
          outlineWidth: 2,
          style: 1,
          pixelOffset: new Cartesian2(0, -20),
          show: true
        } : undefined,
        polyline: isSelected ? {
          positions: [position, Cartesian3.fromDegrees(drone.lon, drone.lat, 0)],
          width: 1,
          material: Color.WHITE.withAlpha(0.5)
        } : undefined
      })

      entitiesRef.current[`drone_${drone.id}`] = entity
    })
  }, [telemetryData, layers.drones, selectedDroneId])

  return (
    <div className="cesium-viewer-container">
      <div ref={cesiumContainerRef} style={{ width: '100%', height: '100%' }} />

      {telemetryData && (
        <div className="viewer-overlay">
          <div className="status-bar">
            <div>Drones: {telemetryData.drones.length}</div>
            <div>Time: {telemetryData.time.toFixed(1)}s</div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CesiumViewer
