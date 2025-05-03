import os
import base64
import requests
import tempfile
import time
import uuid
from PIL import Image
import io
import shutil
from .arabic_utils import normalize_arabic_text
from .gemini_config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_VISION_MODEL

# API endpoint base URL
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

# Create a temporary directory for processing images
TEMP_DIR = os.path.join(tempfile.gettempdir(), f"quran_tafsir_temp_{uuid.uuid4().hex}")
os.makedirs(TEMP_DIR, exist_ok=True)

def cleanup_temp_files():
    """
    Clean up the temporary directory and all its contents.
    Call this periodically or after processing is complete.
    """
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR, exist_ok=True)

def encode_image(image_path):
    """
    Encode an image file to base64.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        str: Base64 encoded image
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Delete the temporary file immediately after encoding
        if TEMP_DIR in image_path:
            try:
                os.remove(image_path)
            except OSError:
                pass
                
        return encoded
    except Exception as e:
        # Ensure file deletion even if encoding fails
        if TEMP_DIR in image_path:
            try:
                os.remove(image_path)
            except OSError:
                pass
        raise e

def image_to_bytes(image):
    """
    Convert a PIL Image to bytes.
    
    Args:
        image (PIL.Image): Image object
        
    Returns:
        bytes: Image bytes
    """
    byte_arr = io.BytesIO()
    image.save(byte_arr, format='PNG')
    return byte_arr.getvalue()

def download_telegram_photo(photo, bot):
    """
    Download a photo from Telegram.
    
    Args:
        photo: Telegram photo object (list of PhotoSize)
        bot: Telegram bot instance
        
    Returns:
        bytes: Image bytes
    """
    # Get the largest photo available
    photo_file = photo[-1]
    
    # Get file from Telegram
    file = bot.get_file(photo_file.file_id)
    
    # Create a temporary file with a unique name
    temp_file_path = os.path.join(TEMP_DIR, f"telegram_photo_{uuid.uuid4().hex}.jpg")
    
    try:
        # Download the file to the temporary location
        file_bytes = file.download_as_bytearray()
        
        with open(temp_file_path, 'wb') as f:
            f.write(file_bytes)
        
        # Read the file back
        with open(temp_file_path, 'rb') as f:
            file_bytes = f.read()
        
        # Delete the temporary file immediately
        try:
            os.remove(temp_file_path)
        except OSError:
            pass
            
        return file_bytes
    except Exception as e:
        # Ensure file deletion even if processing fails
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except OSError:
            pass
        raise e

def validate_quran_verse(text):
    """
    Validate if the extracted text is actually a Quran verse.
    
    Args:
        text (str): The text to validate
        
    Returns:
        tuple: (is_valid, confidence, message)
            - is_valid (bool): Whether the text is a valid Quran verse
            - confidence (int): Confidence score (0-100)
            - message (str): Explanation message
    """
    if not text or len(text.strip()) < 5:
        return False, 0, "The extracted text is too short to be a Quran verse."
    
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in environment variables")
    
    # Build the API request with updated URL format
    url = f"{GEMINI_API_BASE_URL}/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    headers = {
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    Analyze this text: "{text}"
    
    Is this text a verse from the Quran? If yes, which Surah and verse number?
    If it's not a Quran verse, explain why.
    
    Return your answer in the following JSON format:
    {{
      "is_quran_verse": true/false,
      "confidence": <0-100>,
      "explanation": "<brief explanation>",
      "surah_number": <number or null if not a verse>,
      "verse_number": <number or null if not a verse>
    }}
    """
    
    data = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "topK": 32,
            "topP": 1,
            "maxOutputTokens": 1024,
        }
    }
    
    try:
        # Send request
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code != 200:
            raise Exception(f"Error calling Gemini API: {response.text}")
        
        result = response.json()
        
        # Extract response text
        response_text = result['candidates'][0]['content']['parts'][0]['text']
        
        # Extract JSON from response text
        import json
        import re
        
        json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
        if not json_match:
            return False, 0, "Could not validate if this is a Quran verse."
        
        validation_result = json.loads(json_match.group(1))
        
        is_valid = validation_result.get("is_quran_verse", False)
        confidence = validation_result.get("confidence", 0)
        explanation = validation_result.get("explanation", "")
        
        return is_valid, confidence, explanation
        
    except Exception as e:
        return False, 0, f"Error validating text: {str(e)}"

