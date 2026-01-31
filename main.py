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

# ================= TOKENLAR (Environment variables) =================
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN", "8236645335:AAG5paUC631oGqhUp_3zRLHYObQxH8CGgNc")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "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")

# HTML MODE
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")

# Flask app for Render.com
app = Flask(__name__)

# ================= STICKERS =================
STICKERS = [
    "CAACAgIAAxkBAAIBjGbC_V8NRhS2ObgABqYmRf38GILucgAC_hcAAu9pOUqS7VEEVhLQQzQE",
    "CAACAgIAAxkBAAIBjWbC_WBri-ocw3D_nODoxYHt8QzTAAKvGwACgmcAAUoI1hTx2ZR8vTQE",
]

# ================= AI FUNKSIYA =================
def get_ai_response(text):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://telegram.org",
            "X-Title": "Erkinov AI Bot"
        }

        payload = {
            "model": "meta-llama/llama-3.1-8b-instruct",
            "messages": [
                {"role": "system", "content": "O'zbek tilida aniq, tartiblangan va chiroyli javob ber."},
                {"role": "user", "content": text}
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }

        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=20
        )

        if r.status_code != 200:
            return "AI hozir javob bera olmadi."

        return r.json()["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("AI ERROR:", e)
        return "Texnik xato yuz berdi."

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    try:
        bot.send_sticker(message.chat.id, random.choice(STICKERS))
    except:
        pass

    bot.send_message(
        message.chat.id,
        "<b>👋 Salom!</b>\n\nSavolingizni yozing, men javob beraman.\n\n🤖 <i>Men Render.com da 24/7 ishlayman!</i>"
    )

# ================= ASOSIY HANDLER =================
@bot.message_handler(func=lambda m: True)
def handle(m):
    if not m.text:
        return

    text = m.text.lower()

    # Kim yaratdi savoli
    if any(x in text for x in ["kim yaratdi", "yaratuvchi", "seni kim", "kim qildi"]):
        bot.send_message(m.chat.id, "🤖 Bu bot Mehruzbek Erkinov tomonidan yaratilgan.")
        return

    # Typing effekt
    bot.send_chat_action(m.chat.id, "typing")
    wait = bot.send_message(m.chat.id, "⏳ Javob tayyorlanmoqda...")

    ai = get_ai_response(m.text)

    # Kutish xabarini o'chirish
    try:
        bot.delete_message(m.chat.id, wait.message_id)
    except:
        pass

    # Sticker
    try:
        bot.send_sticker(m.chat.id, random.choice(STICKERS))
    except:
        pass

    # ================= CHIROYLI FINAL JAVOB =================
    final_answer = f"""
<b>🧠 Javob:</b>

{ai}

━━━━━━━━━━━━━━
🤖 <b>Erkinov AI</b> | <a href="https://t.me/ErkinovAIBot">@ErkinovAIBot</a>
"""

    bot.send_message(m.chat.id, final_answer)

# ================= FLASK ROUTES (Render.com uchun majburiy) =================
@app.route('/')
def home():
    return "🤖 Erkinov AI Bot ishlayapti! Render.com da 24/7 online"

@app.route('/health')
def health_check():
    return "OK", 200

@app.route('/status')
def status():
    return "Bot faol ✅", 200

# ================= BOT POLLING =================
def run_telegram_bot():
    logging.info("🤖 Telegram Bot ishga tushmoqda...")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            logging.error(f"❌ Bot xatosi: {e}")
            logging.info("⏳ 5 soniyadan keyin qayta uriniladi...")
            time.sleep(5)

# ================= RUN =================
if __name__ == "__main__":
    # Logging sozlash
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("====================================")
    print("🤖 ERKINOV AI BOT ISHGA TUSHDI")
    print("🤖 Render.com da 24/7 online")
    print("====================================")
    
    # Botni alohida threadda ishga tushirish
    bot_thread = Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    # Flask serverni ishga tushirish (Render uchun)
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
