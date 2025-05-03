from .tafsir_processor import process_text_input
from .ocr_processor import process_quran_image, process_telegram_photo, cleanup_temp_files
from .arabic_utils import normalize_arabic_text, strip_tashkeel
from dotenv import load_dotenv
import gc
import atexit

# Load environment variables
load_dotenv()

__all__ = ['get_tafsir_from_text', 'get_tafsir_from_image', 'get_tafsir_from_telegram_photo', 'cleanup_resources']

# Register cleanup function to run at exit
atexit.register(cleanup_temp_files)

# Error class for invalid Quran verses
class InvalidQuranVerseError(Exception):
    """Raised when the extracted text is not a valid Quran verse."""
    def __init__(self, text, confidence, message):
        self.text = text
        self.confidence = confidence
        self.message = message
        super().__init__(f"Invalid Quran verse: {message} (Confidence: {confidence}%)")

def cleanup_resources():
    """
    Clean up any temporary resources and files.
    Call this explicitly if needed, otherwise it will be called on exit.
    """
    cleanup_temp_files()
    gc.collect()

def get_tafsir_from_text(quran_verse_text, tafsir_sources=None, validate=True, language="en"):
    """
    Get tafsir for a Quran verse provided as text, in the requested language.
    
    Args:
        quran_verse_text (str): Arabic text of the Quran verse
        tafsir_sources (list): Optional list of tafsir sources to use
        validate (bool): Whether to validate the text is a Quran verse
        language (str): 'en' for English, 'ar' for Arabic (default: 'en')
        
    Returns:
        dict: Tafsir information
        
    Raises:
        InvalidQuranVerseError: If the text is not a valid Quran verse and validate=True
    """
    try:
        return process_text_input(quran_verse_text, tafsir_sources, language=language)
    finally:
        # Ensure cleanup
        gc.collect()

def get_tafsir_from_image(image_path_or_object, tafsir_sources=None, min_confidence=50, language="en"):
    """
    Get tafsir for a Quran verse extracted from an image, in the requested language.
    
    Args:
        image_path_or_object: Path to image file or PIL Image object
        tafsir_sources (list): Optional list of tafsir sources to use
        min_confidence (int): Minimum confidence threshold (0-100) for validation
        language (str): 'en' for English, 'ar' for Arabic (default: 'en')
        
    Returns:
        dict: Tafsir information
        
    Raises:
        InvalidQuranVerseError: If the extracted text is not a valid Quran verse
    """
    try:
        # Extract the verse text from the image and validate
        verse_text, is_valid, confidence, message = process_quran_image(image_path_or_object)
        
        # Check if it's a valid Quran verse
        if not is_valid or confidence < min_confidence:
            raise InvalidQuranVerseError(verse_text, confidence, message)
        
        # Get the tafsir using the extracted text
        return process_text_input(verse_text, tafsir_sources, language=language)
    finally:
        # Ensure cleanup of any temporary files
        cleanup_temp_files()
        gc.collect()
        # Clear the image reference
        image_path_or_object = None

def get_tafsir_from_telegram_photo(photo, bot, tafsir_sources=None, min_confidence=50, language="en"):
    """
    Get tafsir for a Quran verse extracted from a Telegram photo, in the requested language.
    
    Args:
        photo: Telegram photo object (list of PhotoSize)
        bot: Telegram bot instance
        tafsir_sources (list): Optional list of tafsir sources to use
        min_confidence (int): Minimum confidence threshold (0-100) for validation
        language (str): 'en' for English, 'ar' for Arabic (default: 'en')
        
    Returns:
        dict: Tafsir information
        
    Raises:
        InvalidQuranVerseError: If the extracted text is not a valid Quran verse
    """
    try:
        # Extract the verse text from the Telegram photo and validate
        verse_text, is_valid, confidence, message = process_telegram_photo(photo, bot)
        
        # Check if it's a valid Quran verse
        if not is_valid or confidence < min_confidence:
            raise InvalidQuranVerseError(verse_text, confidence, message)
        
        # Get the tafsir using the extracted text
        return process_text_input(verse_text, tafsir_sources, language=language)
    finally:
        # Ensure cleanup of any temporary files and references
        cleanup_temp_files()
        gc.collect()
        # Clear the photo reference
        photo = None 