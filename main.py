#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import telebot
import requests
import random
import time
import logging
from flask import Flask
from threading import Thread

# ================= TOKENLAR =================
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN", "8236645335:AAG5paUC631oGqhUp_3zRLHYObQxH8CGgNc")

# Bot yaratish
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")

# Flask app
app = Flask(__name__)

# ================= WEBHOOK =================
WEBHOOK_URL = f"https://erkinov-ai-bot.onrender.com/{TELEGRAM_TOKEN}"

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'Bad request', 400

# ================= AI FUNKSIYA =================
def get_ai_response(user_message):
    """Simple AI function"""
    user_lower = user_message.lower()
    
    # Telefon haqida
    if "telefon" in user_lower:
        return "Telefon 1876 yilda Alexander Graham Bell tomonidan ixtiro qilindi."
    
    # Python haqida
    elif "python" in user_lower:
        return "Python - 1991 yilda yaratilgan dasturlash tili. Oddiy va kuchli."
    
    # Jahon urushi
    elif "jahon urushi" in user_lower:
        return "1-jahon urushi: 1914-1918\n2-jahon urushi: 1939-1945"
    
    # Matematika
    elif any(x in user_lower for x in ["2+2", "3*3", "5-1"]):
        return "2+2=4, 3*3=9, 5-1=4"
    
    # O'zbekiston
    elif "o'zbekiston" in user_lower:
        return "O'zbekiston - Markaziy Osiyoda. Poytaxti: Toshkent. Aholisi: 36 million."
    
    # Salom
    elif any(x in user_lower for x in ["salom", "hello", "hi"]):
        return "Assalomu alaykum! Men Erkinov AI Botman. Savolingizni yozing."
    
    # Kim yaratdi
    elif "kim yaratdi" in user_lower:
        return "Mehruzbek Erkinov"
    
    # Umumiy
    else:
        responses = [
            f"'{user_message}' haqida savol. Boshqa mavzu so'rang.",
            "Qiziq savol! Batafsilroq yozing.",
            "Kechirasiz, bu haqda ma'lumotim yo'q.",
            "Boshqa savol bering."
        ]
        return random.choice(responses)

# ================= BOT HANDLERS =================
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "🤖 <b>Erkinov AI Bot</b>\n\n"
        "🧠 Savollaringizga javob beraman!\n\n"
        "📍 /help - Yordam\n"
        "📍 /info - Bot haqida\n\n"
        "✅ Render.com da 24/7 online"
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(
        message,
        "🆘 <b>Yordam:</b>\n\n"
        "1. Savol yozing\n"
        "2. Men javob beraman\n"
        "3. /start - Boshlash\n"
        "4. /info - Ma'lumot\n\n"
        "Misollar:\n"
        "• Telefon haqida\n"
        "• Python nima?\n"
        "• O'zbekiston haqida"
    )

@bot.message_handler(commands=['info'])
def info_cmd(message):
    bot.reply_to(
        message,
        "📊 <b>Bot haqida:</b>\n\n"
        "🤖 Erkinov AI Bot\n"
        "👨‍💻 Yaratuvchi: Mehruzbek\n"
        "🌐 Hosting: Render.com\n"
        "⚡ Status: 24/7 Online\n"
        "🔗 @ErkinovAIBot"
    )

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if not message.text:
        return
    
    user_text = message.text.strip()
    
    # Typing effekt
    bot.send_chat_action(message.chat.id, 'typing')
    time.sleep(0.5)
    
    # AI javobi
    ai_response = get_ai_response(user_text)
    
    # Javob
    response = f"""
🧠 <b>AI Javobi:</b>

{ai_response}

━━━━━━━━━━━━━━
🤖 <b>Erkinov AI Bot</b>
✅ Render.com | 24/7 Online
    """
    
    bot.reply_to(message, response)

# ================= FLASK ROUTES =================
@app.route('/')
def home():
    return "🤖 Erkinov AI Bot - 24/7 Online"

@app.route('/health')
def health():
    return "OK", 200

# ================= MAIN =================
if __name__ == "__main__":
    # Logging
    logging.basicConfig(level=logging.INFO)
    
    print("="*50)
    print("🤖 ERKINOV AI BOT")
    print("✅ Simple Version")
    print("🌐 Webhook Mode")
    print("="*50)
    
    # Webhook
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
        print("✅ Webhook o'rnatildi")
    except Exception as e:
        print(f"⚠️ Webhook xatosi: {e}")
    
    # Server
    port = int(os.getenv("PORT", 10000))
    print(f"🚀 Server {port} portda ishga tushmoqda...")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
