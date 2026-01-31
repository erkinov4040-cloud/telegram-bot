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

# ================= WEBHOOK (409 xatosini oldini olish) =================
# Botni polling emas, webhook rejimida ishlatish
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
        "✅ <i>Bot Render.com da ishlayapti!</i>\n"
        "📍 24/7 online\n"
        "📍 Webhook rejimi\n\n"
        "Savol yozing yoki /help"
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, "📝 Faqat savol yozing, men javob beraman!")

# ================= ASOSIY HANDLER =================
@bot.message_handler(func=lambda m: True)
def handle(m):
    if not m.text:
        return
    
    text = m.text.lower()
    
    if any(x in text for x in ["salom", "hello", "hi"]):
        bot.reply_to(m, "👋 Salom! Savolingizni yozing.")
        return
    
    if any(x in text for x in ["kim yaratdi", "developer"]):
        bot.reply_to(m, "🤖 Mehruzbek Erkinov")
        return
    
    # Echo response
    bot.reply_to(m, f"📨 Siz: <b>{m.text}</b>\n\n✅ Bot Render.com da ishlayapti!")

# ================= FLASK ROUTES =================
@app.route('/')
def home():
    return "🤖 Erkinov Bot - Webhook rejimida ishlayapti!"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/setwebhook')
def set_webhook():
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
        return f"✅ Webhook o'rnatildi: {WEBHOOK_URL}"
    except Exception as e:
        return f"❌ Xato: {str(e)}"

@app.route('/removewebhook')
def remove_webhook():
    try:
        bot.remove_webhook()
        return "✅ Webhook o'chirildi"
    except Exception as e:
        return f"❌ Xato: {str(e)}"

# ================= MAIN =================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("====================================")
    print("🤖 ERKINOV BOT - WEBHOOK MODE")
    print("====================================")
    
    # Portni olish
    port = int(os.getenv("PORT", 10000))
    
    # Webhook ni o'rnatish
    try:
        print("📡 Webhook o'rnatilmoqda...")
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
        print(f"✅ Webhook o'rnatildi: {WEBHOOK_URL}")
    except Exception as e:
        print(f"⚠️ Webhook xatosi: {e}")
        print("ℹ️ Polling rejimiga o'tiladi...")
    
    # Flask server
    print(f"🚀 Server {port} portda ishga tushmoqda...")
    app.run(host='0.0.0.0', port=port, debug=False)
