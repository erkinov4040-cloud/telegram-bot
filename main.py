#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import telebot
import requests
import time
from flask import Flask, request

# Tokenlar
TELEGRAM_TOKEN = "8236645335:AAG5paUC631oGqhUp_3zRLHYObQxH8CGgNc"
DEEPSEEK_API_KEY = "sk-24c2bf32a64a44bc831ce8137edbf58c"

# Bot yaratish
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")

# Flask app
app = Flask(__name__)

# DeepSeek AI
def ask_deepseek(question):
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "O'zbek tilida javob ber."},
                {"role": "user", "content": question}
            ],
            "max_tokens": 1000
        }
        
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            return f"Xato: {response.status_code}"
            
    except Exception as e:
        return f"Xato: {str(e)}"

# Bot handlers
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🤖 Salom! Men DeepSeek AI botman. Savolingizni yozing.")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, "🆗 Faqat savol yozing, men javob beraman.")

# Barcha xabarlar
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if not message.text:
        return
    
    # Typing effekt
    bot.send_chat_action(message.chat.id, 'typing')
    
    # AI javobi
    ai_answer = ask_deepseek(message.text)
    
    # Javob berish
    response = f"""
🧠 AI Javobi:

{ai_answer}

━━━━━━━━━━━━━━
🤖 DeepSeek AI Bot
    """
    
    bot.reply_to(message, response)

# Webhook
@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'OK'

@app.route('/')
def home():
    return "🤖 DeepSeek AI Bot ishlayapti!"

# Ishga tushirish
if __name__ == "__main__":
    print("🤖 Bot ishga tushmoqda...")
    
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
