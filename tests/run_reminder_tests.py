#!/usr/bin/env python3
import unittest
import sys
import os
import asyncio
import importlib.util
import importlib

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def fix_imports():
    """
    Fix the relative imports by creating a module level patch.
    This will monkey patch the sys.modules to have the correct imports.
    """
    print("Fixing imports for tests...")
    
    # First ensure we have the bot module in sys.modules
    if 'bot' not in sys.modules:
        bot_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bot'))
        spec = importlib.util.spec_from_file_location('bot', os.path.join(bot_path, '__init__.py'))
        bot_module = importlib.util.module_from_spec(spec)
        sys.modules['bot'] = bot_module
        spec.loader.exec_module(bot_module)
    
    # Create a patch for utils
    if 'utils' not in sys.modules:
        sys.modules['utils'] = sys.modules['bot.utils']
    
    # Create a patch for streak_counter
    if 'streak_counter' not in sys.modules:
        sys.modules['streak_counter'] = sys.modules['bot.streak_counter']
    
    # Create a patch for database
    if 'database' not in sys.modules:
        sys.modules['database'] = sys.modules['bot.database']
    
    # Create a patch for reminders
    if 'reminders' not in sys.modules:
        sys.modules['reminders'] = sys.modules['bot.reminders']
    
    print("Import patching complete.")

# Fix imports before importing test modules
fix_imports()

# Import the test classes
from test_reminder_timing import TestReminderTiming
from test_end_of_day_notification import TestEndOfDayNotification

def run_async_test(test_case):
    """Run asynchronous test cases."""
    loop = asyncio.get_event_loop()
    for method_name in dir(test_case):
        if method_name.startswith('test_'):
            method = getattr(test_case, method_name)
            if asyncio.iscoroutinefunction(method):
                loop.run_until_complete(method())
            else:
                method()

def run_tests():
    """Run all reminder-related tests."""
    print("=" * 50)
    print("TESTING REMINDER FUNCTIONALITY")
    print("=" * 50)
    print("\n" + "-" * 50)
    print("Testing reminders at designated times:")
    print("-" * 50)
    
    # Test reminder timing
    timing_test = TestReminderTiming()
    run_async_test(timing_test)
    
    print("\n" + "-" * 50)
    print("Testing end-of-day notifications:")
    print("-" * 50)
    
    # Test end-of-day notifications
    eod_test = TestEndOfDayNotification()
    run_async_test(eod_test)
    
    print("\n" + "=" * 50)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 50)

if __name__ == "__main__":
    run_tests() 