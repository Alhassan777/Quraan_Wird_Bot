import os
import tempfile
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from gemini_pipeline import get_tafsir_from_text, get_tafsir_from_image
from utils.utils import (
    get_user_language,
    track_processing_task,
    mark_task_complete,
    mark_task_failed
)
from config.config import MIN_CONFIDENCE, CHECK_MARKS
from database.db_manager import DatabaseManager
from streak_counter.streak_counter import StreakCounter
from datetime import datetime

logger = logging.getLogger(__name__)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages."""
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    lang = get_user_language(user_id)
    text = update.message.text
    
    # Check if the message is a checkmark for streak tracking
    if any(checkmark in text for checkmark in CHECK_MARKS):
        # Use StreakCounter for proper streak handling and messages
        streak_counter = StreakCounter(telegram_id=user_id, username=username)
        current_time = datetime.now()
        
        # Check if user already has a checkmark today
        if streak_counter.has_checkmark_today():
            # User already checked in today, send a reminder that they already completed their portion
            if lang == "ar":
                await update.message.reply_text(
                    "✅ *لقد أكملت بالفعل وردك اليومي!*\n\n"
                    "أحسنت! لقد سجلت قراءتك بالفعل اليوم. عد غدًا لمواصلة سلسلة القراءة الخاصة بك.",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:  # Default to English
                await update.message.reply_text(
                    "✅ *You've already completed your daily portion!*\n\n"
                    "Great job! You've already recorded your reading for today. Come back tomorrow to continue your streak.",
                    parse_mode=ParseMode.MARKDOWN
                )
            return
        
        # Update streak and get current/reverse streak values
        current_streak, reverse_streak = streak_counter.update_streak(True, current_time)
        
        # Create completion message based on language
        completion_msg = ""
        if lang == "ar":
            completion_msg = "✅ *لقد أكملت وردك اليومي!*\n\n"
        else:  # Default to English
            completion_msg = "✅ *You've completed your daily portion!*\n\n"
        
        # Create streak header based on streak status and language
        streak_header = ""
        if current_streak > 0:
            if lang == "ar":
                streak_header = f"🔥 *لديك سلسلة قراءة مستمرة منذ {current_streak} أيام*\n\n"
            else:  # Default to English
                streak_header = f"🔥 *Your current streak: {current_streak} days*\n\n"
        
        # Get appropriate streak message based on the streak status (without header)
        streak_message = streak_counter.get_streak_message(language=lang, include_header=False)
        
        # Send the completion message with streak information
        await update.message.reply_text(
            f"{completion_msg}{streak_header}{streak_message}",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Normal tafsir processing
    task_id = track_processing_task(user_id)
    
    # Send waiting message
    waiting_message = None
    if lang == "en":
        waiting_message = await update.message.reply_text(
            "📖 *Processing your Quranic verse...*\n"
            "I'm looking up the tafsir (explanation) for this verse. This may take a moment.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        waiting_message = await update.message.reply_text(
            "📖 *جاري معالجة الآية القرآنية...*\n"
            "أبحث عن تفسير هذه الآية. قد يستغرق هذا لحظات.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    try:
        result = get_tafsir_from_text(text, language=lang)
        
        # Check if result is properly formatted
        if not isinstance(result, dict):
            raise ValueError(f"Invalid result format from get_tafsir_from_text: {result}")
        
        # Check if the input is not a Quranic verse
        if result.get('error') == 'not_quran_verse' or (
            'verse_info' in result and not result['verse_info'].get('is_quran_verse', True)
        ):
            explanation = result.get('explanation', '')
            if lang == "en":
                await waiting_message.edit_text(
                    "The text you sent doesn't appear to be a Quranic verse. "
                    f"{explanation}\n\n"
                    "*What you can send:*\n"
                    "• Arabic text of a Quran verse (e.g. إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ)\n"
                    "• Verse reference (e.g. 2:255 or Al-Baqarah:255)\n"
                    "• A photo containing Quranic text",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await waiting_message.edit_text(
                    "النص الذي أرسلته لا يبدو أنه آية قرآنية. "
                    f"{explanation}\n\n"
                    "*ما يمكنك إرساله:*\n"
                    "• النص العربي للآية القرآنية (مثل إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ)\n"
                    "• مرجع الآية (مثل ٢:٢٥٥ أو البقرة:٢٥٥)\n"
                    "• صورة تحتوي على نص قرآني",
                    parse_mode=ParseMode.MARKDOWN
                )
            return
        
        # Extract from the nested structure
        verse_info = result.get('verse_info', {})
        if not verse_info:
            raise ValueError(f"Missing verse_info in result: {result}")
        
        # Map result fields to expected names
        tafsir_result = {
            "surah": verse_info.get("surah_number"),
            "verse": verse_info.get("ayah_number"),
            "arabic": verse_info.get("normalized_text", ""),
            "translation": result.get("translated_text", ""),
            "tafsir": result.get("condensed_tafsir", result.get("tafsir_content", "")),
            "confidence": verse_info.get("match_confidence", 0)
        }
        
        # Log for debugging
        logger.debug(f"Tafsir result: {tafsir_result}")
        
        # Ensure there is some content in the tafsir field
        if not tafsir_result["tafsir"] and "tafsir_content" in result:
            tafsir_result["tafsir"] = result["tafsir_content"]
        
        if tafsir_result["confidence"] < MIN_CONFIDENCE:
            if lang == "en":
                await waiting_message.edit_text(
                    "I couldn't confidently identify a Quran verse in this text. "
                    "Please try sending a clearer verse or a photo of the text.\n\n"
                    "*Tip:* You can send Quranic verses in any of these formats:\n"
                    "• Arabic text (e.g. إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ)\n"
                    "• Verse reference (e.g. 2:255 or Al-Baqarah:255)\n"
                    "• Or an image containing Quranic text",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await waiting_message.edit_text(
                    "لم أتمكن من تحديد آية قرآنية في هذا النص بثقة. "
                    "يرجى إرسال آية أوضح أو صورة للنص.\n\n"
                    "*نصيحة:* يمكنك إرسال الآيات القرآنية بأي من هذه الطرق:\n"
                    "• النص العربي (مثل إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ)\n"
                    "• رقم الآية (مثل ٢:٢٥٥ أو البقرة:٢٥٥)\n"
                    "• أو صورة تحتوي على نص قرآني",
                    parse_mode=ParseMode.MARKDOWN
                )
            return
        
        if lang == "en":
            response = (
                f"📖 *Verse {tafsir_result['surah']}:{tafsir_result['verse']}*\n\n"
                f"*Arabic:*\n{tafsir_result['arabic']}\n\n"
                f"*Translation:*\n{tafsir_result['translation']}\n\n"
                f"*Tafsir:*\n{tafsir_result['tafsir']}\n\n"
                f"*Tip:* Send ✅ if you've read this verse today to track your streak."
            )
        else:
            response = (
                f"📖 *الآية {tafsir_result['surah']}:{tafsir_result['verse']}*\n\n"
                f"*النص العربي:*\n{tafsir_result['arabic']}\n\n"
                f"*الترجمة:*\n{tafsir_result['translation']}\n\n"
                f"*التفسير:*\n{tafsir_result['tafsir']}\n\n"
                f"*نصيحة:* أرسل ✅ إذا قرأت هذه الآية اليوم لتتبع سلسلة القراءة الخاصة بك."
            )
        
        # Edit waiting message instead of sending new one
        await waiting_message.edit_text(response, parse_mode=ParseMode.MARKDOWN)
        mark_task_complete(task_id)
        
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        mark_task_failed(task_id, str(e))
        if lang == "en":
            await waiting_message.edit_text(
                "Sorry, I encountered an error processing your request. Please try again.\n\n"
                "If you're trying to get tafsir for a verse, please make sure to send:\n"
                "• The full verse text in Arabic\n"
                "• Or the surah and verse number (e.g., 2:255)\n"
                "• Or an image of the verse",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await waiting_message.edit_text(
                "عذراً، واجهت خطأً في معالجة طلبك. يرجى المحاولة مرة أخرى.\n\n"
                "إذا كنت تحاول الحصول على تفسير لآية، يرجى التأكد من إرسال:\n"
                "• النص الكامل للآية بالعربية\n"
                "• أو رقم السورة والآية (مثل ٢:٢٥٥)\n"
                "• أو صورة للآية",
                parse_mode=ParseMode.MARKDOWN
            )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo messages."""
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    task_id = track_processing_task(user_id)
    
    # Send waiting message
    waiting_message = None
    if lang == "en":
        waiting_message = await update.message.reply_text(
            "🔍 *Processing your image...*\n"
            "I'm extracting and identifying Quranic text from your image. This may take a moment.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        waiting_message = await update.message.reply_text(
            "🔍 *جاري معالجة الصورة...*\n"
            "أستخرج وأحدد النص القرآني من صورتك. قد يستغرق هذا لحظات.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    try:
        # Get the largest photo
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Download the photo to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            await file.download_to_drive(temp_file.name)
            temp_path = temp_file.name
        
        try:
            result = get_tafsir_from_image(temp_path, language=lang)
            
            # Check if result is properly formatted
            if not isinstance(result, dict):
                raise ValueError(f"Invalid result format from get_tafsir_from_image: {result}")
            
            # Extract from the nested structure
            verse_info = result.get('verse_info', {})
            if not verse_info:
                raise ValueError(f"Missing verse_info in result: {result}")
            
            # Map result fields to expected names
            tafsir_result = {
                "surah": verse_info.get("surah_number"),
                "verse": verse_info.get("ayah_number"),
                "arabic": verse_info.get("normalized_text", ""),
                "translation": result.get("translated_text", ""),
                "tafsir": result.get("condensed_tafsir", result.get("tafsir_content", "")),
                "confidence": verse_info.get("match_confidence", 0)
            }
            
            # Log for debugging
            logger.debug(f"Tafsir result: {tafsir_result}")
            
            # Ensure there is some content in the tafsir field
            if not tafsir_result["tafsir"] and "tafsir_content" in result:
                tafsir_result["tafsir"] = result["tafsir_content"]
            
            if tafsir_result["confidence"] < MIN_CONFIDENCE:
                if lang == "en":
                    await waiting_message.edit_text(
                        "I couldn't confidently identify a Quran verse in this image. "
                        "Please try sending a clearer photo.\n\n"
                        "*Tips for better results:*\n"
                        "• Ensure good lighting\n"
                        "• Make sure the text is focused\n"
                        "• Avoid glare or shadows on the text\n"
                        "• You can also type the verse directly as text",
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await waiting_message.edit_text(
                        "لم أتمكن من تحديد آية قرآنية في هذه الصورة بثقة. "
                        "يرجى إرسال صورة أوضح.\n\n"
                        "*نصائح للحصول على نتائج أفضل:*\n"
                        "• تأكد من وجود إضاءة جيدة\n"
                        "• تأكد من وضوح النص\n"
                        "• تجنب الوهج أو الظلال على النص\n"
                        "• يمكنك أيضًا كتابة الآية مباشرة كنص",
                        parse_mode=ParseMode.MARKDOWN
                    )
                return
            
            if lang == "en":
                response = (
                    f"📖 *Verse {tafsir_result['surah']}:{tafsir_result['verse']}*\n\n"
                    f"*Arabic:*\n{tafsir_result['arabic']}\n\n"
                    f"*Translation:*\n{tafsir_result['translation']}\n\n"
                    f"*Tafsir:*\n{tafsir_result['tafsir']}\n\n"
                    f"*Tip:* Send ✅ if you've read this verse today to track your streak."
                )
            else:
                response = (
                    f"📖 *الآية {tafsir_result['surah']}:{tafsir_result['verse']}*\n\n"
                    f"*النص العربي:*\n{tafsir_result['arabic']}\n\n"
                    f"*الترجمة:*\n{tafsir_result['translation']}\n\n"
                    f"*التفسير:*\n{tafsir_result['tafsir']}\n\n"
                    f"*نصيحة:* أرسل ✅ إذا قرأت هذه الآية اليوم لتتبع سلسلة القراءة الخاصة بك."
                )
            
            # Edit waiting message instead of sending new one
            await waiting_message.edit_text(response, parse_mode=ParseMode.MARKDOWN)
            mark_task_complete(task_id)
            
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.error(f"Error deleting temporary file: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error processing photo: {str(e)}")
        mark_task_failed(task_id, str(e))
        if lang == "en":
            await waiting_message.edit_text(
                "Sorry, I encountered an error processing your image. Please try again.\n\n"
                "*Tips:*\n"
                "• Try with a clearer image\n"
                "• Or send the verse as text instead\n"
                "• Make sure the image contains Quranic text",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await waiting_message.edit_text(
                "عذراً، واجهت خطأً في معالجة صورتك. يرجى المحاولة مرة أخرى.\n\n"
                "*نصائح:*\n"
                "• حاول بصورة أوضح\n"
                "• أو أرسل الآية كنص بدلاً من ذلك\n"
                "• تأكد من أن الصورة تحتوي على نص قرآني",
                parse_mode=ParseMode.MARKDOWN
            ) 