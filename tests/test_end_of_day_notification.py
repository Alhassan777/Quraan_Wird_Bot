import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os
import pytz
from datetime import datetime, time, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Fix imports to use absolute paths
from bot.handlers.reminder import check_end_of_day_missed_checkmarks
from bot.database.db_manager import DatabaseManager
from bot.streak_counter.streak_counter import StreakCounter

class TestEndOfDayNotification(unittest.TestCase):
    """Tests to verify end-of-day notifications for users who haven't checked in."""
    
    @patch('bot.handlers.reminder.StreakCounter')
    @patch('bot.handlers.reminder.get_user_language')
    @patch('bot.handlers.reminder.DatabaseManager')
    @patch('bot.handlers.reminder.datetime')
    async def test_notification_sent_for_active_streak(self, mock_datetime, mock_db_manager, 
                                                      mock_language, mock_streak_counter):
        # Mock the current time to be 9:30 PM (end of day)
        mock_now = MagicMock()
        mock_now.time.return_value = time(21, 30, 0)
        mock_now.hour = 21
        mock_now.minute = 30
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        
        # Mock users table response with a user who has an active streak
        mock_user = {
            "telegram_id": 123456789,
            "timezone": "UTC",
            "current_streak": 5,  # 5-day streak
            "reverse_streak": 0
        }
        
        # Mock database response
        mock_db_instance = MagicMock()
        mock_db_manager.return_value = mock_db_instance
        mock_db_instance.supabase.table().select().execute.return_value.data = [mock_user]
        mock_db_instance.get_or_create_user.return_value = mock_user
        
        # Mock template return
        mock_template = {
            "text_used_english": "You haven't read the Quran today!",
            "text_used_arabic": "لم تقرأ القرآن اليوم!",
            "message_english_translation": "Don't let your streak break.",
            "message_arabic_translation": "لا تدع سلسلة القراءة تنكسر."
        }
        mock_db_instance.get_message_template.return_value = mock_template
        
        # Mock user language
        mock_language.return_value = "en"
        
        # Mock streak counter - user has no checkmark today
        mock_streak_instance = MagicMock()
        mock_streak_counter.return_value = mock_streak_instance
        mock_streak_instance.has_checkmark_today.return_value = False
        mock_streak_instance.get_appropriate_threshold.return_value = 1
        
        # Create a mock context for the function call
        mock_context = MagicMock()
        mock_context.bot = MagicMock()
        mock_context.bot.send_message = AsyncMock()
        
        # Call the function
        await check_end_of_day_missed_checkmarks(mock_context)
        
        # Verify the notification was sent
        mock_context.bot.send_message.assert_called_once()
        
        # Verify the telegram_id and some content in the message
        call_args = mock_context.bot.send_message.call_args[1]
        self.assertEqual(call_args['chat_id'], 123456789)
        self.assertIn("Streak Break Alert", call_args['text'])
        self.assertIn("You haven't read the Quran today", call_args['text'])
        
        print("✅ Test passed: End-of-day notification sent for user with active streak")
    
    @patch('bot.handlers.reminder.StreakCounter')
    @patch('bot.handlers.reminder.get_user_language')
    @patch('bot.handlers.reminder.DatabaseManager')
    @patch('bot.handlers.reminder.datetime')
    async def test_notification_sent_with_reverse_streak(self, mock_datetime, mock_db_manager, 
                                                        mock_language, mock_streak_counter):
        # Mock the current time to be 9:30 PM (end of day)
        mock_now = MagicMock()
        mock_now.time.return_value = time(21, 30, 0)
        mock_now.hour = 21
        mock_now.minute = 30
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        
        # Mock users table response with a user who has a reverse streak (missed days)
        mock_user = {
            "telegram_id": 123456789,
            "timezone": "UTC",
            "current_streak": 0,     # No active streak
            "reverse_streak": 3      # 3 days missed
        }
        
        # Mock database response
        mock_db_instance = MagicMock()
        mock_db_manager.return_value = mock_db_instance
        mock_db_instance.supabase.table().select().execute.return_value.data = [mock_user]
        mock_db_instance.get_or_create_user.return_value = mock_user
        
        # Mock template return - using a 3-day warning template
        mock_template = {
            "text_used_english": "Take care of this Quran...",
            "text_used_arabic": "حافظ على هذا القرآن...",
            "message_english_translation": "It's been 3 days since you read the Quran.",
            "message_arabic_translation": "مضت 3 أيام منذ آخر قراءة للقرآن."
        }
        mock_db_instance.get_message_template.return_value = mock_template
        
        # Mock user language
        mock_language.return_value = "en"
        
        # Mock streak counter - user has no checkmark today
        mock_streak_instance = MagicMock()
        mock_streak_counter.return_value = mock_streak_instance
        mock_streak_instance.has_checkmark_today.return_value = False
        mock_streak_instance.get_appropriate_threshold.return_value = 3  # 3-day threshold
        
        # Create a mock context for the function call
        mock_context = MagicMock()
        mock_context.bot = MagicMock()
        mock_context.bot.send_message = AsyncMock()
        
        # Call the function
        await check_end_of_day_missed_checkmarks(mock_context)
        
        # Verify the notification was sent
        mock_context.bot.send_message.assert_called_once()
        
        # Verify the message uses the 3-day template
        call_args = mock_context.bot.send_message.call_args[1]
        self.assertEqual(call_args['chat_id'], 123456789)
        self.assertIn("Take care of this Quran", call_args['text'])
        
        print("✅ Test passed: End-of-day notification sent with appropriate warning for reverse streak")
    
    @patch('bot.handlers.reminder.StreakCounter')
    @patch('bot.handlers.reminder.DatabaseManager')
    @patch('bot.handlers.reminder.datetime')
    async def test_notification_not_sent_with_checkmark(self, mock_datetime, mock_db_manager, mock_streak_counter):
        # Mock the current time to be 9:30 PM (end of day)
        mock_now = MagicMock()
        mock_now.time.return_value = time(21, 30, 0)
        mock_now.hour = 21
        mock_now.minute = 30
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        
        # Mock user with active streak
        mock_user = {
            "telegram_id": 123456789,
            "timezone": "UTC",
            "current_streak": 5,  # 5-day streak
            "reverse_streak": 0
        }
        
        # Mock database response
        mock_db_instance = MagicMock()
        mock_db_manager.return_value = mock_db_instance
        mock_db_instance.supabase.table().select().execute.return_value.data = [mock_user]
        
        # Mock streak counter - user HAS a checkmark today
        mock_streak_instance = MagicMock()
        mock_streak_counter.return_value = mock_streak_instance
        mock_streak_instance.has_checkmark_today.return_value = True  # User already checked in
        
        # Create a mock context for the function call
        mock_context = MagicMock()
        mock_context.bot = MagicMock()
        mock_context.bot.send_message = AsyncMock()
        
        # Call the function
        await check_end_of_day_missed_checkmarks(mock_context)
        
        # Verify no notification was sent
        mock_context.bot.send_message.assert_not_called()
        
        print("✅ Test passed: No notification sent for users who already checked in")
    
    @patch('bot.handlers.reminder.StreakCounter')
    @patch('bot.handlers.reminder.DatabaseManager')
    @patch('bot.handlers.reminder.datetime')
    async def test_notification_not_sent_wrong_time(self, mock_datetime, mock_db_manager, mock_streak_counter):
        # Mock the current time to be 3:00 PM (not end of day)
        mock_now = MagicMock()
        mock_now.time.return_value = time(15, 0, 0)
        mock_now.hour = 15
        mock_now.minute = 0
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        
        # Mock user with active streak
        mock_user = {
            "telegram_id": 123456789,
            "timezone": "UTC",
            "current_streak": 5,  # 5-day streak
            "reverse_streak": 0
        }
        
        # Mock database response
        mock_db_instance = MagicMock()
        mock_db_manager.return_value = mock_db_instance
        mock_db_instance.supabase.table().select().execute.return_value.data = [mock_user]
        
        # Mock streak counter - user has no checkmark today
        mock_streak_instance = MagicMock()
        mock_streak_counter.return_value = mock_streak_instance
        mock_streak_instance.has_checkmark_today.return_value = False
        
        # Create a mock context for the function call
        mock_context = MagicMock()
        mock_context.bot = MagicMock()
        mock_context.bot.send_message = AsyncMock()
        
        # Call the function
        await check_end_of_day_missed_checkmarks(mock_context)
        
        # Verify no notification was sent (wrong time of day)
        mock_context.bot.send_message.assert_not_called()
        
        print("✅ Test passed: No notification sent at the wrong time of day")

if __name__ == "__main__":
    unittest.main() 