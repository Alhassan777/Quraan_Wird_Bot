from datetime import datetime, time
from bot.reminders.reminder_manager import ReminderManager
import uuid

def test_daily_reminders():
    """Test the daily reminder message functionality."""
    
    # Create unique test user ID to avoid collisions
    test_telegram_id = int(str(uuid.uuid4().int)[:10])  # Using first 10 digits of a UUID as telegram_id
    
    print(f"Creating test user with telegram_id: {test_telegram_id}")
    
    # Create a ReminderManager
    reminder_manager = ReminderManager()
    
    # Get a user streak counter
    streak_counter = reminder_manager.get_user_counter(test_telegram_id)
    print(f"Created streak counter for test user")
    
    # Test getting random reminder messages
    print("\nTesting random reminder messages:")
    
    # Get 5 English reminder messages to demonstrate randomness
    print("\nEnglish reminders:")
    for i in range(5):
        en_message = reminder_manager.get_reminder_message(test_telegram_id, language="en")
        print(f"{i+1}. {en_message}")
    
    # Get 5 Arabic reminder messages to demonstrate randomness
    print("\nArabic reminders:")
    for i in range(5):
        ar_message = reminder_manager.get_reminder_message(test_telegram_id, language="ar")
        print(f"{i+1}. {ar_message}")
    
    # Test reminder timing functionality
    current_time = time(8, 0)  # 8:00 AM
    should_send = reminder_manager.should_send_reminder(test_telegram_id, current_time)
    print(f"\nShould send reminder at {current_time}: {should_send}")
    
    # Mark reminder as sent
    reminder_manager.mark_reminder_sent(test_telegram_id, current_time)
    
    # Check if we should send again (should be False now)
    should_send_again = reminder_manager.should_send_reminder(test_telegram_id, current_time)
    print(f"Should send reminder again at {current_time}: {should_send_again}")
    
    # Try a different time
    different_time = time(12, 0)  # 12:00 PM
    should_send_different = reminder_manager.should_send_reminder(test_telegram_id, different_time)
    print(f"Should send reminder at {different_time}: {should_send_different}")
    
    # Record a check-in and see if it stops sending reminders
    current_datetime = datetime.now()
    streak_counter.update_streak(True, current_datetime)
    print(f"\nRecorded a check-in, current streak: {streak_counter.get_streak_message()}")
    
    # Should not send reminder after check-in
    should_send_after_checkin = reminder_manager.should_send_reminder(test_telegram_id, different_time)
    print(f"Should send reminder after check-in: {should_send_after_checkin}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_daily_reminders() 