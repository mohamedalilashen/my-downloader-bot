import telebot
import yt_dlp
import os
import time
from telebot import types
from flask import Flask
from threading import Thread

# --- [ 1. إعدادات السيرفر الوهمي للبقاء حياً ] ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive and running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- [ 2. إعدادات البوت ] ---
BOT_TOKEN = '7684038454:AAGJnvQ-4slEnZzXnghh_JjIXjxKFRWnJxQ'
INSTAGRAM_URL = 'https://www.instagram.com/reel/DUK7suzEgzv/?utm_source=ig_web_copy_link&igsh=NTc4MTIwNjQ2YQ=='

bot = telebot.TeleBot(BOT_TOKEN)
verified_users = set()

# دالة التحميل
def download_video(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video_%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# --- [ 3. منطق الأوامر ] ---

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id in verified_users:
        bot.send_message(message.chat.id, "✅ البوت مفعل! أرسل رابط الفيديو الآن.")
        return

    # زرار واحد فقط في البداية
    markup = types.InlineKeyboardMarkup()
    btn_insta = types.InlineKeyboardButton("📸 تابعني على انستجرام أولاً", url=INSTAGRAM_URL)
    markup.add(btn_insta)
    
    msg = bot.send_message(message.chat.id, 
                     "🚫 الوصول محظور!\n\nيجب متابعة الحساب أولاً.", 
                     reply_markup=markup)
    
    # الانتظار الصامت (10 ثواني)
    time.sleep(10)
    
    # إضافة زر التفعيل بعد الانتظار
    markup_final = types.InlineKeyboardMarkup()
    markup_final.add(btn_insta) 
    btn_verify = types.InlineKeyboardButton("🔓 تفعيل البوت الآن ✅", callback_data="activate_now")
    markup_final.add(btn_verify)
    
    try:
        bot.edit_message_reply_markup(chat_id=message.chat.id, 
                                     message_id=msg.message_id, 
                                     reply_markup=markup_final)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "activate_now")
def activate_now(call):
    verified_users.add(call.from_user.id)
    bot.answer_callback_query(call.id, "🎉 تم تفعيل البوت!")
    bot.edit_message_text(chat_id=call.message.chat.id, 
                         message_id=call.message.message_id, 
                         text="🎯 مبروك! البوت مفتوح الآن.\nأرسل رابط الفيديو (TikTok, Instagram, YouTube) لتحميله.")

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.from_user.id
    
    # حماية: لو مش مفعل يرجعه لنظام الـ 10 ثواني
    if user_id not in verified_users:
        start(message)
        return

    url = message.text
    if url.startswith("http"):
        status_msg = bot.reply_to(message, "⏳ جاري التحميل... انتظر قليلاً.")
        try:
            file_path = download_video(url)
            with open(file_path, 'rb') as video:
                bot.send_video(message.chat.id, video, caption="✅ تم التحميل بواسطة بوتك")
            
            os.remove(file_path)
            bot.delete_message(message.chat.id, status_msg.message_id)
        except Exception:
            bot.edit_message_text("❌ حدث خطأ! تأكد من أن الرابط عام وليس لحساب خاص.", 
                                 message.chat.id, status_msg.message_id)
    else:
        bot.reply_to(message, "⚠️ أرسل رابطاً صحيحاً.")

# --- [ 4. التشغيل النهائي ] ---
if __name__ == "__main__":
    keep_alive() # تشغيل Flask في الخلفية
    print("🚀 البوت يعمل الآن...")
    bot.infinity_polling()