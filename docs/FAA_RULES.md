# FAA Rules and UAS Operating Constraints (Quick Reference)

This visualizer highlights facility ceilings and above-ground-level (AGL) restrictions so operators can keep playback and live telemetry within regulatory limits. Key points to consider when interpreting the map overlays:

## Core altitude rules (14 CFR § 107.51)
- Small UAS must remain at or below 400 ft (≈122 m) AGL unless operating within 400 ft of a structure.
- Minimum distance from clouds: 500 ft below and 2,000 ft horizontally; visibility must be at least 3 statute miles.
- Maximum groundspeed: 87 knots (≈100 mph / 44.7 m/s).
- Night operations require anti-collision lighting visible for at least 3 statute miles (waivers may apply).

## Airspace awareness
- FAA UAS Facility Maps show recommended maximum AGL ceilings near airports and controlled airspace. The visualizer uses cached facility grid cells to colorize the map and warn when a drone exceeds the ceiling.
- Actual authorization for controlled airspace requires LAANC or ATC coordination; facility maps are advisory but informative for planning and simulation playback.
- Keep-out zones such as Temporary Flight Restrictions (TFRs) and Special Use Airspace (SUA) should be overlaid when available; plan future adapters to ingest UDDS/NASR datasets.

## Remote ID considerations
- Remote ID broadcasts include geodetic altitude, height above takeoff, speed, and heading. The planned adapter should map these fields into the unified schema alongside health and link quality.
- Operations without Remote ID must occur in FAA-Recognized Identification Areas (FRIAs) or under exceptions provided by the FAA.

## Geospatial conversions and altitude services
- Many telemetry streams provide mean sea level (MSL) altitude. The visualizer subtracts ground elevation from cached facility cells to compute AGL.
- When ground elevation is unknown, the system falls back to a configurable default but should be paired with terrain data (e.g., FAA facility maps or DEM sources) for accuracy.

## Operational best practices for the visualizer
- Warn the operator when AGL altitude exceeds the facility ceiling at the current grid cell.
- Highlight drones with low battery or degraded link quality so operators can deconflict paths early.
- Keep basemap keys and sensitive configuration server-side to match the simulator’s security posture.
- Provide clear logging and deterministic playback so analysts can reproduce flights and validate compliance.
