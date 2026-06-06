import os
import telebot
from telebot import types
import feedparser
import requests
import threading
import time
import schedule
from datetime import datetime

# ۱. تنظیم توکن و آیدی گروه از طریق متغیرهای محیطی Railway
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# آیدی گروه را هم از سرور می‌گیریم تا با ری‌استارت شدن پاک نشود
# اگر ثبت نشده بود، از روی پیام‌ها به صورت خودکار آپدیت می‌شود
TARGET_CHAT_ID = os.getenv('TARGET_CHAT_ID')
if TARGET_CHAT_ID:
    TARGET_CHAT_ID = int(TARGET_CHAT_ID)

# بانک اطلاعاتی ذخیره اخطارهای کاربران (Warns)
user_warns = {}

# ۲. منابع خبری استراتژیک و رادار کانال‌ها
NEWS_SOURCES = {
    "تسنیم (خط مقدم)": "https://www.tasnimnews.com/fa/rss/feed/0/7/89",
    "فارس (سیاسی)": "https://www.farsnews.ir/rss/politics",
    "مهر (بین‌الملل)": "https://www.mehrnews.com/rss/category/international",
    "المیادین (عربی)": "https://www.almayadeen.net/news/rss",
    "رادار کافه میدون": "https://news.google.com/rss/search?q=Kafe_Meydon&hl=fa&gl=IR&ceid=IR:fa"
}

KEYWORDS = [
    'جنگ', 'موشک', 'توافق', 'آتش‌بس', 'غزه', 'پهپاد', 'لبنان', 'مذاکرات', 'اسرائیل', 
    'آمریکا', 'نظامی', 'پدافند', 'حمله', 'شهید', 'شهادت', 'حزب الله', 'مقاومت', 'سپاه', 
    'ایران', 'پاسخ موشکی', 'انفجار', 'ترامپ', 'trump', 'war', 'missile', 'attack'
]

FORBIDDEN_WORDS = ['دیوث', 'اسکل', 'اشغال', 'بیشرف', 'کثافت', 'احمق', 'کص', 'کیر', 'کون']
ENEMY_WORDS = ['آمریکا', 'اسرائیل', 'صهیونیست', 'نتانیاهو', 'بایدن', 'ترامپ', 'trump']

print("⚔️ دژ استراتژیک و رادار هوشمند عمار (نسخه بهینه‌شده Railway) روشن شد...")

# سیستم مترجم آنلاین زنده
def translate_to_persian(text):
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=fa&dt=t&q={requests.utils.quote(text)}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return "".join([sentence[0] for sentence in response.json()[0] if sentence[0]])
        return text
    except: 
        return text

