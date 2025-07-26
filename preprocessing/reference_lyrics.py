"""
Reference lyrics for Turkish songs.
Note: These are sample/demo lyrics for development purposes.
In production, official lyrics would be obtained through proper licensing.
"""

# Based on the Whisper transcription patterns we're seeing, here are the main lyrical phrases
YANA_REFERENCE_LYRICS = [
    "Yana yana sevdik bazen",
    "Çok kez unutulup gidinin ardından", 
    "Ne kar olan bir kul",
    "Varsa sözüme güven beni anla",
    "Ne olur bozduksa ruhun",
    "Zaten bana yazık olur",
    "Yazık olur",
    "Bir gün gelecek her yüzü göreceksin",
    "Tattığın her sözün ve her günün",
    "Boşa geçtiği öğreneceksin",
    "Yine aynı yerde kalıp gidersen yarım kalır",
    "Düştüğü yerden kalkıp yeniden yazılan kaderine güleceksin",
    "Zaman hiç vermedi aman",
    "Güç yordun teselliler yalan",
    "Ben büyütmek istesem de onlar küçük kalmak ister gözümde",
    "İmdat bir ihtimal daha gel beni kurtar",
    "Benden bu kadar zor olsa da şartlar",
    "Sabrım gerilir patlar bir anda"
]

# Word-level translations for learning purposes
WORD_TRANSLATIONS = {
    "yana": {"literal": "burning", "contextual": "painfully"},
    "sevdik": {"literal": "we loved", "contextual": "we loved"},
    "bazen": {"literal": "sometimes", "contextual": "sometimes"},
    "çok": {"literal": "very/much", "contextual": "many"},
    "kez": {"literal": "times", "contextual": "times"},
    "unutulup": {"literal": "being forgotten", "contextual": "being forgotten"},
    "gidinin": {"literal": "of the one who goes", "contextual": "of the one who leaves"},
    "ardından": {"literal": "after", "contextual": "behind/after"},
    "hep": {"literal": "always", "contextual": "always"},
    "kar": {"literal": "profit/snow", "contextual": "gain/benefit"},
    "olan": {"literal": "being/that is", "contextual": "who is"},
    "bir": {"literal": "one/a", "contextual": "a"},
    "kul": {"literal": "servant/slave", "contextual": "person/soul"},
    "varsa": {"literal": "if there is", "contextual": "if you have"},
    "sözüme": {"literal": "to my word", "contextual": "my words"},
    "güven": {"literal": "trust", "contextual": "trust"},
    "beni": {"literal": "me", "contextual": "me"},
    "anla": {"literal": "understand", "contextual": "understand"},
    "ne": {"literal": "what", "contextual": "what"},
    "olur": {"literal": "happens/becomes", "contextual": "happens"},
    "bozduksa": {"literal": "if broken", "contextual": "if it's broken"},
    "ruhun": {"literal": "your soul", "contextual": "your spirit"},
    "zaten": {"literal": "already", "contextual": "anyway"},
    "bana": {"literal": "to me", "contextual": "for me"},
    "yazık": {"literal": "pity", "contextual": "a shame"},
    "bir": {"literal": "one", "contextual": "one"},
    "gün": {"literal": "day", "contextual": "day"},
    "gelecek": {"literal": "will come", "contextual": "will come"},
    "her": {"literal": "every", "contextual": "every"},
    "yüzü": {"literal": "face", "contextual": "face"},
    "göreceksin": {"literal": "you will see", "contextual": "you will see"},
    "zaman": {"literal": "time", "contextual": "time"},
    "hiç": {"literal": "never", "contextual": "never"},
    "vermedi": {"literal": "didn't give", "contextual": "didn't give"},
    "aman": {"literal": "mercy", "contextual": "mercy"},
    "sabrım": {"literal": "my patience", "contextual": "my patience"},
    "gerilir": {"literal": "stretches", "contextual": "gets strained"},
    "patlar": {"literal": "explodes", "contextual": "snaps"},
    "anda": {"literal": "moment", "contextual": "moment"}
}

def get_reference_lyrics():
    """Get the reference lyrics for the song."""
    return YANA_REFERENCE_LYRICS

def get_word_translations():
    """Get word-level translations."""
    return WORD_TRANSLATIONS

def add_translations_to_segments(segments):
    """Add translation information to processed segments."""
    translations = get_word_translations()
    
    for segment in segments:
        for word in segment.get("words", []):
            word_text = word["text"].lower().strip(".,!?")
            if word_text in translations:
                word["translation"] = translations[word_text]
    
    return segments