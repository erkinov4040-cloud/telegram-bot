#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import telebot
import requests
import time
from flask import Flask, request

# 🔑 TOKENLAR
TELEGRAM_TOKEN = "8236645335:AAG5paUC631oGqhUp_3zRLHYObQxH8CGgNc"
GROQ_API_KEY = "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"

# Bot yaratish
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")

# Flask app
app = Flask(__name__)

# Groq AI
def ask_groq(question):
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "O'zbek tilida javob ber."},
                {"role": "user", "content": question}
            ],
            "max_tokens": 1000
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=20
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            return f"AI javob bera olmadi. Xato: {response.status_code}"
            
    except Exception as e:
        return f"Xato: {str(e)}"

# Bot handlers
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 
        "🤖 <b>Erkinov AI Bot</b>\n\n"
        "Savolingizni yozing, men javob beraman.\n\n"
        "✅ GROQ AI | 100% Bepul\n"
        "✅ Render.com | 24/7 Online"
    )

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if not message.text:
        return
    
    bot.send_chat_action(message.chat.id, 'typing')
    ai_answer = ask_groq(message.text)
    bot.reply_to(message, ai_answer)

# Webhook
@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK'
    return 'Bad request', 400

@app.route('/')
def home():
    return "🤖 Erkinov AI Bot ishlayapti!"

# Ishga tushirish
if __name__ == "__main__":
    print("🤖 Bot ishga tushmoqda...")
    
    # Webhook ni o'rnatish
    try:
        # Avval o'chirish
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook")
        time.sleep(1)
        
        # Yangi o'rnatish
        webhook_url = f"https://erkinov-ai-bot.onrender.com/{TELEGRAM_TOKEN}"
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={webhook_url}")
        print(f"✅ Webhook: {webhook_url}")
    except:
        print("⚠️ Webhook xatosi")
    
    # Server
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
