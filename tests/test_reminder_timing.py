import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os
import pytz
from datetime import datetime, time

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Try both relative and absolute imports
try:
    # Try relative imports first
    from bot.handlers.reminder import check_and_send_reminders
    from bot.database.db_manager import DatabaseManager
    from bot.reminders.reminder_manager import ReminderManager
    from bot.streak_counter.streak_counter import StreakCounter
except ImportError:
    # Fallback to direct imports
    from handlers.reminder import check_and_send_reminders
    from database.db_manager import DatabaseManager
    from reminders.reminder_manager import ReminderManager
    from streak_counter.streak_counter import StreakCounter

class TestReminderTiming(unittest.TestCase):
    """Tests to verify reminders are sent at the correct time."""
    
    @patch('bot.handlers.reminder.DatabaseManager')
    @patch('bot.handlers.reminder.datetime')
    async def test_reminder_exact_time_match(self, mock_datetime, mock_db_manager):
        # Mock the current time to be 8:00 AM exactly
        mock_now = MagicMock()
        mock_now.time.return_value = time(8, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        
        # Mock timezone
        mock_timezone = MagicMock()
        mock_timezone.return_value = pytz.timezone("UTC")
        
        # Mock user with a reminder at 8:00 AM
        mock_user = {
            "telegram_id": 123456789,
            "reminder_times": [time(8, 0, 0)],
            "timezone": "UTC"
        }
        
        # Mock the database manager to return our test user
        mock_db_instance = MagicMock()
        mock_db_manager.return_value = mock_db_instance
        mock_db_instance.get_users_with_reminders.return_value = [mock_user]
        mock_db_instance.get_today_reminders.return_value = []  # No reminders sent today
        
        # Create a mock context for the function call
        mock_context = MagicMock()
        mock_context.job_queue = MagicMock()
        mock_context.job_queue.run_once = AsyncMock()
        
        # Call the function
        await check_and_send_reminders(mock_context)
        
        # Verify the reminder was scheduled
        mock_context.job_queue.run_once.assert_called_once()
        
        # Extract the data passed to run_once
        call_args = mock_context.job_queue.run_once.call_args[1]
        self.assertEqual(call_args['data']['user_id'], 123456789)
        
        print("✅ Test passed: Reminder was scheduled at the exact designated time")
    
    @patch('bot.handlers.reminder.DatabaseManager')
    @patch('bot.handlers.reminder.datetime')
    async def test_reminder_not_sent_different_time(self, mock_datetime, mock_db_manager):
        # Mock the current time to be 8:30 AM (not matching any reminder)
        mock_now = MagicMock()
        mock_now.time.return_value = time(8, 30, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        
        # Mock user with a reminder at 8:00 AM
        mock_user = {
            "telegram_id": 123456789,
            "reminder_times": [time(8, 0, 0)],
            "timezone": "UTC"
        }
        
        # Mock the database manager to return our test user
        mock_db_instance = MagicMock()
        mock_db_manager.return_value = mock_db_instance
        mock_db_instance.get_users_with_reminders.return_value = [mock_user]
        
        # Create a mock context for the function call
        mock_context = MagicMock()
        mock_context.job_queue = MagicMock()
        mock_context.job_queue.run_once = AsyncMock()
        
        # Call the function
        await check_and_send_reminders(mock_context)
        
        # Verify no reminder was scheduled
        mock_context.job_queue.run_once.assert_not_called()
        
        print("✅ Test passed: No reminder was scheduled for non-matching time")
    
    @patch('bot.handlers.reminder.DatabaseManager')
    @patch('bot.handlers.reminder.datetime')
    async def test_reminder_respects_timezone(self, mock_datetime, mock_db_manager):
        # Mock the current time to be 8:00 AM UTC
        mock_now = MagicMock()
        mock_now.time.return_value = time(8, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # Create a custom side effect to handle timezone parameter
        def datetime_side_effect(*args, **kwargs):
            if 'timezone' in kwargs:
                tz = kwargs['timezone']
                if tz.zone == "America/New_York":
                    # Mock that it's 3:00 AM in New York when it's 8:00 AM UTC
                    result = MagicMock()
                    result.time.return_value = time(3, 0, 0)
                    result.hour = 3
                    result.minute = 0
                    return result
            return datetime(*args, **kwargs)
        
        mock_datetime.now.side_effect = datetime_side_effect
        
        # Mock pytz.timezone to return actual timezone objects
        def get_timezone(tz_name):
            return pytz.timezone(tz_name)
        
        with patch('bot.handlers.reminder.pytz.timezone', side_effect=get_timezone):
            # Mock user with a reminder at 8:00 AM in a New York timezone
            mock_user = {
                "telegram_id": 123456789,
                "reminder_times": [time(8, 0, 0)],  # Reminder set for 8:00 AM
                "timezone": "America/New_York"      # But user is in New York
            }
            
            # Mock the database manager to return our test user
            mock_db_instance = MagicMock()
            mock_db_manager.return_value = mock_db_instance
            mock_db_instance.get_users_with_reminders.return_value = [mock_user]
            mock_db_instance.get_today_reminders.return_value = []
            
            # Create a mock context for the function call
            mock_context = MagicMock()
            mock_context.job_queue = MagicMock()
            mock_context.job_queue.run_once = AsyncMock()
            
            # Call the function
            await check_and_send_reminders(mock_context)
            
            # Verify no reminder was scheduled (it should be 3:00 AM in New York)
            mock_context.job_queue.run_once.assert_not_called()
            
            print("✅ Test passed: Timezone differences are respected")
    
    @patch('bot.handlers.reminder.DatabaseManager')
    @patch('bot.handlers.reminder.datetime')
    async def test_reminder_not_sent_twice(self, mock_datetime, mock_db_manager):
        # Mock the current time to be 8:00 AM
        mock_now = MagicMock()
        mock_now.time.return_value = time(8, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        
        # Mock user with a reminder at 8:00 AM
        mock_user = {
            "telegram_id": 123456789,
            "reminder_times": [time(8, 0, 0)],
            "timezone": "UTC"
        }
        
        # Mock the database manager to return our test user
        mock_db_instance = MagicMock()
        mock_db_manager.return_value = mock_db_instance
        mock_db_instance.get_users_with_reminders.return_value = [mock_user]
        
        # Mock that a reminder has already been sent today at 8:00
        mock_db_instance.get_today_reminders.return_value = [
            {"reminder_time": "08:00"}
        ]
        
        # Create a mock context for the function call
        mock_context = MagicMock()
        mock_context.job_queue = MagicMock()
        mock_context.job_queue.run_once = AsyncMock()
        
        # Call the function
        await check_and_send_reminders(mock_context)
        
        # Verify no reminder was scheduled again
        mock_context.job_queue.run_once.assert_not_called()
        
        print("✅ Test passed: Reminder was not sent twice for the same time")

if __name__ == "__main__":
    unittest.main() 