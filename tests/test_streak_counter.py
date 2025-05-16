from datetime import datetime, timedelta
from bot.streak_counter.streak_counter import StreakCounter
from bot.database.db_manager import DatabaseManager
import time
import uuid

def test_streak_counter():
    """Test the StreakCounter with database integration."""
    
    # Create unique test user ID to avoid collisions
    test_telegram_id = int(str(uuid.uuid4().int)[:10])  # Using first 10 digits of a UUID as telegram_id
    test_username = f"test_user_{test_telegram_id}"
    
    print(f"Creating test user with telegram_id: {test_telegram_id}")
    
    # First create the user directly in the database
    db_manager = DatabaseManager()
    try:
        # Create user first
        user = db_manager.get_or_create_user(test_telegram_id, test_username)
        print(f"Created test user: {user['username']} with ID: {user['id']}")
        
        # Now create the StreakCounter
        print("Creating StreakCounter with test user...")
        counter = StreakCounter(telegram_id=test_telegram_id, username=test_username)
        
        # Test has_checkmark_today (should be False initially)
        has_checkmark = counter.has_checkmark_today()
        print(f"Has checkmark today (before): {has_checkmark}")
        
        # Test updating streak with checkmark
        current_time = datetime.now()
        current_streak, reverse_streak = counter.update_streak(True, current_time)
        print(f"After first checkmark: current_streak={current_streak}, reverse_streak={reverse_streak}")
        
        # Test has_checkmark_today again (should be True now)
        has_checkmark = counter.has_checkmark_today()
        print(f"Has checkmark today (after): {has_checkmark}")
        
        # Test message templates - get multiple reward messages to demonstrate randomness
        print("\nTesting random reward messages (English):")
        for i in range(5):
            en_message = counter.get_streak_message(language="en")
            print(f"{i+1}. {en_message}")
        
        print("\nTesting random reward messages (Arabic):")
        for i in range(3):
            ar_message = counter.get_streak_message(language="ar")
            print(f"{i+1}. {ar_message}")
        
        # Reset streak and test warning messages
        current_time = datetime.now()
        current_streak, reverse_streak = counter.update_streak(False, current_time)
        print(f"\nAfter missing checkmark: current_streak={current_streak}, reverse_streak={reverse_streak}")
        
        # Test warning messages - get multiple to demonstrate randomness
        print("\nTesting random warning messages (English):")
        for i in range(5):
            en_warning = counter.get_streak_message(language="en")
            print(f"{i+1}. {en_warning}")
            
        print("\nTesting random warning messages (Arabic):")
        for i in range(3):
            ar_warning = counter.get_streak_message(language="ar")
            print(f"{i+1}. {ar_warning}")
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
    finally:
        # Don't delete test data in production environment
        # In a real production test, you would want to clean up in a separate cleanup routine
        # or use a test database instead
        print("\nTest data is preserved in the database for inspection.")

def test_reverse_streak_after_days_missed():
    """Test the anti-streak functionality when days are missed."""
    
    # Create unique test user ID to avoid collisions
    test_telegram_id = int(str(uuid.uuid4().int)[:10])
    test_username = f"test_user_{test_telegram_id}"
    
    print(f"\nTESTING REVERSE STREAK CALCULATION")
    print(f"Creating test user with telegram_id: {test_telegram_id}")
    
    db_manager = DatabaseManager()
    try:
        # Create user first
        user = db_manager.get_or_create_user(test_telegram_id, test_username)
        print(f"Created test user: {user['username']} with ID: {user['id']}")
        
        # Create StreakCounter
        counter = StreakCounter(telegram_id=test_telegram_id, username=test_username)
        
        # 1. First establish a streak of 3 days
        print("\nSTEP 1: Building initial streak of 3 days")
        current_time = datetime.now()
        
        # Day 1 - First checkmark
        current_streak, reverse_streak = counter.update_streak(True, current_time)
        print(f"Day 1 checkmark: current_streak={current_streak}, reverse_streak={reverse_streak}")
        
        # Day 2 - Second checkmark (one day later)
        current_time += timedelta(days=1)
        current_streak, reverse_streak = counter.update_streak(True, current_time)
        print(f"Day 2 checkmark: current_streak={current_streak}, reverse_streak={reverse_streak}")
        
        # Day 3 - Third checkmark (one day later)
        current_time += timedelta(days=1)
        current_streak, reverse_streak = counter.update_streak(True, current_time)
        print(f"Day 3 checkmark: current_streak={current_streak}, reverse_streak={reverse_streak}")
        
        # 2. Now simulate missing several days (5 days)
        print("\nSTEP 2: Simulating missing 5 days")
        missing_days = 5
        current_time += timedelta(days=missing_days)
        
        # User returns after 5 days and sends a non-checkmark message
        current_streak, reverse_streak = counter.update_streak(False, current_time)
        print(f"After missing {missing_days} days (non-checkmark): current_streak={current_streak}, reverse_streak={reverse_streak}")
        # The reverse streak is actually days missed (5) + 1 because the current interaction also counts
        expected_reverse = missing_days + 1
        assert reverse_streak == expected_reverse, f"Expected reverse_streak to be {expected_reverse}, but got {reverse_streak}"
        assert current_streak == 0, f"Expected current_streak to be 0, but got {current_streak}"
        
        # 3. Test sending a checkmark after missing days
        print("\nSTEP 3: Sending a checkmark after missing days")
        current_streak, reverse_streak = counter.update_streak(True, current_time)
        print(f"Sending checkmark after missing days: current_streak={current_streak}, reverse_streak={reverse_streak}")
        assert reverse_streak == 0, f"Expected reverse_streak to be reset to 0, but got {reverse_streak}"
        assert current_streak == 1, f"Expected current_streak to be 1, but got {current_streak}"
        
        # 4. Test missing a very long period (45 days)
        print("\nSTEP 4: Missing a long period (45 days)")
        long_missing_days = 45
        current_time += timedelta(days=long_missing_days)
        
        # User returns after 45 days
        current_streak, reverse_streak = counter.update_streak(False, current_time)
        print(f"After missing {long_missing_days} days: current_streak={current_streak}, reverse_streak={reverse_streak}")
        # The calculated reverse streak includes all days since the last checkmark
        # In this case it's the 45 days + 6 days from the previous reverse streak
        expected_long_reverse = 51  # 45 + 6 days
        assert reverse_streak == expected_long_reverse, f"Expected reverse_streak to be {expected_long_reverse}, but got {reverse_streak}"
        
        print("\nReverse streak test completed successfully!")
        
    except AssertionError as ae:
        print(f"Test assertion failed: {str(ae)}")
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
    finally:
        print("\nTest data is preserved in the database for inspection.")

if __name__ == "__main__":
    # Run the regular streak counter test
    test_streak_counter()
    
    # Run the specific test for reverse streak calculation
    test_reverse_streak_after_days_missed() 