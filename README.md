# Turkish Lyrics Learning Platform

A sophisticated web application for learning Turkish through synchronized song lyrics with real-time word-level timing visualization and intelligent audio processing.

## 🎵 Features

### Audio Processing & Transcription
- **High-Accuracy Transcription**: Uses ElevenLabs Scribe API for 98%+ accurate Turkish transcription
- **Confidence-Based Processing**: Automatically chooses between ElevenLabs direct processing or Claude-assisted matching based on confidence scores
- **Smart Caching**: Avoids re-processing the same files to save API costs
- **Word-Level Timing**: Precise start/end timestamps for every word

### Interactive Lyrics Display
- **Multiple View Modes**: Karaoke, syllable-level, and simple text views
- **Real-Time Synchronization**: Lyrics highlight in sync with audio playback
- **Clickable Navigation**: Click any word to jump to that timestamp
- **Word-Level Progress**: Red progress bars show real-time playback position within each word
- **Translation Support**: Toggle Turkish-English translations

### Audio Player
- **Variable Speed Playback**: 50-100% speed control in 10% increments with pitch preservation
- **Progress Visualization**: Visual segment blocks showing song structure
- **Seek Controls**: Click anywhere to jump to that position
- **Standard Controls**: Play/pause, time display, progress tracking

### Song Management
- **Download Manager**: Add YouTube songs to your library
- **Pre-populated Library**: Comes with sample Turkish songs
- **Metadata Extraction**: Automatically detects song title, artist, and language
- **Download Status Tracking**: Visual indicators for download progress and status
- **Local Storage**: Persistent song library using browser storage

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- ElevenLabs API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sile16/lyrics.git
   cd lyrics
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your ElevenLabs API key
   echo "ELEVEN_LABS_API_KEY=your_api_key_here" > .env
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install web app dependencies**
   ```bash
   cd web-app
   npm install
   cd ..
   ```

5. **Download a sample song** (optional)
   ```bash
   # Example: Download "Yana Yana" by Semicenk & Reynmen
   yt-dlp "https://youtu.be/Q3cj3lVCxr0" -o "data/raw/yana.mp3" -x --audio-format mp3
   ```

6. **Process the audio** (if you downloaded a song)
   ```bash
   python preprocessing/smart_processor.py
   ```

7. **Start the web application**
   ```bash
   cd web-app
   npm run dev
   ```

8. **Open your browser** to `http://localhost:5173`

### Development Note
For development, always use `npm run dev` which runs the latest code with hot-reload. The `dist/` folder is only for production builds and is git-ignored to avoid confusion.

## 📁 Project Structure

```
turkish-lyrics-poc/
├── preprocessing/              # Audio processing pipeline
│   ├── elevenlabs_processor.py # ElevenLabs API integration
│   ├── smart_processor.py     # Confidence-based processing
│   ├── claude_lyrics_matcher.py # Claude-powered lyrics matching
│   └── reference_lyrics.py    # Reference lyrics data
├── web-app/                   # React web application
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── AudioPlayer.tsx
│   │   │   ├── LyricsDisplay.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   ├── WordTimingDisplay.tsx
│   │   │   └── DownloadManager.tsx
│   │   └── App.tsx           # Main application
│   └── public/
│       └── data/processed/   # Processed lyrics data
├── data/
│   ├── raw/                  # Audio files (not in git)
│   └── processed/            # Processed transcription data
└── requirements.txt          # Python dependencies
```

## 🔧 Usage

### Processing New Songs

1. **Add audio file**
   ```bash
   # Download from YouTube
   yt-dlp "YOUTUBE_URL" -o "data/raw/song_name.mp3" -x --audio-format mp3
   ```

2. **Add reference lyrics**
   Edit `preprocessing/reference_lyrics.py` to add the correct lyrics

3. **Process with smart processor**
   ```bash
   python preprocessing/smart_processor.py
   ```

4. **Copy to web app**
   ```bash
   cp data/processed/song_name_smart_processed.json web-app/public/data/processed/
   ```

### Using the Web Interface

1. **Lyrics Player Tab**
   - Play/pause audio with synchronized lyrics
   - Adjust playback speed (50-100%)
   - Click words to seek to specific timestamps
   - Toggle between view modes (karaoke/syllables/simple)
   - View real-time word-level timing with progress bars

2. **Song Library Tab**
   - Add new songs by pasting YouTube URLs
   - Download and manage your song collection
   - View download status and metadata
   - Select songs to play in the lyrics player

## 🛠 Technical Details

### Audio Processing Pipeline

1. **ElevenLabs Scribe**: High-accuracy Turkish transcription with word-level timestamps
2. **Confidence Analysis**: Checks transcription confidence (>90% = direct use)
3. **Smart Segmentation**: Groups words into logical phrases based on pauses and punctuation
4. **Reference Matching**: Aligns transcription with known correct lyrics
5. **Claude Integration**: Uses Claude Code for intelligent matching when needed

### Frontend Architecture

- **React + TypeScript**: Modern, type-safe frontend
- **Component-Based**: Modular, reusable UI components
- **Real-Time Sync**: Audio and visual elements synchronized via shared state
- **Responsive Design**: Works on desktop and mobile devices

### Key Algorithms

- **Dynamic Time Warping**: For audio-text alignment
- **Confidence-Based Processing**: Optimizes accuracy vs. cost
- **Smart Caching**: Prevents redundant API calls
- **Real-Time Visualization**: Efficient progress tracking and highlighting

## 🌟 Advanced Features

### Word-Level Timing Visualization
- Red progress bars for each word showing exact playback position
- Click any word to jump to its timestamp
- Visual confidence indicators for transcription quality

### Intelligent Processing
- Automatically uses the best processing method based on confidence
- Falls back gracefully when APIs are unavailable
- Caches results to minimize costs

### Song Management
- YouTube integration for easy song addition
- Metadata extraction and management
- Persistent library storage

## 🔑 API Keys & Environment

Create a `.env` file with:
```env
ELEVEN_LABS_API_KEY=your_elevenlabs_api_key_here
```

Get your ElevenLabs API key from: https://elevenlabs.io/

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 🐛 Issues & Support

Report issues on the [GitHub Issues page](https://github.com/sile16/lyrics/issues)

## 🎯 Roadmap

- [ ] Support for more languages
- [ ] Offline mode for processed songs
- [ ] Social features (sharing, playlists)
- [ ] Mobile app version
- [ ] Advanced learning metrics
- [ ] Pronunciation analysis