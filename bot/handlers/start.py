from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from utils.utils import set_user_language

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a language selection message when the command /start is issued."""
    
    keyboard = [
        [KeyboardButton("English"), KeyboardButton("العربية")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "🌟 Welcome to Quran Companion! Please select your preferred language:\n🌟 مرحبًا بك في رفيق القرآن! يرجى اختيار لغتك المفضلة:",
        reply_markup=reply_markup
    )

async def language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection from the user."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if text == "English":
        set_user_language(user_id, "en")
        await update.message.reply_text(
            """
*Welcome to Quran Companion!* 📖✨

This bot helps you stay consistent with your daily Quran reading and reflection.

*How to use this bot:*

• *Get tafsir (explanation):* Simply send any Quranic verse as:
  - Arabic text
  - Verse reference (e.g., 2:255 or Al-Baqarah:255)
  - Image containing Quranic text

• *Track your reading:* Send ✅ after reading to maintain your streak
  
• *Reminders:* Set daily reminders to help you stay consistent

*Commands:*
/start - Start the bot
/help - Get help
/streak - Show your current streak
/dashboard - Show group dashboard (in groups)
/settimezone - Set your timezone
/setreminder - Set daily reminders
/privacy - View privacy policy

Try sending a verse now to get started!
            """.strip(),
            reply_markup=None,
            parse_mode=ParseMode.MARKDOWN
        )
    elif text == "العربية":
        set_user_language(user_id, "ar")
        await update.message.reply_text(
            """
*مرحبًا بك في رفيق القرآن!* 📖✨

هذا البوت يساعدك على المواظبة على قراءة وتدبر وِردك اليومي من القرآن الكريم.

*كيفية استخدام البوت:*

• *الحصول على التفسير:* ما عليك سوى إرسال أي آية قرآنية:
  - كنص عربي
  - كرقم الآية (مثل ٢:٢٥٥ أو البقرة:٢٥٥)
  - صورة تحتوي على نص قرآني

• *تتبع القراءة:* أرسل ✅ بعد القراءة للحفاظ على سلسلة المواظبة
  
• *التذكيرات:* اضبط تذكيرات يومية لمساعدتك على الاستمرار

*الأوامر:*
/start - بدء البوت
/help - الحصول على مساعدة
/streak - عرض سلسلة الاستمرارية الخاصة بك
/dashboard - عرض لوحة المعلومات (في المجموعات)
/settimezone - تعيين المنطقة الزمنية الخاصة بك
/setreminder - تعيين تذكيرات يومية
/privacy - عرض سياسة الخصوصية

جرب إرسال آية الآن للبدء!
            """.strip(),
            reply_markup=None,
            parse_mode=ParseMode.MARKDOWN
        ) 