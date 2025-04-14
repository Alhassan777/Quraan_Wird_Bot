import os
import logging
import time
import signal
import sys
from datetime import datetime, timedelta, timezone
import random
import asyncio
import traceback
import pytz
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackContext
)

# Import our custom modules
from database import init_db, Session, get_user, get_group, get_group_member, populate_quran_quotes
from models import User, Group, GroupMember, QuranQuote
from cache import (
    get_cached_user, set_cached_user, 
    get_cached_group, set_cached_group,
    get_cached_quotes, set_cached_quotes,
    cache_enabled
)
from metrics import (
    setup_metrics, record_checkmark, record_active_user, 
    record_streak_length, record_command_call, 
    record_reminder_send, record_db_operation_latency
)

# Load environment variables
load_dotenv()

# Enable logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL)
)
logger = logging.getLogger(__name__)

# Default timezone
DEFAULT_TIMEZONE = 'America/Los_Angeles'  # PT timezone

async def is_admin(update: Update) -> bool:
    """Check if the user is an admin in the group."""
    if not update.effective_chat.type in ['group', 'supergroup']:
        return True  # In private chats, user is always "admin"
    
    user_id = update.effective_user.id
    
    chat_member = await update.effective_chat.get_member(user_id)
    return chat_member.status in ["administrator", "creator"]

