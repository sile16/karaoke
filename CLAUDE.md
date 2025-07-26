# Claude Code Assistant Guidelines

## 🎯 Development Philosophy
- **DO NOT** create duplicate functionality - always check existing code first
- **DO NOT** create new files without asking - reuse and extend existing components
- **ALWAYS** plan updates to existing code rather than creating new files
- **ASK BEFORE** creating any new component or file
- **USE** `npm run dev` for all development (never `npm start` or `npx serve dist`)

## 📁 Project Structure Overview

### Web Application (`/web-app`)
- **Entry Point**: `src/main.tsx` → `src/App.tsx`
- **Development**: `npm run dev` (http://localhost:5173)
- **Build**: `npm run build` (only for production)

### Key Components Location

#### Main App (`src/App.tsx`)
- **State Management**: Lines 62-68
  - `activeTab`: Controls which tab is shown ('lyrics' | 'manage')
  - `lyricsData`: Current song data for karaoke
  - `currentTime`, `duration`: Audio playback state
- **Tab Navigation**: Lines 110-123
- **Component Rendering**: Lines 127-203

#### Audio Player (`src/components/AudioPlayer.tsx`)
- **Playback Control**: `togglePlayPause()` - Line 50
- **Speed Control**: `handleSpeedChange()` - Line 75 (preserves pitch)
- **Seeking**: `seekToTime()` - Line 85
- **Time Display**: `formatTime()` - Line 98

#### Song Manager (`src/components/SongManager.tsx`) 
**⚠️ PRIMARY COMPONENT - DO NOT DUPLICATE**
- **Song Pipeline**: Lines 98-195
  - `processNewSong()`: Complete pipeline orchestration
  - `extractMetadata()`: YouTube metadata extraction
  - `downloadAudio()`: Audio file download
  - `searchLyrics()`: Multi-source lyrics search
- **User Interface**: 
  - Add song form: Lines 251-266
  - Song cards: Lines 272-356
  - Edit modal: Lines 358-440
- **State**: `songs`, `selectedSong`, `editMode`

#### Lyrics Display (`src/components/LyricsDisplay.tsx`)
- **View Modes**: Lines 54-113
  - `renderKaraokeView()`: Karaoke-style highlighting
  - `renderSyllableView()`: Syllable breakdown
  - `renderSimpleView()`: Plain text
- **Click to Seek**: Lines 60, 85, 102

#### Progress Bar (`src/components/ProgressBar.tsx`)
- **Visual Timeline**: Segment blocks with click-to-seek
- **Current Segment**: Real-time display

#### Word Timing Display (`src/components/WordTimingDisplay.tsx`)
- **Per-Word Progress**: Red progress bars for each word
- **Timing Visualization**: Lines 40-93

### Backend Processing (`/preprocessing`)

#### Smart Processor (`smart_processor.py`)
**⚠️ PRIMARY PROCESSOR - USE THIS**
- **Main Entry**: `process_with_cache()` - Line 18
- **Confidence Logic**: Lines 66-78
- **Caching**: Lines 30-48

#### Pipeline Manager (`pipeline_manager.py`)
- **Version Control**: `CURRENT_VERSION = "2.0.0"`
- **Processing Steps**: Lines 80-130
- **History Tracking**: `get_processing_history()`

#### Lyrics Searcher (`lyrics_searcher.py`)
- **Multi-Source Search**: `search_lyrics()` - Line 22
- **Source Verification**: `verify_sources()` - Line 155
- **Sites**: Genius, AZLyrics, Lyrics.com

#### ElevenLabs Processor (`elevenlabs_processor.py`)
- **API Integration**: `transcribe_audio()` - Line 25
- **Segment Creation**: Lines 91-149

## 🔧 Common Tasks

### Adding a New Feature
1. **CHECK** existing components first
2. **ASK** before creating new files
3. **EXTEND** existing components when possible
4. **UPDATE** this file with new locations

### Modifying Song Processing
- Start with `smart_processor.py`
- Use `pipeline_manager.py` for versioning
- Cache results to avoid re-processing

### UI Changes
- Two tabs only: Karaoke Player | Song Manager
- All song management in `SongManager.tsx`
- Styles in `App.css`

### API Integration Points
- `/api/download-audio` - Audio download endpoint
- `/api/youtube-metadata` - YouTube info extraction  
- `/api/search-lyrics` - Lyrics search endpoint
- `/api/process-song` - Processing pipeline

## ⚠️ Important Notes

### DO NOT:
- Create `DownloadManager.tsx` - already consolidated into `SongManager.tsx`
- Use `npm start` - use `npm run dev`
- Create duplicate song management interfaces
- Build unnecessarily - development doesn't need builds

### ALWAYS:
- Check existing code first
- Ask before creating new files
- Use the smart processor with caching
- Test with `npm run dev`
- Keep the two-tab structure

### File Locations Quick Reference:
```
Web UI Components:     /web-app/src/components/
Audio Processing:      /preprocessing/
Processed Data:        /data/processed/
Raw Audio:            /data/raw/ (git-ignored)
Public Assets:        /web-app/public/
```

### Key Functions by Task:

**Process New Song:**
1. `SongManager.processNewSong()` → 
2. `smart_processor.process_with_cache()` →
3. `pipeline_manager.process_song()`

**Play Karaoke:**
1. `App.handleSongSelect()` →
2. `AudioPlayer.seekToTime()` →
3. `LyricsDisplay` renders with timing

**Edit Song Details:**
1. `SongManager.handleEditSong()` →
2. Modal displays →
3. `SongManager.saveEditedSong()`

## 📝 Testing Commands
```bash
# Run web app
cd web-app && npm run dev

# Process a song
python preprocessing/smart_processor.py

# Check processing history
python preprocessing/pipeline_manager.py
```

## 🚀 Quick Start for New Features
1. Read this file first
2. Check existing components
3. Ask: "Can I extend existing code?"
4. If new file needed, ask first
5. Update this file after changes