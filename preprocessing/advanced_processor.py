import whisper_timestamped as whisper
import json
import os
import numpy as np
from pydub import AudioSegment
from pathlib import Path
import re
from syllable_splitter import split_turkish_word, estimate_syllable_timings

class AdvancedAudioProcessor:
    def __init__(self, model_size="large-v3"):
        """
        Advanced audio processor with chunked processing and alignment.
        
        Args:
            model_size: Whisper model size (large-v3 for best accuracy)
        """
        self.model_size = model_size
        self.model = None
        self.chunk_duration = 15  # seconds
        self.overlap_duration = 5  # seconds
        
    def load_model(self):
        """Load Whisper model."""
        if self.model is None:
            print(f"Loading Whisper model ({self.model_size})...")
            self.model = whisper.load_model(self.model_size)
        return self.model
    
    def chunk_audio(self, audio_path, output_dir="temp_chunks"):
        """
        Split audio into overlapping chunks for better processing.
        
        Args:
            audio_path: Path to the audio file
            output_dir: Directory to store temporary chunks
            
        Returns:
            List of chunk information
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Load audio with pydub
        audio = AudioSegment.from_file(audio_path)
        duration = len(audio) / 1000  # duration in seconds
        
        chunks = []
        chunk_start = 0
        chunk_id = 0
        
        while chunk_start < duration:
            chunk_end = min(chunk_start + self.chunk_duration, duration)
            
            # Extract chunk
            start_ms = chunk_start * 1000
            end_ms = chunk_end * 1000
            chunk_audio = audio[start_ms:end_ms]
            
            # Save chunk
            chunk_filename = f"chunk_{chunk_id:03d}.mp3"
            chunk_path = os.path.join(output_dir, chunk_filename)
            chunk_audio.export(chunk_path, format="mp3")
            
            chunks.append({
                "id": chunk_id,
                "filename": chunk_filename,
                "path": chunk_path,
                "start_time": chunk_start,
                "end_time": chunk_end,
                "duration": chunk_end - chunk_start
            })
            
            # Move to next chunk with overlap
            chunk_start += (self.chunk_duration - self.overlap_duration)
            chunk_id += 1
            
            if chunk_start >= duration:
                break
        
        print(f"Created {len(chunks)} audio chunks")
        return chunks
    
    def process_chunk(self, chunk_path, chunk_start_time):
        """
        Process a single audio chunk with Whisper.
        
        Args:
            chunk_path: Path to the chunk file
            chunk_start_time: Global start time of this chunk
            
        Returns:
            Processed segments with adjusted timestamps
        """
        model = self.load_model()
        
        # Load and process chunk
        audio = whisper.load_audio(chunk_path)
        result = whisper.transcribe(model, audio, language="tr", verbose=False)
        
        # Adjust timestamps to global time
        processed_segments = []
        for segment in result["segments"]:
            adjusted_segment = {
                "text": segment["text"].strip(),
                "start": segment["start"] + chunk_start_time,
                "end": segment["end"] + chunk_start_time,
                "confidence": segment.get("confidence", 0.0),
                "words": []
            }
            
            if "words" in segment:
                for word in segment["words"]:
                    adjusted_word = {
                        "text": word["text"].strip(),
                        "start": word["start"] + chunk_start_time,
                        "end": word["end"] + chunk_start_time,
                        "confidence": word.get("confidence", 0.0)
                    }
                    adjusted_segment["words"].append(adjusted_word)
            
            processed_segments.append(adjusted_segment)
        
        return processed_segments
    
    def merge_overlapping_segments(self, all_segments):
        """
        Merge segments from overlapping chunks, removing duplicates.
        
        Args:
            all_segments: List of all segments from all chunks
            
        Returns:
            Merged and deduplicated segments
        """
        if not all_segments:
            return []
        
        # Sort by start time
        all_segments.sort(key=lambda x: x["start"])
        
        merged = []
        current_segment = all_segments[0].copy()
        
        for segment in all_segments[1:]:
            # Check for overlap
            if segment["start"] <= current_segment["end"]:
                # Choose segment with higher confidence or longer duration
                current_confidence = current_segment.get("confidence", 0)
                segment_confidence = segment.get("confidence", 0)
                
                if segment_confidence > current_confidence:
                    # Extend current segment end time if needed
                    current_segment["end"] = max(current_segment["end"], segment["end"])
                    # Keep the more confident text
                    current_segment["text"] = segment["text"]
                    current_segment["words"] = segment["words"]
                    current_segment["confidence"] = segment_confidence
            else:
                # No overlap, add current segment and start new one
                merged.append(current_segment)
                current_segment = segment.copy()
        
        # Add the last segment
        merged.append(current_segment)
        
        return merged
    
    def process_with_chunks(self, audio_path):
        """
        Process entire audio file using chunked approach.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Combined processing results
        """
        print(f"Processing {audio_path} with chunked approach...")
        
        # Create chunks
        chunks = self.chunk_audio(audio_path)
        
        # Process each chunk
        all_segments = []
        
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}: {chunk['start_time']:.1f}s-{chunk['end_time']:.1f}s")
            
            chunk_segments = self.process_chunk(chunk["path"], chunk["start_time"])
            all_segments.extend(chunk_segments)
            
            # Clean up chunk file
            os.remove(chunk["path"])
        
        # Clean up temp directory
        try:
            os.rmdir("temp_chunks")
        except:
            pass
        
        # Merge overlapping segments
        merged_segments = self.merge_overlapping_segments(all_segments)
        
        print(f"Processed {len(chunks)} chunks into {len(merged_segments)} segments")
        
        return {
            "language": "tr",
            "segments": merged_segments,
            "processing_method": "chunked",
            "model_size": self.model_size,
            "chunk_count": len(chunks)
        }

def main():
    # Initialize processor with large model for best accuracy
    processor = AdvancedAudioProcessor(model_size="large-v3")
    
    # Process audio
    audio_path = "data/raw/yana.mp3"
    results = processor.process_with_chunks(audio_path)
    
    # Save results
    output_path = "data/processed/yana_chunked_large.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Advanced processing complete! Results saved to: {output_path}")
    
    # Print summary
    print(f"\nProcessing Summary:")
    print(f"Model: {results['processing_method']} with {results['model_size']}")
    print(f"Chunks processed: {results['chunk_count']}")
    print(f"Total segments: {len(results['segments'])}")
    print(f"Total words: {sum(len(seg.get('words', [])) for seg in results['segments'])}")
    
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