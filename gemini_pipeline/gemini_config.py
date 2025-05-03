import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# Get Gemini API key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# URLs for tafsir resources
TAFSIR_RESOURCES = [
    "https://quran.com/tafsir",
    "https://www.altafsir.com",
    "https://www.islamicstudies.info/tafheem.php",
    "https://www.islamawakened.com/quran/",
    "https://sunnah.com"
]

# Model configuration - updated to use Gemini 2.0 Flash
GEMINI_MODEL = "gemini-2.0-flash" # For text
GEMINI_VISION_MODEL = "gemini-2.0-flash" # For images (assuming it can handle vision too)

# Define which tafsir sources to use
DEFAULT_TAFSIR_SOURCES = [
    "Ibn Kathir", 
    "Al-Qurtubi", 
    "Al-Tabari",
    "Jalalayn"]

# Telegram bot configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "") 