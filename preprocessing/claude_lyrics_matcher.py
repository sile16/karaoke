import json
import os
import subprocess
import tempfile
from pathlib import Path

class ClaudeLyricsMatcher:
    def __init__(self):
        """
        Claude-powered intelligent lyrics matching system.
        Uses the local Claude Code installation for smart alignment.
        """
        self.temp_dir = tempfile.mkdtemp()
    
    def create_matching_prompt(self, whisper_transcription, reference_lyrics):
        """
        Create a prompt for Claude to intelligently match transcription to reference lyrics.
        
        Args:
            whisper_transcription: Raw transcription from Whisper/ElevenLabs
            reference_lyrics: Known correct lyrics
            
        Returns:
            Formatted prompt for Claude
        """
        prompt = f"""I need help matching audio transcription to reference lyrics for a Turkish song.

**TASK**: Match each transcribed segment to the correct reference lyric line, considering:
1. Turkish phonetic similarities (ş/s, ç/c, ğ/g, etc.)
2. Singing voice distortions
3. Sequential order (lyrics should flow naturally)
4. Timing constraints (segments should not overlap inappropriately)

**TRANSCRIBED SEGMENTS** (with timestamps):
"""
        
        for i, segment in enumerate(whisper_transcription):
            words_text = " ".join([w.get('text', '') for w in segment.get('words', [])])
            prompt += f"{i+1}. [{segment['start']:.1f}s-{segment['end']:.1f}s] \"{segment['text']}\" (words: {words_text})\n"
        
        prompt += f"""

**REFERENCE LYRICS** (correct text):
"""
        
        for i, lyric in enumerate(reference_lyrics):
            prompt += f"{i+1}. \"{lyric}\"\n"
        
        prompt += """

**OUTPUT FORMAT** (JSON only, no explanations):
```json
{
  "matches": [
    {
      "transcription_index": 0,
      "reference_index": 0,
      "confidence": 0.95,
      "reasoning": "exact match",
      "start_time": 10.5,
      "end_time": 14.2
    }
  ],
  "sequential_check": "passed",
  "timing_issues": [],
  "suggested_corrections": []
}
```

Please provide intelligent matching that prioritizes:
1. Sequential lyric flow
2. Phonetic similarity for Turkish
3. Reasonable timing intervals
4. Avoiding overlapping segments
"""
        
        return prompt
    
    def run_claude_matching(self, prompt):
        """
        Run Claude Code to get intelligent lyrics matching.
        
        Args:
            prompt: The matching prompt
            
        Returns:
            Claude's response with matching results
        """
        # Write prompt to temporary file
        prompt_file = os.path.join(self.temp_dir, "matching_prompt.txt")
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        try:
            # Use Claude Code CLI to process the prompt
            print("Running Claude Code for intelligent lyrics matching...")
            result = subprocess.run([
                'claude', 'code', 
                '--file', prompt_file,
                '--output', 'json'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"Claude Code error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("Claude Code timed out")
            return None
        except FileNotFoundError:
            print("Claude Code CLI not found. Falling back to simple matching.")
            return None
    
    def fallback_matching(self, whisper_transcription, reference_lyrics):
        """
        Fallback matching algorithm if Claude Code is not available.
        
        Args:
            whisper_transcription: Transcription segments
            reference_lyrics: Reference lyric lines
            
        Returns:
            Basic matching results
        """
        print("Using fallback matching algorithm...")
        
        from difflib import SequenceMatcher
        
        matches = []
        used_references = set()
        
        for i, segment in enumerate(whisper_transcription):
            best_match = None
            best_score = 0
            
            segment_text = segment['text'].lower().strip()
            
            for j, ref_lyric in enumerate(reference_lyrics):
                if j in used_references:
                    continue
                    
                ref_text = ref_lyric.lower().strip()
                
                # Calculate similarity
                similarity = SequenceMatcher(None, segment_text, ref_text).ratio()
                
                # Bonus for sequential order
                if not matches or j > matches[-1]['reference_index']:
                    similarity += 0.1
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = j
            
            if best_match is not None and best_score > 0.3:
                matches.append({
                    "transcription_index": i,
                    "reference_index": best_match,
                    "confidence": best_score,
                    "reasoning": "fallback_algorithm",
                    "start_time": segment['start'],
                    "end_time": segment['end']
                })
                used_references.add(best_match)
        
        return {
            "matches": matches,
            "sequential_check": "fallback",
            "timing_issues": [],
            "suggested_corrections": []
        }
    
    def process_matching(self, whisper_file, reference_lyrics):
        """
        Main function to process intelligent lyrics matching.
        
        Args:
            whisper_file: Path to Whisper/ElevenLabs transcription
            reference_lyrics: List of reference lyric lines
            
        Returns:
            Intelligent matching results
        """
        # Load transcription data
        with open(whisper_file, 'r', encoding='utf-8') as f:
            transcription_data = json.load(f)
        
        segments = transcription_data['segments']
        
        print(f"Processing {len(segments)} transcribed segments against {len(reference_lyrics)} reference lines...")
        
        # Create prompt for Claude
        prompt = self.create_matching_prompt(segments, reference_lyrics)
        
        # Try Claude Code first
        claude_response = self.run_claude_matching(prompt)
        
        if claude_response:
            try:
                # Parse Claude's response
                # Extract JSON from Claude's response (it might include explanations)
                import re
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', claude_response, re.DOTALL)
                if json_match:
                    matching_result = json.loads(json_match.group(1))
                else:
                    # Try to parse the whole response as JSON
                    matching_result = json.loads(claude_response)
                
                print("Claude Code matching successful!")
                matching_result['method'] = 'claude_code'
                
            except json.JSONDecodeError:
                print("Failed to parse Claude's response, using fallback...")
                matching_result = self.fallback_matching(segments, reference_lyrics)
        else:
            # Use fallback matching
            matching_result = self.fallback_matching(segments, reference_lyrics)
        
        return matching_result
    
    def create_aligned_segments(self, matching_result, transcription_data, reference_lyrics):
        """
        Create final aligned segments based on Claude's intelligent matching.
        
        Args:
            matching_result: Results from Claude matching
            transcription_data: Original transcription data
            reference_lyrics: Reference lyrics
            
        Returns:
            Properly aligned segments
        """
        segments = transcription_data['segments']
        aligned_segments = []
        
        for match in matching_result['matches']:
            trans_idx = match['transcription_index']
            ref_idx = match['reference_index']
            
            if trans_idx < len(segments) and ref_idx < len(reference_lyrics):
                original_segment = segments[trans_idx]
                reference_text = reference_lyrics[ref_idx]
                
                aligned_segment = {
                    "id": f"claude_aligned_{ref_idx:03d}",
                    "text": reference_text,  # Use correct reference text
                    "start": match['start_time'],
                    "end": match['end_time'],
                    "confidence": match['confidence'],
                    "alignment_method": matching_result.get('method', 'claude_code'),
                    "original_transcription": original_segment['text'],
                    "words": []
                }
                
                # Create word-level alignment
                words = reference_text.split()
                if words and 'words' in original_segment:
                    # Distribute timing across reference words
                    segment_duration = match['end_time'] - match['start_time']
                    word_duration = segment_duration / len(words)
                    
                    current_time = match['start_time']
                    for word in words:
                        aligned_word = {
                            "text": word,
                            "start": round(current_time, 3),
                            "end": round(current_time + word_duration, 3),
                            "confidence": match['confidence']
                        }
                        aligned_segment["words"].append(aligned_word)
                        current_time += word_duration
                
                aligned_segments.append(aligned_segment)
        
        return aligned_segments
    
    def cleanup(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

def main():
    """
    Demo function showing Claude-powered lyrics matching.
    """
    from reference_lyrics import get_reference_lyrics
    
    matcher = ClaudeLyricsMatcher()
    
    try:
        # Use ElevenLabs results if available, otherwise Whisper
        input_file = "data/processed/yana_elevenlabs_processed.json"
        if not os.path.exists(input_file):
            input_file = "data/processed/yana_chunked_large.json"
        
        reference_lyrics = get_reference_lyrics()
        
        # Get intelligent matching from Claude
        matching_result = matcher.process_matching(input_file, reference_lyrics)
        
        # Load original transcription
        with open(input_file, 'r', encoding='utf-8') as f:
            transcription_data = json.load(f)
        
        # Create aligned segments
        aligned_segments = matcher.create_aligned_segments(
            matching_result, transcription_data, reference_lyrics
        )
        
        # Create final result
        final_result = {
            "metadata": {
                "title": "Yana Yana",
                "artists": ["Semicenk", "Reynmen"],
                "duration": transcription_data.get('total_duration', 0),
                "language": "tr",
                "alignment_method": "claude_intelligent",
                "alignment_quality": matching_result.get('confidence', 0),
                "claude_method": matching_result.get('method', 'claude_code')
            },
            "segments": aligned_segments,
            "matching_details": matching_result
        }
        
        # Save results
        output_path = "data/processed/yana_claude_aligned.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        
        print(f"Claude-powered alignment complete! Saved to: {output_path}")
        print(f"Method: {final_result['metadata']['claude_method']}")
        print(f"Segments: {len(aligned_segments)}")
        print(f"Matches: {len(matching_result['matches'])}")
        
    finally:
        matcher.cleanup()

if __name__ == "__main__":
    main()