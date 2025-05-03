from datetime import datetime
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

if __name__ == "__main__":
    test_streak_counter() 