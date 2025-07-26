import React from 'react';

interface Word {
  text: string;
  start: number;
  end: number;
  confidence: number;
}

interface Segment {
  id: string;
  text: string;
  start: number;
  end: number;
  words: Word[];
}

interface WordTimingDisplayProps {
  segment: Segment;
  currentTime: number;
  onSeek?: (time: number) => void;
}

export const WordTimingDisplay: React.FC<WordTimingDisplayProps> = ({
  segment,
  currentTime,
  onSeek,
}) => {
  const isSegmentActive = currentTime >= segment.start && currentTime <= segment.end;
  
  if (!isSegmentActive) {
    return null;
  }

  const getWordProgress = (word: Word) => {
    if (currentTime < word.start) return 0;
    if (currentTime > word.end) return 100;
    
    const duration = word.end - word.start;
    const elapsed = currentTime - word.start;
    return Math.min(100, Math.max(0, (elapsed / duration) * 100));
  };

  const getSegmentProgress = () => {
    if (currentTime < segment.start) return 0;
    if (currentTime > segment.end) return 100;
    
    const duration = segment.end - segment.start;
    const elapsed = currentTime - segment.start;
    return Math.min(100, Math.max(0, (elapsed / duration) * 100));
  };

  return (
    <div className="word-timing-display">
      <div className="segment-header">
        <span className="segment-text">{segment.text}</span>
        <span className="segment-time">
          {segment.start.toFixed(1)}s - {segment.end.toFixed(1)}s
        </span>
      </div>
      
      {/* Overall segment progress bar */}
      <div className="segment-progress-container">
        <div className="segment-progress-track">
          <div 
            className="segment-progress-fill"
            style={{ width: `${getSegmentProgress()}%` }}
          />
        </div>
      </div>
      
      {/* Word-level timing visualization */}
      <div className="words-timing-container">
        {segment.words.map((word, index) => {
          const progress = getWordProgress(word);
          const isWordActive = currentTime >= word.start && currentTime <= word.end;
          
          return (
            <div 
              key={index}
              className={`word-timing-item ${isWordActive ? 'active' : ''}`}
              onClick={() => onSeek?.(word.start)}
            >
              <div className="word-text">{word.text}</div>
              <div className="word-timing-info">
                <span className="word-time">
                  {word.start.toFixed(1)}s - {word.end.toFixed(1)}s
                </span>
                <span className="word-confidence">
                  {(word.confidence * 100).toFixed(0)}%
                </span>
              </div>
              
              {/* Red progress line for this word */}
              <div className="word-progress-container">
                <div className="word-progress-track">
                  <div 
                    className="word-progress-fill"
                    style={{ width: `${progress}%` }}
                  />
                  {/* Progress handle */}
                  <div 
                    className="word-progress-handle"
                    style={{ left: `${progress}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};