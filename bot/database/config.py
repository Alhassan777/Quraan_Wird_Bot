import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Database Table Names
USERS_TABLE = "users"
STREAKS_TABLE = "streaks"
CHECK_INS_TABLE = "check_ins"
MESSAGE_TEMPLATES_TABLE = "message_templates"
REMINDERS_TABLE = "reminders"
DAILY_REMINDERS_MESSAGES_TABLE = "daily_reminders_messages" 