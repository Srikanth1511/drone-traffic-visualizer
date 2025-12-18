import React from 'react'
import './PlaybackControls.css'

const PlaybackControls = ({
  currentTime,
  duration,
  isPlaying,
  playbackSpeed,
  onTimeChange,
  onPlayPause,
  onReset,
  onSpeedChange
}) => {
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const handleSliderChange = (e) => {
    const newTime = parseFloat(e.target.value)
    onTimeChange(newTime)
  }

  const speedOptions = [0.5, 1.0, 2.0, 4.0, 8.0]

  return (
    <div className="playback-controls">
      <div className="controls-row">
        {/* Play/Pause Button */}
        <button
          className="control-btn play-pause"
          onClick={onPlayPause}
          title={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? '⏸' : '▶'}
        </button>

        {/* Reset Button */}
        <button className="control-btn" onClick={onReset} title="Reset">
          ⏮
        </button>

        {/* Timeline Slider */}
        <div className="timeline-container">
          <input
            type="range"
            min="0"
            max={duration}
            step="0.1"
            value={currentTime}
            onChange={handleSliderChange}
            className="timeline-slider"
          />
          <div className="time-display">
            <span>{formatTime(currentTime)}</span>
            <span>/</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>

        {/* Speed Selector */}
        <div className="speed-selector">
          <label>Speed:</label>
          <select
            value={playbackSpeed}
            onChange={(e) => onSpeedChange(parseFloat(e.target.value))}
            className="speed-select"
          >
            {speedOptions.map((speed) => (
              <option key={speed} value={speed}>
                {speed}x
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  )
}

export default PlaybackControls
