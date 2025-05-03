from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from utils.utils import get_user_language
from database.db_manager import DatabaseManager

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    
    if lang == "en":
        await update.message.reply_text(
            "*📖 Quran Companion Help Guide 📖*\n\n"
            "*Getting Tafsir (Explanation):*\n"
            "• Send Arabic text of a Quranic verse\n"
            "• Send verse reference (e.g., `2:255` or `Al-Baqarah:255`)\n"
            "• Send a photo of a Quranic verse\n\n"
            "*Tracking Your Reading:*\n"
            "• After reading, send ✅ to mark your daily reading\n"
            "• Use /streak to check your current reading streak\n\n"
            "*Status Updates:*\n"
            "• The bot will show \"Processing...\" while looking up tafsir\n"
            "• If your input isn't recognized, you'll get suggestions\n\n"
            "*Setting Your Timezone:*\n"
            "• Use `/settimezone` followed by your timezone\n"
            "• Format: City or Region/City (e.g., `America/New_York`, `Europe/London`)\n"
            "• Example: `/settimezone Asia/Riyadh`\n\n"
            "*Setting Reminders:*\n"
            "• Use `/setreminder` to set daily reading reminders\n"
            "• Format: Time in 24-hour format (HH:MM)\n"
            "• Example: `/setreminder 05:30` for 5:30 AM\n"
            "• Example: `/setreminder 21:45` for 9:45 PM\n"
            "• Reminders are based on your set timezone\n\n"
            "*Commands:*\n"
            "• `/start` - Restart the bot\n"
            "• `/help` - Show this help message\n"
            "• `/streak` - Show your current streak\n"
            "• `/dashboard` - Show group dashboard (in groups)\n"
            "• `/settimezone` - Set your timezone\n"
            "• `/setreminder` - Set daily reminders\n"
            "• `/privacy` - View privacy policy\n\n"
            "*Examples:*\n"
            "• Send: `إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ`\n"
            "• Send: `108:1` (Surah 108, Verse 1)\n"
            "• Send an image of a Quranic page\n"
            "• Send ✅ after your daily reading",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "*📖 دليل المساعدة لرفيق القرآن 📖*\n\n"
            "*الحصول على التفسير:*\n"
            "• أرسل نص عربي لآية قرآنية\n"
            "• أرسل رقم الآية (مثل `٢:٢٥٥` أو `البقرة:٢٥٥`)\n"
            "• أرسل صورة لآية قرآنية\n\n"
            "*تتبع قراءتك:*\n"
            "• بعد القراءة، أرسل ✅ لتسجيل قراءتك اليومية\n"
            "• استخدم /streak للتحقق من سلسلة القراءة الحالية\n\n"
            "*تحديثات الحالة:*\n"
            "• سيُظهر البوت \"جاري المعالجة...\" أثناء البحث عن التفسير\n"
            "• إذا لم يتم التعرف على مدخلاتك، ستحصل على اقتراحات\n\n"
            "*إعداد المنطقة الزمنية:*\n"
            "• استخدم `/settimezone` متبوعًا بمنطقتك الزمنية\n"
            "• الصيغة: المدينة أو المنطقة/المدينة (مثل `Asia/Riyadh`، `Europe/Cairo`)\n"
            "• مثال: `/settimezone Asia/Riyadh`\n\n"
            "*إعداد التذكيرات:*\n"
            "• استخدم `/setreminder` لضبط تذكيرات القراءة اليومية\n"
            "• الصيغة: الوقت بتنسيق 24 ساعة (HH:MM)\n"
            "• مثال: `/setreminder 05:30` للساعة 5:30 صباحًا\n"
            "• مثال: `/setreminder 21:45` للساعة 9:45 مساءً\n"
            "• تعتمد التذكيرات على المنطقة الزمنية التي حددتها\n\n"
            "*الأوامر:*\n"
            "• `/start` - إعادة تشغيل البوت\n"
            "• `/help` - عرض رسالة المساعدة هذه\n"
            "• `/streak` - عرض سلسلة الاستمرارية الحالية\n"
            "• `/dashboard` - عرض لوحة المعلومات (في المجموعات)\n"
            "• `/settimezone` - تعيين المنطقة الزمنية\n"
            "• `/setreminder` - تعيين تذكيرات يومية\n"
            "• `/privacy` - عرض سياسة الخصوصية\n\n"
            "*أمثلة:*\n"
            "• أرسل: `إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ`\n"
            "• أرسل: `١٠٨:١` (سورة الكوثر، الآية ١)\n"
            "• أرسل صورة لصفحة من القرآن\n"
            "• أرسل ✅ بعد قراءتك اليومية",
            parse_mode=ParseMode.MARKDOWN
        ) 