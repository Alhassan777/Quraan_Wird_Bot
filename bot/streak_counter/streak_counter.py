from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
from config.config import CHECK_MARKS
from database.db_manager import DatabaseManager

class StreakCounter:
    def __init__(self, telegram_id: int = None, username: str = ""):
        self.db_manager = DatabaseManager()
        self.telegram_id = telegram_id
        self.username = username
        self.today_checkmarks: List[datetime] = []
        
        # Load today's check-ins from database if telegram_id is provided
        if telegram_id:
            self._load_todays_checkins()
            
    def _load_todays_checkins(self):
        """Load today's check-ins from the database."""
        if not self.telegram_id:
            return
            
        today_checkins = self.db_manager.get_today_check_ins(self.telegram_id)
        self.today_checkmarks = []
        
        for checkin in today_checkins:
            if checkin.get("checkmark_status"):
                # Convert the ISO format string to datetime (consistently without timezone)
                check_time_str = checkin.get("check_in_time")
                if check_time_str:
                    # Remove timezone info to make it naive
                    if 'T' in check_time_str:
                        check_time_str = check_time_str.split('+')[0].split('Z')[0]
                    check_time = datetime.fromisoformat(check_time_str)
                    self.today_checkmarks.append(check_time)

    def check_for_checkmark(self, message_text: str) -> bool:
        """Check if the message contains any of the valid checkmarks."""
        return any(checkmark in message_text for checkmark in CHECK_MARKS)

    def has_checkmark_today(self) -> bool:
        """Check if user has already sent a checkmark today."""
        if not self.today_checkmarks:
            return False
        
        current_time = datetime.now()
        for check_time in self.today_checkmarks:
            if (current_time - check_time) < timedelta(hours=24):
                return True
        return False

    def update_streak(self, has_checkmark: bool, current_time: datetime) -> Tuple[int, int]:
        """
        Update streak counts based on checkmark presence and timing.
        
        If a user already has a checkmark within the last 24 hours, this won't
        increment the streak again but will record the new checkmark.
        
        Returns: (current_streak, reverse_streak)
        """
        if not self.telegram_id:
            raise ValueError("Cannot update streak without a telegram_id")
            
        # Get user data from database
        user_data = self.db_manager.get_or_create_user(self.telegram_id, self.username)
        
        # Get current streak info
        current_streak = user_data.get("current_streak", 0)
        reverse_streak = user_data.get("reverse_streak", 0)
        last_check_in = user_data.get("last_check_in")
        
        # Handle last_check_in to make timezone consistent
        if last_check_in:
            # Remove timezone info to make it naive
            if 'T' in last_check_in:
                last_check_in = last_check_in.split('+')[0].split('Z')[0]
            last_check_time = datetime.fromisoformat(last_check_in)
        else:
            last_check_time = None
        
        # Clean up old checkmarks (older than 24 hours)
        self.today_checkmarks = [
            check_time for check_time in self.today_checkmarks
            if (current_time - check_time) < timedelta(hours=24)
        ]

        # Load today's check-ins to ensure we have the latest data
        self._load_todays_checkins()
        
        # Check if the user already has a checkmark today
        already_checked_today = self.has_checkmark_today()
        
        if has_checkmark:
            # Add new checkmark time to our local tracking
            self.today_checkmarks.append(current_time)
            # Record check-in in database
            self.db_manager.record_check_in(self.telegram_id, has_checkmark)
        
        if last_check_time is None:
            # First check
            if has_checkmark:
                current_streak = 1
                reverse_streak = 0
            else:
                current_streak = 0
                reverse_streak = 1
        else:
            # Check if within 24 hours of last check
            time_diff = current_time - last_check_time
            
            if time_diff > timedelta(hours=24):
                # Reset streaks if more than 24 hours have passed
                if has_checkmark:
                    current_streak = 1
                    reverse_streak = 0
                else:
                    current_streak = 0
                    reverse_streak = 1
            else:
                # Update streaks based on checkmark presence
                if has_checkmark:
                    # Only increment streak if this is the first checkmark today
                    # or if the last check was on a different calendar day
                    if not already_checked_today or current_time.date() > last_check_time.date():
                        current_streak += 1
                    reverse_streak = 0
                else:
                    current_streak = 0
                    reverse_streak += 1

        # Update user's streak in database
        self.db_manager.update_user_streak(self.telegram_id, current_streak, reverse_streak)
        
        return current_streak, reverse_streak

    def get_appropriate_threshold(self, days: int, is_reward: bool) -> int:
        """Determine the appropriate threshold based on the number of days."""
        if is_reward:
            # Reward thresholds: 1, 7, 30 days
            if days >= 30:
                return 30  # 1_month_reward
            elif days >= 7:
                return 7   # 1_week_reward
            else:
                return 1   # 1_day_reward
        else:
            # Warning thresholds: 1, 3, 5, 7, 30 days
            if days >= 30:
                return 30  # 1_month_warning
            elif days >= 7:
                return 7   # 1_week_warning
            elif days >= 5:
                return 5   # 5_day_warning
            elif days >= 3:
                return 3   # 3_day_warning
            else:
                return 1   # 1_day_warning

    def get_streak_message(self, language: str = 'en', include_header: bool = True) -> str:
        """
        Generate an appropriate message based on current streak status.
        Uses message templates from the database based on streak duration.
        
        Args:
            language: 'en' for English, 'ar' for Arabic
            include_header: Whether to include the streak count header (set to False when adding header separately)
        
        Returns:
            str: A formatted streak message
        """
        if not self.telegram_id:
            # Default message for users without telegram_id
            if language == 'en':
                return "Ready to start your Quran reading journey? Send a checkmark when you're done! 📚"
            else:
                return "هل أنت مستعد لبدء رحلة قراءة القرآن؟ أرسل علامة اختيار عندما تنتهي! 📚"
        
        # Get user data from database
        user_data = self.db_manager.get_or_create_user(self.telegram_id, self.username)
        current_streak = user_data.get("current_streak", 0)
        reverse_streak = user_data.get("reverse_streak", 0)
        
        # Create header based on streak status and language (if requested)
        header = ""
        if include_header:
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
            
        if current_streak > 0:
            # Using reward templates
            threshold = self.get_appropriate_threshold(current_streak, True)
            message_field = "message_english_translation" if language == 'en' else "message_arabic_translation"
            text_field = "text_used_english" if language == 'en' else "text_used_arabic"
            
            template = self.db_manager.get_message_template(
                template_type="reward",
                threshold_days=threshold
            )
            
            if not template:
                # Fallback if no template found
                if language == 'en':
                    return f"{header}Amazing! You've maintained your Quran reading streak for {current_streak} days! 🎉"
                else:
                    return f"{header}رائع! لقد حافظت على سلسلة قراءة القرآن لمدة {current_streak} أيام! 🎉"
            
            return f"{header}{template[text_field]}\n\n{template[message_field]}"
            
        elif reverse_streak > 0:
            # Using warning templates
            threshold = self.get_appropriate_threshold(reverse_streak, False)
            message_field = "message_english_translation" if language == 'en' else "message_arabic_translation"
            text_field = "text_used_english" if language == 'en' else "text_used_arabic"
            
            template = self.db_manager.get_message_template(
                template_type="warning",
                threshold_days=threshold
            )
            
            if not template:
                # Fallback if no template found
                if language == 'en':
                    return f"{header}Don't worry! It's been {reverse_streak} days since your last check-in. You can start again today! 📖"
                else:
                    return f"{header}لا تقلق! لقد مرت {reverse_streak} أيام منذ آخر تسجيل دخول. يمكنك البدء مرة أخرى اليوم! 📖"
            
            return f"{header}{template[text_field]}\n\n{template[message_field]}"
            
        else:
            # Default message for new users
            if language == 'en':
                return f"{header}Ready to start your Quran reading journey? Send a checkmark when you're done! 📚"
            else:
                return f"{header}هل أنت مستعد لبدء رحلة قراءة القرآن؟ أرسل علامة اختيار عندما تنتهي! 📚" 