import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from .env file or environment variables
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("Error: GEMINI_API_KEY is not set in environment variables or .env file")
    print("Please add your API key to the .env file in this format: GEMINI_API_KEY=your_api_key_here")
    exit(1)

# Set the model and API endpoint
MODEL = "gemini-2.0-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

def test_gemini_api():
    """
    Simple test of the Gemini API with a basic prompt
    """
    print(f"Testing Gemini API with model: {MODEL}")
    print(f"API URL: {API_URL.replace(API_KEY, 'API_KEY_HIDDEN')}")
    
    # Set up the request
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": "Tell me about Surah Al-Fatiha in 3 sentences."}]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "topK": 32,
            "topP": 1,
            "maxOutputTokens": 256,
        }
    }
    
    # Send the request
    try:
        print("\nSending request to Gemini API...")
        response = requests.post(API_URL, headers=headers, json=data)
        
        # Check response status
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract and print the response text
            response_text = result['candidates'][0]['content']['parts'][0]['text']
            print("\nAPI Response:")
            print("-" * 80)
            print(response_text)
            print("-" * 80)
            print("\nAPI test successful! Your configuration is working correctly.")
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Exception occurred: {e}")
        return False

def test_quran_verse():
    """
    Test with a Quran verse to identify the surah and ayah
    """
    print("\n\nTesting with a Quran verse...")
    
    # Example verse: Al-Fatiha 1:1
    verse = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
    print(f"Verse: {verse}")
    
    # Set up the request
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "contents": [
            {
                "role": "user",
                "parts": [{
                    "text": f"""
                    This is an Arabic Quran verse: "{verse}"
                    
                    Identify the exact Surah number and Ayah number of this verse.
                    Return only the result in the following JSON format:
                    {{
                      "surah_number": <number>,
                      "ayah_number": <number>,
                      "surah_name_arabic": "<surah name in Arabic>",
                      "surah_name_english": "<surah name in English>",
                      "match_confidence": <0-100>
                    }}
                    """
                }]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "topK": 32,
            "topP": 1,
            "maxOutputTokens": 1024,
        }
    }
    
    # Send the request
    try:
        print("Sending request to Gemini API...")
        response = requests.post(API_URL, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract and print the response text
            response_text = result['candidates'][0]['content']['parts'][0]['text']
            print("\nAPI Response:")
            print("-" * 80)
            print(response_text)
            print("-" * 80)
            
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
            if json_match:
                verse_info = json.loads(json_match.group(1))
                print("\nExtracted verse information:")
                print(f"Surah: {verse_info.get('surah_name_arabic', 'N/A')} ({verse_info.get('surah_name_english', 'N/A')})")
                print(f"Verse: {verse_info.get('surah_number', 'N/A')}:{verse_info.get('ayah_number', 'N/A')}")
                print(f"Confidence: {verse_info.get('match_confidence', 'N/A')}%")
            else:
                print("Could not extract JSON data from response")
                
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Exception occurred: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("GEMINI API CONFIGURATION TEST")
    print("=" * 80)
    
    # Run basic test
    basic_test_success = test_gemini_api()
    
    # If basic test is successful, run Quran verse test
    if basic_test_success:
        test_quran_verse()
        
    print("\nTest completed. Replace 'your_api_key_here' in the .env file with your actual Gemini API key if the test failed.") 