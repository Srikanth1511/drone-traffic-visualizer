import React, { useEffect, useRef, useState } from 'react'
import {
  Viewer,
  Cartesian3,
  Color,
  HeadingPitchRoll,
  Transforms,
  PolylineOutlineMaterialProperty,
  Math as CesiumMath,
  Cartesian2,
  GoogleMaps,
  createGooglePhotorealistic3DTileset
} from 'cesium'
import 'cesium/Build/Cesium/Widgets/widgets.css'
import './CesiumViewer.css'

const CesiumViewer = ({
  scenario,
  telemetryData,
  droneTrails,
  layers,
  onDroneSelect,
  isLoading,
  statusMessage
}) => {
  const viewerRef = useRef(null)
  const cesiumContainerRef = useRef(null)
  const [selectedDroneId, setSelectedDroneId] = useState(null)
  const entitiesRef = useRef({})
  const corridorProgressRef = useRef({})
  const googleTilesetRef = useRef(null)

  // Initialize Cesium Viewer
  useEffect(() => {
    if (!cesiumContainerRef.current || viewerRef.current) return

    // Set Google Maps API key if available
    const googleApiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY
    if (googleApiKey) {
      GoogleMaps.defaultApiKey = googleApiKey
    }

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
      const { originLat, originLon } = scenario

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

  // Toggle Google Photorealistic 3D Tiles
  useEffect(() => {
    if (!viewerRef.current) return

    const viewer = viewerRef.current
    const googleApiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY

    if (layers.googleTiles && googleApiKey) {
      // Add Google 3D Tiles if not already added
      if (!googleTilesetRef.current) {
        try {
          const tileset = createGooglePhotorealistic3DTileset()
          viewer.scene.primitives.add(tileset)
          googleTilesetRef.current = tileset
        } catch (error) {
          console.error('Error loading Google 3D Tiles:', error)
        }
      } else {
        // Show existing tileset
        googleTilesetRef.current.show = true
      }
    } else if (googleTilesetRef.current) {
      // Hide Google 3D Tiles
      googleTilesetRef.current.show = false
    }
  }, [layers.googleTiles])

  // Render corridors with full path visibility
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

    // Add new corridor entities with enhanced visibility
    (scenario.corridors || []).forEach((corridor) => {
      const positions = corridor.centerline.map((point) =>
        Cartesian3.fromDegrees(point[1], point[0], point[2])
      )

      let baseColor = Color.CYAN
      if (corridor.type === 'parallel') baseColor = Color.SKYBLUE
      if (corridor.type === 'switching') baseColor = Color.MAGENTA

      // Full planned path (dimmer, shows complete route)
      const plannedEntity = entities.add({
        id: `corridor_planned_${corridor.id}`,
        name: `${corridor.id} (Planned)`,
        polyline: {
          positions: positions,
          width: 5,
          material: baseColor.withAlpha(0.3),
          clampToGround: false
        }
      })

      entitiesRef.current[`corridor_planned_${corridor.id}`] = plannedEntity

      // Active path (brighter, will show completed portions)
      const activeEntity = entities.add({
        id: `corridor_${corridor.id}`,
        name: corridor.id,
        polyline: {
          positions: positions,
          width: 6,
          material: new PolylineOutlineMaterialProperty({
            color: baseColor.withAlpha(0.8),
            outlineWidth: 2,
            outlineColor: Color.WHITE.withAlpha(0.5)
          }),
          clampToGround: false
        }
      })

      entitiesRef.current[`corridor_${corridor.id}`] = activeEntity
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
        box: {
          dimensions: isSelected ? new Cartesian3(10, 10, 3) : new Cartesian3(8, 8, 2.5),
          material: color,
          outline: true,
          outlineColor: isSelected ? Color.WHITE : Color.BLACK.withAlpha(0.5),
          outlineWidth: isSelected ? 2 : 1
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

  // Render drone trails
  useEffect(() => {
    if (!droneTrails || !viewerRef.current || !layers.trails) return

    const viewer = viewerRef.current
    const entities = viewer.entities

    // Remove old trail entities
    Object.keys(entitiesRef.current).forEach((key) => {
      if (key.startsWith('trail_')) {
        entities.remove(entitiesRef.current[key])
        delete entitiesRef.current[key]
      }
    })

    if (!layers.trails) return

    // Add trail polylines for each drone
    Object.entries(droneTrails).forEach(([droneId, trail]) => {
      if (trail.length < 2) return

      const positions = trail.map((pos) =>
        Cartesian3.fromDegrees(pos.lon, pos.lat, pos.alt)
      )

      // Trail color: teal/green for completed path
      const trailColor = Color.TEAL

      const entity = entities.add({
        id: `trail_${droneId}`,
        name: `${droneId} Trail`,
        polyline: {
          positions: positions,
          width: 4,
          material: trailColor.withAlpha(0.7),
          clampToGround: false
        }
      })

      entitiesRef.current[`trail_${droneId}`] = entity
    })
  }, [droneTrails, layers.trails])

  const droneCount = telemetryData?.drones?.length ?? 0
  const timeLabel = telemetryData?.time !== undefined ? `${telemetryData.time.toFixed(1)}s` : '—'

  return (
    <div className="cesium-viewer-container">
      <div ref={cesiumContainerRef} style={{ width: '100%', height: '100%' }} />

      <div className="viewer-overlay">
        <div className="status-bar">
          <div className="status-pill">Drones: {droneCount}</div>
          <div className="status-pill">Time: {timeLabel}</div>
          <div className="status-pill secondary">{scenario ? scenario.name : 'No scenario loaded'}</div>
          {statusMessage?.text && (
            <div className={`status-pill badge ${statusMessage.type}`}>
              {statusMessage.text}
            </div>
          )}
          {isLoading && <div className="status-pill badge loading">Loading telemetry…</div>}
        </div>
      </div>

      {!scenario && (
        <div className="empty-overlay">
          <div className="empty-title">Awaiting scenario</div>
          <p>Load a scenario from the header to start visualizing drone traffic.</p>
        </div>
      )}
    </div>
  )
}

export default CesiumViewer