async def get_user_datetime(user: User) -> datetime:
    """Get the current datetime in user's timezone."""
    timezone_str = user.timezone or DEFAULT_TIMEZONE
    
    try:
        timezone = pytz.timezone(timezone_str)
        return datetime.now(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        logger.error(f"Unknown timezone {timezone_str} for user {user.telegram_id}")
        # Fallback to default timezone
        timezone = pytz.timezone(DEFAULT_TIMEZONE)
        return datetime.now(timezone)

async def get_random_quote() -> str:
    """Get a random Quran quote from the database or cache."""
    # Try to get quotes from cache first
    quotes = await get_cached_quotes()
    
    if not quotes:
        # If not in cache, get from database
        session = Session()
        try:
            db_quotes = session.query(QuranQuote).all()
            quotes = [quote.text for quote in db_quotes]
            
            # Cache the quotes
            if quotes:
                await set_cached_quotes(quotes)
        except Exception as e:
            logger.error(f"Error getting quotes from database: {e}")
            return "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ"  # Fallback quote
        finally:
            session.close()
    
    # If we have quotes, return a random one
    if quotes:
        return random.choice(quotes)
    
    # Fallback if no quotes are found
    return "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    record_command_call("start")
    
    user = update.effective_user
    await update.message.reply_text(
        f"السلام عليكم {user.first_name}! "
        "أنا بوت تتبع ورد القرآن. استخدم ✅ أو ✔️ للإشارة إلى إكمال وردك اليومي."
        "\n\nCommands:"
        "\n/start - بدء البوت"
        "\n/help - الحصول على مساعدة"
        "\n/streak - عرض سلسلة الاستمرارية الخاصة بك"
        "\n/dashboard - عرض لوحة المعلومات (في المجموعات)"
        "\n/settimezone - تعيين المنطقة الزمنية الخاصة بك"
        "\n/setreminder - تعيين تذكيرات يومية"
    )
    
    # Make sure the user is in our database
    try:
        db_user = await get_user(user.id)
        
        # Update user information if needed
        session = Session()
        try:
            if db_user.first_name != user.first_name or db_user.last_name != user.last_name or db_user.username != user.username:
                db_user.first_name = user.first_name
                db_user.last_name = user.last_name
                db_user.username = user.username
                session.commit()
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        # Don't show error to user, just log it

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    record_command_call("help")
    
    await update.message.reply_text(
        "استخدم ✅ أو ✔️ للإشارة إلى إكمال وردك اليومي."
        "\n\nCommands:"
        "\n/start - بدء البوت"
        "\n/help - الحصول على مساعدة"
        "\n/streak - عرض سلسلة الاستمرارية الخاصة بك"
        "\n/dashboard - عرض لوحة المعلومات (في المجموعات)"
        "\n/settimezone - تعيين المنطقة الزمنية الخاصة بك (PT افتراضيًا)"
        "\n/setreminder - تعيين تذكيرات يومية"
    )

async def set_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set user's timezone."""
    record_command_call("settimezone")
    
    if not context.args:
        await update.message.reply_text(
            "الرجاء تحديد المنطقة الزمنية، مثل: /settimezone Asia/Riyadh"
            "\nالافتراضي هو America/Los_Angeles (PT)"
        )
        return
    
    try:
        timezone_str = context.args[0]
        pytz.timezone(timezone_str)  # Validate timezone
        
        # Get the user from the database
        db_user = await get_user(update.effective_user.id)
        
        # Update user's timezone
        session = Session()
        try:
            db_user = session.query(User).filter(User.telegram_id == update.effective_user.id).first()
            db_user.timezone = timezone_str
            session.commit()
            
            # Update cache
            if cache_enabled():
                user_dict = {
                    "telegram_id": db_user.telegram_id,
                    "timezone": db_user.timezone,
                    "streak": db_user.streak,
                    "last_check": db_user.last_check,
                    "reminder_time": db_user.reminder_time
                }
                await set_cached_user(db_user.telegram_id, user_dict)
            
            await update.message.reply_text(f"تم تعيين المنطقة الزمنية إلى {timezone_str}")
        
        finally:
            session.close()
    
    except pytz.exceptions.UnknownTimeZoneError:
        await update.message.reply_text(
            "منطقة زمنية غير صالحة. يرجى استخدام تنسيق مثل 'Asia/Riyadh'."
        )
    except Exception as e:
        logger.error(f"Error setting timezone: {e}")
        await update.message.reply_text("حدث خطأ أثناء تعيين المنطقة الزمنية. يرجى المحاولة مرة أخرى.")

async def handle_checkmark(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle checkmark emoji to mark completion of daily Quraan reading."""
    if not (update.message and update.message.text and any(mark in update.message.text for mark in ["✅", "✔️"])):
        return
    
    start_time = time.time()
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    try:
        # Get user from database or cache
        cached_user = await get_cached_user(user_id)
        if cached_user:
            # Use cached user data
            record_cache_hit("user")
        else:
            # Get from database
            record_cache_miss("user")
        
        # Always get from database to ensure data consistency
        db_user = await get_user(user_id)
        
        # Update user information
        session = Session()
        try:
            # Make sure we have the latest user data from the database
            db_user = session.query(User).filter(User.telegram_id == user_id).first()
            
            # Get current datetime in user's timezone
            now = await get_user_datetime(db_user)
            today = now.date()
            
            # Check for duplicate in 24-hour window (anti-spam)
            if db_user.last_check:
                last_check_date = db_user.last_check.date()
                if last_check_date == today:
                    await update.message.reply_text("لقد سجلت وردك بالفعل اليوم! 🙏")
                    return
            
            # Update streak
            if db_user.last_check:
                last_check_date = db_user.last_check.date()
                yesterday = (now - timedelta(days=1)).date()
                
                if last_check_date == yesterday:
                    db_user.streak += 1
                elif last_check_date < yesterday:
                    # Streak broken
                    db_user.streak = 1
            else:
                db_user.streak = 1
            
            # Update last check time
            db_user.last_check = now
            
            # If in a group, update group data as well
            if chat_type in ['group', 'supergroup']:
                # Get the group from the database
                group = await get_group(chat_id, update.effective_chat.title)
                
                # Get or create the group member entry
                group_member = await get_group_member(user_id, chat_id)
                group_member.streak = db_user.streak
                group_member.last_check = now
            
            # Commit changes
            session.commit()
            
            # Update cache
            if cache_enabled():
                user_dict = {
                    "telegram_id": db_user.telegram_id,
                    "timezone": db_user.timezone,
                    "streak": db_user.streak,
                    "last_check": db_user.last_check,
                    "reminder_time": db_user.reminder_time
                }
                await set_cached_user(user_id, user_dict)
            
            # Record metrics
            record_checkmark(chat_type)
            record_streak_length(db_user.streak, chat_type)
            record_active_user("daily")
            
            # Send response
            streak = db_user.streak
            await update.message.reply_text(
                f"بارك الله فيك! 🌟 لقد أكملت وردك اليومي. "
                f"سلسلة استمراريتك الحالية: {streak} {'يوم' if streak == 1 else 'أيام'}!"
            )
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error handling checkmark: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text("حدث خطأ أثناء تسجيل وردك. يرجى المحاولة مرة أخرى.")
    
    finally:
        # Record database operation latency
        elapsed = time.time() - start_time
        record_db_operation_latency("handle_checkmark", elapsed)

async def streak_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the user's current streak."""
    record_command_call("streak")
    
    user_id = update.effective_user.id
    
    try:
        # Get user from database
        db_user = await get_user(user_id)
        
        if db_user.streak == 0:
            await update.message.reply_text("لم تبدأ سلسلة الاستمرارية بعد. استخدم ✅ عند اكتمال وردك اليومي.")
            return
        
        streak = db_user.streak
        last_check = db_user.last_check
        
        if last_check:
            formatted_time = last_check.strftime('%Y-%m-%d %H:%M:%S')
        else:
            formatted_time = "غير معروف"
        
        await update.message.reply_text(
            f"سلسلة استمراريتك الحالية: {streak} {'يوم' if streak == 1 else 'أيام'}!\n"
            f"آخر تسجيل: {formatted_time}"
        )
    
    except Exception as e:
        logger.error(f"Error in streak command: {e}")
        await update.message.reply_text("حدث خطأ أثناء استرجاع بيانات السلسلة الخاصة بك. يرجى المحاولة مرة أخرى.")

async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the group dashboard with all users' streaks."""
    record_command_call("dashboard")
    
    if not update.effective_chat.type in ['group', 'supergroup']:
        await update.message.reply_text("الأمر متاح فقط في المجموعات.")
        return
    
    chat_id = update.effective_chat.id
    
    try:
        # Get group from database
        session = Session()
        try:
            # Check if group exists
            group = session.query(Group).filter(Group.telegram_id == chat_id).first()
            
            if not group:
                await update.message.reply_text("لا توجد بيانات متاحة بعد. استخدم ✅ عند اكتمال وردك اليومي.")
                return
            
            # Get all group members
            members = session.query(GroupMember).filter(GroupMember.group_id == chat_id).all()
            
            if not members:
                await update.message.reply_text("لا توجد بيانات متاحة بعد. استخدم ✅ عند اكتمال وردك اليومي.")
                return
            
            # Get users associated with members for name display
            user_ids = [member.user_id for member in members]
            users = session.query(User).filter(User.telegram_id.in_(user_ids)).all()
            
            # Create a mapping of user_id to user for easier access
            user_map = {user.telegram_id: user for user in users}
            
            # Sort members by streak (descending)
            sorted_members = sorted(members, key=lambda x: x.streak, reverse=True)
            
            dashboard = "📊 *لوحة معلومات ورد القرآن* 📊\n\n"
            for i, member in enumerate(sorted_members, 1):
                user = user_map.get(member.user_id)
                if user:
                    name = user.first_name
                    if user.last_name:
                        name += f" {user.last_name}"
                    
                    emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
                    dashboard += f"{emoji} {name}: {member.streak} {'يوم' if member.streak == 1 else 'أيام'}\n"
            
            await update.message.reply_text(dashboard, parse_mode="Markdown")
        
        finally:
            session.close()
    
    except Exception as e:
        logger.error(f"Error in dashboard command: {e}")
        await update.message.reply_text("حدث خطأ أثناء استرجاع بيانات لوحة المعلومات. يرجى المحاولة مرة أخرى.")

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set daily reminder for Quraan reading."""
    record_command_call("setreminder")
    
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "الرجاء تحديد وقت التذكير بالصيغة HH:MM (24 ساعة)، مثل: /setreminder 21:00"
        )
        return
    
    try:
        time_str = context.args[0]
        hours, minutes = map(int, time_str.split(':'))
        
        if not (0 <= hours < 24 and 0 <= minutes < 60):
            raise ValueError("Invalid time format")
        
        user_id = update.effective_user.id
        session = Session()
        
        try:
            # Get user from database
            user = session.query(User).filter(User.telegram_id == user_id).first()
            
            # Set reminder time
            user.reminder_time = time_str
            
            # If in a group, set group reminder as well if user is admin
            if update.effective_chat.type in ['group', 'supergroup'] and await is_admin(update):
                chat_id = update.effective_chat.id
                
                # Get or create group
                group = session.query(Group).filter(Group.telegram_id == chat_id).first()
                if not group:
                    group = Group(telegram_id=chat_id, title=update.effective_chat.title)
                    session.add(group)
                
                # Set reminder time for group
                group.reminder_time = time_str
                group.reminder_set_by = user_id
                
                await update.message.reply_text(
                    f"تم تعيين التذكير اليومي للساعة {time_str}\n"
                    f"تم تعيين التذكير لجميع أعضاء المجموعة أيضًا."
                )
            else:
                await update.message.reply_text(f"تم تعيين التذكير اليومي للساعة {time_str}")
            
            # Commit changes
            session.commit()
            
            # Update cache
            if cache_enabled():
                # Update user cache
                user_dict = {
                    "telegram_id": user.telegram_id,
                    "timezone": user.timezone,
                    "streak": user.streak,
                    "last_check": user.last_check,
                    "reminder_time": user.reminder_time
                }
                await set_cached_user(user_id, user_dict)
                
                # Update group cache if applicable
                if update.effective_chat.type in ['group', 'supergroup'] and await is_admin(update):
                    group_dict = {
                        "telegram_id": chat_id,
                        "title": update.effective_chat.title,
                        "reminder_time": time_str,
                        "reminder_set_by": user_id
                    }
                    await set_cached_group(chat_id, group_dict)
        
        finally:
            session.close()
    
    except (ValueError, IndexError):
        await update.message.reply_text(
            "تنسيق وقت غير صالح. يرجى استخدام الصيغة HH:MM (24 ساعة)، مثل: 21:00"
        )
    except Exception as e:
        logger.error(f"Error setting reminder: {e}")
        await update.message.reply_text("حدث خطأ أثناء تعيين التذكير. يرجى المحاولة مرة أخرى.")

async def send_reminder(context: CallbackContext) -> None:
    """Send daily reminders to users."""
    session = Session()
    try:
        # Get all users with reminder times set
        users = session.query(User).filter(User.reminder_time.isnot(None)).all()
        
        for user in users:
            try:
                # Get current time in user's timezone
                user_now = await get_user_datetime(user)
                reminder_hour, reminder_minute = map(int, user.reminder_time.split(':'))
                
                # Check if it's time to send reminder
                if user_now.hour == reminder_hour and user_now.minute == reminder_minute:
                    # Check if user missed yesterday's check
                    if user.last_check:
                        last_check_date = user.last_check.date()
                        yesterday = (user_now - timedelta(days=1)).date()
                        
                        if last_check_date < yesterday:
                            # User missed yesterday's check
                            message = (
                                "تذكير: لم تكمل وردك أمس! 😔 "
                                "سلسلة استمراريتك تبدأ من جديد. "
                                "تذكر أن تكمل وردك اليوم وتسجله باستخدام ✅"
                            )
                            try:
                                await context.bot.send_message(chat_id=user.telegram_id, text=message)
                                record_reminder_send("missed")
                            except Exception as e:
                                logger.error(f"Failed to send missed streak reminder to {user.telegram_id}: {e}")
                    
                    # Regular daily reminder with a random quote
                    quote = await get_random_quote()
                    
                    message = (
                        f"تذكير: وقت قراءة وردك اليومي من القرآن! 🕌\n\n"
                        f"{quote}\n\n"
                        f"أرسل ✅ عند الانتهاء من القراءة."
                    )
                    
                    try:
                        await context.bot.send_message(chat_id=user.telegram_id, text=message)
                        record_reminder_send("daily")
                    except Exception as e:
                        logger.error(f"Failed to send reminder to {user.telegram_id}: {e}")
            
            except Exception as e:
                logger.error(f"Error processing reminder for user {user.telegram_id}: {e}")
                continue
        
        # Get all groups with reminder times set
        groups = session.query(Group).filter(Group.reminder_time.isnot(None), Group.reminder_set_by.isnot(None)).all()
        
        for group in groups:
            try:
                # Get timezone from the admin who set the reminder
                admin = session.query(User).filter(User.telegram_id == group.reminder_set_by).first()
                admin_timezone = admin.timezone if admin else DEFAULT_TIMEZONE
                
                # Get current time in admin's timezone
                timezone = pytz.timezone(admin_timezone)
                now = datetime.now(timezone)
                
                reminder_hour, reminder_minute = map(int, group.reminder_time.split(':'))
                
                # Check if it's time to send reminder
                if now.hour == reminder_hour and now.minute == reminder_minute:
                    # Get a random quote
                    quote = await get_random_quote()
                    
                    message = (
                        f"تذكير للجميع: وقت قراءة وردكم اليومي من القرآن! 🕌\n\n"
                        f"{quote}\n\n"
                        f"أرسلوا ✅ عند الانتهاء من القراءة."
                    )
                    
                    try:
                        await context.bot.send_message(chat_id=group.telegram_id, text=message)
                        record_reminder_send("group")
                    except Exception as e:
                        logger.error(f"Failed to send reminder to group {group.telegram_id}: {e}")
            
            except Exception as e:
                logger.error(f"Error processing reminder for group {group.telegram_id}: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Error in send_reminder: {e}")
    
    finally:
        session.close()

async def update_active_users_metrics() -> None:
    """Update active users metrics periodically."""
    session = Session()
    try:
        # Get counts of active users
        now = datetime.now(timezone.utc)
        
        # Daily active users (last 24 hours)
        daily_cutoff = now - timedelta(days=1)
        daily_count = session.query(User).filter(User.last_check >= daily_cutoff).count()
        
        # Weekly active users (last 7 days)
        weekly_cutoff = now - timedelta(days=7)
        weekly_count = session.query(User).filter(User.last_check >= weekly_cutoff).count()
        
        # Monthly active users (last 30 days)
        monthly_cutoff = now - timedelta(days=30)
        monthly_count = session.query(User).filter(User.last_check >= monthly_cutoff).count()
        
        # Update gauges
        ACTIVE_USERS.labels(timeframe="daily").set(daily_count)
        ACTIVE_USERS.labels(timeframe="weekly").set(weekly_count)
        ACTIVE_USERS.labels(timeframe="monthly").set(monthly_count)
        
    except Exception as e:
        logger.error(f"Error updating active users metrics: {e}")
    
    finally:
        session.close()

def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main() -> None:
    """Start the bot."""
    # Set up signal handlers
    setup_signal_handlers()
    
    # Initialize database
    try:
        init_db()
        # Populate initial Quran quotes
        populate_quran_quotes()
    except Exception as e:
        logger.critical(f"Failed to initialize database: {e}")
        return
    
    # Set up metrics
    setup_metrics()
    
    # Get bot token from environment variable
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.critical("No TELEGRAM_TOKEN found in environment variables. Please set it in .env file.")
        return
    
    # Enable faster AsyncIO on compatible platforms
    try:
        import uvloop
        uvloop.install()
        logger.info("uvloop installed successfully")
    except ImportError:
        logger.info("uvloop not available, using standard asyncio")
    
    # Create the Application
    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("streak", streak_command))
    application.add_handler(CommandHandler("dashboard", dashboard_command))
    application.add_handler(CommandHandler("settimezone", set_timezone))
    application.add_handler(CommandHandler("setreminder", set_reminder))
    
    # Add message handler for checkmark emoji
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_checkmark))
    
    # Set up job queue for reminders (every minute)
    job_queue = application.job_queue
    job_queue.run_repeating(send_reminder, interval=60, first=10)
    
    # Set up job for updating active users metrics (every hour)
    job_queue.run_repeating(update_active_users_metrics, interval=3600, first=60)
    
    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main() 