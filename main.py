#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import telebot
import requests
import random
import time
import logging
import json
from datetime import datetime
from flask import Flask, request
from threading import Thread, Lock
from queue import Queue
import hashlib
import sqlite3
import threading

# ================= KONFIGURATSIYA =================
class Config:
    # Telegram Token
    TELEGRAM_TOKEN = os.getenv("BOT_TOKEN", "8236645335:AAG5paUC631oGqhUp_3zRLHYObQxH8CGgNc")
    
    # 3 TA BEPUL AI API KEY LAR
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    
    # Webhook URL
    WEBHOOK_URL = f"https://erkinov-ai-bot.onrender.com/{TELEGRAM_TOKEN}"
    
    # Database fayli
    DB_FILE = "bot_database.db"
    
    # AI Model ro'yxati
    AI_MODELS = {
        "groq": {
            "name": "GROQ Llama 3.3",
            "url": "https://api.groq.com/openai/v1/chat/completions",
            "model": "llama-3.3-70b-versatile",
            "speed": "very_fast",
            "free": True
        },
        "deepseek": {
            "name": "DeepSeek Chat",
            "url": "https://api.deepseek.com/chat/completions",
            "model": "deepseek-chat",
            "speed": "fast",
            "free": True
        },
        "openrouter": {
            "name": "OpenRouter Gemma",
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "model": "google/gemma-2-9b-it:free",
            "speed": "medium",
            "free": True
        }
    }

# ================= INITSIALIZATSIYA =================
bot = telebot.TeleBot(Config.TELEGRAM_TOKEN, parse_mode="HTML")
app = Flask(__name__)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database
db_lock = Lock()

# ================= DATABASE =================
def init_database():
    """Database ni yaratish"""
    with db_lock:
        conn = sqlite3.connect(Config.DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        # Foydalanuvchilar jadvali
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0,
                last_active TIMESTAMP
            )
        ''')
        
        # Xabarlar jadvali
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message_text TEXT,
                ai_response TEXT,
                ai_model TEXT,
                response_time REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # AI Stats jadvali
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_stats (
                model_name TEXT PRIMARY KEY,
                total_requests INTEGER DEFAULT 0,
                success_requests INTEGER DEFAULT 0,
                avg_response_time REAL DEFAULT 0,
                last_used TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    logger.info("Database initialized successfully")

def update_user_stats(user_id, username, first_name, last_name, language_code):
    """Foydalanuvchi statistikasini yangilash"""
    with db_lock:
        conn = sqlite3.connect(Config.DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, language_code, last_active, message_count)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 
                    COALESCE((SELECT message_count FROM users WHERE user_id = ?), 0) + 1)
        ''', (user_id, username, first_name, last_name, language_code, user_id))
        
        conn.commit()
        conn.close()

def save_message(user_id, message_text, ai_response, ai_model, response_time):
    """Xabarni databazaga saqlash"""
    with db_lock:
        conn = sqlite3.connect(Config.DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO messages 
            (user_id, message_text, ai_response, ai_model, response_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, message_text, ai_response, ai_model, response_time))
        
        # AI stats yangilash
        cursor.execute('''
            INSERT OR REPLACE INTO ai_stats 
            (model_name, total_requests, success_requests, avg_response_time, last_used)
            VALUES (?,
                    COALESCE((SELECT total_requests FROM ai_stats WHERE model_name = ?), 0) + 1,
                    COALESCE((SELECT success_requests FROM ai_stats WHERE model_name = ?), 0) + 1,
                    (COALESCE((SELECT avg_response_time FROM ai_stats WHERE model_name = ?), 0) * 
                     COALESCE((SELECT total_requests FROM ai_stats WHERE model_name = ?), 0) + ?) / 
                    (COALESCE((SELECT total_requests FROM ai_stats WHERE model_name = ?), 0) + 1),
                    CURRENT_TIMESTAMP)
        ''', (ai_model, ai_model, ai_model, ai_model, ai_model, response_time, ai_model))
        
        conn.commit()
        conn.close()

