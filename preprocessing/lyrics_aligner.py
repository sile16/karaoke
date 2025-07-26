import json
from syllable_splitter import split_turkish_word, estimate_syllable_timings

# Correct lyrics for "Yana Yana" by Semicenk & Reynmen
# Note: Using partial lyrics for demonstration - in production, 
# you'd get these from the artist or lyric database
CORRECT_LYRICS = [
    "Yana yana sevdik bazen",
    "Çok kez unutulup gidinin ardından", 
    "Ne kar olan bir kul",
    "Varsa sözüme güven beni anla",
    "Ne olur bozduksa ruhun",
    "Zaten bana yazık olur"
]

def create_aligned_lyrics(whisper_segments, correct_lyrics):
    """
    Align correct lyrics with Whisper timing information.
    This is a simplified approach - in production you'd use more sophisticated alignment.
    """
    aligned_segments = []
    
    # For this demo, we'll map the segments to our known lyrics
    for i, segment in enumerate(whisper_segments[:len(correct_lyrics)]):
        # Use timing from Whisper but correct lyrics
        aligned_segment = {
            "id": f"seg_{i:03d}",
            "text": correct_lyrics[i],
            "start": segment["start"],
            "end": segment["end"],
            "words": []
        }
        
        # Split lyrics line into words
        words = correct_lyrics[i].split()
        word_count = len(words)
        
        if word_count > 0:
            segment_duration = segment["end"] - segment["start"]
            word_duration = segment_duration / word_count
            
            current_time = segment["start"]
            
            for word in words:
                word_start = current_time
                word_end = current_time + word_duration
                
                # Split word into syllables
                syllables = split_turkish_word(word)
                syllable_timings = estimate_syllable_timings(
                    word_start, word_end, syllables
                )
                
                aligned_word = {
                    "text": word,
                    "start": round(word_start, 3),
                    "end": round(word_end, 3),
                    "confidence": 0.8,  # Placeholder confidence
                    "syllables": syllable_timings
                }
                
                aligned_segment["words"].append(aligned_word)
                current_time += word_duration
        
        aligned_segments.append(aligned_segment)
    
    return aligned_segments

def create_song_metadata():
    """Create metadata for the song."""
    return {
        "title": "Yana Yana",
        "artists": ["Semicenk", "Reynmen"],
        "duration": 147.0,
        "language": "tr",
        "audio_file": "data/raw/yana.mp3"
    }

def add_translations(aligned_segments):
    """Add English translations for demonstration."""
    # Sample translations - in production, these would come from a translation service
    translations = {
        "Yana": {"literal": "Burning", "contextual": "Painfully"},
        "yana": {"literal": "burning", "contextual": "painfully"},
        "sevdik": {"literal": "we loved", "contextual": "we loved"},
        "bazen": {"literal": "sometimes", "contextual": "sometimes"},
        "Çok": {"literal": "Very", "contextual": "Many"},
        "kez": {"literal": "times", "contextual": "times"},
        "unutulup": {"literal": "being forgotten", "contextual": "being forgotten"},
        "gidinin": {"literal": "of the one who leaves", "contextual": "of the one who goes away"},
        "ardından": {"literal": "after", "contextual": "after"}
    }
    
    for segment in aligned_segments:
        for word in segment["words"]:
            word_text = word["text"]
            if word_text in translations:
                word["translation"] = translations[word_text]
    
    return aligned_segments

def main():
    # Load Whisper results
    with open("data/processed/yana_whisper_raw.json", 'r', encoding='utf-8') as f:
        whisper_data = json.load(f)
    
    # Create aligned lyrics
    aligned_segments = create_aligned_lyrics(whisper_data["segments"], CORRECT_LYRICS)
    
    # Add translations
    aligned_segments = add_translations(aligned_segments)
    
    # Create final structure
    final_data = {
        "metadata": create_song_metadata(),
        "segments": aligned_segments
    }
    
    # Save aligned results
    output_path = "data/processed/yana_aligned.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"Aligned lyrics saved to: {output_path}")
    
    # Print summary
    print(f"\nAlignment Summary:")
    print(f"Total segments: {len(aligned_segments)}")
    print(f"Total words: {sum(len(seg['words']) for seg in aligned_segments)}")
    
    # Show first segment details
    if aligned_segments:
        first_segment = aligned_segments[0]
        print(f"\nFirst segment example:")
        print(f"Text: {first_segment['text']}")
        print(f"Time: {first_segment['start']:.2f}s - {first_segment['end']:.2f}s")
        print(f"Words with syllables:")
        
        for word in first_segment["words"][:3]:  # Show first 3 words
            syllables = [s["text"] for s in word["syllables"]]
            print(f"  {word['text']}: {'-'.join(syllables)} "
                  f"({word['start']:.2f}s-{word['end']:.2f}s)")
            if "translation" in word:
                print(f"    → {word['translation']['literal']}")

if __name__ == "__main__":
    main()