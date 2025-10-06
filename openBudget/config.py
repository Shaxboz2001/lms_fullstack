import os
from dotenv import load_dotenv

load_dotenv()

# Bot sozlamalari
BOT_TOKEN = os.getenv("BOT_TOKEN", "8077089698:AAFiK2Wtt008LWfo6C-RkZ499YeHEqbQ52g")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "1661832397").split(',')))

# Loyiha sozlamalari
DEFAULT_PROJECT_LINK = os.getenv("DEFAULT_PROJECT_LINK", "https://openbudget.uz/boards/initiatives/initiative/52/0a92555a-2504-4032-aefb-6af8fadc97d5")
DEFAULT_PROJECT_TITLE = os.getenv("DEFAULT_PROJECT_TITLE", "Ochiq byudjet loyihasi")
VOTE_REWARD = int(os.getenv("VOTE_REWARD", 5000))  # so'm

# Ma'lumotlar bazasi
DATABASE_FILE = os.getenv("DATABASE_FILE", "votes.db")

# WebApp sozlamalari
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-webapp-domain.com")

# Xabarlar
MESSAGES = {
    "start": "👋 Assalomu alaykum! Ovoz berish uchun telefon raqamingizni yuboring (+998XXXXXXXXX formatida).",
    "phone_received": "✅ Telefon raqamingiz qabul qilindi! Endi ovoz berish uchun loyihaga o'ting va screenshot yuboring.",
    "incorrect_phone": "❌ Noto'g'ri telefon raqami formati! Iltimos, +998XXXXXXXXX formatida yuboring.",
    "screenshot_received": "✅ Screenshot qabul qilindi! Admin tekshiruvidan so'ng sizga javob beramiz.",
    "incorrect_screenshot": "❌ Iltimos, to'g'ri screenshot yuboring!",
    "vote_confirmed": "🎉 Tabriklaymiz! Sizning ovozingiz tasdiqlandi. Balansingizga {reward} so'm qo'shildi.",
    "vote_rejected": "❌ Kechirasiz, sizning ovozingiz quyidagi sabablarga ko'ra qabul qilinmadi:\n- Screenshotda ovoz berganingiz ko'rinmayapti\n- Noto'g'ri loyiha ko'rsatilgan",
    "already_voted": "⚠️ Siz allaqachon ovoz bergansiz! Keyingi loyihalarda ishtirok etishingiz mumkin.",
    "balance_info": "💰 Sizning balansingiz: {balance} so'm",
    "vote_status": "📊 Sizning ovoz holatingiz:\n\n🔗 Loyiha: {project}\n📅 Sana: {date}\n🔄 Holat: {status}",
    "no_active_project": "ℹ️ Hozircha aktiv loyihalar mavjud emas. Iltimos, keyinroq urinib ko'ring."
}