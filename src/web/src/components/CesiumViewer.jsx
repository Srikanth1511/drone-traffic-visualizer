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
  createGooglePhotorealistic3DTileset,
  Rectangle,
  ScreenSpaceEventHandler,
  ScreenSpaceEventType
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
  statusMessage,
  facilityCells,
  onStatus,
  googleApiKey
}) => {
  const viewerRef = useRef(null)
  const cesiumContainerRef = useRef(null)
  const [selectedDroneId, setSelectedDroneId] = useState(null)
  const entitiesRef = useRef({})
  const googleTilesetRef = useRef(null)
  const facilityEntitiesRef = useRef([])
  const trailEntitiesRef = useRef({})
  const recentTrailEntitiesRef = useRef({})

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

  useEffect(() => {
    const apiKey = googleApiKey || import.meta.env.VITE_GOOGLE_MAPS_API_KEY
    if (apiKey) {
      GoogleMaps.defaultApiKey = apiKey
    }
  }, [googleApiKey])

  // Fly to scenario location
  useEffect(() => {
    if (scenario && viewerRef.current) {
      const { originLat, originLon } = scenario

      viewerRef.current.camera.flyTo({
        destination: Cartesian3.fromDegrees(originLon, originLat, 1200),
        orientation: {
          heading: CesiumMath.toRadians(0),
          pitch: CesiumMath.toRadians(-35),
          roll: 0.0
        },
        duration: 1.5
      })
    }
  }, [scenario])

  // Toggle Google Photorealistic 3D Tiles
  useEffect(() => {
    if (!viewerRef.current) return

    const viewer = viewerRef.current
    const apiKey = googleApiKey || import.meta.env.VITE_GOOGLE_MAPS_API_KEY

    const addTiles = async () => {
      if (googleTilesetRef.current) {
        googleTilesetRef.current.show = true
        return
      }

      try {
        if (!apiKey) {
          onStatus?.('error', 'Google 3D Tiles need VITE_GOOGLE_MAPS_API_KEY in src/web/.env.local (Map Tiles API + billing)')
          return
        }

        const tileset = await createGooglePhotorealistic3DTileset()
        viewer.scene.primitives.add(tileset)
        googleTilesetRef.current = tileset

        if (tileset.readyPromise) {
          tileset.readyPromise
            .then(() => onStatus?.('success', 'Google 3D Tiles loaded'))
            .catch((err) => {
              console.error('Google 3D Tiles failed to become ready', err)
              onStatus?.('error', 'Google 3D Tiles failed to load. Check API key and billing.')
              googleTilesetRef.current = null
            })
        }
      } catch (error) {
        console.error('Error loading Google 3D Tiles:', error)
        onStatus?.('error', 'Google 3D Tiles failed to load. Check API key and billing.')
        googleTilesetRef.current = null
      }
    }

    if (layers.googleTiles && apiKey) {
      addTiles()
    } else if (googleTilesetRef.current) {
      // Hide Google 3D Tiles
      googleTilesetRef.current.show = false
    }
  }, [layers.googleTiles, googleApiKey, onStatus])

  // Render facility map overlays
  useEffect(() => {
    if (!viewerRef.current) return

    const viewer = viewerRef.current
    const entities = viewer.entities

    facilityEntitiesRef.current.forEach((entity) => entities.remove(entity))
    facilityEntitiesRef.current = []

    if (!layers.facilityMap || !facilityCells?.length) return

    facilityCells.forEach((cell) => {
      const rectangle = Rectangle.fromDegrees(
        cell.lonMin,
        cell.latMin,
        cell.lonMax,
        cell.latMax
      )

      const entity = entities.add({
        id: `facility_${cell.lonMin}_${cell.latMin}`,
        name: 'Facility ceiling',
        rectangle: {
          coordinates: rectangle,
          material: Color.fromBytes(255, 193, 7, 90),
          outline: true,
          outlineColor: Color.fromBytes(255, 193, 7, 150),
          outlineWidth: 1
        },
        description: `Ceiling: ${cell.maxAltitudeAgl}m AGL`
      })

      facilityEntitiesRef.current.push(entity)
    })
  }, [facilityCells, layers.facilityMap])

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
    if (!viewerRef.current) return

    const viewer = viewerRef.current
    const entities = viewer.entities
    const modelUri = import.meta.env.VITE_DRONE_MODEL_URL
    const activeIds = new Set()

    if (layers.drones && telemetryData?.drones) {
      telemetryData.drones.forEach((drone) => {
        const entityId = `drone_${drone.id}`
        const position = Cartesian3.fromDegrees(drone.lon, drone.lat, drone.alt_msl)
        const heading = CesiumMath.toRadians(drone.heading)
        const hpr = new HeadingPitchRoll(heading, 0, 0)
        const orientation = Transforms.headingPitchRollQuaternion(position, hpr)

        let color = Color.LIME
        if (drone.health === 'WARNING') color = Color.YELLOW
        if (drone.health === 'ERROR') color = Color.RED
        if (drone.health === 'OFFLINE') color = Color.GRAY

        const isSelected = drone.id === selectedDroneId
        let entity = entitiesRef.current[entityId] || entities.getById(entityId)

        if (!entity) {
          entity = entities.add({ id: entityId })
        }

        entity.name = drone.id
        entity.position = position
        entity.orientation = orientation
        entity.droneData = drone

        if (modelUri) {
          entity.model = {
            uri: modelUri,
            minimumPixelSize: isSelected ? 60 : 40,
            maximumScale: 220,
            scale: 1.2,
            color: color.withAlpha(isSelected ? 1 : 0.9),
            silhouetteSize: isSelected ? 3 : 1.5,
            silhouetteColor: isSelected ? Color.WHITE : color.withAlpha(0.5)
          }
          entity.box = undefined
          entity.ellipsoid = undefined
        } else {
          entity.model = undefined
          entity.box = undefined
          entity.ellipsoid = {
            radii: isSelected ? new Cartesian3(12, 12, 4.5) : new Cartesian3(9, 9, 3),
            material: color.withAlpha(0.92),
            outline: true,
            outlineColor: Color.WHITE.withAlpha(isSelected ? 0.9 : 0.5),
            shadows: 1
          }
        }

        entity.label = isSelected ? {
          text: drone.id,
          font: '12px sans-serif',
          fillColor: Color.WHITE,
          outlineColor: Color.BLACK,
          outlineWidth: 2,
          style: 1,
          pixelOffset: new Cartesian2(0, -20),
          show: true
        } : undefined

        entity.polyline = isSelected ? {
          positions: [position, Cartesian3.fromDegrees(drone.lon, drone.lat, 0)],
          width: 1,
          material: Color.WHITE.withAlpha(0.5)
        } : undefined

        entitiesRef.current[entityId] = entity
        activeIds.add(entityId)
      })
    }

    // Remove drones that are no longer present or when the layer is disabled
    Object.keys(entitiesRef.current).forEach((key) => {
      if (key.startsWith('drone_') && (!layers.drones || !activeIds.has(key))) {
        if (entitiesRef.current[key]) {
          entities.remove(entitiesRef.current[key])
        }
        delete entitiesRef.current[key]
      }
    })
  }, [telemetryData, layers.drones, selectedDroneId])

  // Render drone trails
  useEffect(() => {
    if (!viewerRef.current) return

    const viewer = viewerRef.current
    const entities = viewer.entities
    const activeTrailIds = new Set()
    const activeRecentIds = new Set()

    if (layers.trails && droneTrails) {
      Object.entries(droneTrails).forEach(([droneId, trail]) => {
        if (trail.length < 2) return

        const trailPositions = Cartesian3.fromDegreesArrayHeights(
          trail.flatMap((pos) => [pos.lon, pos.lat, pos.alt])
        )

        const trailId = `trail_${droneId}`
        let trailEntity = trailEntitiesRef.current[trailId] || entities.getById(trailId)

        if (!trailEntity) {
          trailEntity = entities.add({
            id: trailId,
            name: `${droneId} Trail`,
            polyline: {
              positions: trailPositions,
              width: 4,
              material: Color.TEAL.withAlpha(0.7),
              clampToGround: false
            }
          })
        } else {
          trailEntity.polyline.positions = trailPositions
        }

        trailEntitiesRef.current[trailId] = trailEntity
        activeTrailIds.add(trailId)

        // Recent breadcrumb (last ~5s)
        const cutoff = telemetryData?.time ? telemetryData.time - 5 : null
        const recentPoints = cutoff !== null ? trail.filter((p) => p.time >= cutoff) : []

        if (recentPoints.length > 1) {
          const recentId = `trail_recent_${droneId}`
          const recentPositions = Cartesian3.fromDegreesArrayHeights(
            recentPoints.flatMap((pos) => [pos.lon, pos.lat, pos.alt])
          )

          let recentEntity = recentTrailEntitiesRef.current[recentId] || entities.getById(recentId)
          if (!recentEntity) {
            recentEntity = entities.add({
              id: recentId,
              name: `${droneId} Breadcrumb`,
              polyline: {
                positions: recentPositions,
                width: 6,
                material: new PolylineOutlineMaterialProperty({
                  color: Color.CHARTREUSE.withAlpha(0.9),
                  outlineColor: Color.WHITE.withAlpha(0.6),
                  outlineWidth: 2
                }),
                clampToGround: false
              }
            })
          } else {
            recentEntity.polyline.positions = recentPositions
          }

          recentTrailEntitiesRef.current[recentId] = recentEntity
          activeRecentIds.add(recentId)
        }
      })
    }

    const cleanupMap = (store, activeSet) => {
      Object.keys(store).forEach((id) => {
        if (!layers.trails || !activeSet.has(id)) {
          if (store[id]) {
            entities.remove(store[id])
          }
          delete store[id]
        }
      })
    }

    cleanupMap(trailEntitiesRef.current, activeTrailIds)
    cleanupMap(recentTrailEntitiesRef.current, activeRecentIds)
  }, [droneTrails, layers.trails, telemetryData])

  const droneCount = telemetryData?.drones?.length ?? 0
  const timeLabel = telemetryData?.time !== undefined ? `${telemetryData.time.toFixed(1)}s` : '—'

  return (
    <div className="cesium-viewer-container">
      <div ref={cesiumContainerRef} style={{ width: '100%', height: '100%' }} />

      <div className="viewer-overlay">
        <div className="status-bar">
          <div className="status-pill">Drones: {droneCount}</div>
          <div className="status-pill">Time: {timeLabel}</div>
          {statusMessage?.text && (
            <div className={`status-pill badge ${statusMessage.type}`}>
              {statusMessage.text}
            </div>
          )}
          {isLoading && <div className="status-pill badge loading">Loading…</div>}
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