# ۳. مغز متفکر و چت‌بات ابرپیشرفته عمار
def advanced_ai_chat(user_message, user_name):
    msg = user_message.lower()
    
    if any(w in msg for w in ["توافق", "برجام", "مذاکره", "فایده توافق"]):
        return (f"جناب {user_name} عزیز، نگاه به مسئله توافق نباید سطحی و بر اساس خوش‌بینی به غرب باشد. "
                "در منطق انقلاب، توافق یک ابزار استراتژیک برای اتمام حجت با افکار عمومی دنیا، خنثی کردن پروژه ایران‌هراسی "
                "و اتمام بهانه‌های اقتصادی است. عهدشکنی مکرر مستکبرین (مثل ترامپ و بایدن) نشان داد که ذات غرب غیرقابل اعتماد است. "
                "فایده توافق هوشمندانه این است که در صورت نقض عهد از سوی دشمن، دست نظام برای پاسخ‌های جهشی، پیشرفت‌های هسته‌ای "
                "و ضربات محکم‌تر در میدان کاملاً باز خواهد بود. توافق یک تاکتیک است، اصل مقاومت و اتکا به درون است!")

    elif any(w in msg for w in ["موشک", "پاسخ موشکی", "پاسخ ایران", "بمباران"]):
        return (f"برادر دغدغه‌مند من {user_name} جان، در دکترین دفاعی ما، پاسخ موشکی و تنبیه متجاوز یک ضرورت حیاتی برای "
                "حفظ امنیت پایدار ملت است. اگر در برابر حماقت‌های رژیم صهیونیستی و آمریکا پاسخ قاطع داده نشود، دشمن جری‌تر خواهد شد. "
                "سیلی‌های موشکی سپاه و ارتش نه تنها هیمنه پوشالی استکبار را در منطقه فرو ریخت، بلکه پیامی واضح به اتاق‌های فکر "
                "واشنگتن و تل‌آویو فرستاد که دوران 'بزن و در رو' به پایان رسیده و هرگونه تجاوز با بارانی از موشک‌های نقطه‌زن پاسخ داده می‌شود.")

    elif any(w in msg for w in ["تحلیل", "اوضاع", "سیاسی", "جنگ"]):
        return (f"جناب {user_name} عزیز، رصد میدانی نشون میده دشمن در جبهه نظامی به بن‌بست کامل خورده و توان تقابل با محور مقاومت را ندارد. "
                "به همین دلیل تمام توانش رو آورده روی 'جنگ شناختی' و پمپاژ دروغ و ناامیدی در فضای مجازی تا اراده ملت را سست کند. "
                "امروز سنگین‌ترین وظیفه ما، 'جهاد تبیین'، افشای شایعات، دوری از انفعال و گوش به فرمان ولایت بودنه. افق رو به جلو "
                "فوق‌العاده روشن است و به فضل الهی فتح نهایی بسیار نزدیکه؛ باید با قدرت ایستادگی کنیم! ✌️")

    elif any(w in msg for w in ["خسته", "ناامید", "سخت"]):
        return (f"مؤمن و ناامیدی؟ اصلاً و ابداً {user_name} جان! مسیر حق همیشه همراه با ابتلائات، تحریم‌ها و فشارهای شدید است؛ "
                "این سنت الهی برای غربال آخرالزمانی است. سختی‌ها نشانه نزدیک شدن به قله است. "
                "یادمون نره: 'أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ'. یک صلوات حیدری پسند بفرست و با انگیزه دوچندان به سنگرت "
                "در فضای مجازی و کف میدان ادامه بده که صاحب اصلی این انقلاب، تک‌تک این پایداری‌ها رو رصد می‌کنه. یا علی ممد!")

    elif any(w in msg for w in ["سلام", "درود", "علیک"]):
        return (f"سلام و درود خالصانه و برادرانه خدا بر شما افسر جنگ نرم، جناب {user_name} عزیز. "
                "امیدوارم طاعاتتون قبول حق باشه و قدم‌هاتون در سنگر defense از آرمان‌های انقلاب استوار بماند. "
                "بنده به عنوان خادم کوچک این قرارگاه در خدمت شما هستم، امر بفرمایید برادر؟ 🌸")

    elif any(w in msg for w in ["ممنون", "تشکر", "سپاس"]):
        return f"خواهش می‌کنم جناب {user_name} عزیز، انجام وظیفه بود. سایه‌تون مستدام، عاقبتتون شهدایی و التماس دعای فرج."

    return (f"فرمایش شما کاملاً متین و قابل استفاده است جناب {user_name}. بنده به عنوان دستیار هوشمند قرارگاه در خدمت شما هستم. "
            "می‌تونید برای رصد اخبار زنده خط مقدم و بررسی وضعیت آسمان کشور، دکمه‌های شیشه‌ای زیر پیام راهنما رو لمس کنید.")

