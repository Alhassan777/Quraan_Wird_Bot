import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEFAULT_TIMEZONE = 'America/Los_Angeles'  # PT timezone

# Checkmark symbols
CHECK_MARKS = [
    "✅",  # White Heavy Check Mark
    "✔️",  # Heavy Check Mark with variation selector
    "✔",   # Heavy Check Mark without variation selector
    "✓",   # Check Mark
    "☑️",  # Ballot Box with Check
    "☑",   # Ballot Box with Check without variation selector
    "🗸",   # Light Check Mark
]

# Processing task settings
TASK_EXPIRY_TIME = 600  # 10 minutes in seconds
CLEANUP_INTERVAL = 300  # 5 minutes in seconds

# Job queue settings
REMINDER_INTERVAL = 60  # 1 minute in seconds
METRICS_UPDATE_INTERVAL = 3600  # 1 hour in seconds

# Tafsir settings
MIN_CONFIDENCE = 50  # Minimum confidence for OCR 