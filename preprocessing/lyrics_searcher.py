import requests
import json
import re
import time
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
from urllib.parse import quote

class LyricsSearcher:
    """
    Web-based lyrics searcher that finds lyrics from multiple sources
    and verifies them for accuracy.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds between requests
    
    def search_lyrics(self, title: str, artist: str, language: str = "tr") -> Dict[str, Any]:
        """
        Search for lyrics from multiple sources and verify consistency.
        
        Args:
            title: Song title
            artist: Artist name
            language: Language code (tr, en, etc.)
            
        Returns:
            Dictionary with sources and verification results
        """
        print(f"Searching lyrics for: {artist} - {title} ({language})")
        
        sources = []
        search_results = {
            "title": title,
            "artist": artist,
            "language": language,
            "sources": [],
            "verified": False,
            "confidence": 0.0,
            "search_summary": {}
        }
        
        try:
            # Search multiple sources
            sources.extend(self.search_genius(title, artist))
            sources.extend(self.search_azlyrics(title, artist))
            sources.extend(self.search_lyrics_com(title, artist))
            
            # Language-specific sources
            if language == "tr":
                sources.extend(self.search_turkish_sources(title, artist))
            
            # Filter and verify sources
            verified_sources = self.verify_sources(sources)
            
            search_results["sources"] = verified_sources
            search_results["verified"] = len(verified_sources) >= 2
            search_results["confidence"] = self.calculate_confidence(verified_sources)
            search_results["search_summary"] = {
                "total_sources_found": len(sources),
                "verified_sources": len(verified_sources),
                "search_methods": ["genius", "azlyrics", "lyrics_com", "turkish_sources"] if language == "tr" else ["genius", "azlyrics", "lyrics_com"]
            }
            
            print(f"Found {len(verified_sources)} verified sources (confidence: {search_results['confidence']:.2f})")
            
        except Exception as e:
            print(f"Lyrics search error: {e}")
            search_results["error"] = str(e)
        
        return search_results
    
    def rate_limit(self):
        """Implement rate limiting between requests."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def search_genius(self, title: str, artist: str) -> List[Dict[str, Any]]:
        """Search Genius.com for lyrics."""
        sources = []
        
        try:
            self.rate_limit()
            
            # Search for the song
            search_query = f"{artist} {title}"
            search_url = f"https://genius.com/api/search/multi?q={quote(search_query)}"
            
            response = self.session.get(search_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Look for song matches
                for section in data.get('response', {}).get('sections', []):
                    if section.get('type') == 'song':
                        for hit in section.get('hits', [])[:3]:  # Top 3 results
                            song = hit.get('result', {})
                            song_url = song.get('url')
                            
                            if song_url:
                                lyrics = self.extract_genius_lyrics(song_url)
                                if lyrics:
                                    sources.append({
                                        "url": song_url,
                                        "site_name": "Genius",
                                        "lyrics": lyrics,
                                        "confidence": self.calculate_match_confidence(title, artist, song),
                                        "metadata": {
                                            "song_title": song.get('title', ''),
                                            "artist_name": song.get('primary_artist', {}).get('name', ''),
                                            "page_views": song.get('stats', {}).get('pageviews', 0)
                                        }
                                    })
        except Exception as e:
            print(f"Genius search error: {e}")
        
        return sources
    
    def extract_genius_lyrics(self, url: str) -> Optional[str]:
        """Extract lyrics from a Genius page."""
        try:
            self.rate_limit()
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                html = response.text
                
                # Look for lyrics in various containers
                lyrics_patterns = [
                    r'<div[^>]*data-lyrics-container[^>]*>(.*?)</div>',
                    r'<div[^>]*class="[^"]*lyrics[^"]*"[^>]*>(.*?)</div>',
                    r'<p[^>]*>(.*?)</p>'
                ]
                
                for pattern in lyrics_patterns:
                    matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
                    if matches:
                        # Clean up HTML tags and extract text
                        lyrics_html = ''.join(matches)
                        lyrics_text = re.sub(r'<[^>]+>', '\n', lyrics_html)
                        lyrics_text = re.sub(r'\n+', '\n', lyrics_text).strip()
                        
                        if len(lyrics_text) > 100:  # Reasonable lyrics length
                            return lyrics_text
            
        except Exception as e:
            print(f"Error extracting Genius lyrics: {e}")
        
        return None
    
    def search_azlyrics(self, title: str, artist: str) -> List[Dict[str, Any]]:
        """Search AZLyrics for lyrics."""
        sources = []
        
        try:
            # AZLyrics uses a specific URL format
            clean_artist = re.sub(r'[^a-zA-Z0-9]', '', artist.lower())
            clean_title = re.sub(r'[^a-zA-Z0-9]', '', title.lower())
            
            url = f"https://www.azlyrics.com/lyrics/{clean_artist}/{clean_title}.html"
            
            self.rate_limit()
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                html = response.text
                
                # AZLyrics specific pattern
                pattern = r'<!-- Usage of azlyrics\.com content.*?-->(.*?)<!--'
                match = re.search(pattern, html, re.DOTALL)
                
                if match:
                    lyrics_html = match.group(1)
                    lyrics_text = re.sub(r'<[^>]+>', '\n', lyrics_html)
                    lyrics_text = re.sub(r'\n+', '\n', lyrics_text).strip()
                    
                    if len(lyrics_text) > 100:
                        sources.append({
                            "url": url,
                            "site_name": "AZLyrics",
                            "lyrics": lyrics_text,
                            "confidence": 0.9,  # AZLyrics is generally reliable
                            "metadata": {
                                "method": "direct_url"
                            }
                        })
        
        except Exception as e:
            print(f"AZLyrics search error: {e}")
        
        return sources
    
    def search_lyrics_com(self, title: str, artist: str) -> List[Dict[str, Any]]:
        """Search Lyrics.com for lyrics."""
        sources = []
        
        try:
            search_query = f"{artist} {title}"
            search_url = f"https://www.lyrics.com/serp.php?st={quote(search_query)}"
            
            self.rate_limit()
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                html = response.text
                
                # Look for song links
                link_pattern = r'href="(/lyric/[^"]+)"'
                links = re.findall(link_pattern, html)
                
                for link in links[:2]:  # Check top 2 results
                    full_url = f"https://www.lyrics.com{link}"
                    lyrics = self.extract_lyrics_com_lyrics(full_url)
                    
                    if lyrics:
                        sources.append({
                            "url": full_url,
                            "site_name": "Lyrics.com",
                            "lyrics": lyrics,
                            "confidence": 0.8,
                            "metadata": {
                                "method": "search_result"
                            }
                        })
        
        except Exception as e:
            print(f"Lyrics.com search error: {e}")
        
        return sources
    
    def extract_lyrics_com_lyrics(self, url: str) -> Optional[str]:
        """Extract lyrics from Lyrics.com page."""
        try:
            self.rate_limit()
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                html = response.text
                
                # Lyrics.com specific pattern
                pattern = r'<pre[^>]*id="lyric-body-text"[^>]*>(.*?)</pre>'
                match = re.search(pattern, html, re.DOTALL)
                
                if match:
                    lyrics_html = match.group(1)
                    lyrics_text = re.sub(r'<[^>]+>', '\n', lyrics_html)
                    lyrics_text = re.sub(r'\n+', '\n', lyrics_text).strip()
                    
                    return lyrics_text if len(lyrics_text) > 100 else None
        
        except Exception as e:
            print(f"Error extracting Lyrics.com lyrics: {e}")
        
        return None
    
    def search_turkish_sources(self, title: str, artist: str) -> List[Dict[str, Any]]:
        """Search Turkish-specific lyrics sources."""
        sources = []
        
        try:
            # Example Turkish lyrics sites (implement as needed)
            turkish_sites = [
                "sarki-sozleri.com",
                "turkuler.com",
                "lyrics.az"
            ]
            
            # This would implement Turkish-specific search logic
            # For now, return empty list
            pass
        
        except Exception as e:
            print(f"Turkish sources search error: {e}")
        
        return sources
    
    def verify_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verify and rank sources based on consistency."""
        if not sources:
            return []
        
        verified = []
        
        # Group similar lyrics
        groups = []
        for source in sources:
            lyrics = source["lyrics"]
            
            # Find similar group
            found_group = False
            for group in groups:
                if self.lyrics_similarity(lyrics, group[0]["lyrics"]) > 0.8:
                    group.append(source)
                    found_group = True
                    break
            
            if not found_group:
                groups.append([source])
        
        # Sort groups by size and confidence
        groups.sort(key=lambda g: (len(g), max(s["confidence"] for s in g)), reverse=True)
        
        # Take the best group(s)
        if groups:
            # Add sources from the largest group
            verified.extend(groups[0])
            
            # If we have multiple good groups, add representative sources
            for group in groups[1:]:
                if len(group) >= 2:  # Only if multiple sources agree
                    verified.append(max(group, key=lambda s: s["confidence"]))
        
        return verified
    
    def lyrics_similarity(self, lyrics1: str, lyrics2: str) -> float:
        """Calculate similarity between two lyrics texts."""
        # Normalize texts
        norm1 = re.sub(r'[^\w\s]', '', lyrics1.lower())
        norm2 = re.sub(r'[^\w\s]', '', lyrics2.lower())
        
        # Use sequence matcher
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def calculate_match_confidence(self, title: str, artist: str, song_data: Dict[str, Any]) -> float:
        """Calculate confidence that a found song matches the search."""
        title_sim = SequenceMatcher(None, title.lower(), song_data.get('title', '').lower()).ratio()
        artist_sim = SequenceMatcher(None, artist.lower(), song_data.get('artist_name', '').lower()).ratio()
        
        return (title_sim * 0.6 + artist_sim * 0.4)
    
    def calculate_confidence(self, sources: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence in the lyrics search results."""
        if not sources:
            return 0.0
        
        if len(sources) == 1:
            return sources[0]["confidence"] * 0.7  # Single source penalty
        
        # Multiple sources - check agreement
        if len(sources) >= 2:
            similarity = self.lyrics_similarity(sources[0]["lyrics"], sources[1]["lyrics"])
            base_confidence = sum(s["confidence"] for s in sources) / len(sources)
            
            return min(0.95, base_confidence * similarity)
        
        return 0.0

def main():
    """Demo the lyrics searcher."""
    searcher = LyricsSearcher()
    
    # Test with a known song
    result = searcher.search_lyrics("Yana Yana", "Semicenk Reynmen", "tr")
    
    print(f"\nLyrics Search Results:")
    print(f"Verified: {result['verified']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Sources found: {len(result['sources'])}")
    
    for i, source in enumerate(result['sources'][:2]):
        print(f"\nSource {i+1}: {source['site_name']}")
        print(f"URL: {source['url']}")
        print(f"Confidence: {source['confidence']:.2f}")
        print(f"Lyrics preview: {source['lyrics'][:200]}...")

if __name__ == "__main__":
    main()