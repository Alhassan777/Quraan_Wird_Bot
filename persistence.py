import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Function to convert datetime objects to string for JSON serialization
def datetime_to_str(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

# Function to convert datetime strings back to datetime objects
def str_to_datetime(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "last_check" and isinstance(value, str):
                try:
                    data[key] = datetime.fromisoformat(value)
                except ValueError:
                    logger.error(f"Could not convert {value} to datetime")
            elif isinstance(value, dict):
                str_to_datetime(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        str_to_datetime(item)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                str_to_datetime(item)
    return data

def save_data(user_data, group_data, filename="bot_data.json"):
    """Save bot data to a JSON file."""
    try:
        data = {
            "user_data": user_data,
            "group_data": group_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, default=datetime_to_str, ensure_ascii=False, indent=2)
        
        logger.info(f"Data saved to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving data: {e}")
        return False

def load_data(filename="bot_data.json"):
    """Load bot data from a JSON file."""
    if not os.path.exists(filename):
        logger.info(f"Data file {filename} not found. Starting with empty data.")
        return {}, {}
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert string keys back to integers for user_id and chat_id
        user_data = {int(k): v for k, v in data.get("user_data", {}).items()}
        
        group_data = {}
        for chat_id_str, chat_data in data.get("group_data", {}).items():
            chat_id = int(chat_id_str)
            group_data[chat_id] = {}
            
            # Convert nested user IDs to integers too
            for user_id_str, user_data_item in chat_data.items():
                if user_id_str in ("reminder_time", "reminder_set_by"):
                    # These are not user IDs but string keys
                    group_data[chat_id][user_id_str] = user_data_item
                    if user_id_str == "reminder_set_by":
                        group_data[chat_id][user_id_str] = int(user_data_item)
                else:
                    group_data[chat_id][int(user_id_str)] = user_data_item
        
        # Convert datetime strings back to datetime objects
        user_data = str_to_datetime(user_data)
        group_data = str_to_datetime(group_data)
        
        logger.info(f"Data loaded from {filename}")
        return user_data, group_data
    
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return {}, {} 