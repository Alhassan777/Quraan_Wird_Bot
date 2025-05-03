from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from streak_counter.streak_counter import StreakCounter
from utils.utils import get_user_language
from database.db_manager import DatabaseManager
import logging

logger = logging.getLogger(__name__)

async def streak_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the user's current streak status."""
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    lang = get_user_language(user_id)
    
    # Create a streak counter for the user
    streak_counter = StreakCounter(telegram_id=user_id, username=username)
    
    # Get user data to display streak information
    db_manager = DatabaseManager()
    user_data = db_manager.get_or_create_user(user_id, username)
    current_streak = user_data.get("current_streak", 0)
    
    # Create header based on current streak
    header = ""
    if current_streak > 0:
        if lang == "ar":
            header = f"🔥 *لديك سلسلة قراءة مستمرة منذ {current_streak} أيام*\n\n"
        else:  # Default to English
            header = f"🔥 *Your current streak: {current_streak} days*\n\n"
    
    # Get streak message without the header (since we add it separately)
    streak_message = streak_counter.get_streak_message(language=lang, include_header=False)
    
    # Title based on language
    title = "📊 *Your Quran Reading Streak*" if lang != "ar" else "📊 *سلسلة قراءة القرآن الخاصة بك*"
    
    # Send the streak message with title and header
    await update.message.reply_text(
        f"{title}\n\n{header}{streak_message}",
        parse_mode=ParseMode.MARKDOWN
    ) 