# ================= AI ENGINE - ASOSIY QISMI =================
class AIEngine:
    """Intelligent AI engine - 3 ta AI dan eng yaxshisini tanlaydi"""
    
    def __init__(self):
        self.available_models = []
        self.check_available_models()
        
    def check_available_models(self):
        """Mavjud AI modellarini tekshirish"""
        self.available_models = []
        
        # GROQ ni tekshirish
        if Config.GROQ_API_KEY and len(Config.GROQ_API_KEY) > 10:
            self.available_models.append("groq")
            logger.info("✅ GROQ AI mavjud")
        
        # DeepSeek ni tekshirish
        if Config.DEEPSEEK_API_KEY and len(Config.DEEPSEEK_API_KEY) > 10:
            self.available_models.append("deepseek")
            logger.info("✅ DeepSeek AI mavjud")
        
        # OpenRouter ni tekshirish
        if Config.OPENROUTER_API_KEY and len(Config.OPENROUTER_API_KEY) > 10:
            self.available_models.append("openrouter")
            logger.info("✅ OpenRouter AI mavjud")
        
        if not self.available_models:
            logger.warning("⚠️ Hech qanday AI API key topilmadi. Local rejimda ishlaydi.")
        
        return self.available_models
    
    def get_best_model(self):
        """Eng yaxshi modelni tanlash"""
        if not self.available_models:
            return None
        
        # Avval GROQ, keyin DeepSeek, keyin OpenRouter
        preferred_order = ["groq", "deepseek", "openrouter"]
        
        for model in preferred_order:
            if model in self.available_models:
                return model
        
        return self.available_models[0]
    
    def call_groq_ai(self, prompt):
        """GROQ AI ga so'rov yuborish"""
        try:
            headers = {
                "Authorization": f"Bearer {Config.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": Config.AI_MODELS["groq"]["model"],
                "messages": [
                    {
                        "role": "system",
                        "content": """Siz Erkinov AI Bot - foydali va do'stona assistantsiz. 
                        O'zbek tilida aniq, to'liq va chiroyli javob bering. 
                        Javob uzunligi 100-500 so'z oralig'ida bo'lsin."""
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1500,
                "top_p": 0.9
            }
            
            start_time = time.time()
            response = requests.post(
                Config.AI_MODELS["groq"]["url"],
                headers=headers,
                json=payload,
                timeout=15
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "response": result["choices"][0]["message"]["content"].strip(),
                    "model": "groq",
                    "response_time": response_time
                }
            else:
                return {
                    "success": False,
                    "error": f"GROQ API xatosi: {response.status_code}",
                    "response_time": response_time
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"GROQ xatosi: {str(e)}",
                "response_time": 0
            }
    
    def call_deepseek_ai(self, prompt):
        """DeepSeek AI ga so'rov yuborish"""
        try:
            headers = {
                "Authorization": f"Bearer {Config.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": Config.AI_MODELS["deepseek"]["model"],
                "messages": [
                    {
                        "role": "system",
                        "content": "O'zbek tilida sifatli va to'liq javob bering."
                    },
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            start_time = time.time()
            response = requests.post(
                Config.AI_MODELS["deepseek"]["url"],
                headers=headers,
                json=payload,
                timeout=20
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "response": result["choices"][0]["message"]["content"].strip(),
                    "model": "deepseek",
                    "response_time": response_time
                }
            else:
                return {
                    "success": False,
                    "error": f"DeepSeek API xatosi: {response.status_code}",
                    "response_time": response_time
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"DeepSeek xatosi: {str(e)}",
                "response_time": 0
            }
    
    def call_openrouter_ai(self, prompt):
        """OpenRouter AI ga so'rov yuborish"""
        try:
            headers = {
                "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://t.me/ErkinovAIBot",
                "X-Title": "Erkinov AI Bot"
            }
            
            payload = {
                "model": Config.AI_MODELS["openrouter"]["model"],
                "messages": [
                    {
                        "role": "system",
                        "content": "O'zbek tilida javob bering."
                    },
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000
            }
            
            start_time = time.time()
            response = requests.post(
                Config.AI_MODELS["openrouter"]["url"],
                headers=headers,
                json=payload,
                timeout=25
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "response": result["choices"][0]["message"]["content"].strip(),
                    "model": "openrouter",
                    "response_time": response_time
                }
            else:
                return {
                    "success": False,
                    "error": f"OpenRouter API xatosi: {response.status_code}",
                    "response_time": response_time
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"OpenRouter xatosi: {str(e)}",
                "response_time": 0
            }
    
    def call_local_ai(self, prompt):
        """Local AI - API kerak emas"""
        prompt_lower = prompt.lower()
        
        # Knowledge base
        knowledge_base = {
            "telefon": "Telefon 1876 yilda Alexander Graham Bell tomonidan ixtiro qilindi. Birinchi telefon simli edi.",
            "python": "Python - 1991 yilda Guido van Rossum tomonidan yaratilgan. Oddiy, kuchli dasturlash tili. AI, veb, ma'lumotlar tahlili uchun.",
            "jahon urushi": "1-jahon urushi: 1914-1918\n2-jahon urushi: 1939-1945\nIkkinchi jahon urushi eng halokatli urush bo'ldi.",
            "o'zbekiston": "O'zbekiston - Markaziy Osiyoda joylashgan davlat. Poytaxti: Toshkent. Aholisi: 36 million. Mustaqillik: 1991 yil.",
            "dasturlash": "Dasturlash - kompyuterga vazifa bajarishni o'rgatish. Mashhur tillar: Python, JavaScript, Java, C++.",
            "internet": "Internet 1960-yillarda ARPANET sifatida boshlangan. WWW 1989 yilda Tim Berners-Lee tomonidan yaratilgan.",
            "ai": "AI (Sun'iy Intellekt) - mashinalarning inson kabi fikrlashi va qaror qabul qilishi. ChatGPT, Gemini kabi.",
            "render.com": "Render.com - bulut hosting platformasi. Python, Node.js, Docker ilovalari uchun. 750 soat/oy bepul."
        }
        
        # Savolni tahlil qilish
        response = None
        for keyword, answer in knowledge_base.items():
            if keyword in prompt_lower:
                response = answer
                break
        
        if not response:
            responses = [
                f"'{prompt}' haqida aniq ma'lumotim yo'q. Quyidagi mavzularda savol bering: telefon, python, jahon urushi, O'zbekiston, dasturlash.",
                f"Qiziq savol! '{prompt}' haqida ma'lumot to'plashim kerak.",
                f"Kechirasiz, bu mavzuda javob bera olmayman. Boshqa savol bering.",
                f"Bu mavzu murakkab. Soddaroq savol yozing."
            ]
            response = random.choice(responses)
        
        return {
            "success": True,
            "response": response,
            "model": "local",
            "response_time": 0.1
        }
    
    def get_ai_response(self, prompt):
        """Asosiy AI javobi olish funksiyasi"""
        start_time = time.time()
        
        # Avval best model orqali
        best_model = self.get_best_model()
        
        if best_model == "groq":
            result = self.call_groq_ai(prompt)
            if result["success"]:
                return result
            else:
                logger.warning(f"GROQ xatosi: {result.get('error')}")
        
        if best_model == "deepseek" or (best_model == "groq" and not result.get("success", False)):
            result = self.call_deepseek_ai(prompt)
            if result["success"]:
                return result
            else:
                logger.warning(f"DeepSeek xatosi: {result.get('error')}")
        
        if best_model == "openrouter" or not result.get("success", False):
            result = self.call_openrouter_ai(prompt)
            if result["success"]:
                return result
        
        # Agar barcha API lar ishlamasa, Local AI
        logger.info("Barcha API lar ishlamadi. Local AI ishlatiladi.")
        return self.call_local_ai(prompt)

# AI Engine ni yaratish
ai_engine = AIEngine()

# ================= TELEGRAM HANDLERS =================
@bot.message_handler(commands=['start', 'boshlash'])
def start_command(message):
    """Start komandasi"""
    user = message.from_user
    update_user_stats(user.id, user.username, user.first_name, user.last_name, user.language_code)
    
    welcome_text = f"""
✨ <b>Assalomu alaykum, {user.first_name}!</b> ✨

🤖 <b>Erkinov Professional AI Bot</b> ga xush kelibsiz!

🚀 <b>Men quyidagi AI lar bilan ishlayman:</b>
{'✅ GROQ AI (Llama 3.3 - Eng tez)' if 'groq' in ai_engine.available_models else '❌ GROQ AI (Key kiritilmagan)'}
{'✅ DeepSeek AI' if 'deepseek' in ai_engine.available_models else '❌ DeepSeek AI (Key kiritilmagan)'}
{'✅ OpenRouter AI' if 'openrouter' in ai_engine.available_models else '❌ OpenRouter AI (Key kiritilmagan)'}
✅ Local AI (Har doim mavjud)

📝 <b>Savol misollari:</b>
• Telefon qachon ixtiro qilindi?
• Python dasturlash tili haqida
• O'zbekistonning poytaxti qayerda?
• 2-jahon urushi haqida ma'lumot

🔧 <b>Buyruqlar:</b>
/help - Yordam
/stats - Statistika
/models - AI modellar
/apikey - API key qo'shish

🌐 <b>Hosting:</b> Render.com (24/7 Online)
🧠 <b>AI Engine:</b> Professional Multi-AI System

<i>Faqat savolingizni yozing va javob oling!</i>
    """
    
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['help', 'yordam'])
def help_command(message):
    """Yordam komandasi"""
    help_text = """
🆘 <b>YORDAM VA QO'LLANMA</b>

📝 <b>Foydalanish:</b>
1. Oddiy savol yozing (masalan: "Python nima?")
2. Bot avtomatik eng yaxshi AI dan javob oladi
3. Savol aniq va to'liq bo'lishi kerak

🔧 <b>Buyruqlar:</b>
/start - Botni ishga tushirish
/stats - Foydalanuvchi statistikasi
/models - Mavjud AI modellar
/apikey - API key qo'shish
/status - Bot holati
/ping - Server tekshiruvi

🧠 <b>AI Modellar:</b>
• GROQ AI - Eng tez va aqlli
• DeepSeek AI - Chuqur javoblar
• OpenRouter AI - Turli modellar
• Local AI - API kerak emas

🔑 <b>API Key Olish:</b>
1. /apikey buyrug'ini yuboring
2. Ko'rsatilgan saytga o'ting
3. API key oling
4. Render.com da Environment ga qo'shing

📊 <b>Statistika:</b>
• Har bir javob vaqt o'lchanadi
• AI modellar samaradorligi kuzatiladi
• Foydalanuvchi faolligi saqlanadi

🌐 <b>Texnik ma'lumot:</b>
• Hosting: Render.com
• Doimiy online: 24/7
• Kod: Python 3.13
• Framework: Flask + pyTelegramBotAPI

<i>Savolingiz bo'lsa, bemalol so'rang!</i>
    """
    
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['stats', 'statistika'])
def stats_command(message):
    """Statistika komandasi"""
    user_id = message.from_user.id
    
    with db_lock:
        conn = sqlite3.connect(Config.DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        # Foydalanuvchi statistikasi
        cursor.execute('''
            SELECT message_count, last_active FROM users WHERE user_id = ?
        ''', (user_id,))
        user_stats = cursor.fetchone()
        
        # AI statistikasi
        cursor.execute('''
            SELECT model_name, total_requests, success_requests, avg_response_time 
            FROM ai_stats ORDER BY total_requests DESC
        ''')
        ai_stats = cursor.fetchall()
        
        # Umumiy statistika
        cursor.execute('SELECT COUNT(*) FROM messages')
        total_messages = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM users')
        total_users = cursor.fetchone()[0]
        
        conn.close()
    
    if user_stats:
        message_count, last_active = user_stats
        
        stats_text = f"""
📊 <b>BOT STATISTIKASI</b>

👤 <b>Shaxsiy statistika:</b>
• Xabarlar soni: <code>{message_count}</code>
• So'nggi faollik: <code>{last_active}</code>

🤖 <b>AI Modellar statistika:</b>
"""
        
        for model in ai_stats:
            model_name, total_req, success_req, avg_time = model
            success_rate = (success_req / total_req * 100) if total_req > 0 else 0
            
            stats_text += f"""
• <b>{model_name.upper()}:</b>
  - So'rovlar: {total_req}
  - Muvaffaqiyat: {success_rate:.1f}%
  - O'rtacha vaqt: {avg_time:.2f}s
"""
        
        stats_text += f"""
🌐 <b>Umumiy statistika:</b>
• Jami xabarlar: <code>{total_messages}</code>
• Jami foydalanuvchilar: <code>{total_users}</code>
• Faol AI modellar: <code>{len(ai_engine.available_models)}</code>
"""
        
        bot.reply_to(message, stats_text)
    else:
        bot.reply_to(message, "📊 Statistika topilmadi. Bir necha xabar yuboring.")

@bot.message_handler(commands=['models', 'modellar'])
def models_command(message):
    """AI modellar haqida ma'lumot"""
    models_text = """
🧠 <b>MAVJUD AI MODELLAR</b>

"""
    
    for model_id, model_info in Config.AI_MODELS.items():
        is_available = model_id in ai_engine.available_models
        
        models_text += f"""
{'✅' if is_available else '❌'} <b>{model_info['name']}</b>
• Model: <code>{model_info['model']}</code>
• Tezlik: {model_info['speed']}
• Status: {'<b>FAOL</b>' if is_available else 'Nofaol'}
• Narx: {'100% BEPUL' if model_info['free'] else 'To\'lovli'}
"""
    
    models_text += f"""
    
🔧 <b>Joriy holat:</b>
• Tanlangan model: <code>{ai_engine.get_best_model() or 'local'}</code>
• Mavjud modellar: {len(ai_engine.available_models)}
• Zaxira modellar: {len(Config.AI_MODELS) - len(ai_engine.available_models)}

<i>Bot avtomatik eng yaxshi modelni tanlaydi.</i>
"""
    
    bot.reply_to(message, models_text)

@bot.message_handler(commands=['apikey'])
def apikey_command(message):
    """API key qo'shish yo'riqnomasi"""
    apikey_text = """
🔑 <b>API KEY QO'SHISH YO'RIQNOMASI</b>

🚀 <b>1. GROQ API Key (Tavsiya etiladi):</b>
1. <a href="https://console.groq.com">console.groq.com</a> ga o'ting
2. Google hisobi bilan login qiling
3. "API Keys" → "Create new key"
4. Key ni nusxalang
5. Render.com → Environment → GROQ_API_KEY

🌌 <b>2. DeepSeek API Key:</b>
1. <a href="https://platform.deepseek.com/api_keys">platform.deepseek.com/api_keys</a>
2. Hisob oching
3. API key yarating
4. Render.com → Environment → DEEPSEEK_API_KEY

🔄 <b>3. OpenRouter API Key:</b>
1. <a href="https://openrouter.ai/keys">openrouter.ai/keys</a>
2. Hisob oching
3. Key yarating
4. Render.com → Environment → OPENROUTER_API_KEY

📝 <b>Render.com da qo'shish:</b>
1. render.com dashboard ga o'ting
2. erkinov-ai-bot serviceni tanlang
3. "Environment" bo'limiga o'ting
4. "Add Environment Variable" bosing
5. Key va Value ni kiriting
6. "Save Changes" bosing
7. "Manual Deploy" → "Deploy latest commit"

💡 <b>Maslahat:</b>
• GROQ eng yaxshi variant (tez va bepul)
• Key larni hech kimga bermang
• Har safar yangilangandan keyin bot restart bo'ladi

<i>Key qo'shgach, /start buyrug'i bilan tekshiring.</i>
"""
    
    bot.reply_to(message, apikey_text, disable_web_page_preview=True)

@bot.message_handler(commands=['status', 'holat'])
def status_command(message):
    """Bot holati"""
    import psutil
    import datetime
    
    # System stats
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Bot stats
    current_time = datetime.datetime.now()
    uptime = current_time - start_time if 'start_time' in globals() else datetime.timedelta(0)
    
    status_text = f"""
⚡ <b>BOT HOLATI VA STATISTIKA</b>

🖥️ <b>Tizim resurslari:</b>
• CPU ishlatilishi: <code>{cpu_percent}%</code>
• Xotira ishlatilishi: <code>{memory.percent}%</code>
• Disk ishlatilishi: <code>{disk.percent}%</code>

🤖 <b>Bot statistikasi:</b>
• Ish vaqti: <code>{str(uptime).split('.')[0]}</code>
• Faol AI modellar: <code>{len(ai_engine.available_models)}</code>
• Eng yaxshi model: <code>{ai_engine.get_best_model() or 'local'}</code>
• Webhook: <code>{'✅ Faol' if Config.WEBHOOK_URL else '❌ Nofaol'}</code>

🌐 <b>Tarmoq:</b>
• Hosting: <code>Render.com</code>
• URL: <code>{Config.WEBHOOK_URL.split('/')[0] + '//' + Config.WEBHOOK_URL.split('/')[2]}</code>
• Port: <code>{os.getenv('PORT', '10000')}</code>

📊 <b>AI modellar holati:</b>
"""
    
    for model_id in Config.AI_MODELS:
        is_available = model_id in ai_engine.available_models
        status_text += f"• {Config.AI_MODELS[model_id]['name']}: {'🟢 Faol' if is_available else '🔴 Nofaol'}\n"
    
    status_text += "\n<i>Bot to'liq funksional va ishlamoqda!</i>"
    
    bot.reply_to(message, status_text)

@bot.message_handler(commands=['ping'])
def ping_command(message):
    """Ping test"""
    start_ping = time.time()
    msg = bot.reply_to(message, "🏓 <i>Ping o'lchanmoqda...</i>")
    end_ping = time.time()
    
    ping_time = (end_ping - start_ping) * 1000  # ms ga
    
    response_text = f"""
🏓 <b>Pong!</b>

⏱️ <b>Natijalar:</b>
• Bot javob vaqti: <code>{ping_time:.2f} ms</code>
• Server vaqti: <code>{datetime.datetime.now().strftime('%H:%M:%S')}</code>
• Server sanasi: <code>{datetime.datetime.now().strftime('%d.%m.%Y')}</code>

🌐 <b>Server:</b>
• Status: <code>🟢 Online</code>
• Uptime: <code>24/7</code>
• Hosting: <code>Render.com</code>

<i>Bot to'liq ishlamoqda va tezkor!</i>
"""
    
    bot.edit_message_text(
        response_text,
        chat_id=message.chat.id,
        message_id=msg.message_id
    )

# ================= ASOSIY HANDLER =================
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Barcha xabarlarni qayta ishlash"""
    if not message.text or message.text.startswith('/'):
        return
    
    user = message.from_user
    user_text = message.text.strip()
    
    # Foydalanuvchi statistikasini yangilash
    update_user_stats(
        user.id, 
        user.username, 
        user.first_name, 
        user.last_name, 
        user.language_code
    )
    
    # Typing effekt
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Kutish xabarini yuborish
    wait_msg = bot.reply_to(
        message, 
        f"⏳ <i>AI javob tayyorlanmoqda ({ai_engine.get_best_model() or 'local'})...</i>"
    )
    
    try:
        # AI javobini olish
        start_time = time.time()
        ai_result = ai_engine.get_ai_response(user_text)
        response_time = time.time() - start_time
        
        # Kutish xabarini o'chirish
        try:
            bot.delete_message(message.chat.id, wait_msg.message_id)
        except:
            pass
        
        # Xabarni saqlash
        save_message(
            user.id,
            user_text,
            ai_result["response"],
            ai_result["model"],
            response_time
        )
        
        # Chiroyli javob formatlash
        response_text = f"""
🧠 <b>AI Javobi:</b>

{ai_result["response"]}

━━━━━━━━━━━━━━
📊 <b>Statistika:</b>
• Model: <code>{ai_result['model'].upper()}</code>
• Vaqt: <code>{response_time:.2f} soniya</code>
• Uzunlik: <code>{len(ai_result['response'])} belgi</code>

🤖 <b>Erkinov Professional AI Bot</b>
🌐 <a href="https://t.me/ErkinovAIBot">@ErkinovAIBot</a>
        """
        
        # Xabarni yuborish
        bot.reply_to(message, response_text, disable_web_page_preview=True)
        
    except Exception as e:
        logger.error(f"Xatolik: {str(e)}")
        bot.reply_to(message, f"❌ <b>Xatolik yuz berdi:</b>\n\n<code>{str(e)}</code>")

# ================= WEBHOOK HANDLER =================
@app.route(f'/{Config.TELEGRAM_TOKEN}', methods=['POST'])
def webhook_handler():
    """Webhook handler"""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'Bad request', 400

@app.route('/')
def home():
    """Asosiy sahifa"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Erkinov Professional AI Bot</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            margin-top: 50px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }
        h1 {
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            opacity: 0.8;
            margin-bottom: 40px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .stat-box {
            background: rgba(255, 255, 255, 0.15);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            transition: transform 0.3s;
        }
        .stat-box:hover {
            transform: translateY(-5px);
        }
        .stat-value {
            font-size: 2em;
            font-weight
