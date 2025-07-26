import json
import numpy as np
from dtw import dtw
import re
import difflib
from syllable_splitter import split_turkish_word, estimate_syllable_timings

def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj

class AdvancedLyricsAligner:
    def __init__(self):
        """
        Advanced lyrics aligner using Dynamic Time Warping and text similarity.
        """
        self.turkish_stopwords = {'ve', 'bir', 'bu', 'da', 'de', 'ile', 'için', 'var', 'yok'}
        
    def normalize_text(self, text):
        """
        Normalize text for better matching.
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation except Turkish characters
        text = re.sub(r'[^\w\sçğıöşüÇĞIİÖŞÜ]', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def extract_words(self, text):
        """Extract words from text, filtering stopwords."""
        words = self.normalize_text(text).split()
        return [w for w in words if w and w not in self.turkish_stopwords]
    
    def calculate_text_similarity(self, text1, text2):
        """
        Calculate similarity between two text segments.
        
        Args:
            text1, text2: Text strings to compare
            
        Returns:
            Similarity score (0-1)
        """
        words1 = set(self.extract_words(text1))
        words2 = set(self.extract_words(text2))
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def create_similarity_matrix(self, whisper_segments, reference_lines):
        """
        Create similarity matrix between Whisper segments and reference lyrics.
        
        Args:
            whisper_segments: List of Whisper transcription segments
            reference_lines: List of reference lyric lines
            
        Returns:
            Similarity matrix
        """
        matrix = np.zeros((len(whisper_segments), len(reference_lines)))
        
        for i, w_seg in enumerate(whisper_segments):
            for j, ref_line in enumerate(reference_lines):
                similarity = self.calculate_text_similarity(w_seg['text'], ref_line)
                matrix[i, j] = similarity
        
        return matrix
    
    def align_with_dtw(self, whisper_segments, reference_lines):
        """
        Use Dynamic Time Warping to align segments with reference lyrics.
        
        Args:
            whisper_segments: Whisper transcription segments
            reference_lines: Reference lyric lines
            
        Returns:
            Alignment mapping
        """
        # Create similarity matrix (convert to distance by subtracting from 1)
        similarity_matrix = self.create_similarity_matrix(whisper_segments, reference_lines)
        distance_matrix = 1 - similarity_matrix
        
        # Apply DTW
        alignment = dtw(distance_matrix)
        distance = alignment.distance
        path = list(zip(alignment.index1, alignment.index2))
        
        # Extract alignment path
        alignments = []
        for whisper_idx, ref_idx in path:
            if whisper_idx < len(whisper_segments) and ref_idx < len(reference_lines):
                alignments.append({
                    'whisper_segment': whisper_segments[whisper_idx],
                    'reference_line': reference_lines[ref_idx],
                    'whisper_index': whisper_idx,
                    'reference_index': ref_idx,
                    'similarity': similarity_matrix[whisper_idx, ref_idx]
                })
        
        return alignments, distance
    
    def create_aligned_segments(self, alignments, reference_lines):
        """
        Create final aligned segments with timing and correct lyrics.
        
        Args:
            alignments: DTW alignment results
            reference_lines: Reference lyric lines
            
        Returns:
            List of aligned segments
        """
        aligned_segments = []
        
        # Group alignments by reference line
        ref_groups = {}
        for alignment in alignments:
            ref_idx = alignment['reference_index']
            if ref_idx not in ref_groups:
                ref_groups[ref_idx] = []
            ref_groups[ref_idx].append(alignment)
        
        # Create segments for each reference line
        for ref_idx in sorted(ref_groups.keys()):
            group = ref_groups[ref_idx]
            reference_text = reference_lines[ref_idx]
            
            # Get timing from Whisper segments in this group
            start_time = float(min(a['whisper_segment']['start'] for a in group))
            end_time = float(max(a['whisper_segment']['end'] for a in group))
            
            # Calculate average confidence
            avg_confidence = float(np.mean([
                a['whisper_segment'].get('confidence', 0.5) for a in group
            ]))
            
            # Create aligned segment
            aligned_segment = {
                "id": f"aligned_{ref_idx:03d}",
                "text": reference_text,
                "start": start_time,
                "end": end_time,
                "confidence": avg_confidence,
                "alignment_quality": float(np.mean([a['similarity'] for a in group])),
                "words": []
            }
            
            # Create word-level alignment
            words = reference_text.split()
            if words:
                segment_duration = end_time - start_time
                word_duration = segment_duration / len(words)
                
                current_time = start_time
                for word in words:
                    word_start = current_time
                    word_end = current_time + word_duration
                    
                    # Split into syllables
                    syllables = split_turkish_word(word)
                    syllable_timings = estimate_syllable_timings(
                        word_start, word_end, syllables
                    )
                    
                    aligned_word = {
                        "text": word,
                        "start": round(word_start, 3),
                        "end": round(word_end, 3),
                        "confidence": avg_confidence,
                        "syllables": syllable_timings
                    }
                    
                    aligned_segment["words"].append(aligned_word)
                    current_time += word_duration
            
            aligned_segments.append(aligned_segment)
        
        return aligned_segments
    
    def process_alignment(self, whisper_file, reference_lyrics):
        """
        Main processing function for advanced alignment.
        
        Args:
            whisper_file: Path to Whisper transcription JSON
            reference_lyrics: List of reference lyric lines
            
        Returns:
            Advanced alignment results
        """
        # Load Whisper results
        with open(whisper_file, 'r', encoding='utf-8') as f:
            whisper_data = json.load(f)
        
        whisper_segments = whisper_data['segments']
        
        print(f"Aligning {len(whisper_segments)} Whisper segments with {len(reference_lyrics)} reference lines...")
        
        # Perform DTW alignment
        alignments, total_distance = self.align_with_dtw(whisper_segments, reference_lyrics)
        
        # Create final aligned segments
        aligned_segments = self.create_aligned_segments(alignments, reference_lyrics)
        
        # Calculate overall alignment quality
        if alignments:
            avg_similarity = float(np.mean([a['similarity'] for a in alignments]))
            alignment_quality = avg_similarity
        else:
            alignment_quality = 0.0
        
        print(f"Alignment complete! Quality score: {alignment_quality:.3f}")
        
        return {
            "metadata": {
                "title": "Yana Yana",
                "artists": ["Semicenk", "Reynmen"],
                "duration": whisper_segments[-1]['end'] if whisper_segments else 0,
                "language": "tr",
                "alignment_method": "DTW",
                "alignment_quality": alignment_quality,
                "total_distance": float(total_distance)
            },
            "segments": aligned_segments,
            "raw_alignments": alignments[:10]  # Keep first 10 for debugging
        }

from reference_lyrics import get_reference_lyrics, add_translations_to_segments

def main():
    """
    Main function to demonstrate advanced alignment.
    """
    aligner = AdvancedLyricsAligner()
    
    # Use the chunked processing results if available, otherwise fall back to basic
    whisper_file = "data/processed/yana_chunked_large.json"
    if not os.path.exists(whisper_file):
        whisper_file = "data/processed/yana_whisper_raw.json"
    
    # Get reference lyrics
    reference_lyrics = get_reference_lyrics()
    
    # Process alignment
    results = aligner.process_alignment(whisper_file, reference_lyrics)
    
    # Add translations to the results
    results["segments"] = add_translations_to_segments(results["segments"])
    
    # Save results (convert numpy types for JSON serialization)
    output_path = "data/processed/yana_dtw_aligned.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(convert_numpy_types(results), f, ensure_ascii=False, indent=2)
    
    print(f"DTW alignment saved to: {output_path}")
    
    # Print summary
    metadata = results['metadata']
    print(f"\nAlignment Summary:")
    print(f"Method: {metadata['alignment_method']}")
    print(f"Quality: {metadata['alignment_quality']:.3f}")
    print(f"Segments: {len(results['segments'])}")
    
    # Show alignment quality for each segment
    print(f"\nSegment Quality Scores:")
    for i, segment in enumerate(results['segments'][:5]):
        print(f"  {i+1}. '{segment['text'][:30]}...' - Quality: {segment.get('alignment_quality', 0):.3f}")

if __name__ == "__main__":
    import os
    main()