import csv
from typing import List, Dict
from .db_manager import DatabaseManager

def import_message_templates(csv_path: str):
    """Import message templates from CSV file into Supabase."""
    db = DatabaseManager()
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Convert CSV row to database format
            template = {
                "message_type": row.get("message_type"),
                "streak_range": row.get("streak_range"),
                "time_of_day": row.get("time_of_day"),
                "message_text": row.get("message_text"),
                "language": row.get("language", "en")
            }
            
            # Insert into database
            db.supabase.table("message_templates").insert(template).execute()

def import_user_data(csv_path: str):
    """Import user data from CSV file into Supabase."""
    db = DatabaseManager()
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            user = {
                "telegram_id": int(row.get("telegram_id")),
                "username": row.get("username"),
                "current_streak": int(row.get("current_streak", 0)),
                "longest_streak": int(row.get("longest_streak", 0)),
                "reverse_streak": int(row.get("reverse_streak", 0))
            }
            
            # Insert into database
            db.supabase.table("users").insert(user).execute()

if __name__ == "__main__":
    # Example usage
    import_message_templates("path/to/message_templates.csv")
    import_user_data("path/to/user_data.csv") 