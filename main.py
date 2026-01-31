#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import telebot
import random
import time
import logging
from flask import Flask
from threading import Thread

# ================= TOKENLAR =================
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN", "8236645335:AAG5paUC631oGqhUp_3zRLHYObQxH8CGgNc")

# HTML MODE
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")

# Flask app for Render
app = Flask(__name__)

# ================= WEBHOOK =================
WEBHOOK_URL = f"https://erkinov-ai-bot.onrender.com/{TELEGRAM_TOKEN}"

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    import json
    from flask import request
    
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'Bad request', 400

# ================= STICKERS =================
STICKERS = [
    "CAACAgIAAxkBAAIBjGbC_V8NRhS2ObgABqYmRf38GILucgAC_hcAAu9pOUqS7VEEVhLQQzQE",
    "CAACAgIAAxkBAAIBjWbC_WBri-ocw3D_nODoxYHt8QzTAAKvGwACgmcAAUoI1hTx2ZR8vTQE",
]

# ================= LOCAL AI FUNKSIYA (API KERAK EMAS!) =================
def get_ai_response(user_message):
    """Local AI javobi - hech qanday API kerak emas!"""
    
    # Savolni tahlil qilish
    user_message_lower = user_message.lower()
    
    # Matematika savollari
    if any(word in user_message_lower for word in ["2+2", "3*3", "5-1", "10/2", "hisobla", "hisob", "sum", "plus"]):
        if "2+2" in user_message_lower:
            return "2 + 2 = 4"
        elif "3*3" in user_message_lower:
            return "3 × 3 = 9"
        elif "5-1" in user_message_lower:
            return "5 - 1 = 4"
        elif "10/2" in user_message_lower:
            return "10 ÷ 2 = 5"
        else:
            return "Matematik hisoblash uchun aniq misol yozing (masalan: 5+3)"
    
    # Jahon urushi haqida
    if any(word in user_message_lower for word in ["jahon urushi", "world war", "urush", "war"]):
        if "2" in user_message_lower or "ikkinchi" in user_message_lower:
            return "Ikkinchi jahon urushi 1939-1945 yillar oralig'ida bo'lib o'tdi. U dunyo tarixidagi eng halokatli urush bo'lib, 60 milliondan ortiq odam halok bo'ldi."
        elif "1" in user_message_lower or "birinchi" in user_message_lower:
            return "Birinchi jahon urushi 1914-1918 yillar oralig'ida bo'lib o'tdi. U 'Barcha urushlarni tugatadigan urush' deb atalgan."
        else:
            return "Jahon urushi haqida:\n• 1-jahon urushi: 1914-1918\n• 2-jahon urushi: 1939-1945"
    
    # Python haqida
    if "python" in user_message_lower:
        return "Python - dunyoning eng mashhur dasturlash tillaridan biri. Oddiy, o'qish oson va kuchli. Veb-saytlar, AI, ma'lumotlar tahlili uchun ishlatiladi."
    
    # Dasturlash
    if any(word in user_message_lower for word in ["dasturlash", "programming", "kod", "code"]):
        return "Dasturlash - kompyuterga vazifa bajarishni o'rgatish san'ati. Mashhur tillar: Python, JavaScript, Java, C++. Boshlash uchun Python tavsiya etiladi."
    
    # O'zbekiston haqida
    if any(word in user_message_lower for word in ["o'zbekiston", "uzbekistan", "toshkent", "samarqand"]):
        return "O'zbekiston - Markaziy Osiyoda joylashgan davlat. Poytaxti - Toshkent. Mashhur shaharlari: Samarqand, Buxoro, Xiva. Aholisi 36 million."
    
    # Salomlashish
    if any(word in user_message_lower for word in ["salom", "hello", "hi", "assalom"]):
        return "Assalomu alaykum! Men Erkinov AI Botman. Savolingizga javob berishga harakat qilaman."
    
    # Rahmat
    if any(word in user_message_lower for word in ["rahmat", "thanks", "thank you", "tashakkur"]):
        return "Sizga ham rahmat! Yana savollaringiz bo'lsa, bemalol so'rang."
    
    # Kim yaratdi
    if any(word in user_message_lower for word in ["kim yaratdi", "yaratuvchi", "developer", "kim qildi"]):
        return "Bu bot Mehruzbek Erkinov tomonidan yaratilgan va Render.com da 24/7 ishlaydi."
    
    # Bot haqida
    if any(word in user_message_lower for word in ["bot", "sen", "siz", "who are you"]):
        return "Men Erkinov AI Botman. Savollaringizga javob beraman. Render.com da doimiy ishlayman."
    
    # Vaqt/sana
    if any(word in user_message_lower for word in ["vaqt", "time", "sana", "date"]):
        import datetime
        now = datetime.datetime.now()
        return f"Hozir: {now.strftime('%H:%M:%S')}\nSana: {now.strftime('%d-%m-%Y')}\n(Toshkent vaqti)"
    
    # Umumiy savollar uchun intelligent javoblar
    responses = [
        f"Savolingiz: '{user_message}'. Bu haqda aniq ma'lumotim yo'q, lekin qisqacha:\nBu mavzu qiziqarli, ko'proq o'qib chiqing.",
        f"'{user_message}' haqida savol berdingiz. Men hozircha bu mavzuda chuqur ma'lumotga ega emasman.",
        f"Kechirasiz, '{user_message}' haqida aniq javob bera olmayman. Boshqa savolingiz bo'lsa, yozing.",
        f"Qiziq savol! '{user_message}' haqida o'ylab ko'raman. Hozircha javob berolmayman.",
    ]
    
    return random.choice(responses)

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    try:
        bot.send_sticker(message.chat.id, random.choice(STICKERS))
    except:
        pass

    bot.reply_to(
        message,
        "🤖 <b>Erkinov AI Bot</b>\n\n"
        "🧠 <i>Local AI rejimida ishlayman!</i>\n\n"
        "📝 <b>Savol misollari:</b>\n"
        "• 2+2 qancha?\n"
        "• Python nima?\n"
        "• Jahon urushi qachon?\n"
        "• O'zbekiston haqida\n\n"
        "📍 /help - Barcha buyruqlar\n"
        "📍 /topics - Mavzular ro'yxati\n\n"
        "✅ <i>Render.com | 24/7 Online</i>"
    )

