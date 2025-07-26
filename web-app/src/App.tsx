import React, { useState, useEffect } from 'react';
import { AudioPlayer } from './components/AudioPlayer';
import { LyricsDisplay } from './components/LyricsDisplay';
import { ControlPanel } from './components/ControlPanel';
import { ProgressBar } from './components/ProgressBar';
import { WordTimingDisplay } from './components/WordTimingDisplay';
import { DownloadManager } from './components/DownloadManager';
import { SongManager } from './components/SongManager';
import './App.css';

// Load the smart-processed lyrics data (confidence-based ElevenLabs)
const loadAlignedData = async () => {
  try {
    const response = await fetch('/data/processed/yana_smart_processed.json');
    return await response.json();
  } catch (error) {
    console.error('Failed to load smart processed data:', error);
    // Fallback to Claude aligned data
    try {
      const response = await fetch('/data/processed/yana_claude_aligned.json');
      return await response.json();
    } catch (error2) {
      console.error('Failed to load fallback data:', error2);
      return sampleLyricsData;
    }
  }
};

// Fallback sample data
const sampleLyricsData = {
  metadata: {
    title: "Turkish Song Sample", 
    artists: ["Artist"],
    duration: 147.0,
    language: "tr",
    alignment_method: "sample",
    alignment_quality: 0.0
  },
  segments: [
    {
      id: "seg_001",
      text: "Sample Turkish text",
      start: 0.5,
      end: 4.0,
      words: [
        {
          text: "Sample",
          start: 0.5,
          end: 1.5,
          confidence: 0.8,
          syllables: [
            { text: "Sam", start: 0.5, end: 1.0 },
            { text: "ple", start: 1.0, end: 1.5 }
          ],
          translation: { literal: "example", contextual: "example" }
        }
      ]
    }
  ]
};

function App() {
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [viewMode, setViewMode] = useState<'karaoke' | 'syllables' | 'simple'>('karaoke');
  const [showTranslations, setShowTranslations] = useState(true);
  const [lyricsData, setLyricsData] = useState(sampleLyricsData);
  const [activeTab, setActiveTab] = useState<'lyrics' | 'downloads' | 'manage'>('lyrics');
  const audioPlayerRef = React.useRef<any>(null);

  // Load the actual lyrics data
  useEffect(() => {
    // Load the smart-processed lyrics data (confidence-based ElevenLabs)
    loadAlignedData()
      .then(data => setLyricsData(data))
      .catch(error => {
        console.log('Could not load smart processed data:', error);
      });
  }, []);

  const handleTimeUpdate = (time: number) => {
    setCurrentTime(time);
  };

  const handleLoadedMetadata = (audioDuration: number) => {
    setDuration(audioDuration);
  };

  const handleSeek = (time: number) => {
    setCurrentTime(time);
    // Seek the actual audio player
    if (audioPlayerRef.current) {
      audioPlayerRef.current.seekToTime(time);
    }
  };

  const handleSongSelect = (song: any) => {
    // Switch to lyrics tab when a song is selected
    setActiveTab('lyrics');
    // Here you could load the selected song's data
    console.log('Selected song:', song);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Turkish Lyrics Learning</h1>
        <p>Learn Turkish through synchronized lyrics</p>
        
        {/* Tab navigation */}
        <div className="tab-navigation">
          <button
            className={`tab-button ${activeTab === 'lyrics' ? 'active' : ''}`}
            onClick={() => setActiveTab('lyrics')}
          >
            🎤 Karaoke Player
          </button>
          <button
            className={`tab-button ${activeTab === 'manage' ? 'active' : ''}`}
            onClick={() => setActiveTab('manage')}
          >
            🎵 Song Manager
          </button>
          <button
            className={`tab-button ${activeTab === 'downloads' ? 'active' : ''}`}
            onClick={() => setActiveTab('downloads')}
          >
            📁 Simple Library
          </button>
        </div>
      </header>

      <main className="app-main">
        {activeTab === 'lyrics' && (
          <>
            <div className="current-song-info">
              <h2>{lyricsData.metadata.title}</h2>
              <p>by {lyricsData.metadata.artists.join(', ')}</p>
            </div>

            <div className="audio-section">
              <AudioPlayer
                ref={audioPlayerRef}
                audioSrc="/data/raw/yana.mp3"
                onTimeUpdate={handleTimeUpdate}
                onLoadedMetadata={handleLoadedMetadata}
                onSeek={handleSeek}
              />
            </div>

            <div className="controls-section">
              <ControlPanel
                viewMode={viewMode}
                onViewModeChange={setViewMode}
                showTranslations={showTranslations}
                onTranslationsToggle={() => setShowTranslations(!showTranslations)}
              />
            </div>

            <div className="progress-section">
              <ProgressBar
                segments={lyricsData.segments}
                currentTime={currentTime}
                duration={duration || lyricsData.metadata.duration}
                onSeek={(time) => setCurrentTime(time)}
              />
            </div>

            <div className="lyrics-section">
              <LyricsDisplay
                segments={lyricsData.segments}
                currentTime={currentTime}
                showTranslations={showTranslations}
                viewMode={viewMode}
                onSeek={handleSeek}
              />
            </div>

            {/* Word timing display for active segment */}
            <div className="word-timing-section">
              {lyricsData.segments
                .filter(segment => currentTime >= segment.start && currentTime <= segment.end)
                .map(segment => (
                  <WordTimingDisplay
                    key={segment.id}
                    segment={segment}
                    currentTime={currentTime}
                    onSeek={handleSeek}
                  />
                ))}
            </div>

            <div className="debug-section">
              <p>Current Time: {currentTime.toFixed(2)}s</p>
              <p>Total Duration: {duration.toFixed(2)}s</p>
              <p>View Mode: {viewMode}</p>
              <p>Show Translations: {showTranslations ? 'Yes' : 'No'}</p>
              {lyricsData.metadata?.alignment_method && (
                <>
                  <p>Alignment Method: {lyricsData.metadata.alignment_method}</p>
                  <p>Alignment Quality: {lyricsData.metadata.alignment_quality?.toFixed(3)}</p>
                </>
              )}
            </div>
          </>
        )}

        {activeTab === 'manage' && (
          <SongManager onSongSelect={handleSongSelect} />
        )}

        {activeTab === 'downloads' && (
          <DownloadManager onSongSelect={handleSongSelect} />
        )}
      </main>
    </div>
  );
}

export default App
