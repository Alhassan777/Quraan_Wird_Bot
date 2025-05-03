from supabase import create_client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def inspect_database():
    """Print information about the database tables to help troubleshoot issues."""
    
    # Check users table
    print("== Users Table ==")
    try:
        response = supabase.table("users").select("*").execute()
        users = response.data
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"  ID: {user.get('id')}, Telegram ID: {user.get('telegram_id')}, Username: {user.get('username')}")
    except Exception as e:
        print(f"Error querying users table: {str(e)}")
        
    # Check streaks table
    print("\n== Streaks Table ==")
    try:
        response = supabase.table("streaks").select("*").execute()
        streaks = response.data
        print(f"Found {len(streaks)} streak records:")
        for streak in streaks:
            print(f"  ID: {streak.get('id')}, User ID: {streak.get('user_id')}, Current Streak: {streak.get('current_streak')}")
    except Exception as e:
        print(f"Error querying streaks table: {str(e)}")
        
    # Check check_ins table
    print("\n== Check-ins Table ==")
    try:
        response = supabase.table("check_ins").select("*").execute()
        check_ins = response.data
        print(f"Found {len(check_ins)} check-in records:")
        for check_in in check_ins:
            print(f"  ID: {check_in.get('id')}, User ID: {check_in.get('user_id')}, Time: {check_in.get('check_in_time')}")
    except Exception as e:
        print(f"Error querying check_ins table: {str(e)}")
        
    # Check message_templates table
    print("\n== Message Templates Table ==")
    try:
        response = supabase.table("message_templates").select("*").execute()
        templates = response.data
        print(f"Found {len(templates)} message templates:")
        template_types = {}
        for template in templates:
            key = f"{template.get('template_type')}_{template.get('threshold_days')}"
            if key not in template_types:
                template_types[key] = 0
            template_types[key] += 1
        
        for key, count in template_types.items():
            print(f"  {key}: {count} entries")
    except Exception as e:
        print(f"Error querying message_templates table: {str(e)}")

if __name__ == "__main__":
    inspect_database() 