# ================= HELP =================
@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(
        message,
        "🆘 <b>Yordam:</b>\n\n"
        "1. Faqat savol yozing\n"
        "2. /start - Boshlash\n"
        "3. /topics - Mavzular\n"
        "4. /info - Bot haqida\n"
        "5. /ping - Holatni tekshirish\n\n"
        "🧠 <i>Local AI - API kerak emas!</i>"
    )

# ================= TOPICS =================
@bot.message_handler(commands=['topics', 'mavzular'])
def topics_cmd(message):
    bot.reply_to(
        message,
        "📚 <b>Mavzular:</b>\n\n"
        "🔹 Matematika (2+2, 5*3)\n"
        "🔹 Tarix (Jahon urushi)\n"
        "🔹 Dasturlash (Python)\n"
        "🔹 Geografiya (O'zbekiston)\n"
        "🔹 Vaqt va sana\n"
        "🔹 Bot haqida\n\n"
        "📝 <i>Istalgan savolni yozing!</i>"
    )

# ================= INFO =================
@bot.message_handler(commands=['info'])
def info_cmd(message):
    bot.reply_to(
        message,
        "📊 <b>Bot haqida:</b>\n\n"
        "🤖 <b>Erkinov AI Bot</b>\n"
        "👨‍💻 Yaratuvchi: Mehruzbek Erkinov\n"
        "🌐 Hosting: Render.com\n"
        "⚡ Status: 24/7 Online\n"
        "🧠 AI: Local Intelligence\n"
        "🔗 Username: @ErkinovAIBot\n\n"
        "✅ <i>Hech qanday API kerak emas!</i>"
    )

# ================= PING =================
@bot.message_handler(commands=['ping', 'status'])
def ping_cmd(message):
    import datetime
    now = datetime.datetime.now()
    bot.reply_to(
        message,
        f"🟢 <b>Bot faol!</b>\n\n"
        f"🕐 Vaqt: {now.strftime('%H:%M:%S')}\n"
        f"📅 Sana: {now.strftime('%d.%m.%Y')}\n"
        f"🌐 Server: Render.com\n"
        f"⚡ Holat: Online 24/7\n"
        f"🧠 AI: Local mode"
    )

# ================= ASOSIY HANDLER =================
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if not message.text:
        return
    
    user_text = message.text.strip()
    
    # Typing effekti
    bot.send_chat_action(message.chat.id, 'typing')
    time.sleep(1)  # Real AI effekti uchun
    
    # AI javobi
    ai_response = get_ai_response(user_text)
    
    # Sticker (50% ehtimol bilan)
    if random.random() > 0.5:
        try:
            bot.send_sticker(message.chat.id, random.choice(STICKERS))
        except:
            pass
    
    # Chiroyli javob
    formatted_response = f"""
🧠 <b>AI Javobi:</b>

{ai_response}

━━━━━━━━━━━━━━
🤖 <b>Erkinov AI</b> | @ErkinovAIBot
    """
    
    bot.reply_to(message, formatted_response)

# ================= FLASK ROUTES =================
@app.route('/')
def home():
    return "🤖 Erkinov AI Bot - Local AI rejimida ishlaydi!"

@app.route('/health')
def health():
    return "✅ OK - Bot faol", 200

@app.route('/setwebhook')
def set_webhook():
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
        return f"✅ Webhook o'rnatildi: {WEBHOOK_URL}"
    except Exception as e:
        return f"❌ Xato: {str(e)}"

# ================= MAIN =================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("====================================")
    print("🤖 ERKINOV AI BOT - LOCAL AI")
    print("🌐 Webhook Mode: Active")
    print("✅ API kerak emas!")
    print("====================================")
    
    # Webhook
    try:
        print("📡 Webhook o'rnatilmoqda...")
        bot.remove_webhook()
        time.sleep(2)
        bot.set_webhook(url=WEBHOOK_URL)
        print(f"✅ Webhook o'rnatildi")
    except Exception as e:
        print(f"⚠️ Webhook xatosi: {e}")
    
    # Server
    port = int(os.getenv("PORT", 10000))
    print(f"🚀 Server {port} portda ishga tushmoqda...")
    app.run(host='0.0.0.0', port=port, debug=False)
