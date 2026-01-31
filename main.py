#!/usr/bin/env python3

import os
import telebot
import requests
import time
from flask import Flask, request

# Tokenlar
TELEGRAM_TOKEN = "8236645335:AAG5paUC631oGqhUp_3zRLHYObQxH8CGgNc"
GROQ_API_KEY = "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"

# Bot
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")
app = Flask(__name__)

# AI
def ask_groq(question):
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "O'zbek tilida javob ber."},
                {"role": "user", "content": question}
            ]
        }
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=20
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        return "AI javob bera olmadi."
    except:
        return "Xato yuz berdi."

# Handlers
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🤖 Salom! Savolingizni yozing.")

@bot.message_handler(func=lambda m: True)
def handle(message):
    bot.send_chat_action(message.chat.id, 'typing')
    answer = ask_groq(message.text)
    bot.reply_to(message, answer)

# Webhook
@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return ''

@app.route('/')
def home():
    return "🤖 Bot ishlayapti!"

# Run
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
