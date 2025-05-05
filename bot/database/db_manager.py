from supabase import create_client, Client
from datetime import datetime, time
from typing import Dict, List, Optional
import random
from .config import (
    SUPABASE_URL,
    SUPABASE_KEY,
    USERS_TABLE,
    STREAKS_TABLE,
    CHECK_INS_TABLE,
    MESSAGE_TEMPLATES_TABLE,
    REMINDERS_TABLE,
    DAILY_REMINDERS_MESSAGES_TABLE
)
import logging
import json

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # User Operations
    def get_or_create_user(self, telegram_id: int, username: str) -> Dict:
        """Get user by telegram_id or create if not exists."""
        response = self.supabase.table(USERS_TABLE).select("*").eq("telegram_id", telegram_id).execute()
        
        if response.data:
            user = response.data[0]
            # Get streak info for the user
            streak = self.get_or_create_streak(user["id"])
            # Store user ID separately to avoid it being overwritten
            user_id = user["id"]
            # Add streak data under a separate key
            user["streak_data"] = streak
            # Add streak fields to the main user object for convenience
            user["current_streak"] = streak.get("current_streak", 0)
            user["reverse_streak"] = streak.get("reverse_streak", 0)
            user["last_check_in"] = streak.get("last_check_in")
            # Ensure user_id is preserved
            user["id"] = user_id
            return user
        
        # Create new user
        new_user = {
            "telegram_id": telegram_id,
            "username": username,
        }
        
        response = self.supabase.table(USERS_TABLE).insert(new_user).execute()
        user = response.data[0]
        user_id = user["id"]  # Store user ID separately
        
        # Create streak record for the new user
        streak = self.get_or_create_streak(user_id)
        # Add streak data under a separate key
        user["streak_data"] = streak
        # Add streak fields to the main user object
        user["current_streak"] = streak.get("current_streak", 0)
        user["reverse_streak"] = streak.get("reverse_streak", 0)
        user["last_check_in"] = streak.get("last_check_in")
        # Ensure user_id is preserved
        user["id"] = user_id
        
        return user

    # Streak Operations
    def get_or_create_streak(self, user_id: str) -> Dict:
        """Get or create streak record for a user."""
        response = self.supabase.table(STREAKS_TABLE).select("*").eq("user_id", user_id).execute()
        
        if response.data:
            return response.data[0]
        
        # Create new streak record (matching the actual schema)
        new_streak = {
            "user_id": user_id,
            "current_streak": 0,
            "reverse_streak": 0,
        }
        
        response = self.supabase.table(STREAKS_TABLE).insert(new_streak).execute()
        return response.data[0]

    def update_user_streak(self, telegram_id: int, current_streak: int, reverse_streak: int):
        """Update user's streak information."""
        # Get user record
        user = self.get_or_create_user(telegram_id, "")
        
        # Prepare data to update
        data = {
            "current_streak": current_streak,
            "reverse_streak": reverse_streak,
            "last_check_in": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Update the streak record - using user_id as the foreign key
        self.supabase.table(STREAKS_TABLE).update(data).eq("user_id", user["id"]).execute()

    # Check-in Operations
    def record_check_in(self, telegram_id: int, has_checkmark: bool):
        """Record a user's check-in."""
        user = self.get_or_create_user(telegram_id, "")
        check_in = {
            "user_id": user["id"],  # This now correctly points to the user ID
            "check_in_time": datetime.utcnow().isoformat(),
            "checkmark_status": has_checkmark
        }
        self.supabase.table(CHECK_INS_TABLE).insert(check_in).execute()

    def get_today_check_ins(self, telegram_id: int) -> List[Dict]:
        """Get all check-ins for a user today."""
        user = self.get_or_create_user(telegram_id, "")
        today = datetime.utcnow().date()
        
        response = self.supabase.table(CHECK_INS_TABLE)\
            .select("*")\
            .eq("user_id", user["id"])\
            .gte("check_in_time", today.isoformat())\
            .execute()
        
        return response.data

    # Message Template Operations
    def get_message_template(self, template_type: str, threshold_days: int) -> Optional[Dict]:
        """
        Get a message template based on template type and threshold days.
        template_type: 'reward' or 'warning'
        threshold_days: 1, 3, 5, 7, 30
        
        Randomly selects from all matching templates to provide variety.
        """
        try:
            response = self.supabase.table(MESSAGE_TEMPLATES_TABLE)\
                .select("*")\
                .eq("template_type", template_type)\
                .eq("threshold_days", threshold_days)\
                .execute()
            
            if response.data:
                # Randomly select a message from matching templates
                template = random.choice(response.data)
                logger.debug(f"Found template for {template_type} and {threshold_days} days")
                return template
                
            # If no template found for the exact threshold, try to find any template of the same type
            logger.warning(f"No template found for {template_type} with threshold_days={threshold_days}. Trying any threshold.")
            
            fallback_response = self.supabase.table(MESSAGE_TEMPLATES_TABLE)\
                .select("*")\
                .eq("template_type", template_type)\
                .execute()
                
            if fallback_response.data:
                # Randomly select from any template of the same type
                template = random.choice(fallback_response.data)
                logger.debug(f"Using fallback template for {template_type}")
                return template
                
            # If still no template, log and return None
            logger.warning(f"No {template_type} templates found in the database.")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving message template: {str(e)}")
            return None

    def get_random_daily_reminder(self, language: str = 'en') -> str:
        """
        Get a random reminder message from the daily reminders table.
        Returns a message in the specified language.
        """
        # Get all reminder messages
        response = self.supabase.table(DAILY_REMINDERS_MESSAGES_TABLE).select("*").execute()
        
        if not response.data:
            # Fallback messages if no reminders found in database
            if language == 'en':
                return "It's time for your daily Quran reading! Keep up your streak! 📖"
            else:
                return "حان وقت قراءة القرآن اليومية! حافظ على تواصلك! 📖"
        
        # Choose a random reminder
        reminder = random.choice(response.data)
        
        # Return the message in the appropriate language
        if language == 'en':
            return reminder.get("reminder_english", "Time for your daily Quran reading! 📖")
        else:
            return reminder.get("reminder_arabic", "حان وقت قراءة القرآن اليومية! 📖")

    # Reminder Operations
    def record_reminder_sent(self, telegram_id: int, reminder_time: time):
        """Record that a reminder was sent to a user."""
        user = self.get_or_create_user(telegram_id, "")
        reminder = {
            "user_id": user["id"],  # This now correctly points to the user ID
            "reminder_time": reminder_time.isoformat(),
            "sent_at": datetime.utcnow().isoformat()
        }
        self.supabase.table(REMINDERS_TABLE).insert(reminder).execute()

    def get_today_reminders(self, telegram_id: int) -> List[Dict]:
        """Get all reminders sent to a user today."""
        user = self.get_or_create_user(telegram_id, "")
        today = datetime.utcnow().date()
        
        response = self.supabase.table(REMINDERS_TABLE)\
            .select("*")\
            .eq("user_id", user["id"])\
            .gte("sent_at", today.isoformat())\
            .execute()
        
        return response.data

    def set_user_reminder(self, telegram_id: int, reminder_time: time):
        """
        Set a reminder time for a user.
        Updates user record with the reminder time.
        """
        try:
            user = self.get_or_create_user(telegram_id, "")
            
            # Try to get existing reminder times if the column exists
            try:
                response = self.supabase.table(USERS_TABLE).select("reminder_times").eq("id", user["id"]).execute()
                
                if response.data and response.data[0].get("reminder_times"):
                    reminder_times = response.data[0]["reminder_times"]
                    # Handle the case when reminder_times is a string
                    if isinstance(reminder_times, str):
                        try:
                            # Try to convert from JSON string if it's serialized
                            reminder_times = json.loads(reminder_times)
                        except json.JSONDecodeError:
                            # If not a valid JSON, treat as a single item list
                            reminder_times = [reminder_times]
                else:
                    reminder_times = []
            except Exception as e:
                # If column doesn't exist, create a new empty list
                logger.warning(f"Error retrieving reminder_times: {str(e)}. Using empty list.")
                reminder_times = []
            
            # Ensure reminder_times is a list
            if not isinstance(reminder_times, list):
                reminder_times = [reminder_times] if reminder_times else []
            
            # Convert reminder_time to string (HH:MM) format for storage
            time_str = reminder_time.strftime("%H:%M")
            
            # Add the new time if not already present
            if time_str not in reminder_times:
                reminder_times.append(time_str)
            
            # Try updating the user with the new reminder times
            try:
                # Update user record with new reminder times
                self.supabase.table(USERS_TABLE).update({"reminder_times": reminder_times}).eq("id", user["id"]).execute()
                return True
            except Exception as e:
                logger.error(f"Error updating reminder_times: {str(e)}. The column might not exist in the database.")
                return False
        except Exception as e:
            logger.error(f"Error in set_user_reminder: {str(e)}")
            return False

    def get_users_with_reminders(self) -> List[Dict]:
        """
        Get all users who have scheduled reminders.
        Returns a list of user objects with their telegram_id, reminder_times, and timezone info.
        """
        try:
            # Query all users for now, will filter those with reminders in Python
            response = self.supabase.table(USERS_TABLE)\
                .select("id, telegram_id, username, reminder_times, timezone")\
                .execute()
            
            users_with_reminders = []
            
            for user in response.data:
                # Skip users without reminder_times field or with empty reminder_times
                if not user.get("reminder_times"):
                    continue
                
                reminder_times_data = user.get("reminder_times")
                
                # Handle case when reminder_times is a string
                if isinstance(reminder_times_data, str):
                    try:
                        # Try to convert from JSON string if it's serialized
                        reminder_times_data = json.loads(reminder_times_data)
                    except json.JSONDecodeError:
                        # If not a valid JSON, treat as a single item list
                        reminder_times_data = [reminder_times_data]
                
                # Ensure it's a list
                if not isinstance(reminder_times_data, list):
                    reminder_times_data = [reminder_times_data] if reminder_times_data else []
                
                # Parse reminder_times from strings to time objects
                reminder_times = []
                for time_str in reminder_times_data:
                    try:
                        hour, minute = map(int, time_str.split(":"))
                        reminder_times.append(time(hour, minute))
                    except (ValueError, TypeError):
                        # Skip invalid time strings
                        continue
                
                # Only add users who have at least one valid reminder time
                if reminder_times:
                    # Add parsed reminder times to user object
                    user["reminder_times"] = reminder_times
                    users_with_reminders.append(user)
                
            logger.info(f"Found {len(users_with_reminders)} users with reminders")
            return users_with_reminders
            
        except Exception as e:
            logger.error(f"Error in get_users_with_reminders: {str(e)}")
            return []

    def update_user_timezone(self, telegram_id: int, timezone_str: str):
        """
        Update a user's timezone setting.
        """
        user = self.get_or_create_user(telegram_id, "")
        
        # Update user record with new timezone
        self.supabase.table(USERS_TABLE).update({"timezone": timezone_str}).eq("id", user["id"]).execute()

    def update_user_reminder_times(self, telegram_id: int, reminder_times: List[str]):
        """
        Update all reminder times for a user.
        
        Args:
            telegram_id: The user's Telegram ID
            reminder_times: List of reminder times in "HH:MM" format
        """
        try:
            user = self.get_or_create_user(telegram_id, "")
            
            # Ensure reminder_times is a list
            if not isinstance(reminder_times, list):
                if reminder_times:
                    reminder_times = [reminder_times]
                else:
                    reminder_times = []
            
            # Try updating user record with new reminder times
            try:
                self.supabase.table(USERS_TABLE).update({"reminder_times": reminder_times}).eq("id", user["id"]).execute()
                return True
            except Exception as e:
                logger.error(f"Error updating reminder_times: {str(e)}. The column might not exist in the database.")
                return False
        except Exception as e:
            logger.error(f"Error in update_user_reminder_times: {str(e)}")
            return False 