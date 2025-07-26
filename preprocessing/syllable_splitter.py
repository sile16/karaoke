import re
from hyphenate import hyphenate_word

def split_turkish_word(word):
    """
    Split a Turkish word into syllables using rules and the hyphenate library.
    Turkish syllabification follows specific rules based on vowels and consonants.
    """
    # Turkish vowels
    vowels = 'aeıioöuüAEIİOÖUÜ'
    
    # Clean the word of punctuation for syllabification
    clean_word = re.sub(r'[^\w]', '', word)
    
    if not clean_word:
        return []
    
    # Try using the hyphenate library first
    try:
        syllables = hyphenate_word(clean_word, language='tr')
        if syllables and len(syllables) > 1:
            return syllables
    except:
        pass
    
    # Fallback to basic Turkish syllabification rules
    syllables = []
    current_syllable = ""
    
    for i, char in enumerate(clean_word):
        current_syllable += char
        
        if char in vowels:
            # Look ahead to determine syllable boundary
            if i + 1 < len(clean_word):
                next_char = clean_word[i + 1]
                
                # If next char is consonant
                if next_char not in vowels:
                    # If there's another char after the consonant
                    if i + 2 < len(clean_word):
                        next_next_char = clean_word[i + 2]
                        
                        # If next_next is vowel, include the consonant in current syllable
                        if next_next_char in vowels:
                            current_syllable += next_char
                            i += 1
                    
                    # End current syllable
                    syllables.append(current_syllable)
                    current_syllable = ""
                else:
                    # Two vowels in a row, split between them
                    syllables.append(current_syllable)
                    current_syllable = ""
    
    # Add remaining characters
    if current_syllable:
        if syllables:
            # Attach remaining consonants to the last syllable
            if all(c not in vowels for c in current_syllable):
                syllables[-1] += current_syllable
            else:
                syllables.append(current_syllable)
        else:
            syllables.append(current_syllable)
    
    return syllables if syllables else [clean_word]

def estimate_syllable_timings(word_start, word_end, syllables):
    """
    Estimate timing for each syllable within a word.
    Uses simple linear distribution as a starting point.
    """
    if not syllables:
        return []
    
    word_duration = word_end - word_start
    syllable_count = len(syllables)
    
    # Simple equal distribution (can be improved with phonetic analysis)
    syllable_duration = word_duration / syllable_count
    
    timings = []
    current_time = word_start
    
    for syllable in syllables:
        timings.append({
            "text": syllable,
            "start": round(current_time, 3),
            "end": round(current_time + syllable_duration, 3)
        })
        current_time += syllable_duration
    
    return timings

def process_lyrics_with_syllables(segments):
    """
    Process lyrics segments to add syllable information.
    """
    processed_segments = []
    
    for segment in segments:
        processed_segment = segment.copy()
        
        if "words" in segment:
            processed_words = []
            
            for word in segment["words"]:
                processed_word = word.copy()
                
                # Split word into syllables
                syllables = split_turkish_word(word["text"])
                
                # Estimate syllable timings
                syllable_timings = estimate_syllable_timings(
                    word["start"], 
                    word["end"], 
                    syllables
                )
                
                processed_word["syllables"] = syllable_timings
                processed_words.append(processed_word)
            
            processed_segment["words"] = processed_words
        
        processed_segments.append(processed_segment)
    
    return processed_segments

# Test the syllable splitter
if __name__ == "__main__":
    test_words = [
        "Yana", "yana", "sevdik", "bazen",
        "unutulup", "gidinin", "ardından",
        "Türkiye", "merhaba", "teşekkür"
    ]
    
    print("Turkish Syllable Splitter Test:")
    print("-" * 40)
    
    for word in test_words:
        syllables = split_turkish_word(word)
        print(f"{word:15} -> {' - '.join(syllables)}")