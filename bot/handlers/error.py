import logging
from telegram import Update
from telegram.ext import ContextTypes
from utils.utils import get_user_language

logger = logging.getLogger(__name__)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot."""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_user:
        user_id = update.effective_user.id
        lang = get_user_language(user_id)
        
        if lang == "en":
            error_message = (
                "Sorry, something went wrong. Please try again later or contact support."
            )
        else:
            error_message = (
                "عذراً، حدث خطأ ما. يرجى المحاولة مرة أخرى لاحقاً أو التواصل مع الدعم."
            )
        
        try:
            await update.effective_message.reply_text(error_message)
        except Exception as e:
            logger.error(f"Error sending error message: {str(e)}") 