# ۴. فرمان راهنما
@bot.message_handler(commands=['help', 'start', 'راهنما'])
def send_help(message):
    global TARGET_CHAT_ID
    if not TARGET_CHAT_ID:
        TARGET_CHAT_ID = message.chat.id
    user_name = message.from_user.first_name if message.from_user.first_name else "برادر"
    
    help_text = (
        f"🤖 *به قرارگاه رادار و دستیار هوشمند عمار خوش آمدید، جناب {user_name}*\n\n"
        "✨ *چت‌بات هوشمند:* کافیه کلمه 'عمار' رو در پیامتون بیارید یا روی پیامم ریپلای کنید تا با تحلیل‌های عمیق گفتگو کنیم.\n\n"
        "📡 *سیستم‌های فعال:* پادگان خودکار (سیستم اخطار ۳ تایی فحش) | رادار زنده کافه میدون و خبرگزاری‌ها | حکومت نظامی شبانه\n\n"
        "📰 جهت استخراج آخرین اخبار و تحلیل‌های زنده خط مقدم، دکمه زیر را لمس کنید:"
    )
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("📰 آخرین اخبار داغ و تحلیل‌ها", callback_data="get_hot_news")
    btn2 = types.InlineKeyboardButton("🚀 وضعیت آسمان کشور", callback_data="sky_status")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown', reply_markup=markup)

# ۵. تابع واکشی اخبار
def fetch_hot_news(chat_id):
    bot.send_message(chat_id, "🔍 در حال اسکن زنده رسانه‌ها، کانال کافه میدون و ترجمه فوری اخبار بین‌الملل... لطفاً صبور باشید.")
    collected_titles = []
    
    for source_name, url in NEWS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            count = 0
            for entry in feed.entries:
                title = entry.title
                summary = entry.summary if 'summary' in entry else ""
                full_content = (title + " " + summary).lower()
                
                if any(kw in full_content for kw in KEYWORDS):
                    if "رویترز" in source_name or "المیادین" in source_name: 
                        title = translate_to_persian(title)
                    
                    hashtag = "#تحلیل_میدان" if "کافه میدون" in source_name else "#رصد_خط_مقدم"
                    collected_titles.append(f"{hashtag}\n• {title} ({source_name})")
                    count += 1
                if count >= 3: break
        except: pass

    bulletin = f"📰 *بولتن جامع تحولات خط مقدم و رسانه‌ها*\n🗓️ تاریخ: {datetime.now().strftime('%Y-%m-%d | %H:%M')}\n✍ *---------------------------------------------\n\n*"
    if collected_titles:
        bulletin += "\n\n".join(collected_titles)
        bulletin += "\n\n📊 *تحلیل اجمالی عمار:* تحرکات رسانه‌ای دشمن نشان‌دهنده هراس از پاسخ‌های پدافندی و موشکی کشور است. جبهه مقاومت در عالی‌ترین سطح آمادگی قرار دارد."
    else:
        bulletin += "⚠️ خبر جدید و مرتبطی یافت نشد. لطفاً کمی بعد مجدداً تلاش کنید."
    bot.send_message(chat_id, bulletin, parse_mode='Markdown')

# ۶. مدیریت کلیک روی دکمه‌های شیشه‌ای
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "get_hot_news": fetch_hot_news(call.message.chat.id)
    elif call.data == "sky_status":
        bot.send_message(call.message.chat.id, "🚀 *گزارش آخرین وضعیت آسمان کشور:*\n\nآسمان سراسر میهن اسلامی تحت رصد ترکیبی و شبانه‌روزی رادارهای پیشرفته ارتش و سپاه قرار دارد. پدافند هوایی در وضعیت هوشیاری ۱۰۰ درصدی است. هرگونه تجاوز یا گستاخی دشمن صهیونیستی با پاسخ فوری، کوبنده و ویران‌کننده مواجه خواهد شد. امنیت برقرار است، دل‌ها استوار.")

