import json
import os
from pathlib import Path
from elevenlabs_processor import ElevenLabsProcessor
from reference_lyrics import get_reference_lyrics

class SmartProcessor:
    def __init__(self, confidence_threshold=0.9):
        """
        Smart processor that uses ElevenLabs data directly when confidence is high,
        and Claude matching when confidence is lower.
        
        Args:
            confidence_threshold: Minimum confidence to use ElevenLabs data directly
        """
        self.confidence_threshold = confidence_threshold
        self.eleven_labs = ElevenLabsProcessor()
    
    def process_with_cache(self, audio_path, force_reprocess=False):
        """
        Process audio with caching to avoid re-processing the same file.
        
        Args:
            audio_path: Path to audio file
            force_reprocess: Force reprocessing even if cache exists
            
        Returns:
            Processing results
        """
        # Create cache path
        audio_name = Path(audio_path).stem
        cache_dir = Path("data/processed/cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        elevenlabs_cache = cache_dir / f"{audio_name}_elevenlabs_raw.json"
        processed_cache = cache_dir / f"{audio_name}_smart_processed.json"
        
        # Check if we have cached ElevenLabs results
        if elevenlabs_cache.exists() and not force_reprocess:
            print(f"Using cached ElevenLabs results from {elevenlabs_cache}")
            with open(elevenlabs_cache, 'r', encoding='utf-8') as f:
                raw_elevenlabs = json.load(f)
        else:
            print(f"Processing {audio_path} with ElevenLabs...")
            raw_elevenlabs = self.eleven_labs.transcribe_audio(audio_path)
            
            # Cache the raw results
            with open(elevenlabs_cache, 'w', encoding='utf-8') as f:
                json.dump(raw_elevenlabs, f, ensure_ascii=False, indent=2)
            print(f"Cached ElevenLabs results to {elevenlabs_cache}")
        
        # Process the results
        return self.smart_process_transcription(raw_elevenlabs, audio_name)
    
    def smart_process_transcription(self, raw_elevenlabs, audio_name):
        """
        Smart processing that uses confidence-based decisions.
        
        Args:
            raw_elevenlabs: Raw ElevenLabs API response
            audio_name: Name of the audio file for caching
            
        Returns:
            Smart processed results
        """
        words = [w for w in raw_elevenlabs.get('words', []) if w.get('type') == 'word']
        reference_lyrics = get_reference_lyrics()
        
        # Check language confidence
        language_confidence = raw_elevenlabs.get('language_probability', 0)
        print(f"Language detection confidence: {language_confidence:.3f}")
        
        if language_confidence >= self.confidence_threshold:
            print("High confidence - using ElevenLabs data directly")
            return self.process_high_confidence(words, reference_lyrics, raw_elevenlabs)
        else:
            print("Lower confidence - using Claude-assisted matching")
            return self.process_with_claude_assistance(words, reference_lyrics, raw_elevenlabs)
    
    def process_high_confidence(self, words, reference_lyrics, raw_elevenlabs):
        """
        Process high-confidence ElevenLabs data directly.
        """
        language_confidence = raw_elevenlabs.get('language_probability', 0)
        # Group words into segments based on natural breaks
        segments = []
        current_words = []
        current_start = None
        segment_id = 0
        
        # Simple approach: use ElevenLabs transcription directly and map to reference
        elevenlabs_text = " ".join([w['text'] for w in words])
        
        # For high confidence, create segments that closely match ElevenLabs timing
        for i, word in enumerate(words):
            if current_start is None:
                current_start = word['start']
            
            current_words.append(word)
            
            # End segment on punctuation, long pauses, or max length
            should_end = False
            
            if word['text'].strip().endswith(('.', '?', '!', ',')):
                should_end = True
            elif i < len(words) - 1:
                gap = words[i + 1]['start'] - word['end']
                if gap > 1.0:  # 1 second pause
                    should_end = True
            elif len(current_words) >= 8:  # Max 8 words per segment
                should_end = True
            elif i == len(words) - 1:  # Last word
                should_end = True
            
            if should_end:
                # Create segment
                segment_text = " ".join([w['text'] for w in current_words])
                
                # Try to match with reference lyrics
                best_match = self.find_best_reference_match(segment_text, reference_lyrics, segment_id)
                
                processed_words = []
                for word_data in current_words:
                    processed_words.append({
                        "text": word_data['text'],
                        "start": word_data['start'],
                        "end": word_data['end'],
                        "confidence": 1.0  # High confidence from ElevenLabs
                    })
                
                segments.append({
                    "id": f"smart_{segment_id:03d}",
                    "text": best_match if best_match else segment_text,
                    "start": current_start,
                    "end": word['end'],
                    "confidence": 1.0,
                    "method": "elevenlabs_direct",
                    "original_transcription": segment_text,
                    "words": processed_words
                })
                
                # Reset for next segment
                current_words = []
                current_start = None
                segment_id += 1
        
        return {
            "metadata": {
                "title": "Yana Yana",
                "artists": ["Semicenk", "Reynmen"],
                "duration": words[-1]['end'] if words else 0,
                "language": "tr",
                "alignment_method": "smart_elevenlabs_direct",
                "alignment_quality": language_confidence,
                "processing_method": "high_confidence"
            },
            "segments": segments,
            "raw_elevenlabs": {
                "language_probability": raw_elevenlabs.get('language_probability', 0),
                "total_words": len(words)
            }
        }
    
    def find_best_reference_match(self, transcribed_text, reference_lyrics, segment_index):
        """
        Find the best matching reference lyric for a transcribed segment.
        """
        from difflib import SequenceMatcher
        
        transcribed_lower = transcribed_text.lower().strip()
        best_match = None
        best_score = 0
        
        # Try to find the best match in reference lyrics
        for ref_line in reference_lyrics:
            ref_lower = ref_line.lower().strip()
            score = SequenceMatcher(None, transcribed_lower, ref_lower).ratio()
            
            if score > best_score:
                best_score = score
                best_match = ref_line
        
        # Only use reference if similarity is high enough
        if best_score > 0.6:
            return best_match
        
        # Otherwise return the original transcription
        return transcribed_text
    
    def process_with_claude_assistance(self, words, reference_lyrics, raw_elevenlabs):
        """
        Process with Claude assistance for lower confidence data.
        """
        # For now, fall back to the ElevenLabs processor approach
        # This could be enhanced with Claude matching later
        elevenlabs_processor = ElevenLabsProcessor()
        return elevenlabs_processor.process_transcription_result(raw_elevenlabs)

def main():
    """
    Main function to demonstrate smart processing.
    """
    processor = SmartProcessor(confidence_threshold=0.9)
    
    # Process the audio file
    audio_path = "data/raw/yana.mp3"
    results = processor.process_with_cache(audio_path)
    
    # Save results
    output_path = "data/processed/yana_smart_processed.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Smart processing complete! Results saved to: {output_path}")
    
    # Print summary
    print(f"\nSmart Processing Summary:")
    print(f"Method: {results['metadata']['processing_method']}")
    print(f"Language confidence: {results['raw_elevenlabs']['language_probability']:.3f}")
    print(f"Total segments: {len(results['segments'])}")
    print(f"Duration: {results['metadata']['duration']:.2f}s")
    
    # Show first few segments with timing
    print(f"\nFirst 3 segments:")
    for i, segment in enumerate(results['segments'][:3]):
        print(f"\nSegment {i+1}:")
        print(f"  Text: {segment['text']}")
        print(f"  Time: {segment['start']:.2f}s - {segment['end']:.2f}s")
        print(f"  Method: {segment['method']}")
        if 'original_transcription' in segment:
            print(f"  Original: {segment['original_transcription']}")

if __name__ == "__main__":
    main()