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
  onSpeedChange,
  onStepBackward,
  onStepForward,
  isLoading,
  isReady
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
  const disabled = !isReady || isLoading
  const progressPercent = duration ? Math.min(100, Math.round((currentTime / duration) * 100)) : 0

  return (
    <div className="playback-controls">
      <div className="controls-row">
        <div className="control-group">
          <button
            className="control-btn play-pause"
            onClick={onPlayPause}
            title={isPlaying ? 'Pause' : 'Play'}
            disabled={disabled}
          >
            {isPlaying ? '⏸' : '▶'}
          </button>

          <button className="control-btn" onClick={onReset} title="Reset" disabled={disabled}>
            ⏮ Reset
          </button>

          <button className="control-btn ghost" onClick={onStepBackward} title="Step backward" disabled={disabled}>
            -2s
          </button>
          <button className="control-btn ghost" onClick={onStepForward} title="Step forward" disabled={disabled}>
            +2s
          </button>
        </div>

        <div className="timeline-container">
          <div className="timeline-labels">
            <span>{formatTime(currentTime)}</span>
            <span className="muted">{progressPercent}%</span>
            <span>{formatTime(duration)}</span>
          </div>
          <input
            type="range"
            min="0"
            max={duration || 0}
            step="0.1"
            value={currentTime}
            onChange={handleSliderChange}
            className="timeline-slider"
            disabled={disabled}
          />
        </div>

        <div className="speed-selector">
          <label>Speed</label>
          <div className="speed-options">
            {speedOptions.map((speed) => (
              <button
                key={speed}
                onClick={() => onSpeedChange(speed)}
                className={`speed-chip ${playbackSpeed === speed ? 'active' : ''}`}
                disabled={disabled}
              >
                {speed}x
              </button>
            ))}
          </div>
        </div>
      </div>

      {!isReady && (
        <div className="controls-helper">Load a scenario to enable playback controls.</div>
      )}
      {isLoading && isReady && (
        <div className="controls-helper">Syncing telemetry…</div>
      )}
    </div>
  )
}

export default PlaybackControls
