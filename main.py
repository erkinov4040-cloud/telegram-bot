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
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "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")

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

# ================= AI FUNKSIYA (YANGILANGAN) =================
def get_ai_response(user_message):
    """OpenRouter API orqali AI javobi olish"""
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://t.me/ErkinovAIBot",
            "X-Title": "Erkinov AI Bot"
        }
        
        # ISHLASHI KAFOLATLANGAN MODEL
        payload = {
            "model": "google/gemini-2.0-flash-exp:free",  # ✅ Bepul va ishlaydi
            "messages": [
                {
                    "role": "system", 
                    "content": "Siz foydali va do'stona AI assistantsiz. O'zbek tilida aniq, tushunarli va foydali javob bering."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "max_tokens": 600,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            error_msg = f"API xatosi: {response.status_code}"
            logging.error(f"AI API xatosi: {error_msg}")
            
            # Oddiy javob qaytarish
            simple_responses = [
                "Kechirasiz, AI hozircha javob bera olmaydi. Qisqa savol bering.",
                "Texnik xato. Iltimos, savolingizni qayta yozing.",
                "AI tizimida muammo. Tez orada tuzatiladi."
            ]
            return random.choice(simple_responses)
            
    except requests.exceptions.Timeout:
        return "Javob kutish vaqti oshib ketdi. Iltimos, qisqa savol bering."
    except Exception as e:
        logging.error(f"AI xatosi: {str(e)}")
        return "Texnik xato yuz berdi. Keyinroq urinib ko'ring."

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
        "🎯 <i>Men OpenRouter AI bilan ishlayman!</i>\n\n"
        "📝 <b>Savolingizni yozing:</b>\n"
        "• Dasturlash\n"
        "• Matematika\n"
        "• Tarix\n"
        "• Yoki istalgan mavzu\n\n"
        "📍 /help - Yordam\n"
        "📍 /info - Bot haqida\n\n"
        "✅ <i>Render.com da 24/7 online</i>"
    )

# ================= HELP =================
@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(
        message,
        "🆘 <b>Yordam:</b>\n\n"
        "1. Faqat savol yozing - AI javob beradi\n"
        "2. /start - Boshlash\n"
        "3. /info - Bot haqida\n"
        "4. /ping - Bot faolligini tekshirish\n\n"
        "🤖 <i>AI Model: Gemini 2.0 Flash</i>"
    )

# ================= INFO =================
@bot.message_handler(commands=['info', 'about'])
def info_cmd(message):
    bot.reply_to(
        message,
        "📊 <b>Bot haqida:</b>\n\n"
        "🤖 <b>Erkinov AI Bot</b>\n"
        "👨‍💻 Yaratuvchi: Mehruzbek Erkinov\n"
        "🌐 Hosting: Render.com\n"
        "⚡ Status: 24/7 Online\n"
        "🧠 AI: OpenRouter + Gemini 2.0\n"
        "🔗 Link: @ErkinovAIBot\n\n"
        "✅ <i>Barcha savollaringizga javob beraman!</i>"
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
        f"⚡ Holat: Online 24/7"
    )

# ================= ASOSIY HANDLER (AI JAVOB) =================
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if not message.text:
        return
    
    user_text = message.text.strip()
    
    # Maxsus so'zlar
    text_lower = user_text.lower()
    
    if any(x in text_lower for x in ["salom", "hello", "hi", "assalom"]):
        bot.reply_to(message, "👋 Salom! Savolingizni yozing, men AI yordamida javob beraman.")
        return
    
    if any(x in text_lower for x in ["kim yaratdi", "yaratuvchi", "developer", "kim qildi"]):
        bot.reply_to(message, "🤖 Bu bot Mehruzbek Erkinov tomonidan yaratilgan.")
        return
    
    if any(x in text_lower for x in ["rahmat", "thanks", "thank you", "tashakkur"]):
        bot.reply_to(message, "❤️ Sizga ham rahmat! Yana savolingiz bo'lsa yozing.")
        return
    
    # Typing effekti
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Kutish xabarini yuborish
    wait_msg = bot.reply_to(message, "⏳ <i>AI javob tayyorlanmoqda...</i>")
    
    try:
        # AI javobi
        ai_response = get_ai_response(user_text)
        
        # Kutish xabarini o'chirish
        try:
            bot.delete_message(message.chat.id, wait_msg.message_id)
        except:
            pass
        
        # Sticker
        try:
            bot.send_sticker(message.chat.id, random.choice(STICKERS))
        except:
            pass
        
        # Chiroyli formatdagi javob
        formatted_response = f"""
🧠 <b>AI Javobi:</b>

{ai_response}

━━━━━━━━━━━━━━
🤖 <b>Erkinov AI</b> | @ErkinovAIBot
        """
        
        bot.reply_to(message, formatted_response)
        
    except Exception as e:
        logging.error(f"Xatolik: {str(e)}")
        bot.reply_to(message, "❌ Kechirasiz, xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")

# ================= FLASK ROUTES =================
@app.route('/')
def home():
    return "🤖 Erkinov AI Bot - OpenRouter AI bilan ishlaydi!"

@app.route('/health')
def health():
    return "✅ OK - Bot va AI faol", 200

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
    # Logging sozlash
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("====================================")
    print("🤖 ERKINOV AI BOT - RENDER.COM")
    print("🧠 AI: OpenRouter + Gemini 2.0 Flash")
    print("🌐 Webhook Mode: Active")
    print("====================================")
    
    # Webhook ni o'rnatish
    try:
        print("📡 Webhook o'rnatilmoqda...")
        bot.remove_webhook()
        time.sleep(2)
        bot.set_webhook(url=WEBHOOK_URL)
        print(f"✅ Webhook o'rnatildi: {WEBHOOK_URL}")
    except Exception as e:
        print(f"⚠️ Webhook xatosi: {e}")
    
    # Server port
    port = int(os.getenv("PORT", 10000))
    
    # Flask server
    print(f"🚀 Server {port} portda ishga tushmoqda...")
    app.run(host='0.0.0.0', port=port, debug=False)
