import logging
import pytz
import re
from datetime import datetime, time
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ParseMode
from bot.utils.utils import get_user_language, get_user_datetime
from bot.reminders.reminder_manager import ReminderManager
from bot.database.db_manager import DatabaseManager
from bot.streak_counter.streak_counter import StreakCounter
from bot.database.config import USERS_TABLE

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
                    "يمكنك إعداد عدة تذكيرات باستخدام الأمر عدة مرات.\n"
                    "لعرض التذكيرات الحالية، استخدم `/listreminders`\n"
                    "لحذف تذكير، استخدم `/deletereminder 08:00`",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text(
                    "Please specify the reminder time in 24-hour format. Example: `/setreminder 08:00`\n\n"
                    "You can set multiple reminders by using the command multiple times.\n"
                    "To view your current reminders, use `/listreminders`\n"
                    "To delete a reminder, use `/deletereminder 08:00`",
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
        
        # Get all current reminders for display
        reminders = reminder_manager.get_reminders_for_user(user_id)
        reminders_count = len(reminders)
        
        response_message = ""
        if lang == "ar":
            response_message = (f"✅ تم إضافة تذكير يومي في الساعة `{time_str}` بتوقيت {escaped_timezone}.\n\n"
                f"لديك الآن {reminders_count} {('تذكيرات' if reminders_count > 1 else 'تذكير')}.\n\n"
                f"• استخدم `/listreminders` لعرض جميع التذكيرات الخاصة بك\n"
                f"• استخدم `/deletereminder {time_str}` لحذف هذا التذكير")
        else:
            response_message = (f"✅ Daily reminder added for `{time_str}` {escaped_timezone} time.\n\n"
                f"You now have {reminders_count} {('reminders' if reminders_count > 1 else 'reminder')}.\n\n"
                f"• Use `/listreminders` to view all your reminders\n"
                f"• Use `/deletereminder {time_str}` to delete this reminder")
                
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
        
        # Create a list of reminders with delete instructions
        reminders_list = ""
        for i, time_str in enumerate(sorted(reminders), 1):
            if lang == "ar":
                reminders_list += f"{i}. `{time_str}` - لحذف هذا التذكير: `/deletereminder {time_str}`\n"
            else:
                reminders_list += f"{i}. `{time_str}` - To delete: `/deletereminder {time_str}`\n"
        
        # Escape any special markdown characters in timezone_str to prevent parsing errors
        escaped_timezone = timezone_str.replace('_', '\\_')
        
        response_message = ""
        if lang == "ar":
            response_message = (f"⏰ *التذكيرات اليومية الخاصة بك*\n\n"
                f"المنطقة الزمنية: `{escaped_timezone}`\n\n"
                f"{reminders_list}\n"
                f"• لإضافة تذكيرات جديدة، استخدم `/setreminder HH:MM`\n"
                f"• يمكنك ضبط عدة تذكيرات في أوقات مختلفة")
        else:
            response_message = (f"⏰ *Your Daily Reminders*\n\n"
                f"Timezone: `{escaped_timezone}`\n\n"
                f"{reminders_list}\n"
                f"• To add new reminders, use `/setreminder HH:MM`\n"
                f"• You can set multiple reminders at different times")
                
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
        
        # Get the remaining reminders count for display
        remaining_reminders = reminder_manager.get_reminders_for_user(user_id)
        remaining_count = len(remaining_reminders)
        
        response_message = ""
        if lang == "ar":
            response_message = f"✅ تم حذف التذكير في الساعة `{time_str}`."
            if remaining_count > 0:
                response_message += f"\n\nلا يزال لديك {remaining_count} {('تذكيرات' if remaining_count > 1 else 'تذكير')}."
                response_message += f"\nاستخدم `/listreminders` لعرض التذكيرات المتبقية."
            else:
                response_message += "\n\nليس لديك أي تذكيرات متبقية. استخدم `/setreminder HH:MM` لإضافة تذكير جديد."
        else:
            response_message = f"✅ Reminder at `{time_str}` has been deleted."
            if remaining_count > 0:
                response_message += f"\n\nYou still have {remaining_count} {('reminders' if remaining_count > 1 else 'reminder')}."
                response_message += f"\nUse `/listreminders` to view your remaining reminders."
            else:
                response_message += "\n\nYou don't have any reminders left. Use `/setreminder HH:MM` to add a new one."
            
        logger.info(f"Successfully deleted reminder at {time_str} for user {user_id}")
        await update.message.reply_text(response_message, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        logger.error(f"Error in deletereminder command: {str(e)}", exc_info=True)
        await update.message.reply_text(f"❌ An error occurred: {str(e)}\nPlease try again later.")

async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send reminder messages to users who have scheduled reminders."""
    job = context.job
    user_id = job.data.get("user_id")
    reminder_time = job.data.get("reminder_time")
    
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
        
        # Mark reminder as sent using the correct reminder time
        if reminder_time:
            reminder_manager.mark_reminder_sent(user_id, reminder_time)
        else:
            # Fallback to current time if no specific time was provided
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
        
        # Schedule an end-of-day check for users who missed their checkmark
        application.job_queue.run_repeating(
            check_end_of_day_missed_checkmarks,
            interval=3600,  # Check every hour
            first=60       # Start 60 seconds after bot startup
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
                    
                    # Compare only hours and minutes, not seconds
                    current_hour_min = (current_time.hour, current_time.minute)
                    
                    # Check if any reminder time matches the current time (exactly on the hour and minute)
                    for reminder_time in reminder_times:
                        reminder_hour_min = (reminder_time.hour, reminder_time.minute)
                        
                        if current_hour_min == reminder_hour_min:
                            logger.info(f"Scheduling reminder for user {user_id} at {reminder_time.strftime('%H:%M')}")
                            
                            # Check if we've already sent this reminder today
                            sent_reminders = db_manager.get_today_reminders(user_id)
                            already_sent = False
                            
                            for sent in sent_reminders:
                                sent_time_str = sent.get("reminder_time", "")
                                if sent_time_str:
                                    try:
                                        sent_h, sent_m = map(int, sent_time_str.split(":"))
                                        if (sent_h, sent_m) == reminder_hour_min:
                                            already_sent = True
                                            break
                                    except:
                                        pass
                            
                            if not already_sent:
                                # Check if user has already sent a checkmark today
                                try:
                                    streak_counter = StreakCounter(telegram_id=user_id)
                                    has_checkmark = streak_counter.has_checkmark_today()
                                    if has_checkmark:
                                        logger.debug(f"User {user_id} already checked in today, skipping reminder")
                                    else:
                                        logger.debug(f"User {user_id} has not checked in today, sending reminder")
                                        # Schedule a job to send the reminder
                                        context.job_queue.run_once(
                                            send_reminder,
                                            0,  # Run immediately
                                            data={"user_id": user_id, "reminder_time": reminder_time}
                                        )
                                except Exception as e:
                                    logger.error(f"Error checking if user {user_id} has checkmark today: {str(e)}")
                                    # If there's an error checking for checkmarks, send the reminder anyway
                                    logger.debug(f"Sending reminder to user {user_id} despite checkmark check error")
                                    context.job_queue.run_once(
                                        send_reminder,
                                        0,  # Run immediately
                                        data={"user_id": user_id, "reminder_time": reminder_time}
                                    )
                            else:
                                logger.debug(f"Reminder for user {user_id} at {reminder_time.strftime('%H:%M')} already sent today")
                except pytz.exceptions.UnknownTimeZoneError:
                    logger.error(f"Invalid timezone '{timezone_str}' for user {user_id}")
                except Exception as e:
                    logger.error(f"Error processing reminder for user {user_id}: {str(e)}", exc_info=True)
            except Exception as e:
                logger.error(f"Error processing user in reminder check: {str(e)}", exc_info=True)
                
    except Exception as e:
        logger.error(f"Error in check_and_send_reminders: {str(e)}", exc_info=True)

async def check_end_of_day_missed_checkmarks(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Check at the end of the day for users who haven't submitted a checkmark.
    Send them a notification about breaking their streak.
    """
    try:
        logger.debug("Running end-of-day missed checkmark check")
        
        # Get all users from database
        db_manager = DatabaseManager()
        
        # Get all users from the database
        response = db_manager.supabase.table(USERS_TABLE).select("*").execute()
        users = response.data
        
        for user in users:
            try:
                user_id = user.get("telegram_id")
                timezone_str = user.get("timezone", "America/Los_Angeles")
                
                if not user_id:
                    continue
                
                # Get user's local time
                try:
                    timezone = pytz.timezone(timezone_str)
                    user_local_time = datetime.now(timezone)
                    
                    # Only proceed if it's end of day (between 21:00 and 22:00)
                    if not (21 <= user_local_time.hour < 22):
                        continue
                    
                    # Create streak counter for this user
                    streak_counter = StreakCounter(telegram_id=user_id)
                    
                    # Check if user already has a checkmark today
                    if streak_counter.has_checkmark_today():
                        continue
                    
                    # User doesn't have a checkmark today and it's end of day
                    # Get their streak information
                    user_data = db_manager.get_or_create_user(user_id, "")
                    current_streak = user_data.get("current_streak", 0)
                    
                    # Only send notification if they had a streak to break or need a warning
                    # Get user's reverse streak (days without activity)
                    reverse_streak = user_data.get("reverse_streak", 0)
                    
                    # Get appropriate threshold for warning message
                    # If they're about to break a streak, it's day 0 of missing (treat as day 1)
                    days_missing = reverse_streak if reverse_streak > 0 else 1
                    
                    # Get user's language
                    lang = get_user_language(user_id)
                    
                    # Get warning template based on threshold days
                    threshold = streak_counter.get_appropriate_threshold(days_missing, False)
                    template = db_manager.get_message_template(template_type="warning", threshold_days=threshold)
                    
                    message = ""
                    if template:
                        # Get the appropriate text fields
                        header = ""
                        text = ""
                        message_text = ""
                        
                        if current_streak > 0:
                            # Create header for users with active streak
                            if lang == "ar":
                                header = f"⚠️ *تنبيه انقطاع القراءة*\n\n"
                            else:
                                header = f"⚠️ *Streak Break Alert*\n\n"
                        else:
                            # Create header for users without active streak
                            if lang == "ar":
                                header = f"📖 *تذكير القراءة اليومية*\n\n"
                            else:
                                header = f"📖 *Daily Reading Reminder*\n\n"
                        
                        # Get text field
                        if lang == 'ar':
                            text = template.get("text_used_arabic", "")
                        else:
                            text = template.get("text_used_english", "")
                        
                        # Get message field
                        if lang == 'ar':
                            message_text = template.get("message_arabic_translation", "")
                        else:
                            message_text = template.get("message_english_translation", "")
                        
                        # If text field is empty, use a fallback
                        if not text:
                            if lang == 'ar':
                                text = "لم تقرأ القرآن اليوم بعد!"
                            else:
                                text = "You haven't read the Quran today yet!"
                        
                        # Create the full message
                        message = f"{header}{text}"
                        
                        # Add the message_text if it exists
                        if message_text:
                            message += f"\n\n{message_text}"
                            
                        # Add a call to action based on their current streak
                        if current_streak > 0:
                            if lang == 'ar':
                                message += f"\n\nسلسلة قراءتك المستمرة لمدة {current_streak} أيام ستنقطع عند منتصف الليل. ما زال لديك وقت للقراءة وإرسال علامة اختيار للحفاظ على سلسلتك! ✅"
                            else:
                                message += f"\n\nYour {current_streak}-day streak will break at midnight. You still have time to read and send a checkmark to maintain your streak! ✅"
                    else:
                        # Fallback message if no template found
                        if current_streak > 0:
                            if lang == "ar":
                                message = (f"⚠️ *تنبيه انقطاع القراءة*\n\n"
                                          f"لقد انقطعت عن القراءة اليوم! سلسلة قراءتك المستمرة لمدة {current_streak} أيام ستنقطع عند منتصف الليل.\n\n"
                                          f"ما زال لديك وقت للقراءة وإرسال علامة اختيار للحفاظ على سلسلتك! 📖")
                            else:
                                message = (f"⚠️ *Streak Break Alert*\n\n"
                                          f"You haven't read the Quran today! Your {current_streak}-day streak will break at midnight.\n\n"
                                          f"You still have time to read and send a checkmark to maintain your streak! 📖")
                        elif reverse_streak > 0:
                            if lang == "ar":
                                message = (f"📖 *تذكير القراءة اليومية*\n\n"
                                          f"لقد مرت {reverse_streak} أيام منذ آخر قراءة للقرآن. استأنف رحلتك اليوم!")
                            else:
                                message = (f"📖 *Daily Reading Reminder*\n\n"
                                          f"It's been {reverse_streak} days since your last Quran reading. Resume your journey today!")
                        else:
                            # Skip users who don't have an active streak and haven't missed days yet
                            continue
                    
                    # Send the message
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    
                    logger.info(f"Sent end-of-day warning to user {user_id} with streak={current_streak}, reverse_streak={reverse_streak}")
                    
                except pytz.exceptions.UnknownTimeZoneError:
                    logger.error(f"Invalid timezone '{timezone_str}' for user {user_id}")
                except Exception as e:
                    logger.error(f"Error processing end-of-day check for user {user_id}: {str(e)}", exc_info=True)
            except Exception as e:
                logger.error(f"Error processing user in end-of-day check: {str(e)}", exc_info=True)
                
    except Exception as e:
        logger.error(f"Error in check_end_of_day_missed_checkmarks: {str(e)}", exc_info=True) 