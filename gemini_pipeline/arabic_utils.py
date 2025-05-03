import re

# Diacritical marks (Tashkeel) in Arabic
ARABIC_DIACRITICS = re.compile("""
    [\u064B-\u065F]  # Fathatan, Dammatan, Kasratan, Fatha, Damma, Kasra, Shadda, Sukun, etc.
    |
    [\u0610-\u061A]  # Arabic Diacritical Marks for Koranic Annotations
    |
    [\u06D6-\u06DC]  # Arabic Small Waqf, Sajdah, etc.
    |
    [\u06DF-\u06E4]  # Arabic Small High Rounded Zero, etc.
    |
    [\u06E7\u06E8]    # Arabic Small High Yeh, Noon
    |
    [\u06EA-\u06ED]  # Arabic Empty Centre Low Stop, etc.
    """, re.VERBOSE)

def strip_tashkeel(text):
    """
    Remove Arabic diacritical marks (tashkeel) from the text.
    
    Args:
        text (str): Arabic text with diacritical marks
        
    Returns:
        str: Clean text without diacritical marks
    """
    if not text:
        return text
    
    return ARABIC_DIACRITICS.sub('', text)

def normalize_arabic_text(text):
    """
    Normalize Arabic text by:
    1. Removing diacritical marks
    2. Normalizing different forms of Alef (أ,إ,آ -> ا)
    3. Removing special characters and extra spaces
    
    Args:
        text (str): Raw Arabic text
        
    Returns:
        str: Normalized Arabic text
    """
    if not text:
        return text
    
    # Remove tashkeel (diacritical marks)
    text = strip_tashkeel(text)
    
    # Normalize different forms of Alef
    text = re.sub('[أإآ]', 'ا', text)
    
    # Remove non-Arabic characters (keeping spaces and numbers and colons for verse references)
    text = re.sub(r'[^\u0600-\u06FF\s0-9:.]', '', text)
    
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_quran_reference(text):
    """
    Try to extract a Quran reference from text in various formats
    like "2:255" (Surah 2, Ayah 255) or "البقرة 255" (Surah Al-Baqarah, Ayah 255)
    
    Args:
        text (str): Text containing potential Quran reference
        
    Returns:
        dict: Dictionary with surah_number and ayah_number or None if not found
    """
    # Look for the format "X:Y" (Surah:Ayah)
    match = re.search(r'(\d+)[:\-](\d+)', text)
    if match:
        return {
            'surah_number': int(match.group(1)),
            'ayah_number': int(match.group(2))
        }
    
    # More advanced extraction logic can be added here
    
    return None 