# ۷. مدیریت پیام‌ها و فیلتر الفاظ
@bot.message_handler(func=lambda message: message.text)
def main_handler(message):
    global TARGET_CHAT_ID
    if not TARGET_CHAT_ID:
        TARGET_CHAT_ID = message.chat.id
    
    text = message.text.strip()
    text_lower = text.lower()
    user_id = message.from_user.id
    user_name = message.from_user.first_name if message.from_user.first_name else "برادر"
    
    if any(w in text_lower for w in FORBIDDEN_WORDS):
        if any(enemy in text_lower for enemy in ENEMY_WORDS):
            bot.reply_to(message, "✊ مرگ بر مستکبرین و ستمگران روزگار! لعنت خدا بر ترامپ، نتانیاهو و منش استکباری دشمنان اسلام.")
        else:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                user_warns[user_id] = user_warns.get(user_id, 0) + 1
                
                if user_warns[user_id] >= 3:
                    bot.restrict_chat_member(message.chat.id, user_id, until_date=int(time.time() + 43200))
                    bot.send_message(message.chat.id, f"🚨 کاربر {user_name} به دلیل دریافت ۳ اخطار رسمی، به مدت ۱۲ ساعت ممنوع‌الفعال (Mute) شد!")
                    user_warns[user_id] = 0
                else:
                    bot.send_message(message.chat.id, f"⚠️ جناب {user_name}، ارسال الفاظ نامناسب در قرارگاه ممنوع است!\n❌ *اخطار ثبت شده: {user_warns[user_id]} از ۳*")
            except Exception as e: print(f"Admin Error: {e}")
        return

    if text_lower == "اخبار" or text_lower == "/news":
        fetch_hot_news(message.chat.id)
        return

    if "عمار" in text_lower or (message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id):
        try:
            bot.send_chat_action(message.chat.id, 'typing')
            clean_text = text.replace("عمار", "").strip()
            ai_response = advanced_ai_chat(clean_text if clean_text else "سلام", user_name)
            bot.reply_to(message, ai_response)
        except: pass

# ۸. زمان‌بندی خودکار
def send_night_announcement():
    if TARGET_CHAT_ID:
        try:
            announcement = (
                "🚨 **بسم الله القاصم الجبارین**\n\n"
                "⏰ ساعت به وقت قرارگاه ۲۰:۳۰\n"
                "✊ **وقت لرزاندن پایه‌های استکباره، همگی بریم خیابان...**\n\n"
                "رفقا هماهنگ، با صلابت و پرشور جهت نصرت جبهه حق و تجمع انقلابی حرکت کنید. "
                "فضای مجازی سنگر ماست، اما کف میدان محل فتح نهایی است! یا علی..."
            )
            bot.send_message(TARGET_CHAT_ID, announcement, parse_mode='Markdown')
        except: pass

def lock_group():
    if TARGET_CHAT_ID:
        try:
            config = types.ChatPermissions(can_send_messages=False)
            bot.set_chat_permissions(TARGET_CHAT_ID, config)
            bot.send_message(TARGET_CHAT_ID, "🌙 *حکومت‌نظامی قرارگاه!*\n\nجهت حفظ نظم و امنیت، گروه تا ساعت ۰۷:۰۰ صبح قفل می‌باشد. التماس دعای فرج.")
        except: pass

def unlock_group():
    if TARGET_CHAT_ID:
        try:
            config = types.ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
            bot.set_chat_permissions(TARGET_CHAT_ID, config)
            bot.send_message(TARGET_CHAT_ID, "☀️ *صبحکم الله بالخیر و السعاده*\n\nقفل قرارگاه باز شد. سنگر مجازی دغدغه‌مندان انقلاب آماده فعالیت است.")
        except: pass

def run_schedule():
    # نکته: ساعت Railway بر اساس UTC (ساعت جهانی) است. 
    # زمان‌بندی‌ها را بر اساس ساعت رسمی سرور تنظیم کن.
    schedule.every().day.at("17:00").do(send_night_announcement) # ساعت ۲۰:۳۰ ایران (حدودی به وقت UTC)
    schedule.every().day.at("20:30").do(lock_group)             # ساعت ۱۲ شب ایران
    schedule.every().day.at("03:30").do(unlock_group)           # ساعت ۷ صبح ایران
    while True:
        schedule.run_pending()
        time.sleep(1)

timer_thread = threading.Thread(target=run_schedule)
timer_thread.daemon = True
timer_thread.start()

bot.infinity_polling()
