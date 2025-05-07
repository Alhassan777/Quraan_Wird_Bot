import logging
import signal
import sys
import os

# Add parent directory to path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)

# Using absolute imports for clarity
from bot.config.config import TELEGRAM_TOKEN, LOG_LEVEL
from bot.handlers.start import start, language_selection
from bot.handlers.help import help_command
from bot.handlers.tafsir import handle_text, handle_photo
from bot.handlers.error import error_handler
from bot.handlers.streak import streak_command
from bot.handlers.reminder import register_reminder_handlers
from bot.database.db_manager import DatabaseManager

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL)
)
logger = logging.getLogger(__name__)

def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def init_db():
    """Initialize the database connection."""
    logger.info("Initializing database connection...")
    # Create an instance of the database manager
    # This will establish the connection to the database
    db_manager = DatabaseManager()
    return db_manager

def populate_quran_quotes():
    """Populate initial Quran quotes if needed."""
    logger.info("Checking if Quran quotes need to be populated...")
    # This function would normally populate initial data
    # For now, it's just a placeholder

def setup_metrics():
    """Set up metrics collection."""
    logger.info("Setting up metrics collection...")
    # This function would set up metrics collection
    # For now, it's just a placeholder

def main() -> None:
    """Start the bot."""
    # Set up signal handlers
    setup_signal_handlers()
    
    # Initialize database
    try:
        db_manager = init_db()
        # Populate initial Quran quotes
        populate_quran_quotes()
    except Exception as e:
        logger.critical(f"Failed to initialize database: {e}")
        return
    
    # Set up metrics
    setup_metrics()
    
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("streak", streak_command))
    
    # Register reminder handlers
    logger.info("Registering reminder handlers...")
    register_reminder_handlers(application)
    
    # Add language selection handler (must come before text/photo handlers)
    application.add_handler(MessageHandler(
        filters.TEXT & (filters.Regex("^English$") | filters.Regex("^العربية$")),
        language_selection
    ))
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the Bot
    logger.info("Bot starting...")
    
    # Use webhook in production (Railway), otherwise use polling
    if os.environ.get('RAILWAY_STATIC_URL'):
        port = int(os.environ.get('PORT', 8443))
        app_name = os.environ.get('RAILWAY_STATIC_URL')
        
        # Remove potential https:// prefix for the webhook URL
        if app_name.startswith('https://'):
            app_name = app_name[8:]
        
        # Make sure to drop any existing webhook to prevent conflicts
        logger.info("Removing any existing webhook to prevent conflicts...")
        application.bot.delete_webhook()
            
        # Set webhook using the RAILWAY_STATIC_URL
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=TELEGRAM_TOKEN,
            webhook_url=f"https://{app_name}/{TELEGRAM_TOKEN}",
            drop_pending_updates=True  # Add this to ignore pending updates
        )
        logger.info(f"Started webhook on port {port}")
    else:
        # Use polling for local development
        application.run_polling(drop_pending_updates=True)  # Add this to start with a clean state
        logger.info("Started polling")

if __name__ == '__main__':
    main() 