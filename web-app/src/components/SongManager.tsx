import React, { useState, useEffect } from 'react';

interface LyricsSource {
  url: string;
  siteName: string;
  lyrics: string;
  confidence: number;
}

interface Song {
  id: string;
  youtubeUrl: string;
  title: string;
  artist: string;
  language: string;
  status: 'new' | 'downloading' | 'downloaded' | 'lyrics_searching' | 'lyrics_found' | 'processing' | 'ready' | 'error';
  downloadedAt?: string;
  audioFilePath?: string;
  
  // Lyrics management
  lyricsStatus: 'none' | 'searching' | 'found' | 'verified' | 'user_edited';
  lyricsSources: LyricsSource[];
  finalLyrics: string;
  lyricsVerified: boolean;
  
  // Processing
  processingVersion?: string;
  processedAt?: string;
  processedDataPath?: string;
  
  // Metadata
  duration?: number;
  thumbnailUrl?: string;
  addedAt: string;
  updatedAt: string;
  error?: string;
}

interface SongManagerProps {
  onSongSelect?: (song: Song) => void;
}

export const SongManager: React.FC<SongManagerProps> = ({ onSongSelect }) => {
  const [songs, setSongs] = useState<Song[]>([]);
  const [newYoutubeUrl, setNewYoutubeUrl] = useState('');
  const [selectedSong, setSelectedSong] = useState<Song | null>(null);
  const [editMode, setEditMode] = useState(false);

  // Pre-populated songs with better metadata
  const defaultSongs: Song[] = [
    {
      id: 'yana-yana-semicenk-reynmen',
      youtubeUrl: 'https://youtu.be/Q3cj3lVCxr0',
      title: 'Yana Yana',
      artist: 'Semicenk & Reynmen',
      language: 'tr',
      status: 'ready',
      downloadedAt: new Date().toISOString(),
      audioFilePath: '/data/raw/yana.mp3',
      lyricsStatus: 'verified',
      lyricsSources: [
        {
          url: 'https://example-lyrics-site1.com/yana-yana',
          siteName: 'LyricsSite1',
          lyrics: '[Processed and verified lyrics]',
          confidence: 0.95
        }
      ],
      finalLyrics: '[Final verified lyrics content]',
      lyricsVerified: true,
      processingVersion: '1.0.0',
      processedAt: new Date().toISOString(),
      processedDataPath: '/data/processed/yana_smart_processed.json',
      duration: 142.46,
      addedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
  ];

  useEffect(() => {
    loadSongs();
  }, []);

  const loadSongs = () => {
    const savedSongs = localStorage.getItem('karaokeSongLibrary');
    if (savedSongs) {
      setSongs(JSON.parse(savedSongs));
    } else {
      setSongs(defaultSongs);
      saveSongs(defaultSongs);
    }
  };

  const saveSongs = (updatedSongs: Song[]) => {
    setSongs(updatedSongs);
    localStorage.setItem('karaokeSongLibrary', JSON.stringify(updatedSongs));
  };

  const extractVideoId = (url: string): string | null => {
    const regex = /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/;
    const match = url.match(regex);
    return match ? match[1] : null;
  };

  const addNewSong = async () => {
    if (!newYoutubeUrl.trim()) return;

    const videoId = extractVideoId(newYoutubeUrl);
    if (!videoId) {
      alert('Please enter a valid YouTube URL');
      return;
    }

    const newSong: Song = {
      id: `song-${Date.now()}`,
      youtubeUrl: newYoutubeUrl,
      title: 'Extracting...',
      artist: 'Unknown',
      language: 'auto-detect',
      status: 'new',
      lyricsStatus: 'none',
      lyricsSources: [],
      finalLyrics: '',
      lyricsVerified: false,
      addedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    const updatedSongs = [newSong, ...songs];
    saveSongs(updatedSongs);
    setNewYoutubeUrl('');

    // Start the processing pipeline
    await processNewSong(newSong);
  };

  const processNewSong = async (song: Song) => {
    try {
      // Step 1: Extract metadata
      await extractMetadata(song);
      
      // Step 2: Download audio
      await downloadAudio(song);
      
      // Step 3: Search for lyrics
      await searchLyrics(song);
      
    } catch (error) {
      updateSongStatus(song.id, 'error', { error: error instanceof Error ? error.message : 'Unknown error' });
    }
  };

  const extractMetadata = async (song: Song) => {
    updateSongStatus(song.id, 'downloading');
    
    try {
      // Simulate metadata extraction API call
      const response = await fetch(`/api/youtube-metadata?url=${encodeURIComponent(song.youtubeUrl)}`);
      
      if (response.ok) {
        const metadata = await response.json();
        updateSong(song.id, {
          title: metadata.title || song.title,
          artist: metadata.artist || metadata.uploader || 'Unknown',
          duration: metadata.duration,
          thumbnailUrl: metadata.thumbnail,
          language: detectLanguage(metadata.title, metadata.description)
        });
      }
    } catch (error) {
      console.warn('Metadata extraction failed, using defaults');
    }
  };

  const downloadAudio = async (song: Song) => {
    try {
      const response = await fetch('/api/download-audio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          youtubeUrl: song.youtubeUrl,
          songId: song.id
        })
      });

      if (response.ok) {
        const result = await response.json();
        updateSong(song.id, {
          status: 'downloaded',
          downloadedAt: new Date().toISOString(),
          audioFilePath: result.filePath
        });
      } else {
        throw new Error('Download failed');
      }
    } catch (error) {
      throw new Error(`Audio download failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const searchLyrics = async (song: Song) => {
    updateSong(song.id, { status: 'lyrics_searching', lyricsStatus: 'searching' });

    try {
      const response = await fetch('/api/search-lyrics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: song.title,
          artist: song.artist,
          language: song.language
        })
      });

      if (response.ok) {
        const lyricsData = await response.json();
        const sources: LyricsSource[] = lyricsData.sources || [];
        
        // Check if we have matching sources
        const verified = sources.length >= 2 && 
          sources[0].lyrics === sources[1].lyrics &&
          sources[0].lyrics.length > 100;

        updateSong(song.id, {
          status: verified ? 'lyrics_found' : 'lyrics_searching',
          lyricsStatus: verified ? 'verified' : 'found',
          lyricsSources: sources,
          finalLyrics: sources[0]?.lyrics || '',
          lyricsVerified: verified
        });

        if (verified) {
          // Auto-process if lyrics are verified
          await processSong(song.id);
        }
      }
    } catch (error) {
      console.warn('Lyrics search failed:', error);
      updateSong(song.id, { lyricsStatus: 'none' });
    }
  };

  const processSong = async (songId: string) => {
    updateSongStatus(songId, 'processing');

    try {
      const response = await fetch('/api/process-song', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          songId,
          processingVersion: '1.0.0'
        })
      });

      if (response.ok) {
        const result = await response.json();
        updateSong(songId, {
          status: 'ready',
          processingVersion: '1.0.0',
          processedAt: new Date().toISOString(),
          processedDataPath: result.dataPath
        });
      } else {
        throw new Error('Processing failed');
      }
    } catch (error) {
      updateSongStatus(songId, 'error', { error: error instanceof Error ? error.message : 'Processing failed' });
    }
  };

  const detectLanguage = (title: string, description?: string): string => {
    const text = `${title} ${description || ''}`.toLowerCase();
    
    // Simple language detection based on common words/patterns
    if (text.match(/[\u0600-\u06FF]/)) return 'ar'; // Arabic
    if (text.match(/[\u4e00-\u9fff]/)) return 'zh'; // Chinese
    if (text.match(/[\u3040-\u309f\u30a0-\u30ff]/)) return 'ja'; // Japanese
    if (text.match(/[\u0400-\u04ff]/)) return 'ru'; // Russian
    if (text.match(/[\u011e\u011f\u0130\u0131\u015e\u015f]/)) return 'tr'; // Turkish
    if (text.match(/[àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]/)) return 'fr'; // French
    if (text.match(/[äöüß]/)) return 'de'; // German
    if (text.match(/[áéíóúñü]/)) return 'es'; // Spanish
    
    return 'en'; // Default to English
  };

  const updateSong = (songId: string, updates: Partial<Song>) => {
    const updatedSongs = songs.map(song =>
      song.id === songId
        ? { ...song, ...updates, updatedAt: new Date().toISOString() }
        : song
    );
    saveSongs(updatedSongs);
  };

  const updateSongStatus = (songId: string, status: Song['status'], additionalUpdates?: Partial<Song>) => {
    updateSong(songId, { status, ...additionalUpdates });
  };

  const handleEditSong = (song: Song) => {
    setSelectedSong(song);
    setEditMode(true);
  };

  const saveEditedSong = () => {
    if (!selectedSong) return;
    
    updateSong(selectedSong.id, {
      title: selectedSong.title,
      artist: selectedSong.artist,
      language: selectedSong.language,
      finalLyrics: selectedSong.finalLyrics,
      lyricsStatus: 'user_edited'
    });
    
    setEditMode(false);
    setSelectedSong(null);
  };

  const getStatusIcon = (status: Song['status']) => {
    switch (status) {
      case 'ready': return '✅';
      case 'processing': return '⚙️';
      case 'lyrics_found': return '📝';
      case 'lyrics_searching': return '🔍';
      case 'downloaded': return '⬇️';
      case 'downloading': return '⏳';
      case 'error': return '❌';
      default: return '🆕';
    }
  };

  const getStatusText = (song: Song) => {
    switch (song.status) {
      case 'ready': return 'Ready to Play';
      case 'processing': return 'Processing Audio...';
      case 'lyrics_found': return `Lyrics Found (${song.lyricsVerified ? 'Verified' : 'Needs Review'})`;
      case 'lyrics_searching': return 'Searching Lyrics...';
      case 'downloaded': return 'Audio Downloaded';
      case 'downloading': return 'Downloading...';
      case 'error': return `Error: ${song.error}`;
      default: return 'New Song';
    }
  };

  return (
    <div className="song-manager">
      <div className="song-manager-header">
        <h2>Song Library Management</h2>
        <p>Add, edit, and process songs for karaoke learning</p>
      </div>

      {/* Add New Song */}
      <div className="add-song-section">
        <h3>Add New Song</h3>
        <div className="add-song-form">
          <input
            type="text"
            placeholder="Paste YouTube URL here..."
            value={newYoutubeUrl}
            onChange={(e) => setNewYoutubeUrl(e.target.value)}
            className="youtube-url-input"
          />
          <button
            onClick={addNewSong}
            disabled={!newYoutubeUrl.trim()}
            className="add-song-button"
          >
            Add & Process Song
          </button>
        </div>
        <p className="processing-note">
          This will automatically download audio, search for lyrics, and process for karaoke use.
        </p>
      </div>

      {/* Songs List */}
      <div className="songs-list">
        <h3>Song Library ({songs.length} songs)</h3>
        <div className="songs-grid">
          {songs.map((song) => (
            <div key={song.id} className={`song-card ${song.status}`}>
              <div className="song-header">
                <div className="song-info">
                  <h4 className="song-title">{song.title}</h4>
                  <p className="song-artist">{song.artist}</p>
                  <div className="song-meta">
                    <span className="song-language">
                      {song.language.toUpperCase()}
                    </span>
                    <span className="song-duration">
                      {song.duration ? `${Math.floor(song.duration / 60)}:${(song.duration % 60).toString().padStart(2, '0')}` : '—'}
                    </span>
                  </div>
                </div>
                {song.thumbnailUrl && (
                  <img src={song.thumbnailUrl} alt={song.title} className="song-thumbnail" />
                )}
              </div>

              <div className="song-status">
                <span className="status-indicator">
                  {getStatusIcon(song.status)} {getStatusText(song)}
                </span>
                {song.processingVersion && (
                  <span className="processing-version">v{song.processingVersion}</span>
                )}
              </div>

              {song.lyricsStatus !== 'none' && (
                <div className="lyrics-info">
                  <p className="lyrics-status">
                    Lyrics: {song.lyricsVerified ? '✅ Verified' : '⚠️ Needs Review'} 
                    ({song.lyricsSources.length} sources)
                  </p>
                  {song.finalLyrics && (
                    <div className="lyrics-preview">
                      {song.finalLyrics.substring(0, 100)}...
                    </div>
                  )}
                </div>
              )}

              <div className="song-actions">
                {song.status === 'ready' && (
                  <button
                    onClick={() => onSongSelect?.(song)}
                    className="play-button"
                  >
                    Play in Karaoke
                  </button>
                )}
                
                <button
                  onClick={() => handleEditSong(song)}
                  className="edit-button"
                >
                  Edit Details
                </button>

                {song.status === 'lyrics_found' && !song.lyricsVerified && (
                  <button
                    onClick={() => processSong(song.id)}
                    className="process-button"
                  >
                    Process Song
                  </button>
                )}

                {song.status === 'error' && (
                  <button
                    onClick={() => processNewSong(song)}
                    className="retry-button"
                  >
                    Retry
                  </button>
                )}

                <a
                  href={song.youtubeUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="youtube-link"
                >
                  View on YouTube
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Edit Modal */}
      {editMode && selectedSong && (
        <div className="edit-modal-overlay">
          <div className="edit-modal">
            <h3>Edit Song: {selectedSong.title}</h3>
            
            <div className="edit-form">
              <label>
                Title:
                <input
                  type="text"
                  value={selectedSong.title}
                  onChange={(e) => setSelectedSong({...selectedSong, title: e.target.value})}
                />
              </label>
              
              <label>
                Artist:
                <input
                  type="text"
                  value={selectedSong.artist}
                  onChange={(e) => setSelectedSong({...selectedSong, artist: e.target.value})}
                />
              </label>
              
              <label>
                Language:
                <select
                  value={selectedSong.language}
                  onChange={(e) => setSelectedSong({...selectedSong, language: e.target.value})}
                >
                  <option value="tr">Turkish</option>
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="ar">Arabic</option>
                  <option value="ru">Russian</option>
                  <option value="zh">Chinese</option>
                  <option value="ja">Japanese</option>
                </select>
              </label>
              
              <label>
                Lyrics:
                <textarea
                  value={selectedSong.finalLyrics}
                  onChange={(e) => setSelectedSong({...selectedSong, finalLyrics: e.target.value})}
                  rows={10}
                  placeholder="Paste or edit the song lyrics here..."
                />
              </label>
            </div>

            <div className="edit-actions">
              <button onClick={saveEditedSong} className="save-button">Save Changes</button>
              <button onClick={() => {setEditMode(false); setSelectedSong(null);}} className="cancel-button">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};