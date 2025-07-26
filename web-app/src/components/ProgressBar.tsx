import React from 'react';

interface Segment {
  id: string;
  text: string;
  start: number;
  end: number;
}

interface ProgressBarProps {
  segments: Segment[];
  currentTime: number;
  duration: number;
  onSeek: (time: number) => void;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  segments,
  currentTime,
  duration,
  onSeek,
}) => {
  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percentage = clickX / rect.width;
    const newTime = percentage * duration;
    onSeek(newTime);
  };

  const getCurrentSegment = () => {
    return segments.find(segment => 
      currentTime >= segment.start && currentTime <= segment.end
    );
  };

  const currentSegment = getCurrentSegment();
  const progressPercentage = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="progress-bar-container">
      <div className="progress-bar-wrapper" onClick={handleClick}>
        {/* Segment blocks */}
        <div className="segments-track">
          {segments.map((segment, index) => {
            const startPercent = (segment.start / duration) * 100;
            const widthPercent = ((segment.end - segment.start) / duration) * 100;
            const isActive = currentSegment?.id === segment.id;
            
            return (
              <div
                key={segment.id}
                className={`segment-block ${isActive ? 'active' : ''}`}
                style={{
                  left: `${startPercent}%`,
                  width: `${widthPercent}%`,
                }}
                title={`${segment.text} (${segment.start.toFixed(1)}s-${segment.end.toFixed(1)}s)`}
              >
                <span className="segment-number">{index + 1}</span>
              </div>
            );
          })}
        </div>
        
        {/* Progress indicator */}
        <div className="progress-track">
          <div 
            className="progress-fill" 
            style={{ width: `${progressPercentage}%` }}
          />
          <div 
            className="progress-handle" 
            style={{ left: `${progressPercentage}%` }}
          />
        </div>
      </div>
      
      {/* Current segment info */}
      {currentSegment && (
        <div className="current-segment-info">
          <span className="segment-text">
            "{currentSegment.text}"
          </span>
          <span className="segment-timing">
            {currentTime.toFixed(1)}s / {duration.toFixed(1)}s
          </span>
        </div>
      )}
    </div>
  );
};