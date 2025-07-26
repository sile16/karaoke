import json
import os
import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from smart_processor import SmartProcessor
from elevenlabs_processor import ElevenLabsProcessor

class ProcessingPipeline:
    """
    Versioned processing pipeline for songs.
    Allows reprocessing with newer versions while keeping historical data.
    """
    
    CURRENT_VERSION = "2.0.0"
    
    def __init__(self):
        self.smart_processor = SmartProcessor()
        self.eleven_labs = ElevenLabsProcessor()
        
    def get_version_info(self) -> Dict[str, Any]:
        """Get current pipeline version and capabilities."""
        return {
            "version": self.CURRENT_VERSION,
            "capabilities": [
                "elevenlabs_scribe",
                "confidence_based_processing", 
                "smart_segmentation",
                "claude_matching",
                "word_level_timing",
                "caching"
            ],
            "processors": {
                "elevenlabs": "1.0.0",
                "smart_processor": "1.0.0",
                "claude_matcher": "1.0.0"
            },
            "created_at": datetime.datetime.now().isoformat()
        }
    
    def process_song(self, song_data: Dict[str, Any], force_reprocess: bool = False) -> Dict[str, Any]:
        """
        Process a song through the complete pipeline.
        
        Args:
            song_data: Song metadata including audio path, title, artist, etc.
            force_reprocess: Force reprocessing even if current version exists
            
        Returns:
            Complete processed song data
        """
        song_id = song_data['id']
        audio_path = song_data.get('audioFilePath', f"data/raw/{song_id}.mp3")
        
        # Check if we need to process
        existing_data = self.load_existing_processed_data(song_id)
        if existing_data and not force_reprocess:
            existing_version = existing_data.get('metadata', {}).get('processing_version')
            if existing_version == self.CURRENT_VERSION:
                print(f"Song {song_id} already processed with current version {self.CURRENT_VERSION}")
                return existing_data
        
        print(f"Processing song {song_id} with pipeline version {self.CURRENT_VERSION}")
        
        # Create processing record
        processing_record = {
            "song_id": song_id,
            "processing_version": self.CURRENT_VERSION,
            "started_at": datetime.datetime.now().isoformat(),
            "input_data": song_data,
            "steps": []
        }
        
        try:
            # Step 1: Smart audio processing
            step_result = self.process_audio_step(audio_path, song_data, processing_record)
            if not step_result["success"]:
                raise Exception(f"Audio processing failed: {step_result['error']}")
            
            audio_result = step_result["result"]
            
            # Step 2: Lyrics alignment (if lyrics provided)
            if song_data.get('finalLyrics'):
                step_result = self.align_lyrics_step(audio_result, song_data, processing_record)
                if step_result["success"]:
                    audio_result = step_result["result"]
            
            # Step 3: Finalize and package
            final_result = self.finalize_processing(audio_result, song_data, processing_record)
            
            # Save processing record
            self.save_processing_record(song_id, processing_record)
            
            # Save final result
            self.save_processed_data(song_id, final_result)
            
            return final_result
            
        except Exception as e:
            processing_record["error"] = str(e)
            processing_record["failed_at"] = datetime.datetime.now().isoformat()
            self.save_processing_record(song_id, processing_record)
            raise
    
    def process_audio_step(self, audio_path: str, song_data: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any]:
        """Process audio with smart processor."""
        step_start = datetime.datetime.now()
        
        try:
            # Use smart processor with caching
            result = self.smart_processor.process_with_cache(audio_path, force_reprocess=False)
            
            step_record = {
                "step": "audio_processing",
                "processor": "smart_processor",
                "started_at": step_start.isoformat(),
                "completed_at": datetime.datetime.now().isoformat(),
                "success": True,
                "metadata": {
                    "segments_count": len(result.get('segments', [])),
                    "duration": result.get('metadata', {}).get('duration', 0),
                    "language_confidence": result.get('raw_elevenlabs', {}).get('language_probability', 0)
                }
            }
            record["steps"].append(step_record)
            
            return {"success": True, "result": result}
            
        except Exception as e:
            step_record = {
                "step": "audio_processing", 
                "processor": "smart_processor",
                "started_at": step_start.isoformat(),
                "failed_at": datetime.datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }
            record["steps"].append(step_record)
            
            return {"success": False, "error": str(e)}
    
    def align_lyrics_step(self, audio_result: Dict[str, Any], song_data: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any]:
        """Align provided lyrics with audio transcription."""
        step_start = datetime.datetime.now()
        
        try:
            from claude_lyrics_matcher import ClaudeLyricsMatcher
            
            # Split lyrics into lines
            lyrics_lines = [line.strip() for line in song_data['finalLyrics'].split('\n') if line.strip()]
            
            # Create temporary file for matching
            temp_audio_file = f"temp_audio_{song_data['id']}.json"
            with open(temp_audio_file, 'w', encoding='utf-8') as f:
                json.dump(audio_result, f, ensure_ascii=False)
            
            try:
                matcher = ClaudeLyricsMatcher()
                matching_result = matcher.process_matching(temp_audio_file, lyrics_lines)
                
                # Create aligned segments
                aligned_segments = matcher.create_aligned_segments(
                    matching_result, audio_result, lyrics_lines
                )
                
                # Update audio result with aligned data
                audio_result['segments'] = aligned_segments
                audio_result['metadata']['alignment_method'] = 'claude_lyrics_aligned'
                audio_result['metadata']['lyrics_source'] = 'user_provided'
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_audio_file):
                    os.remove(temp_audio_file)
                matcher.cleanup()
            
            step_record = {
                "step": "lyrics_alignment",
                "processor": "claude_lyrics_matcher", 
                "started_at": step_start.isoformat(),
                "completed_at": datetime.datetime.now().isoformat(),
                "success": True,
                "metadata": {
                    "aligned_segments": len(aligned_segments),
                    "lyrics_lines": len(lyrics_lines),
                    "matching_method": matching_result.get('method', 'unknown')
                }
            }
            record["steps"].append(step_record)
            
            return {"success": True, "result": audio_result}
            
        except Exception as e:
            step_record = {
                "step": "lyrics_alignment",
                "processor": "claude_lyrics_matcher",
                "started_at": step_start.isoformat(), 
                "failed_at": datetime.datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }
            record["steps"].append(step_record)
            
            # Return original result if alignment fails
            return {"success": True, "result": audio_result}
    
    def finalize_processing(self, audio_result: Dict[str, Any], song_data: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize processing and create final karaoke-ready data."""
        
        final_result = {
            "metadata": {
                "title": song_data.get('title', 'Unknown'),
                "artists": [song_data.get('artist', 'Unknown')],
                "duration": audio_result.get('metadata', {}).get('duration', 0),
                "language": song_data.get('language', 'auto'),
                "processing_version": self.CURRENT_VERSION,
                "processed_at": datetime.datetime.now().isoformat(),
                "alignment_method": audio_result.get('metadata', {}).get('alignment_method', 'smart_processing'),
                "alignment_quality": audio_result.get('metadata', {}).get('alignment_quality', 0),
                "source_info": {
                    "youtube_url": song_data.get('youtubeUrl'),
                    "audio_file": song_data.get('audioFilePath'),
                    "lyrics_source": song_data.get('lyricsStatus', 'none')
                }
            },
            "segments": audio_result.get('segments', []),
            "processing_info": {
                "pipeline_version": self.CURRENT_VERSION,
                "version_info": self.get_version_info(),
                "processing_steps": len(record["steps"]),
                "total_processing_time": self.calculate_processing_time(record)
            }
        }
        
        record["completed_at"] = datetime.datetime.now().isoformat()
        record["final_result_segments"] = len(final_result["segments"])
        
        return final_result
    
    def calculate_processing_time(self, record: Dict[str, Any]) -> float:
        """Calculate total processing time in seconds."""
        if "started_at" in record and "completed_at" in record:
            start = datetime.datetime.fromisoformat(record["started_at"])
            end = datetime.datetime.fromisoformat(record["completed_at"])
            return (end - start).total_seconds()
        return 0
    
    def load_existing_processed_data(self, song_id: str) -> Optional[Dict[str, Any]]:
        """Load existing processed data if it exists."""
        processed_file = f"data/processed/{song_id}_processed_v{self.CURRENT_VERSION}.json"
        if os.path.exists(processed_file):
            with open(processed_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def save_processed_data(self, song_id: str, data: Dict[str, Any]) -> str:
        """Save processed data with version."""
        os.makedirs("data/processed", exist_ok=True)
        
        # Save with version
        versioned_file = f"data/processed/{song_id}_processed_v{self.CURRENT_VERSION}.json"
        with open(versioned_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Also save as current (for web app)
        current_file = f"data/processed/{song_id}_processed.json"
        with open(current_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return versioned_file
    
    def save_processing_record(self, song_id: str, record: Dict[str, Any]) -> str:
        """Save processing record for debugging and history."""
        os.makedirs("data/processed/processing_logs", exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"data/processed/processing_logs/{song_id}_v{self.CURRENT_VERSION}_{timestamp}.json"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        
        return log_file
    
    def get_processing_history(self, song_id: str) -> List[Dict[str, Any]]:
        """Get processing history for a song."""
        log_dir = Path("data/processed/processing_logs")
        if not log_dir.exists():
            return []
        
        history = []
        for log_file in log_dir.glob(f"{song_id}_*.json"):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    history.append(json.load(f))
            except Exception:
                continue
        
        # Sort by processing time
        history.sort(key=lambda x: x.get('started_at', ''), reverse=True)
        return history

def main():
    """Demo the versioned processing pipeline."""
    pipeline = ProcessingPipeline()
    
    # Example song data (as would come from the web interface)
    song_data = {
        "id": "yana-yana-demo",
        "title": "Yana Yana",
        "artist": "Semicenk & Reynmen", 
        "language": "tr",
        "youtubeUrl": "https://youtu.be/Q3cj3lVCxr0",
        "audioFilePath": "data/raw/yana.mp3",
        "finalLyrics": "Yana yana sevdik bazen\nÇok kez unutulup gidenin ardından\n[Additional lyrics would go here]",
        "lyricsStatus": "user_provided"
    }
    
    try:
        # Process the song
        result = pipeline.process_song(song_data)
        
        print("\n✅ Processing completed successfully!")
        print(f"Version: {result['metadata']['processing_version']}")
        print(f"Segments created: {len(result['segments'])}")
        print(f"Processing time: {result['processing_info']['total_processing_time']:.2f}s")
        
        # Show processing history
        history = pipeline.get_processing_history(song_data['id'])
        print(f"\nProcessing history: {len(history)} runs")
        
    except Exception as e:
        print(f"\n❌ Processing failed: {e}")

if __name__ == "__main__":
    main()