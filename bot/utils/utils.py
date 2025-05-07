import logging
import time
import gc
import threading
import pytz
import uuid
from datetime import datetime, timedelta
import sys

# Safely import config - allow for fallbacks in test environment
try:
    from bot.config.config import (
        LOG_LEVEL, DEFAULT_TIMEZONE, TASK_EXPIRY_TIME,
        CLEANUP_INTERVAL
    )
except ImportError:
    # Default values for tests
    LOG_LEVEL = "INFO"
    DEFAULT_TIMEZONE = "UTC"
    TASK_EXPIRY_TIME = 3600  # 1 hour
    CLEANUP_INTERVAL = 300   # 5 minutes

# Try to import optional dependencies
try:
    from bot.gemini_pipeline.ocr_processor import cleanup_temp_files
except ImportError:
    # Mock function for tests
    def cleanup_temp_files():
        pass

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL)
)
logger = logging.getLogger(__name__)

# Dictionary to track processing status
processing_tasks = {}

# Dictionary to track user language preferences
user_language = {}

def get_user_language(user_id: int) -> str:
    """Get user's preferred language."""
    return user_language.get(user_id, "ar")

def set_user_language(user_id: int, lang: str) -> None:
    """Set user's preferred language."""
    user_language[user_id] = lang

def get_user_datetime(timezone_str: str = None) -> datetime:
    """Get the current datetime in user's timezone."""
    timezone_str = timezone_str or DEFAULT_TIMEZONE
    
    try:
        timezone = pytz.timezone(timezone_str)
        return datetime.now(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        logger.error(f"Unknown timezone {timezone_str}")
        # Fallback to default timezone
        timezone = pytz.timezone(DEFAULT_TIMEZONE)
        return datetime.now(timezone)

def track_processing_task(user_id: int) -> str:
    """Track a new processing task for a user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        str: A unique task ID for tracking
    """
    task_id = str(uuid.uuid4())
    processing_tasks[task_id] = {
        "user_id": user_id,
        "timestamp": time.time(),
        "status": "processing"
    }
    return task_id

def mark_task_complete(task_id: str) -> None:
    """Mark a processing task as complete."""
    if task_id in processing_tasks:
        processing_tasks[task_id]["status"] = "complete"

def mark_task_failed(task_id: str, error: str = None) -> None:
    """Mark a processing task as failed."""
    if task_id in processing_tasks:
        processing_tasks[task_id]["status"] = "failed"
        if error:
            processing_tasks[task_id]["error"] = error

def get_user_tasks(user_id: int) -> dict:
    """Get all processing tasks for a user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        dict: A dictionary of task_id -> task_info for this user
    """
    user_tasks = {}
    for task_id, task_info in processing_tasks.items():
        if task_info.get("user_id") == user_id:
            user_tasks[task_id] = task_info
    return user_tasks

def cleanup_expired_tasks() -> None:
    """Clean up expired processing tasks."""
    current_time = time.time()
    expired_tasks = []
    
    for task_id, task_info in processing_tasks.items():
        if current_time - task_info["timestamp"] > TASK_EXPIRY_TIME:
            expired_tasks.append(task_id)
    
    for task_id in expired_tasks:
        processing_tasks.pop(task_id, None)

def periodic_cleanup() -> None:
    """Run periodic cleanup of temporary files and processed data."""
    while True:
        try:
            # Clean up temporary files
            cleanup_temp_files()
            
            # Clean up expired processing tasks
            cleanup_expired_tasks()
            
            # Force garbage collection
            gc.collect()
            
        except Exception as e:
            logger.error(f"Error in cleanup thread: {e}")
            
        # Sleep for cleanup interval
        time.sleep(CLEANUP_INTERVAL)

# Start the cleanup thread
cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start() 