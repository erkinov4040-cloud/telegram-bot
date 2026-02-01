#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import logging
import requests
import telebot
from flask import Flask, request
from PIL import Image
import tempfile
import subprocess

# Ovoz → matnga
import whisper

# Rasm → OCR
from pytesseract import image_to_string

# ================= CONFIG =================
TELEGRAM_TOKEN = "8236645335:AAG5paUC631oGqhUp_3zRLHYObQxH8CGgNc"
GROQ_API_KEY = "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"
ADMIN_ID = 7447606350

BOT_NAME = "Erkinov AI"
BOT_USERNAME = "@ErkinovAIBOT"
DEVELOPER = "Erkinov Mehruzbek"

MODEL = "llama-3.3-70b-versatile"
SYSTEM_PROMPT = "Siz professional AI assistantsiz. O'zbek tilida aniq va to'liq javob bering."

# ================= LOGGING =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ================= DATABASE =================
DB_FILE = "users.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "total_messages": 0}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def update_user(user_id):
    db = load_db()
    uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {"messages": 0, "last_seen": ""}
    db["users"][uid]["messages"] += 1
    db["users"][uid]["last_seen"] = time.strftime("%Y-%m-%d %H:%M:%S")
    db["total_messages"] += 1
    save_db(db)

# ================= BOT =================
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")
app = Flask(__name__)

# ================= GROQ AI =================
def ask_groq(question):
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        data = {
            "model": MODEL,
            "max_tokens": 2000,
            "temperature": 0.7,
            "top_p": 0.9,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question}
            ]
        }

        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                          headers=headers, json=data, timeout=30)

        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        return "⚠️ AI hozir javob bera olmadi."
    except Exception as e:
        logging.error(f"GROQ ERROR: {e}")
        return "❌ AI server bilan bog'lanishda xato yuz berdi."

# ================= START & HELP =================
@bot.message_handler(commands=['start'])
def start(msg):
    update_user(msg.from_user.id)
    text = f"""
<b>✨ {BOT_NAME}</b>

Salom! Men sizga savollar, tarjima, kod va AI maslahatlarida yordam bera olaman.

Savolingizni yozing 👇

━━━━━━━━━━━━━━
👨‍💻 Developer: <b>{DEVELOPER}</b>
"""
    bot.reply_to(msg, text)

@bot.message_handler(commands=['help'])
def help_cmd(msg):
    text = f"""
<b>ℹ️ Yordam ({BOT_NAME})</b>

━━━━━━━━━━━━━━
/start - Botni boshlash  
/help - Yordam  
/stats - Statistika  
/ping - Server holati  

🤖 AI savol berish uchun shunchaki matn yozing.
━━━━━━━━━━━━━━
"""
    bot.reply_to(msg, text)

@bot.message_handler(commands=['ping'])
def ping(msg):
    start = time.time()
    bot.send_chat_action(msg.chat.id, "typing")
    end = time.time()
    bot.reply_to(msg, f"🏓 Pong! {round((end-start)*1000)} ms")

@bot.message_handler(commands=['stats'])
def stats(msg):
    db = load_db()
    users = len(db["users"])
    total = db["total_messages"]
    text = f"""
<b>📊 Bot Statistikasi</b>

━━━━━━━━━━━━━━
👥 Foydalanuvchilar: <b>{users}</b>
💬 Jami xabarlar: <b>{total}</b>
━━━━━━━━━━━━━━
"""
    bot.reply_to(msg, text)

@bot.message_handler(commands=['admin'])
def admin_panel(msg):
    if msg.from_user.id != ADMIN_ID:
        return bot.reply_to(msg, "⛔ Siz admin emassiz!")
    db = load_db()
    text = f"""
<b>👑 ADMIN PANEL</b>

━━━━━━━━━━━━━━
👥 Users: {len(db["users"])}
💬 Messages: {db["total_messages"]}
━━━━━━━━━━━━━━
"""
    bot.reply_to(msg, text)

# ================= MEDIA HANDLER (Voice, Photo, Video) =================
@bot.message_handler(content_types=['voice', 'photo', 'video'])
def media_handler(msg):
    update_user(msg.from_user.id)
    bot.send_chat_action(msg.chat.id, "typing")

    text = ""

    # Ovozli habar
    if msg.content_type == "voice":
        file_info = bot.get_file(msg.voice.file_id)
        file_path = file_info.file_path
        downloaded_file = bot.download_file(file_path)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as f:
            f.write(downloaded_file)
            temp_path = f.name
        
        model = whisper.load_model("small")
        result = model.transcribe(temp_path)
        text = result["text"]

    # Rasmli habar
    elif msg.content_type == "photo":
        file_info = bot.get_file(msg.photo[-1].file_id)
        file_path = file_info.file_path
        downloaded_file = bot.download_file(file_path)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            f.write(downloaded_file)
            temp_path = f.name
        
        image = Image.open(temp_path)
        text = image_to_string(image, lang="eng")  # kerak bo'lsa 'uzb+eng'

    # Video habar
    elif msg.content_type == "video":
        file_info = bot.get_file(msg.video.file_id)
        file_path = file_info.file_path
        downloaded_file = bot.download_file(file_path)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
            f.write(downloaded_file)
            temp_path = f.name
        
        # Video dan audio ajratish
        audio_path = temp_path + ".wav"
        subprocess.run([
            "ffmpeg", "-y", "-i", temp_path,
            "-ar", "16000", "-ac", "1", "-vn", audio_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        # Whisper bilan transkript
        model = whisper.load_model("small")
        result = model.transcribe(audio_path)
        text = result["text"]

    # Agar matn bo‘lmasa
    if text.strip() == "":
        bot.send_message(msg.chat.id, "❌ Hech qanday matn topilmadi. Iltimos qayta yuboring.")
        return

    # AI javob
    answer = ask_groq(text)
    reply = f"""
{answer}

━━━━━━━━━━━━━━
🤖 {BOT_NAME} | {BOT_USERNAME}
"""
    bot.send_message(msg.chat.id, reply)

# ================= AI HANDLER (TEXT) =================
@bot.message_handler(content_types=['text'])
def ai_handler(msg):
    update_user(msg.from_user.id)
    bot.send_chat_action(msg.chat.id, "typing")

    logging.info(f"{msg.from_user.id}: {msg.text}")

    answer = ask_groq(msg.text)
    reply = f"""
{answer}

━━━━━━━━━━━━━━
🤖 {BOT_NAME} | {BOT_USERNAME}
"""
    bot.reply_to(msg, reply)

# ================= WEBHOOK =================
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
    return ""

@app.route("/")
def home():
    return "🤖 Erkinov AI ishlayapti!"

@app.route('/health')
def health():
    return "✅ OK", 200

# ================= RUN =================
if __name__ == "__main__":
    print("="*50)
    print("🤖 ERKINOV PROFESSIONAL AI BOT")
    print("🧠 GROQ Llama 3.3 70B")
    print("🌐 Webhook Mode + Voice, OCR, Video")
    print("="*50)
    
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
