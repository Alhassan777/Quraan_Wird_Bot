from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_tables():
    # Users table
    users_sql = """
    create table if not exists users (
        id uuid primary key default uuid_generate_v4(),
        telegram_id bigint unique not null,
        username text,
        language text default 'en',
        timezone text default 'UTC',
        created_at timestamp with time zone default now()
    );
    """

    # Streaks table
    streaks_sql = """
    create table if not exists streaks (
        id uuid primary key default uuid_generate_v4(),
        user_id uuid references users(id) on delete cascade,
        current_streak integer default 0,
        reverse_streak integer default 0,
        last_check_in timestamp with time zone,
        updated_at timestamp with time zone default now()
    );
    """

    # Check-ins table
    check_ins_sql = """
    create table if not exists check_ins (
        id uuid primary key default uuid_generate_v4(),
        user_id uuid references users(id) on delete cascade,
        check_in_time timestamp with time zone default now(),
        checkmark_status boolean not null,
        created_at timestamp with time zone default now()
    );
    """

    # Message templates table
    message_templates_sql = """
    create table if not exists message_templates (
        id uuid primary key default uuid_generate_v4(),
        template_type text not null,         -- 'reward' or 'warning'
        threshold_days integer not null,     -- 1, 3, 5, 7, 30 days
        text_used_english text,              -- citation (hadith/aya) in English
        text_used_arabic text,               -- citation in Arabic
        message_arabic_translation text,     -- interpretive message in Arabic
        message_english_translation text,    -- interpretive message in English
        created_at timestamp with time zone default now()
    );
    """

    # Reminders table
    reminders_sql = """
    create table if not exists reminders (
        id uuid primary key default uuid_generate_v4(),
        user_id uuid references users(id) on delete cascade,
        reminder_time time not null,
        sent_at timestamp with time zone default now()
    );
    """

    # Execute SQL
    for sql in [users_sql, streaks_sql, check_ins_sql, message_templates_sql, reminders_sql]:
        response = supabase.rpc("execute_sql", {"sql": sql}).execute()
        print(response)

if __name__ == "__main__":
    create_tables() 