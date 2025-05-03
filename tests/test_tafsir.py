import os
import json
import sys
from dotenv import load_dotenv

# Add parent directory to path to resolve imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import the pipeline functions
from gemini_pipeline import get_tafsir_from_text, cleanup_resources

def test_tafsir(verse_text):
    """
    Test the tafsir pipeline with a verse.
    """
    print(f"\n=== Testing Tafsir for: ===\n{verse_text}\n")
    
    try:
        # Get tafsir for the text
        result = get_tafsir_from_text(verse_text)
        
        # Print the results in a readable format
        verse_info = result["verse_info"]
        print(f"✅ Verse identified successfully!")
        print(f"\nSurah: {verse_info['surah_name_arabic']} ({verse_info['surah_name_english']})")
        print(f"Verse Number: {verse_info['surah_number']}:{verse_info['ayah_number']}")
        print(f"Confidence: {verse_info.get('match_confidence', 'N/A')}%")
        print(f"Normalized Text: {verse_info['normalized_text']}")
        
        print(f"\nTafsir Sources: {', '.join(result['tafsir_sources'])}")
        
        print("\n=== TAFSIR CONTENT ===\n")
        print(result["tafsir_content"])
        print("\n=== END OF TAFSIR ===\n")
        
        # Save the result to a JSON file for reference
        output_file = "tafsir_result.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\nFull result saved to: {output_file}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        # Clean up resources
        cleanup_resources()

if __name__ == "__main__":
    # Check if GEMINI_API_KEY is set
    if not os.getenv("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY is not set in environment variables.")
        print("Please set the GEMINI_API_KEY environment variable or create a .env file.")
        exit(1)
    
    # Test verses
    test_verses = [
        # Al-Fatiha 1:1 (The Opening)
        "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
        
        # Al-Baqarah 2:255 (Ayat al-Kursi)
        "واضربوهن ف المضاجع",
        
        # You can add more verses to test here
    ]
    
    # Run tests
    for i, verse in enumerate(test_verses):
        print(f"\n{'='*80}\nTEST {i+1}\n{'='*80}")
        test_tafsir(verse) 