def extract_text_from_image(image_path_or_object):
    """
    Extract text from an image using Google Gemini Vision API.
    
    Args:
        image_path_or_object: Either a path to image file, a PIL Image object,
                              or bytes from a downloaded Telegram photo
        
    Returns:
        str: Extracted text
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in environment variables")
    
    temp_file_path = None
    
    try:
        # Prepare the image
        if isinstance(image_path_or_object, str):
            # It's a file path
            encoded_image = encode_image(image_path_or_object)
        elif isinstance(image_path_or_object, bytes) or isinstance(image_path_or_object, bytearray):
            # It's bytes from Telegram or other source
            # Create a temporary file to work with
            temp_file_path = os.path.join(TEMP_DIR, f"temp_image_{uuid.uuid4().hex}.jpg")
            with open(temp_file_path, 'wb') as f:
                f.write(image_path_or_object)
            encoded_image = encode_image(temp_file_path)
        elif hasattr(image_path_or_object, 'save'):  # Check if it's a PIL Image
            # It's an image object - convert to bytes without saving to disk
            image_bytes = image_to_bytes(image_path_or_object)
            encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        else:
            raise ValueError("Unsupported image type. Must be file path, PIL Image, or bytes.")
        
        # Build the API request with updated URL format
        url = f"{GEMINI_API_BASE_URL}/models/{GEMINI_VISION_MODEL}:generateContent?key={GEMINI_API_KEY}"
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": "Extract any Arabic Quran verse from this image. Return only the text, exactly as it appears, without any additional information or commentary."
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": encoded_image
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "topK": 32,
                "topP": 1,
                "maxOutputTokens": 1024,
            }
        }
        
        # Send request
        response = requests.post(url, headers=headers, json=data)
        
        # Clear the encoded image from memory to free up resources
        encoded_image = None
        
        if response.status_code != 200:
            raise Exception(f"Error calling Gemini API: {response.text}")
        
        result = response.json()
        
        # Extract text from response
        extracted_text = result['candidates'][0]['content']['parts'][0]['text']
        return normalize_arabic_text(extracted_text)
    except (KeyError, IndexError) as e:
        raise Exception(f"Error parsing Gemini API response: {e}")
    finally:
        # Clean up any temporary files
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                pass

def process_quran_image(image_path_or_object):
    """
    Process an image containing a Quran verse and return the normalized text.
    
    Args:
        image_path_or_object: Path to image file, PIL Image object, 
                             or bytes from Telegram photo
        
    Returns:
        tuple: (text, is_valid, confidence, message)
            - text (str): Normalized Quran verse text
            - is_valid (bool): Whether the text is a valid Quran verse
            - confidence (int): Confidence score (0-100)
            - message (str): Validation message
    """
    try:
        # Extract text from image
        extracted_text = extract_text_from_image(image_path_or_object)
        
        # Normalize the extracted text
        normalized_text = normalize_arabic_text(extracted_text)
        
        # Validate if it's a Quran verse
        is_valid, confidence, message = validate_quran_verse(normalized_text)
        
        return normalized_text, is_valid, confidence, message
    finally:
        # Schedule periodic cleanup
        if time.time() % 60 < 1:  # Run cleanup approximately once per minute
            cleanup_temp_files()

def process_telegram_photo(photo, bot):
    """
    Process a Quran verse from a Telegram photo and return the normalized text.
    
    Args:
        photo: Telegram photo object (list of PhotoSize)
        bot: Telegram bot instance
        
    Returns:
        tuple: (text, is_valid, confidence, message)
            - text (str): Normalized Quran verse text
            - is_valid (bool): Whether the text is a valid Quran verse
            - confidence (int): Confidence score (0-100)
            - message (str): Validation message
    """
    try:
        # Download the photo from Telegram
        photo_bytes = download_telegram_photo(photo, bot)
        
        # Process the image
        result = process_quran_image(photo_bytes)
        
        # Clear the photo bytes from memory
        photo_bytes = None
        
        return result
    finally:
        # Trigger cleanup after processing
        cleanup_temp_files() 