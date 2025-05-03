import os
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the pipeline functions
from gemini_pipeline import (
    get_tafsir_from_text, 
    get_tafsir_from_image, 
    InvalidQuranVerseError,
    cleanup_resources
)

def validate_text_example(text):
    """
    Example of validating a text input.
    """
    print(f"\n--- Validating text: '{text}' ---")
    
    try:
        # Try to get tafsir with validation enabled
        result = get_tafsir_from_text(text, validate=True)
        
        # If we get here, the text is a valid Quran verse
        verse_info = result["verse_info"]
        print(f"✅ Valid Quran verse detected!")
        print(f"Surah: {verse_info['surah_name_arabic']} ({verse_info['surah_name_english']})")
        print(f"Verse: {verse_info['surah_number']}:{verse_info['ayah_number']}")
        print(f"Confidence: {verse_info.get('match_confidence', 'N/A')}%")
        
    except InvalidQuranVerseError as e:
        # Text is not a valid Quran verse
        print(f"❌ Invalid Quran verse!")
        print(f"Detected text: {e.text}")
        print(f"Confidence: {e.confidence}%")
        print(f"Reason: {e.message}")
    
    except Exception as e:
        print(f"Error: {e}")

def validate_image_example(image_path, min_confidence=50):
    """
    Example of validating an image input.
    """
    print(f"\n--- Validating image: {image_path} ---")
    
    if not os.path.exists(image_path):
        print(f"Image file not found: {image_path}")
        return
    
    try:
        # Load the image
        image = Image.open(image_path)
        
        # Try to get tafsir with validation enabled
        result = get_tafsir_from_image(image, min_confidence=min_confidence)
        
        # If we get here, the image contains a valid Quran verse
        verse_info = result["verse_info"]
        print(f"✅ Valid Quran verse detected in image!")
        print(f"Extracted text: {verse_info['normalized_text']}")
        print(f"Surah: {verse_info['surah_name_arabic']} ({verse_info['surah_name_english']})")
        print(f"Verse: {verse_info['surah_number']}:{verse_info['ayah_number']}")
        print(f"Confidence: {verse_info.get('match_confidence', 'N/A')}%")
        
    except InvalidQuranVerseError as e:
        # Image doesn't contain a valid Quran verse
        print(f"❌ Invalid Quran verse in image!")
        print(f"Extracted text: {e.text}")
        print(f"Confidence: {e.confidence}%")
        print(f"Reason: {e.message}")
    
    except Exception as e:
        print(f"Error: {e}")

def main():
    """
    Run the validation examples.
    """
    print("=== Quran Verse Validation Examples ===")
    
    # Valid Quran verse example
    valid_verse = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
    validate_text_example(valid_verse)
    
    # Invalid text example
    invalid_text = "هذا ليس آية من القرآن الكريم"
    validate_text_example(invalid_text)
    
    # English text example
    english_text = "This is not a Quran verse"
    validate_text_example(english_text)
    
    # Image examples - replace with actual paths to test
    quran_image_path = "quran_verse_image.jpg"  # Replace with actual path
    validate_image_example(quran_image_path)
    
    non_quran_image_path = "non_quran_image.jpg"  # Replace with actual path
    validate_image_example(non_quran_image_path)
    
    # Clean up resources
    cleanup_resources()

if __name__ == "__main__":
    main() 