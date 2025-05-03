import logging
import pytz
import re
from datetime import datetime, time
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ParseMode
from utils.utils import get_user_language, get_user_datetime
from reminders.reminder_manager import ReminderManager
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

# Global reminder manager
reminder_manager = ReminderManager()

# Dictionary to store user timezones
user_timezones = {}

async def settimezone_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set the user's timezone."""
    try:
        logger.info(f"Processing settimezone command from user {update.effective_user.id}")
        
        user_id = update.effective_user.id
        lang = get_user_language(user_id)
        
        # Check if there's a timezone argument
        if not context.args:
            logger.info(f"User {user_id} did not provide timezone argument")
            if lang == "ar":
                await update.message.reply_text(
                    "يرجى تحديد المنطقة الزمنية الخاصة بك. مثال: `/settimezone Asia/Riyadh`\n\n"
                    "يمكنك العثور على قائمة المناطق الزمنية [هنا](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text(
                    "Please specify your timezone. Example: `/settimezone Europe/London`\n\n"
                    "You can find a list of timezones [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).",
                    parse_mode=ParseMode.MARKDOWN
                )
            return
        
        # Get the timezone from the argument
        timezone_str = context.args[0]
        logger.info(f"User {user_id} attempting to set timezone to: {timezone_str}")
        
        # Validate the timezone
        try:
            timezone = pytz.timezone(timezone_str)
            
            # Store the timezone for this user
            user_timezones[user_id] = timezone_str
            
            # Update in database
            db_manager = DatabaseManager()
            db_manager.update_user_timezone(user_id, timezone_str)
            
            # Get the current time in the user's timezone
            now = datetime.now(timezone)
            time_str = now.strftime("%H:%M")
            
            # Escape any special markdown characters in timezone_str to prevent parsing errors
            escaped_timezone = timezone_str.replace('_', '\\_')
            
            response_message = ""
            if lang == "ar":
                response_message = (f"✅ تم ضبط المنطقة الزمنية الخاصة بك إلى `{escaped_timezone}`.\n"
                    f"الوقت المحلي: {time_str}")
            else:
                response_message = (f"✅ Your timezone has been set to `{escaped_timezone}`.\n"
                    f"Local time: {time_str}")
                
            logger.info(f"Successfully set timezone to {timezone_str} for user {user_id}")
            await update.message.reply_text(response_message, parse_mode=ParseMode.MARKDOWN)
            
        except pytz.exceptions.UnknownTimeZoneError:
            error_message = ""
            # Escape any special markdown characters in timezone_str to prevent parsing errors
            escaped_timezone = timezone_str.replace('_', '\\_')
            
            if lang == "ar":
                error_message = f"❌ `{escaped_timezone}` ليست منطقة زمنية صالحة. يرجى استخدام منطقة زمنية صالحة."
            else:
                error_message = f"❌ `{escaped_timezone}` is not a valid timezone. Please use a valid timezone."
                
            logger.warning(f"Invalid timezone '{timezone_str}' specified by user {user_id}")
            await update.message.reply_text(error_message, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error in settimezone command: {str(e)}", exc_info=True)
        await update.message.reply_text(f"❌ An error occurred: {str(e)}\nPlease try again later.")

async def setreminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set a daily reminder for Quran reading."""
    try:
        logger.info(f"Processing setreminder command from user {update.effective_user.id}")
        
        user_id = update.effective_user.id
        lang = get_user_language(user_id)
        
        # Check if there's a time argument
        if not context.args:
            logger.info(f"User {user_id} did not provide time argument")
            if lang == "ar":
                await update.message.reply_text(
                    "يرجى تحديد وقت التذكير بتنسيق 24 ساعة. مثال: `/setreminder 08:00`\n\n"
                    "يمكنك إعداد عدة تذكيرات عن طريق استخدام الأمر عدة مرات.",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text(
                    "Please specify the reminder time in 24-hour format. Example: `/setreminder 08:00`\n\n"
                    "You can set multiple reminders by using the command multiple times.",
                    parse_mode=ParseMode.MARKDOWN
                )
            return
        
        # Get the time from the argument
        time_str = context.args[0]
        logger.info(f"User {user_id} attempting to set reminder at: {time_str}")
        
        # Validate the time format (HH:MM)
        if not re.match(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$", time_str):
            error_message = ""
            if lang == "ar":
                error_message = "❌ تنسيق الوقت غير صالح. يرجى استخدام تنسيق 24 ساعة (مثل `08:00` أو `21:30`)."
            else:
                error_message = "❌ Invalid time format. Please use 24-hour format (like `08:00` or `21:30`)."
                
            logger.warning(f"Invalid time format '{time_str}' specified by user {user_id}")
            await update.message.reply_text(error_message, parse_mode=ParseMode.MARKDOWN)
            return
        
        # Parse the time
        hour, minute = map(int, time_str.split(":"))
        reminder_time = time(hour, minute)
        
        # Get the user's timezone (or use default)
        db_manager = DatabaseManager()
        user_data = db_manager.get_or_create_user(user_id, "")
        timezone_str = user_data.get("timezone", "America/Los_Angeles")
        
        # Store the reminder for this user
        logger.info(f"Storing reminder time {time_str} for user {user_id}")
        success = db_manager.set_user_reminder(user_id, reminder_time)
        
        if not success:
            # Even if DB storage fails, still add to local memory for this session
            reminder_manager.set_custom_reminder_time(user_id, reminder_time)
            
            # Inform the user about partial success
            warning_msg = ""
            if lang == "ar":
                warning_msg = ("⚠️ تم إعداد التذكير مؤقتًا، ولكن قد لا يستمر بعد إعادة تشغيل البوت.\n"
                    "يرجى الاتصال بمسؤول النظام لإصلاح مشكلة قاعدة البيانات.")
            else:
                warning_msg = ("⚠️ Reminder set temporarily, but may not persist after bot restart.\n"
                    "Please contact the admin to fix the database issue.")
                
            await update.message.reply_text(warning_msg, parse_mode=ParseMode.MARKDOWN)
            return
        
        # Also store in reminder manager for immediate use
        reminder_manager.set_custom_reminder_time(user_id, reminder_time)
        
        # Calculate the time in user's timezone
        timezone = pytz.timezone(timezone_str)
        now = datetime.now(timezone)
        reminder_datetime = datetime.combine(now.date(), reminder_time)
        
        # Escape any special markdown characters in timezone_str to prevent parsing errors
        escaped_timezone = timezone_str.replace('_', '\\_')
        
        response_message = ""
        if lang == "ar":
            response_message = (f"✅ تم إعداد تذكير يومي في الساعة `{time_str}` بتوقيت {escaped_timezone}.\n\n"
                f"سوف أذكرك بقراءة القرآن يوميًا في هذا الوقت.")
        else:
            response_message = (f"✅ Daily reminder set for `{time_str}` {escaped_timezone} time.\n\n"
                f"I'll remind you to read the Quran daily at this time.")
                
        logger.info(f"Successfully set reminder at {time_str} for user {user_id}")
        await update.message.reply_text(response_message, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        logger.error(f"Error in setreminder command: {str(e)}", exc_info=True)
        await update.message.reply_text(f"❌ An error occurred: {str(e)}\nPlease try again later.")

async def listreminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all reminders set for the user."""
    try:
        logger.info(f"Processing listreminders command from user {update.effective_user.id}")
        
        user_id = update.effective_user.id
        lang = get_user_language(user_id)
        
        # Get the user's reminders
        reminders = reminder_manager.get_reminders_for_user(user_id)
        logger.info(f"Retrieved {len(reminders)} reminders for user {user_id}")
        
        # Get the user's timezone
        db_manager = DatabaseManager()
        user_data = db_manager.get_or_create_user(user_id, "")
        timezone_str = user_data.get("timezone", "America/Los_Angeles")
        
        if not reminders:
            response_message = ""
            if lang == "ar":
                response_message = ("⚠️ لم تقم بإعداد أي تذكيرات بعد.\n\n"
                    "استخدم الأمر `/setreminder HH:MM` لإعداد تذكير.")
            else:
                response_message = ("⚠️ You haven't set any reminders yet.\n\n"
                    "Use the `/setreminder HH:MM` command to set a reminder.")
                    
            logger.info(f"No reminders found for user {user_id}")
            await update.message.reply_text(response_message, parse_mode=ParseMode.MARKDOWN)
            return
        
        # Create a list of reminders
        reminders_list = "\n".join([f"• `{time_str}`" for time_str in sorted(reminders)])
        
        # Escape any special markdown characters in timezone_str to prevent parsing errors
        escaped_timezone = timezone_str.replace('_', '\\_')
        
        response_message = ""
        if lang == "ar":
            response_message = (f"⏰ *التذكيرات اليومية الخاصة بك*\n\n"
                f"المنطقة الزمنية: `{escaped_timezone}`\n\n"
                f"{reminders_list}\n\n"
                f"لحذف تذكير، استخدم الأمر `/deletereminder HH:MM`")
        else:
            response_message = (f"⏰ *Your Daily Reminders*\n\n"
                f"Timezone: `{escaped_timezone}`\n\n"
                f"{reminders_list}\n\n"
                f"To delete a reminder, use `/deletereminder HH:MM`")
                
        logger.info(f"Successfully listed reminders for user {user_id}")
        await update.message.reply_text(response_message, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        logger.error(f"Error in listreminders command: {str(e)}", exc_info=True)
        await update.message.reply_text(f"❌ An error occurred: {str(e)}\nPlease try again later.")

async def deletereminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a specific reminder."""
    try:
        logger.info(f"Processing deletereminder command from user {update.effective_user.id}")
        
        user_id = update.effective_user.id
        lang = get_user_language(user_id)
        
        # Check if there's a time argument
        if not context.args:
            logger.info(f"User {user_id} did not provide time argument")
            if lang == "ar":
                await update.message.reply_text(
                    "يرجى تحديد وقت التذكير الذي ترغب في حذفه بتنسيق 24 ساعة. مثال: `/deletereminder 08:00`\n\n"
                    "لعرض قائمة التذكيرات الخاصة بك، استخدم الأمر `/listreminders`",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text(
                    "Please specify the reminder time to delete in 24-hour format. Example: `/deletereminder 08:00`\n\n"
                    "To view your reminders, use the `/listreminders` command.",
                    parse_mode=ParseMode.MARKDOWN
                )
            return
        
        # Get the time from the argument
        time_str = context.args[0]
        logger.info(f"User {user_id} attempting to delete reminder at: {time_str}")
        
        # Validate the time format (HH:MM)
        if not re.match(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$", time_str):
            error_message = ""
            if lang == "ar":
                error_message = "❌ تنسيق الوقت غير صالح. يرجى استخدام تنسيق 24 ساعة (مثل `08:00` أو `21:30`)."
            else:
                error_message = "❌ Invalid time format. Please use 24-hour format (like `08:00` or `21:30`)."
                
            logger.warning(f"Invalid time format '{time_str}' specified by user {user_id}")
            await update.message.reply_text(error_message, parse_mode=ParseMode.MARKDOWN)
            return
        
        # Get existing reminders
        reminders = reminder_manager.get_reminders_for_user(user_id)
        
        # Check if the reminder exists
        if time_str not in reminders:
            error_message = ""
            if lang == "ar":
                error_message = (f"❌ لم يتم العثور على تذكير في الساعة `{time_str}`.\n\n"
                    f"لعرض قائمة التذكيرات الخاصة بك، استخدم الأمر `/listreminders`")
            else:
                error_message = (f"❌ No reminder found at `{time_str}`.\n\n"
                    f"To view your reminders, use the `/listreminders` command.")
                    
            logger.warning(f"No reminder found at time '{time_str}' for user {user_id}")
            await update.message.reply_text(error_message, parse_mode=ParseMode.MARKDOWN)
            return
        
        # Parse the time
        hour, minute = map(int, time_str.split(":"))
        reminder_time = time(hour, minute)
        
        # Delete the reminder
        logger.info(f"Deleting reminder at time {time_str} for user {user_id}")
        success = reminder_manager.delete_reminder(user_id, reminder_time)
        
        if not success:
            # Inform the user about potential issues
            warning_msg = ""
            if lang == "ar":
                warning_msg = ("⚠️ تم حذف التذكير من الذاكرة المؤقتة، ولكن قد تكون هناك مشكلة في التحديث في قاعدة البيانات.\n"
                    "يرجى الاتصال بمسؤول النظام إذا استمرت المشكلة.")
            else:
                warning_msg = ("⚠️ Reminder deleted from memory, but there may be an issue updating the database.\n"
                    "Please contact the admin if the problem persists.")
                
            await update.message.reply_text(warning_msg, parse_mode=ParseMode.MARKDOWN)
            return
        
        response_message = ""
        if lang == "ar":
            response_message = f"✅ تم حذف التذكير في الساعة `{time_str}`."
        else:
            response_message = f"✅ Reminder at `{time_str}` has been deleted."
            
        logger.info(f"Successfully deleted reminder at {time_str} for user {user_id}")
        await update.message.reply_text(response_message, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        logger.error(f"Error in deletereminder command: {str(e)}", exc_info=True)
        await update.message.reply_text(f"❌ An error occurred: {str(e)}\nPlease try again later.")

async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send reminder messages to users who have scheduled reminders."""
    job = context.job
    user_id = job.data.get("user_id")
    
    if not user_id:
        logger.error("No user_id in job data")
        return
    
    lang = get_user_language(user_id)
    
    # Get the reminder message
    reminder_message = reminder_manager.get_reminder_message(user_id, language=lang)
    
    try:
        # Send the reminder
        await context.bot.send_message(
            chat_id=user_id,
            text=f"⏰ *Quran Reading Reminder*\n\n{reminder_message}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Mark reminder as sent
        current_time = datetime.now().time()
        reminder_manager.mark_reminder_sent(user_id, current_time)
        
    except Exception as e:
        logger.error(f"Error sending reminder to user {user_id}: {str(e)}")

def register_reminder_handlers(application):
    """Register all reminder-related handlers."""
    application.add_handler(CommandHandler("settimezone", settimezone_command))
    application.add_handler(CommandHandler("setreminder", setreminder_command))
    application.add_handler(CommandHandler("listreminders", listreminders_command))
    application.add_handler(CommandHandler("deletereminder", deletereminder_command))
    
    # Check if job_queue is available before scheduling
    if application.job_queue is not None:
        logger.info("Setting up reminder job queue...")
        # Schedule the job queue to check for reminders every minute
        application.job_queue.run_repeating(
            check_and_send_reminders,
            interval=60,  # Check every minute
            first=10      # Start 10 seconds after bot startup
        )
    else:
        logger.warning("JobQueue not available. Reminder jobs will not run automatically.")
        logger.warning("To use JobQueue, install with: pip install 'python-telegram-bot[job-queue]'")

async def check_and_send_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check for users who need reminders and send them."""
    try:
        logger.debug("Checking for users who need reminders")
        
        # Get all users with reminders
        db_manager = DatabaseManager()
        users_with_reminders = db_manager.get_users_with_reminders()
        
        logger.debug(f"Found {len(users_with_reminders)} users with reminders")
        
        for user in users_with_reminders:
            try:
                user_id = user.get("telegram_id")
                reminder_times = user.get("reminder_times", [])
                timezone_str = user.get("timezone", "America/Los_Angeles")
                
                if not user_id or not reminder_times:
                    logger.warning(f"Skipping user with invalid data: {user}")
                    continue
                
                # Get current time in user's timezone
                try:
                    timezone = pytz.timezone(timezone_str)
                    current_datetime = datetime.now(timezone)
                    current_time = current_datetime.time()
                    
                    # Check if any reminder time matches the current time (within 1 minute)
                    for reminder_time in reminder_times:
                        current_minutes = current_time.hour * 60 + current_time.minute
                        reminder_minutes = reminder_time.hour * 60 + reminder_time.minute
                        
                        if abs(current_minutes - reminder_minutes) <= 1:
                            logger.info(f"Scheduling reminder for user {user_id} at {reminder_time.strftime('%H:%M')}")
                            
                            # Schedule a job to send the reminder
                            context.job_queue.run_once(
                                send_reminder,
                                0,  # Run immediately
                                data={"user_id": user_id}
                            )
                            break
                except pytz.exceptions.UnknownTimeZoneError:
                    logger.error(f"Invalid timezone '{timezone_str}' for user {user_id}")
                except Exception as e:
                    logger.error(f"Error processing reminder for user {user_id}: {str(e)}", exc_info=True)
            except Exception as e:
                logger.error(f"Error processing user in reminder check: {str(e)}", exc_info=True)
                
    except Exception as e:
        logger.error(f"Error in check_and_send_reminders: {str(e)}", exc_info=True) 