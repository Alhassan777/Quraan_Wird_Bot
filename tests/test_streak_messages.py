from datetime import datetime, timedelta
import uuid
from bot.streak_counter.streak_counter import StreakCounter
from bot.database.db_manager import DatabaseManager
from bot.database.config import MESSAGE_TEMPLATES_TABLE

def test_streak_messages():
    """Test that streak messages work correctly, especially warning messages for missed days."""
    
    # Create unique test user ID to avoid collisions
    test_telegram_id = int(str(uuid.uuid4().int)[:10])  # Using first 10 digits of a UUID as telegram_id
    test_username = f"test_user_{test_telegram_id}"
    
    print(f"Creating test user with telegram_id: {test_telegram_id}")
    
    # Create a database manager and streak counter
    db_manager = DatabaseManager()
    try:
        # First, create the user
        user = db_manager.get_or_create_user(test_telegram_id, test_username)
        print(f"Created test user: {user['username']} with ID: {user['id']}")
        
        counter = StreakCounter(telegram_id=test_telegram_id, username=test_username)
        
        # Test 1: Initial streak message for a new user
        print("\nTest 1: Initial streak message for a new user")
        initial_message = counter.get_streak_message(language="en")
        print(f"Initial message: {initial_message}")
        assert "Start your reading streak today" in initial_message, "New user message should contain prompt to start"
        
        # Test 2: Message after first checkmark (reward message)
        print("\nTest 2: Message after first checkmark (reward message)")
        current_time = datetime.now()
        current_streak, reverse_streak = counter.update_streak(True, current_time)
        print(f"Streak after checkmark: current={current_streak}, reverse={reverse_streak}")
        assert current_streak == 1, "Current streak should be 1 after first checkmark"
        assert reverse_streak == 0, "Reverse streak should be 0 after checkmark"
        
        reward_message = counter.get_streak_message(language="en")
        print(f"Reward message: {reward_message}")
        assert "Your current streak: 1 days" in reward_message, "Reward message should mention streak"
        
        # Test 3: Message after missing a day (warning message)
        print("\nTest 3: Message after missing a day (warning message)")
        # Simulate missing a day by setting the last check to 2 days ago
        two_days_ago = datetime.now() - timedelta(days=2)
        # Update directly in database
        db_manager.update_user_streak(test_telegram_id, 0, 1)
        # Update last_check_in to be in the past
        db_manager.supabase.table("streaks").update({
            "last_check_in": two_days_ago.isoformat()
        }).eq("user_id", user["id"]).execute()
        print("Set user to have missed 1 day")
        
        # Reload counter to get updated streak info
        counter = StreakCounter(telegram_id=test_telegram_id, username=test_username)
        warning_message = counter.get_streak_message(language="en")
        print(f"Warning message: {warning_message}")
        assert "Days of inactivity: 1" in warning_message, "Warning message should mention missed days"
        
        # Test 4: Message after missing 3 days
        print("\nTest 4: Message after missing 3 days")
        db_manager.update_user_streak(test_telegram_id, 0, 3)
        # Update last_check_in to be in the past
        four_days_ago = datetime.now() - timedelta(days=4)
        db_manager.supabase.table("streaks").update({
            "last_check_in": four_days_ago.isoformat()
        }).eq("user_id", user["id"]).execute()
        print("Set user to have missed 3 days")
        
        # Reload counter to get updated streak info
        counter = StreakCounter(telegram_id=test_telegram_id, username=test_username)
        warning_message = counter.get_streak_message(language="en")
        print(f"3-day warning message: {warning_message}")
        assert "Days of inactivity: 3" in warning_message, "Warning message should mention 3 missed days"
        
        # Test 5: Message after missing 7 days
        print("\nTest 5: Message after missing 7 days")
        db_manager.update_user_streak(test_telegram_id, 0, 7)
        # Update last_check_in to be in the past
        eight_days_ago = datetime.now() - timedelta(days=8)
        db_manager.supabase.table("streaks").update({
            "last_check_in": eight_days_ago.isoformat()
        }).eq("user_id", user["id"]).execute()
        print("Set user to have missed 7 days")
        
        # Reload counter to get updated streak info
        counter = StreakCounter(telegram_id=test_telegram_id, username=test_username)
        warning_message = counter.get_streak_message(language="en")
        print(f"7-day warning message: {warning_message}")
        assert "Days of inactivity: 7" in warning_message, "Warning message should mention 7 missed days"
        
        # Test 6: Test with database error (no templates found)
        print("\nTest 6: Test with database error (no templates found)")
        # Save the actual table name
        original_table = MESSAGE_TEMPLATES_TABLE
        # Temporarily change the table name to simulate a missing table
        import bot.database.config
        bot.database.config.MESSAGE_TEMPLATES_TABLE = "nonexistent_table"
        
        # This should still work thanks to our error handling and fallback messages
        fallback_message = counter.get_streak_message(language="en")
        print(f"Fallback message when templates missing: {fallback_message}")
        assert "Days of inactivity: 7" in fallback_message, "Fallback message should contain basic streak info"
        
        # Restore the original table name
        bot.database.config.MESSAGE_TEMPLATES_TABLE = original_table
        
        # Test 7: Resuming streak after break
        print("\nTest 7: Resuming streak after break")
        current_time = datetime.now()
        current_streak, reverse_streak = counter.update_streak(True, current_time)
        print(f"Streak after resuming: current={current_streak}, reverse={reverse_streak}")
        assert current_streak == 1, "Current streak should be 1 after resuming"
        assert reverse_streak == 0, "Reverse streak should be 0 after resuming"
        
        resumed_message = counter.get_streak_message(language="en")
        print(f"Resumed streak message: {resumed_message}")
        assert "Your current streak: 1 days" in resumed_message, "Resumed message should show new streak of 1"
        
        print("\nAll streak message tests passed successfully!")
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        raise
        
if __name__ == "__main__":
    test_streak_messages() 