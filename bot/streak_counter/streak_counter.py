from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
from bot.config.config import CHECK_MARKS
from bot.database.db_manager import DatabaseManager

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
            
            # Check if more than 1 full day (24 hours) has passed since the last check-in
            time_since_last_check = current_time - last_check_time
            if time_since_last_check > timedelta(days=1):
                # If more than 1 day has passed with no check-in, reset the streak and 
                # increase the reverse streak by the number of days missed
                days_missed = time_since_last_check.days  # No cap on missed days
                if days_missed > 0:
                    current_streak = 0
                    reverse_streak = days_missed
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
                # Streak already reset in the earlier check, now handle the current action
                if has_checkmark:
                    current_streak = 1
                    reverse_streak = 0
                # If no checkmark, the reverse streak was already updated above
            else:
                # Update streaks based on checkmark presence
                if has_checkmark:
                    # Only increment streak if this is the first checkmark today
                    # or if the last check was on a different calendar day
                    if not already_checked_today or current_time.date() > last_check_time.date():
                        current_streak += 1
                    reverse_streak = 0
                else:
                    # If no checkmark today and within 24 hours, don't change the streak
                    # but don't increment it either
                    pass

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
            
        try:
            if current_streak > 0:
                # Using reward templates
                threshold = self.get_appropriate_threshold(current_streak, True)
                
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
                
                # Try to get message fields, with fallbacks if fields don't exist
                text = ""
                message = ""
                
                # Get text field
                if language == 'en':
                    text = template.get("text_used_english", "")
                else:
                    text = template.get("text_used_arabic", "")
                
                # Get message field
                if language == 'en':
                    message = template.get("message_english_translation", "")
                    if not message:
                        message = "Keep up your daily Quran reading streak! Every day brings you closer to Allah."
                else:
                    message = template.get("message_arabic_translation", "")
                    if not message:
                        message = "حافظ على سلسلة قراءة القرآن اليومية! كل يوم يقربك من الله."
                
                return f"{header}{text}\n\n{message}"
                
            elif reverse_streak > 0:
                # Using warning templates
                threshold = self.get_appropriate_threshold(reverse_streak, False)
                
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
                
                # Try to get message fields, with fallbacks if fields don't exist
                text = ""
                message = ""
                
                # Get text field
                if language == 'en':
                    text = template.get("text_used_english", "")
                else:
                    text = template.get("text_used_arabic", "")
                
                # Get message field
                if language == 'en':
                    message = template.get("message_english_translation", "")
                    if not message:
                        message = f"It's been {reverse_streak} days since your last Quran reading. Resume your journey today!"
                else:
                    message = template.get("message_arabic_translation", "")
                    if not message:
                        message = f"لقد مضت {reverse_streak} أيام منذ آخر قراءة للقرآن. استأنف رحلتك اليوم!"
                
                # If we have both text and message, return them
                if text and message:
                    return f"{header}{text}\n\n{message}"
                # If we only have text, just return that with the header
                elif text:
                    return f"{header}{text}"
                # If we only have message, just return that with the header
                elif message:
                    return f"{header}{message}"
                # If we have neither, return a fallback message
                else:
                    if language == 'en':
                        return f"{header}Don't worry! It's been {reverse_streak} days since your last check-in. You can start again today! 📖"
                    else:
                        return f"{header}لا تقلق! لقد مرت {reverse_streak} أيام منذ آخر تسجيل دخول. يمكنك البدء مرة أخرى اليوم! 📖"
            else:
                # Default message for new users
                if language == 'en':
                    return f"{header}Ready to start your Quran reading journey? Send a checkmark when you're done! 📚"
                else:
                    return f"{header}هل أنت مستعد لبدء رحلة قراءة القرآن؟ أرسل علامة اختيار عندما تنتهي! 📚"
        except Exception as e:
            # If anything goes wrong, return a simple fallback message
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating streak message: {str(e)}")
            
            if current_streak > 0:
                if language == 'en':
                    return f"{header}Amazing! You've maintained your Quran reading streak for {current_streak} days! 🎉"
                else:
                    return f"{header}رائع! لقد حافظت على سلسلة قراءة القرآن لمدة {current_streak} أيام! 🎉"
            elif reverse_streak > 0:
                if language == 'en':
                    return f"{header}Don't worry! It's been {reverse_streak} days since your last check-in. You can start again today! 📖"
                else:
                    return f"{header}لا تقلق! لقد مرت {reverse_streak} أيام منذ آخر تسجيل دخول. يمكنك البدء مرة أخرى اليوم! 📖"
            else:
                if language == 'en':
                    return f"{header}Ready to start your Quran reading journey? Send a checkmark when you're done! 📚"
                else:
                    return f"{header}هل أنت مستعد لبدء رحلة قراءة القرآن؟ أرسل علامة اختيار عندما تنتهي! 📚" 