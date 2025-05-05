from datetime import datetime, time
import uuid
from bot.database.db_manager import DatabaseManager
from bot.reminders.reminder_manager import ReminderManager

def test_reminder_string_handling():
    """Test that reminder functions handle string and list type correctly."""
    
    # Create unique test user ID to avoid collisions
    test_telegram_id = int(str(uuid.uuid4().int)[:10])  # Using first 10 digits of a UUID as telegram_id
    test_username = f"test_user_{test_telegram_id}"
    
    print(f"Creating test user with telegram_id: {test_telegram_id}")
    
    # Create a database manager and reminder manager
    db_manager = DatabaseManager()
    reminder_manager = ReminderManager()
    
    try:
        # First, create the user
        user = db_manager.get_or_create_user(test_telegram_id, test_username)
        print(f"Created test user: {user['username']} with ID: {user['id']}")
        
        # Test 1: Set a reminder with set_user_reminder
        reminder_time = time(8, 0)  # 8:00 AM
        print(f"\nTest 1: Setting reminder at {reminder_time.strftime('%H:%M')}...")
        success = db_manager.set_user_reminder(test_telegram_id, reminder_time)
        print(f"set_user_reminder result: {success}")
        
        # Verify the reminder was set
        user_data = db_manager.get_or_create_user(test_telegram_id, "")
        reminders = user_data.get("reminder_times", [])
        print(f"Reminders after setting first one: {reminders}")
        assert "08:00" in reminders, "First reminder should be set"
        
        # Test 2: Add another reminder
        second_reminder = time(12, 0)  # 12:00 PM
        print(f"\nTest 2: Setting second reminder at {second_reminder.strftime('%H:%M')}...")
        success = db_manager.set_user_reminder(test_telegram_id, second_reminder)
        print(f"set_user_reminder result: {success}")
        
        # Verify both reminders exist
        user_data = db_manager.get_or_create_user(test_telegram_id, "")
        reminders = user_data.get("reminder_times", [])
        print(f"Reminders after setting second one: {reminders}")
        assert "08:00" in reminders, "First reminder should still exist"
        assert "12:00" in reminders, "Second reminder should be set"
        
        # Test 3: Test update_user_reminder_times with a string
        string_reminder = "16:00"  # 4:00 PM as a string
        print(f"\nTest 3: Testing update_user_reminder_times with a string: {string_reminder}")
        # Intentionally pass a string instead of a list to test our fix
        success = db_manager.update_user_reminder_times(test_telegram_id, string_reminder)
        print(f"update_user_reminder_times with string result: {success}")
        
        # Verify the reminder was updated correctly
        user_data = db_manager.get_or_create_user(test_telegram_id, "")
        reminders = user_data.get("reminder_times", [])
        print(f"Reminders after update with string: {reminders}")
        
        # Could be a string or a list in the database, but should be usable as a list
        if isinstance(reminders, str):
            print("Reminder is stored as a string in the database")
            # If it's stored as a string, it should contain our reminder
            assert string_reminder in reminders, "String reminder should be in the database value"
        else:
            # If it's stored as a list, it should be a list with our reminder
            assert isinstance(reminders, list), "Reminders should be a list when not a string"
            assert string_reminder in reminders, "String reminder should be in the list"
        
        # Test 4: Test get_users_with_reminders can handle various formats
        print("\nTest 4: Testing get_users_with_reminders...")
        # First set reminder_times to a string to simulate the issue
        db_manager.supabase.table("users").update({"reminder_times": "08:00"}).eq("id", user["id"]).execute()
        print("Set reminder_times to a string value in database")
        
        # Now try to get users with reminders
        users = db_manager.get_users_with_reminders()
        print(f"Found {len(users)} users with reminders")
        
        # Verify our test user is in the results
        test_user_found = False
        for u in users:
            if u.get("telegram_id") == test_telegram_id:
                test_user_found = True
                print(f"Found test user in results with reminder_times: {u.get('reminder_times')}")
                # Verify reminder_times was properly converted to time objects
                assert isinstance(u.get("reminder_times"), list), "reminder_times should be a list"
                assert all(isinstance(t, time) for t in u.get("reminder_times")), "All items should be time objects"
                break
        
        assert test_user_found, "Test user should be found in get_users_with_reminders results"
        
        # Test 5: Test reminder_manager functions...
        print("\nTest 5: Testing reminder manager functions...")
        # Make sure we can get reminders for a user
        reminders = reminder_manager.get_reminders_for_user(test_telegram_id)
        print(f"Reminders from reminder_manager: {reminders}")
        assert isinstance(reminders, list), "get_reminders_for_user should return a list"
        
        # Verify deletion functionality
        # First add a new clear reminder that we'll definitely delete
        new_time = time(9, 30)  # 9:30 AM
        print(f"Adding new reminder at {new_time.strftime('%H:%M')} to test deletion...")
        reminder_manager.set_custom_reminder_time(test_telegram_id, new_time)
        
        # Verify it was added
        reminders = reminder_manager.get_reminders_for_user(test_telegram_id)
        print(f"Reminders after adding: {reminders}")
        assert "09:30" in reminders, "New reminder should be in the list" 
        
        # Now delete it
        print(f"Deleting reminder at {new_time.strftime('%H:%M')}...")
        success = reminder_manager.delete_reminder(test_telegram_id, new_time)
        print(f"delete_reminder result: {success}")
        
        # Verify deletion worked
        reminders = reminder_manager.get_reminders_for_user(test_telegram_id)
        print(f"Reminders after deletion: {reminders}")
        assert "09:30" not in reminders, "Deleted reminder should not be in the list"
        
        print("\nAll reminder string handling tests passed successfully!")
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        raise
        
if __name__ == "__main__":
    test_reminder_string_handling() 