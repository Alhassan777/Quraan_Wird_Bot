from datetime import datetime, time
from typing import List, Dict, Optional
from streak_counter.streak_counter import StreakCounter
import logging

logger = logging.getLogger(__name__)

class ReminderManager:
    def __init__(self):
        # Default reminder times (can be customized per user later)
        self.reminder_times = [
            time(8, 0),   # Morning
            time(12, 0),  # Noon
            time(16, 0),  # Afternoon
            time(20, 0)   # Evening
        ]
        self.user_streak_counters: Dict[int, StreakCounter] = {}
        self.sent_reminders: Dict[int, List[time]] = {}
        self.user_custom_reminders: Dict[int, List[time]] = {}

    def get_user_counter(self, user_id: int) -> StreakCounter:
        """Get or create a streak counter for a user."""
        if user_id not in self.user_streak_counters:
            # Create StreakCounter with the user's telegram_id
            self.user_streak_counters[user_id] = StreakCounter(telegram_id=user_id)
            self.sent_reminders[user_id] = []
        return self.user_streak_counters[user_id]

    def should_send_reminder(self, user_id: int, current_time: time) -> bool:
        """
        Check if a reminder should be sent for a user at the current time.
        Returns True if:
        1. The current time matches a reminder time (default or custom)
        2. The user hasn't sent a checkmark today
        3. We haven't sent a reminder at this time today
        """
        streak_counter = self.get_user_counter(user_id)
        
        # Don't send if user has already checked in today
        if streak_counter.has_checkmark_today():
            return False

        # Get user's custom reminder times
        user_reminder_times = self.get_user_custom_reminder_times(user_id)
        
        # Check if current time matches any reminder time (with 1 minute tolerance)
        current_minutes = current_time.hour * 60 + current_time.minute
        matches_reminder_time = False
        
        for reminder_time in user_reminder_times:
            reminder_minutes = reminder_time.hour * 60 + reminder_time.minute
            if abs(current_minutes - reminder_minutes) <= 1:
                matches_reminder_time = True
                break
                
        if not matches_reminder_time:
            return False

        # Check if we've already sent a reminder at this time
        for sent_time in self.sent_reminders.get(user_id, []):
            sent_minutes = sent_time.hour * 60 + sent_time.minute
            if abs(current_minutes - sent_minutes) <= 1:
                return False

        return True

    def get_reminder_message(self, user_id: int, language: str = 'en') -> str:
        """
        Get a personalized reminder message for the user.
        Uses a random message from the daily_reminders_messages table and includes streak information.
        """
        streak_counter = self.get_user_counter(user_id)
        
        # Get user data to display streak information
        user_data = streak_counter.db_manager.get_or_create_user(user_id, "")
        current_streak = user_data.get("current_streak", 0)
        reverse_streak = user_data.get("reverse_streak", 0)
        
        # Create header based on streak status and language
        header = ""
        if current_streak > 0:
            if language == "ar":
                header = f"🔥 *لديك سلسلة قراءة مستمرة منذ {current_streak} أيام*\n\n"
            else:  # Default to English
                header = f"🔥 *Your current streak: {current_streak} days*\n\n"
        elif reverse_streak > 0:
            if language == "ar":
                header = f"⚠️ *أيام الانقطاع: {reverse_streak} أيام*\n\n"
            else:  # Default to English
                header = f"⚠️ *Days of inactivity: {reverse_streak} days*\n\n"
        else:
            if language == "ar":
                header = "📚 *ابدأ سلسلة القراءة الخاصة بك اليوم!*\n\n"
            else:  # Default to English
                header = "📚 *Start your reading streak today!*\n\n"
        
        # Get a random reminder message from the database
        reminder_message = streak_counter.db_manager.get_random_daily_reminder(language)
        
        # Combine header and reminder message
        return f"{header}{reminder_message}"

    def mark_reminder_sent(self, user_id: int, reminder_time: time):
        """Mark a reminder as sent for a user."""
        if user_id not in self.sent_reminders:
            self.sent_reminders[user_id] = []
        self.sent_reminders[user_id].append(reminder_time)
        
        # Record in the database that this reminder was sent
        streak_counter = self.get_user_counter(user_id)
        streak_counter.db_manager.record_reminder_sent(user_id, reminder_time)

    def reset_daily_reminders(self, user_id: int):
        """Reset the sent reminders for a user at the start of a new day."""
        if user_id in self.sent_reminders:
            self.sent_reminders[user_id] = []

    def get_next_reminder_time(self, current_time: time) -> Optional[time]:
        """Get the next reminder time after the current time."""
        for reminder_time in sorted(self.reminder_times):
            if reminder_time > current_time:
                return reminder_time
        return self.reminder_times[0]  # Return first time of next day 

    def set_custom_reminder_time(self, user_id: int, reminder_time: time):
        """
        Set a custom reminder time for a user.
        This will be used in place of the default reminder times.
        """
        # Get user counter to ensure we have access to the database
        streak_counter = self.get_user_counter(user_id)
        
        # If this is a new reminder time for the user, add it to their custom times
        if user_id not in self.user_custom_reminders:
            self.user_custom_reminders[user_id] = []
        
        # Add the reminder time if it's not already in the list
        if reminder_time not in self.user_custom_reminders[user_id]:
            self.user_custom_reminders[user_id].append(reminder_time)
            
        # Store in database through the streak counter's db_manager
        streak_counter.db_manager.set_user_reminder(user_id, reminder_time)

    def get_user_custom_reminder_times(self, user_id: int) -> List[time]:
        """
        Get all custom reminder times for a user.
        If no custom times are set, returns the default reminder times.
        """
        # Get user counter to ensure we have access to the database
        streak_counter = self.get_user_counter(user_id)
        
        # Get user data from database
        user_data = streak_counter.db_manager.get_or_create_user(user_id, "")
        
        # Get reminder times from database
        user_reminder_times = user_data.get("reminder_times", [])
        
        # If no custom times are set, return default times
        if not user_reminder_times:
            return self.reminder_times
            
        return user_reminder_times 

    def get_reminders_for_user(self, user_id: int) -> List[str]:
        """
        Get all reminder times for a user formatted as HH:MM strings.
        """
        # Get user counter to ensure we have access to the database
        streak_counter = self.get_user_counter(user_id)
        
        # Get user data from database
        user_data = streak_counter.db_manager.get_or_create_user(user_id, "")
        
        # Get reminder times from database
        reminder_times = user_data.get("reminder_times", [])
        
        # If no times are set, convert default times to strings
        if not reminder_times:
            reminder_times = [t.strftime("%H:%M") for t in self.reminder_times]
            
        return reminder_times
        
    def delete_reminder(self, user_id: int, reminder_time: time) -> bool:
        """
        Delete a specific reminder time for a user.
        Returns True if successful, False otherwise.
        """
        try:
            # Get user counter to ensure we have access to the database
            streak_counter = self.get_user_counter(user_id)
            
            # Get existing reminder times
            user_data = streak_counter.db_manager.get_or_create_user(user_id, "")
            reminder_times = user_data.get("reminder_times", [])
            
            # Convert reminder_time to string format
            time_str = reminder_time.strftime("%H:%M")
            
            # Remove the time if it exists
            if time_str in reminder_times:
                reminder_times.remove(time_str)
                
                # Update in database
                db_success = streak_counter.db_manager.update_user_reminder_times(user_id, reminder_times)
                
                # Also update local cache
                if user_id in self.user_custom_reminders:
                    self.user_custom_reminders[user_id] = [
                        t for t in self.user_custom_reminders[user_id] if t != reminder_time
                    ]
                
                return db_success
            else:
                # Just clean up local cache if reminder didn't exist in database
                if user_id in self.user_custom_reminders:
                    self.user_custom_reminders[user_id] = [
                        t for t in self.user_custom_reminders[user_id] if t != reminder_time
                    ]
                return True
        except Exception as e:
            # Log the error and return False
            logger.error(f"Error deleting reminder: {str(e)}")
            return False 