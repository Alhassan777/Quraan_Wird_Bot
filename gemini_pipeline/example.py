import os
import json
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the pipeline functions
from gemini_pipeline import get_tafsir_from_text, get_tafsir_from_image

def print_tafsir_result(result):
    """
    Pretty print the tafsir result.
    """
    verse_info = result["verse_info"]
    print("\n" + "="*80)
    print(f"Surah: {verse_info['surah_name_arabic']} ({verse_info['surah_name_english']})")
    print(f"Verse: {verse_info['surah_number']}:{verse_info['ayah_number']}")
    print(f"Original Text: {verse_info['normalized_text']}")
    print(f"Confidence: {verse_info.get('match_confidence', 'N/A')}%")
    print("="*80)
    
    print("\nTafsir Sources:", ", ".join(result["tafsir_sources"]))
    print("\nTafsir Content:")
    print("-"*80)
    print(result["tafsir_content"])
    print("="*80 + "\n")

def example_text_input():
    """
    Example of processing a Quran verse from text input.
    """
    print("\n[Example: Text Input]")
    
    # Example Quran verse text (Al-Fatiha, 1:1)
    verse_text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
    
    # Get tafsir
    try:
        result = get_tafsir_from_text(verse_text)
        print_tafsir_result(result)
        
        # Save the result to a JSON file
        with open("text_tafsir_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        print("Result saved to text_tafsir_result.json")
        
    except Exception as e:
        print(f"Error: {e}")

def example_image_input():
    """
    Example of processing a Quran verse from an image.
    """
    print("\n[Example: Image Input]")
    
    # Path to an image containing a Quran verse
    # This is just a placeholder - replace with your actual image path
    image_path = "quran_verse_image.jpg"
    
    if not os.path.exists(image_path):
        print(f"Warning: Image file {image_path} does not exist.")
        print("Please replace with an actual image path to test the image processing functionality.")
        return
    
    # Get tafsir
    try:
        result = get_tafsir_from_image(image_path)
        print_tafsir_result(result)
        
        # Save the result to a JSON file
        with open("image_tafsir_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        print("Result saved to image_tafsir_result.json")
        
    except Exception as e:
        print(f"Error: {e}")

def main():
    """
    Main function to run the examples.
    """
    print("Quran Tafsir with Gemini AI - Examples")
    print("="*50)
    
    # Check if GEMINI_API_KEY is set
    if not os.getenv("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY is not set in environment variables.")
        print("Please set the GEMINI_API_KEY environment variable or create a .env file.")
        return
    
    # Run the text input example
    example_text_input()
    
    # Run the image input example
    example_image_input()

if __name__ == "__main__":
    main() 