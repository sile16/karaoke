import React, { useState, useEffect } from 'react';

interface Song {
  id: string;
  youtubeUrl: string;
  title: string;
  artist: string;
  language: string;
  downloadStatus: 'not_downloaded' | 'downloading' | 'downloaded' | 'error';
  downloadedAt?: string;
  error?: string;
}

interface DownloadManagerProps {
  onSongSelect?: (song: Song) => void;
}

export const DownloadManager: React.FC<DownloadManagerProps> = ({
  onSongSelect,
}) => {
  const [songs, setSongs] = useState<Song[]>([]);
  const [newYoutubeUrl, setNewYoutubeUrl] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  // Pre-populated song list
  const defaultSongs: Song[] = [
    {
      id: 'yana-yana',
      youtubeUrl: 'https://youtu.be/Q3cj3lVCxr0',
      title: 'Yana Yana',
      artist: 'Semicenk & Reynmen',
      language: 'tr',
      downloadStatus: 'downloaded', // Already downloaded
      downloadedAt: new Date().toISOString()
    },
    {
      id: 'sample-turkish-1',
      youtubeUrl: 'https://youtu.be/example1',
      title: 'Sample Turkish Song',
      artist: 'Sample Artist',
      language: 'tr',
      downloadStatus: 'not_downloaded'
    },
    {
      id: 'sample-turkish-2',
      youtubeUrl: 'https://youtu.be/example2',
      title: 'Another Turkish Song',
      artist: 'Another Artist',
      language: 'tr',
      downloadStatus: 'not_downloaded'
    }
  ];

  useEffect(() => {
    // Load songs from localStorage or use defaults
    const savedSongs = localStorage.getItem('turkishLyricsSongs');
    if (savedSongs) {
      setSongs(JSON.parse(savedSongs));
    } else {
      setSongs(defaultSongs);
      localStorage.setItem('turkishLyricsSongs', JSON.stringify(defaultSongs));
    }
  }, []);

  const saveSongs = (updatedSongs: Song[]) => {
    setSongs(updatedSongs);
    localStorage.setItem('turkishLyricsSongs', JSON.stringify(updatedSongs));
  };

  const extractVideoId = (url: string): string | null => {
    const regex = /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/;
    const match = url.match(regex);
    return match ? match[1] : null;
  };

  const downloadSong = async (song: Song) => {
    // Update status to downloading
    const updatedSongs = songs.map(s => 
      s.id === song.id 
        ? { ...s, downloadStatus: 'downloading' as const }
        : s
    );
    saveSongs(updatedSongs);

    try {
      // Call backend API to download the song
      const response = await fetch('/api/download', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          youtubeUrl: song.youtubeUrl,
          songId: song.id
        }),
      });

      if (response.ok) {
        // Update status to downloaded
        const finalSongs = songs.map(s => 
          s.id === song.id 
            ? { 
                ...s, 
                downloadStatus: 'downloaded' as const,
                downloadedAt: new Date().toISOString()
              }
            : s
        );
        saveSongs(finalSongs);
      } else {
        throw new Error('Download failed');
      }
    } catch (error) {
      // Update status to error
      const errorSongs = songs.map(s => 
        s.id === song.id 
          ? { 
              ...s, 
              downloadStatus: 'error' as const,
              error: error instanceof Error ? error.message : 'Unknown error'
            }
          : s
      );
      saveSongs(errorSongs);
    }
  };

  const addNewSong = async () => {
    if (!newYoutubeUrl.trim()) return;

    setIsAdding(true);
    
    try {
      const videoId = extractVideoId(newYoutubeUrl);
      if (!videoId) {
        throw new Error('Invalid YouTube URL');
      }

      // Try to get video info from YouTube API or metadata
      const response = await fetch(`/api/video-info?url=${encodeURIComponent(newYoutubeUrl)}`);
      
      let title = 'Unknown Title';
      let artist = 'Unknown Artist';
      let language = 'tr'; // Default to Turkish

      if (response.ok) {
        const videoInfo = await response.json();
        title = videoInfo.title || title;
        artist = videoInfo.artist || artist;
        language = videoInfo.language || language;
      }

      const newSong: Song = {
        id: `song-${Date.now()}`,
        youtubeUrl: newYoutubeUrl,
        title,
        artist,
        language,
        downloadStatus: 'not_downloaded'
      };

      const updatedSongs = [...songs, newSong];
      saveSongs(updatedSongs);
      setNewYoutubeUrl('');
    } catch (error) {
      alert(`Error adding song: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsAdding(false);
    }
  };

  const getStatusIcon = (status: Song['downloadStatus']) => {
    switch (status) {
      case 'downloaded':
        return '✅';
      case 'downloading':
        return '⏳';
      case 'error':
        return '❌';
      default:
        return '⬇️';
    }
  };

  const getStatusText = (status: Song['downloadStatus']) => {
    switch (status) {
      case 'downloaded':
        return 'Downloaded';
      case 'downloading':
        return 'Downloading...';
      case 'error':
        return 'Error';
      default:
        return 'Not Downloaded';
    }
  };

  return (
    <div className="download-manager">
      <div className="download-manager-header">
        <h2>Song Library</h2>
        <p>Download and manage Turkish songs for lyrics learning</p>
      </div>

      {/* Add new song section */}
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
            disabled={isAdding || !newYoutubeUrl.trim()}
            className="add-song-button"
          >
            {isAdding ? 'Adding...' : 'Add Song'}
          </button>
        </div>
      </div>

      {/* Songs list */}
      <div className="songs-list">
        <h3>Available Songs</h3>
        {songs.length === 0 ? (
          <p className="no-songs">No songs available. Add some songs to get started!</p>
        ) : (
          <div className="songs-grid">
            {songs.map((song) => (
              <div key={song.id} className="song-card">
                <div className="song-info">
                  <h4 className="song-title">{song.title}</h4>
                  <p className="song-artist">{song.artist}</p>
                  <div className="song-meta">
                    <span className="song-language">Language: {song.language.toUpperCase()}</span>
                    <span className="song-status">
                      {getStatusIcon(song.downloadStatus)} {getStatusText(song.downloadStatus)}
                    </span>
                  </div>
                  {song.error && (
                    <p className="song-error">Error: {song.error}</p>
                  )}
                </div>
                
                <div className="song-actions">
                  {song.downloadStatus === 'not_downloaded' && (
                    <button
                      onClick={() => downloadSong(song)}
                      className="download-button"
                    >
                      Download
                    </button>
                  )}
                  {song.downloadStatus === 'downloaded' && (
                    <button
                      onClick={() => onSongSelect?.(song)}
                      className="select-button"
                    >
                      Select
                    </button>
                  )}
                  {song.downloadStatus === 'error' && (
                    <button
                      onClick={() => downloadSong(song)}
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
        )}
      </div>
    </div>
  );
};