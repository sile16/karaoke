import React from 'react';

interface Syllable {
  text: string;
  start: number;
  end: number;
}

interface Word {
  text: string;
  start: number;
  end: number;
  confidence: number;
  syllables: Syllable[];
  translation?: {
    literal: string;
    contextual?: string;
  };
}

interface Segment {
  id: string;
  text: string;
  start: number;
  end: number;
  words: Word[];
}

interface LyricsDisplayProps {
  segments: Segment[];
  currentTime: number;
  showTranslations: boolean;
  viewMode: 'karaoke' | 'syllables' | 'simple';
  onSeek?: (time: number) => void;
}

export const LyricsDisplay: React.FC<LyricsDisplayProps> = ({
  segments,
  currentTime,
  showTranslations,
  viewMode,
  onSeek,
}) => {
  const isWordActive = (word: Word) => {
    return currentTime >= word.start && currentTime <= word.end;
  };

  const isSyllableActive = (syllable: Syllable) => {
    return currentTime >= syllable.start && currentTime <= syllable.end;
  };

  const isSegmentActive = (segment: Segment) => {
    return currentTime >= segment.start && currentTime <= segment.end;
  };

  const renderSyllableView = (word: Word) => {
    return (
      <span 
        className={`word ${isWordActive(word) ? 'active' : ''}`}
        onClick={() => onSeek?.(word.start)}
        style={{ cursor: 'pointer' }}
      >
        {word.syllables.map((syllable, index) => (
          <span
            key={index}
            className={`syllable ${isSyllableActive(syllable) ? 'syllable-active' : ''}`}
          >
            {syllable.text}
            {index < word.syllables.length - 1 && '-'}
          </span>
        ))}
        {showTranslations && word.translation && (
          <span className="translation">
            ({word.translation.literal})
          </span>
        )}
      </span>
    );
  };

  const renderKaraokeView = (word: Word) => {
    return (
      <span 
        className={`word ${isWordActive(word) ? 'karaoke-active' : ''}`}
        onClick={() => onSeek?.(word.start)}
        style={{ cursor: 'pointer' }}
      >
        {word.text}
        {showTranslations && word.translation && (
          <span className="translation">
            ({word.translation.literal})
          </span>
        )}
      </span>
    );
  };

  const renderSimpleView = (word: Word) => {
    return (
      <span 
        className="word"
        onClick={() => onSeek?.(word.start)}
        style={{ cursor: 'pointer' }}
      >
        {word.text}
        {showTranslations && word.translation && (
          <span className="translation">
            ({word.translation.literal})
          </span>
        )}
      </span>
    );
  };

  return (
    <div className="lyrics-display">
      {segments.map((segment) => (
        <div
          key={segment.id}
          className={`segment ${isSegmentActive(segment) ? 'segment-active' : ''}`}
        >
          <div className="segment-text">
            {segment.words.map((word, index) => (
              <React.Fragment key={index}>
                {viewMode === 'syllables' && renderSyllableView(word)}
                {viewMode === 'karaoke' && renderKaraokeView(word)}
                {viewMode === 'simple' && renderSimpleView(word)}
                {index < segment.words.length - 1 && ' '}
              </React.Fragment>
            ))}
          </div>
          
          {/* Show timing info for debugging */}
          <div className="segment-timing">
            {segment.start.toFixed(1)}s - {segment.end.toFixed(1)}s
          </div>
        </div>
      ))}
    </div>
  );
};