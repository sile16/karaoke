import whisper_timestamped as whisper
import json
import os
from pathlib import Path

def process_audio_with_whisper(audio_path, model_size="medium", language="tr"):
    """
    Process audio file with Whisper to get word-level timestamps.
    
    Args:
        audio_path: Path to the audio file
        model_size: Size of Whisper model (tiny, base, small, medium, large)
        language: Language code (tr for Turkish)
    
    Returns:
        Dictionary with transcription and word-level timestamps
    """
    print(f"Loading Whisper model ({model_size})...")
    model = whisper.load_model(model_size)
    
    print(f"Processing audio file: {audio_path}")
    audio = whisper.load_audio(audio_path)
    
    # Transcribe with word-level timestamps
    result = whisper.transcribe(model, audio, language=language, verbose=True)
    
    # Extract segments with word timestamps
    processed_segments = []
    
    for segment in result["segments"]:
        processed_segment = {
            "id": f"seg_{segment['id']:03d}",
            "text": segment["text"].strip(),
            "start": segment["start"],
            "end": segment["end"],
            "words": []
        }
        
        # Process words if available
        if "words" in segment:
            for word in segment["words"]:
                processed_word = {
                    "text": word["text"].strip(),
                    "start": word["start"],
                    "end": word["end"],
                    "confidence": word.get("confidence", 0.0)
                }
                processed_segment["words"].append(processed_word)
        
        processed_segments.append(processed_segment)
    
    return {
        "language": result["language"],
        "segments": processed_segments,
        "full_text": result["text"]
    }

def save_results(results, output_path):
    """Save processed results to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Results saved to: {output_path}")

def main():
    # Paths
    audio_path = "data/raw/yana.mp3"
    output_path = "data/processed/yana_whisper_raw.json"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Process audio
    results = process_audio_with_whisper(audio_path)
    
    # Save results
    save_results(results, output_path)
    
    # Print summary
    print(f"\nProcessing complete!")
    print(f"Language detected: {results['language']}")
    print(f"Total segments: {len(results['segments'])}")
    
    # Show first few segments
    print("\nFirst 3 segments:")
    for i, segment in enumerate(results['segments'][:3]):
        print(f"\nSegment {i+1}:")
        print(f"  Text: {segment['text']}")
        print(f"  Time: {segment['start']:.2f}s - {segment['end']:.2f}s")
        print(f"  Words: {len(segment['words'])}")

if __name__ == "__main__":
    main()