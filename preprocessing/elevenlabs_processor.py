import os
import json
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ElevenLabsProcessor:
    def __init__(self):
        """
        ElevenLabs Scribe processor for high-accuracy song transcription.
        """
        self.api_key = os.getenv('ELEVEN_LABS_API_KEY')
        if not self.api_key:
            raise ValueError("ELEVEN_LABS_API_KEY not found in environment variables")
        
        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "xi-api-key": self.api_key,
        }
    
    def transcribe_audio(self, audio_path, language="tr"):
        """
        Transcribe audio using ElevenLabs Scribe model.
        
        Args:
            audio_path: Path to the audio file
            language: Language code (tr for Turkish)
            
        Returns:
            Transcription results with word-level timestamps
        """
        print(f"Processing {audio_path} with ElevenLabs Scribe...")
        
        # Prepare the file upload
        files = {
            'file': open(audio_path, 'rb')
        }
        
        # Request parameters for optimal lyrics transcription
        data = {
            'model_id': 'scribe_v1',  # Most accurate Scribe model
            'language': language,
            'timestamp_granularity': 'word',  # Word-level timestamps
        }
        
        try:
            # Make the API request
            response = requests.post(
                f"{self.base_url}/speech-to-text",
                files=files,
                data=data,
                headers=self.headers
            )
        finally:
            files['file'].close()
        
        if response.status_code != 200:
            raise Exception(f"ElevenLabs API error: {response.status_code} - {response.text}")
        
        result = response.json()
        print(f"Transcription complete! Detected language: {result.get('detected_language', 'unknown')}")
        
        return result
    
    def process_transcription_result(self, result):
        """
        Process ElevenLabs transcription result into our format.
        
        Args:
            result: Raw ElevenLabs API response
            
        Returns:
            Processed segments compatible with our pipeline
        """
        # ElevenLabs Scribe returns a flat list of words, we need to group them into sentences/segments
        words = [w for w in result.get('words', []) if w.get('type') == 'word']
        
        if not words:
            return {
                "language": result.get('language_code', 'tr'),
                "segments": [],
                "processing_method": "elevenlabs_scribe",
                "model": "scribe-v1",
                "total_duration": 0
            }
        
        # Group words into logical segments (sentences/phrases)
        segments = []
        current_segment_words = []
        current_segment_start = words[0]['start']
        segment_id = 0
        
        for i, word in enumerate(words):
            current_segment_words.append(word)
            
            # Check if we should end current segment
            should_end_segment = False
            
            # End segment on punctuation
            if word['text'].strip().endswith(('.', '?', '!', ',')):
                should_end_segment = True
            
            # End segment on long pause (> 1 second gap to next word)
            elif i < len(words) - 1:
                gap_to_next = words[i + 1]['start'] - word['end']
                if gap_to_next > 1.0:
                    should_end_segment = True
            
            # End segment if it's getting too long (> 10 words)
            elif len(current_segment_words) >= 10:
                should_end_segment = True
            
            # Always end at the last word
            elif i == len(words) - 1:
                should_end_segment = True
            
            if should_end_segment:
                # Create segment
                segment_text = " ".join([w['text'].strip() for w in current_segment_words])
                segment_end = word['end']
                
                processed_words = []
                for word_data in current_segment_words:
                    processed_words.append({
                        "text": word_data['text'].strip(),
                        "start": word_data['start'],
                        "end": word_data['end'],
                        "confidence": 1.0  # ElevenLabs is very confident
                    })
                
                segments.append({
                    "id": f"elevenlabs_{segment_id:03d}",
                    "text": segment_text,
                    "start": current_segment_start,
                    "end": segment_end,
                    "confidence": 1.0,
                    "words": processed_words
                })
                
                # Reset for next segment
                current_segment_words = []
                segment_id += 1
                if i < len(words) - 1:
                    current_segment_start = words[i + 1]['start']
        
        return {
            "language": result.get('language_code', 'tr'),
            "segments": segments,
            "processing_method": "elevenlabs_scribe",
            "model": "scribe-v1",
            "total_duration": words[-1]['end'] if words else 0
        }
    
    def process_audio_file(self, audio_path):
        """
        Complete processing pipeline using ElevenLabs.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Processed transcription data
        """
        # Transcribe with ElevenLabs
        raw_result = self.transcribe_audio(audio_path)
        
        # Process into our format
        processed_result = self.process_transcription_result(raw_result)
        
        # Save raw result for debugging
        raw_output_path = "data/processed/yana_elevenlabs_raw.json"
        os.makedirs(os.path.dirname(raw_output_path), exist_ok=True)
        
        with open(raw_output_path, 'w', encoding='utf-8') as f:
            json.dump(raw_result, f, ensure_ascii=False, indent=2)
        
        print(f"Raw ElevenLabs result saved to: {raw_output_path}")
        
        return processed_result

def main():
    """
    Main function to process audio with ElevenLabs Scribe.
    """
    processor = ElevenLabsProcessor()
    
    # Process the audio file
    audio_path = "data/raw/yana.mp3"
    results = processor.process_audio_file(audio_path)
    
    # Save processed results
    output_path = "data/processed/yana_elevenlabs_processed.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"ElevenLabs processing complete! Results saved to: {output_path}")
    
    # Print summary
    print(f"\nProcessing Summary:")
    print(f"Method: {results['processing_method']}")
    print(f"Model: {results['model']}")
    print(f"Language: {results['language']}")
    print(f"Total segments: {len(results['segments'])}")
    print(f"Total words: {sum(len(seg.get('words', [])) for seg in results['segments'])}")
    print(f"Duration: {results['total_duration']:.2f}s")
    
    # Show first few segments
    print(f"\nFirst 3 segments:")
    for i, segment in enumerate(results['segments'][:3]):
        print(f"\nSegment {i+1}:")
        print(f"  Text: {segment['text']}")
        print(f"  Time: {segment['start']:.2f}s - {segment['end']:.2f}s")
        print(f"  Words: {len(segment.get('words', []))}")
        print(f"  Confidence: {segment.get('confidence', 0):.3f}")

if __name__ == "__main__":
    main()