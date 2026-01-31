#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot
import requests
import time

# 🔑 GROQ API KEY
TELEGRAM_TOKEN = "8236645335:AAG5paUC631oGqhUp_3zRLHYObQxH8CGgNc"
GROQ_API_KEY = "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"

# Bot yaratish
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")

# Groq AI - 100% BEPUL!
def ask_groq(question):
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system", 
                    "content": "Siz foydali va do'stona AI assistantsiz. O'zbek tilida aniq va tushunarli javob bering."
                },
                {"role": "user", "content": question}
            ],
            "max_tokens": 1500,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=25
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        elif response.status_code == 401:
            return "❌ GROQ API key noto'g'ri."
        elif response.status_code == 429:
            return "⚠️ Kunlik limit tugadi. Ertaga qayta urinib ko'ring."
        else:
            return f"❌ Xato kodi: {response.status_code}"
            
    except Exception as e:
        return f"❌ Xato: {str(e)}"

# Bot handlers
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 
        "🤖 <b>Erkinov AI Bot</b>\n\n"
        "✨ Sun’iy intellekt yordamchisi (Llama 3.3 70B)\n\n"
        "Savolingizni yozing, men javob beraman.\n\n"
        "📌 /help - Yordam\n"
        "📌 /info - Bot haqida\n"
        "📌 /groq - AI haqida\n\n"
        "🟢 Status: 24/7 Online"
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message,
        "🆘 <b>Yordam menyusi:</b>\n\n"
        "✍️ Savol yozing — AI javob beradi\n"
        "🔄 /start - Botni qayta ishga tushirish\n"
        "ℹ️ /info - Bot haqida ma’lumot\n\n"
        "⚡ Juda tez va bepul AI xizmati"
    )

@bot.message_handler(commands=['info'])
def info_cmd(message):
    bot.reply_to(message,
        "📊 <b>Bot haqida:</b>\n\n"
        "🤖 Nomi: Erkinov AI Bot\n"
        "👨‍💻 Yaratuvchi: Mehruzbek Erkinov\n"
        "🌐 Hosting: Render.com\n"
        "🟢 Holat: 24/7 Online\n"
        "✨ AI: GROQ Llama 3.3 70B\n"
        "💰 Narx: Bepul\n"
        "🔗 Telegram: @ErkinovAIBot"
    )

@bot.message_handler(commands=['groq'])
def groq_cmd(message):
    bot.reply_to(message,
        "🚀 <b>GROQ AI:</b>\n\n"
        "• Model: Llama 3.3 70B\n"
        "• Tezlik: Juda tez (GPU superchip)\n"
        "• Limit: Kunlik bepul tokenlar\n"
        "• Til: O‘zbekcha qo‘llab-quvvatlanadi\n"
        "• Narx: 100% bepul\n"
        "• Sayt: console.groq.com"
    )

# Barcha xabarlar
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if not message.text:
        return
    
    bot.send_chat_action(message.chat.id, 'typing')
    
    ai_answer = ask_groq(message.text)
    
    response = f"""
✨ <b>AI Javobi:</b>

{ai_answer}

━━━━━━━━━━━━━━━━━━
🤖 <b>Erkinov AI Bot</b>
✨ GROQ | Llama 3.3 70B
🟢 24/7 Online • 💰 Bepul
    """
    
    bot.reply_to(message, response)

# Ishga tushirish
print("="*55)
print("🤖 ERKINOV AI BOT ISHGA TUSHDI")
print("✨ Model: Llama 3.3 70B")
print("🟢 Status: Online")
print("💰 100% BEPUL")
print("="*55)

while True:
    try:
        bot.polling(none_stop=True, timeout=30)
    except Exception as e:
        print(f"❌ Xato: {e}")
        time.sleep(5)
