import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    CallbackQuery,
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ================= CONFIG =================
BOT_TOKEN = "8077089698:AAFiK2Wtt008LWfo6C-RkZ499YeHEqbQ52g"
ADMIN_IDS = [1661832397]
VOTE_REWARD = 5000

MESSAGES = {
    "start": "🎉 <b>Ovoz berish botiga xush kelibsiz!</b>\n\nQuyidagi tugmalardan birini tanlang:",
    "no_active_project": "⚠️ Hozircha faol loyihalar mavjud emas.",
    "incorrect_phone": "❌ Noto'g'ri telefon raqami formati. Iltimos, +998XXXXXXXXX formatida kiriting.",
    "phone_received": "📱 <b>Raqamingiz qabul qilindi!</b>\nEndi ovoz berish screenshotini yuboring.",
    "incorrect_screenshot": "❌ Iltimos, haqiqiy screenshot yuboring.",
    "screenshot_received": "🖼 <b>Screenshot qabul qilindi!</b>\nAdminlar tasdiqlashini kuting.",
    "balance_info": "💰 <b>Sizning balansingiz:</b> {balance} so'm",
    "vote_confirmed": "🎉 <b>Tabriklaymiz!</b>\nSizning ovozingiz tasdiqlandi. {reward} so'm hisobingizga qo'shildi.",
    "admin_only": "⛔ <b>Siz admin emassiz!</b>"
}

BUTTONS = {
    "vote": "🗳 Ovoz berish",
    "balance": "💰 Balans",
    "my_votes": "📊 Mening ovozlarim",
    "admin_panel": "👨‍💻 Admin paneli",
    "stats": "📈 Statistika",
    "pending_votes": "⏳ Tasdiqlanmagan ovozlar",
    "back": "🔙 Orqaga",
    "confirm": "✅ Tasdiqlash",
    "reject": "❌ Rad etish",
    "projects": "📋 Loyihalar ro'yxati",
    "add_project": "➕ Loyiha qo'shish",
    "set_active": "⭐ Faollashtirish"
}

# ================= STATES =================
class VoteStates(StatesGroup):
    waiting_phone = State()
    waiting_screenshot = State()

# ================= DATABASE MODELS =================
class User:
    def __init__(self, user_id, full_name, username=None, phone=None):
        self.id = user_id
        self.full_name = full_name
        self.username = username
        self.phone = phone
        self.balance = 0

class Project:
    def __init__(self, id, title, link, is_active=False):
        self.id = id
        self.title = title
        self.link = link
        self.is_active = is_active

class Vote:
    def __init__(self, id, user_id, project_id, phone, photo_id, is_confirmed=False):
        self.id = id
        self.user_id = user_id
        self.project_id = project_id
        self.phone = phone
        self.photo_id = photo_id
        self.is_confirmed = is_confirmed
        self.created_at = datetime.now()

# ================= DATABASE (SIMPLE) =================
users_db = []
projects_db = []
votes_db = []
current_id = 1

def init_db():
    global users_db, projects_db, votes_db, current_id
    users_db = []
    projects_db = [
        Project(1, "OpenBudget loyihasi", "https://openbudget.uz/boards/initiatives/initiative/52/0a92555a-2504-4032-aefb-6af8fadc97d5", True)
    ]
    votes_db = []
    current_id = 1

def get_user(user_id):
    for user in users_db:
        if user.id == user_id:
            return user
    return None

def add_user(user_id, full_name, username=None):
    user = get_user(user_id)
    if user:
        return user
    user = User(user_id, full_name, username)
    users_db.append(user)
    return user

def update_user_phone(user_id, phone):
    user = get_user(user_id)
    if user:
        user.phone = phone
        return True
    return False

def add_vote(user_id, project_id, photo_id, phone):
    global current_id
    vote = Vote(current_id, user_id, project_id, phone, photo_id)
    votes_db.append(vote)
    current_id += 1
    return vote

def confirm_vote(vote_id):
    for vote in votes_db:
        if vote.id == vote_id and not vote.is_confirmed:
            vote.is_confirmed = True
            user = get_user(vote.user_id)
            if user:
                user.balance += VOTE_REWARD
            return True
    return False

def get_active_project():
    return next((p for p in projects_db if p.is_active), None)

def get_user_balance(user_id):
    user = get_user(user_id)
    return user.balance if user else 0

def get_vote_stats():
    total = len(votes_db)
    confirmed = sum(1 for v in votes_db if v.is_confirmed)
    pending = total - confirmed
    return {"total_votes": total, "confirmed_votes": confirmed, "pending_votes": pending}

def get_user_votes(user_id):
    return [v for v in votes_db if v.user_id == user_id]

def get_pending_votes():
    return [v for v in votes_db if not v.is_confirmed]

def get_all_projects():
    return projects_db

def get_project(project_id):
    return next((p for p in projects_db if p.id == project_id), None)

def get_vote(vote_id):
    return next((v for v in votes_db if v.id == vote_id), None)

def get_project_stats(project_id):
    votes = [v for v in votes_db if v.project_id == project_id]
    return {"total": len(votes),
            "confirmed": sum(1 for v in votes if v.is_confirmed),
            "pending": sum(1 for v in votes if not v.is_confirmed)}

def set_project_active(project_id):
    for p in projects_db:
        p.is_active = (p.id == project_id)
    return True

# ================= INIT BOT =================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())
init_db()

# ================= KEYBOARDS =================
def get_main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=BUTTONS["vote"]), KeyboardButton(text=BUTTONS["balance"])],
        [KeyboardButton(text=BUTTONS["my_votes"])]
    ]
    if is_admin:
        kb.append([KeyboardButton(text=BUTTONS["admin_panel"])])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_vote_keyboard(project_link: str):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🌐 Loyihaga o'tish", url=project_link),
        InlineKeyboardButton(text="🗳 Ovoz berish", web_app=WebAppInfo(url=project_link))
    )
    return builder.as_markup()

def get_vote_actions_keyboard(vote_id):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=BUTTONS["confirm"], callback_data=f"confirm:{vote_id}"),
        InlineKeyboardButton(text=BUTTONS["reject"], callback_data=f"reject:{vote_id}")
    )
    return builder.as_markup()

# ================= HANDLERS =================
@dp.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    add_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer(MESSAGES["start"], reply_markup=get_main_keyboard(is_admin))

@dp.message(F.text == BUTTONS["vote"])
async def vote_command(message: Message, state: FSMContext):
    project = get_active_project()
    if not project:
        await message.answer(MESSAGES["no_active_project"])
        return
    await message.answer("📱 Telefon raqamingizni yuboring:\nFormat: <code>+998XXXXXXXXX</code>", reply_markup=ReplyKeyboardRemove())
    await state.set_state(VoteStates.waiting_phone)
    await state.update_data(project_id=project.id)

@dp.message(VoteStates.waiting_phone, F.text.regexp(r'^\+998\d{9}$'))
async def process_phone(message: Message, state: FSMContext):
    phone = message.text
    if any(v.phone == phone for v in get_user_votes(message.from_user.id)):
        await message.answer("❌ Bu raqamdan allaqachon ovoz bergansiz!")
        await state.clear()
        return
    update_user_phone(message.from_user.id, phone)
    data = await state.get_data()
    project = get_project(data["project_id"])
    await message.answer(MESSAGES["phone_received"], reply_markup=get_vote_keyboard(project.link))
    await state.set_state(VoteStates.waiting_screenshot)
    await state.update_data(phone=phone)

@dp.message(VoteStates.waiting_phone)
async def invalid_phone(message: Message):
    await message.answer(MESSAGES["incorrect_phone"])

@dp.message(VoteStates.waiting_screenshot, F.photo)
async def process_screenshot(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id
    vote = add_vote(message.from_user.id, data["project_id"], photo_id, data["phone"])
    caption = f"🆕 Yangi ovoz:\n👤 {message.from_user.full_name}\n📱 {data['phone']}\n🆔 {message.from_user.id}\n📅 {vote.created_at.strftime('%Y-%m-%d %H:%M')}"
    await bot.send_photo(ADMIN_IDS[0], photo_id, caption=caption, reply_markup=get_vote_actions_keyboard(vote.id))
    await message.answer(MESSAGES["screenshot_received"])
    await state.clear()

@dp.message(VoteStates.waiting_screenshot)
async def invalid_screenshot(message: Message):
    await message.answer(MESSAGES["incorrect_screenshot"])

@dp.message(F.text == BUTTONS["balance"])
async def balance_command(message: Message):
    balance = get_user_balance(message.from_user.id)
    await message.answer(MESSAGES["balance_info"].format(balance=balance), reply_markup=get_main_keyboard(message.from_user.id in ADMIN_IDS))

@dp.message(F.text == BUTTONS["my_votes"])
async def my_votes_command(message: Message):
    votes = get_user_votes(message.from_user.id)
    if not votes:
        await message.answer("ℹ️ Siz hali ovoz bermagansiz.")
        return
    text = "📊 <b>Sizning ovozlaringiz:</b>\n\n"
    for i, v in enumerate(votes, 1):
        pr = get_project(v.project_id)
        status = "✅ Tasdiqlangan" if v.is_confirmed else "⏳ Kutilmoqda"
        text += f"{i}. {pr.title}\n📅 {v.created_at.strftime('%d.%m.%Y %H:%M')}\n📱 {v.phone}\n{status}\n\n"
    await message.answer(text)

@dp.callback_query(F.data.startswith("confirm:"))
async def confirm_vote_callback(callback: CallbackQuery):
    vote_id = int(callback.data.split(":")[1])
    vote = get_vote(vote_id)
    if not vote:
        await callback.answer("❌ Ovoz topilmadi!", show_alert=True)
        return
    if vote.is_confirmed:
        await callback.answer("⚠️ Allaqachon tasdiqlangan!", show_alert=True)
        return
    confirm_vote(vote.id)
    user = get_user(vote.user_id)
    if user:
        try:
            await bot.send_message(user.id, MESSAGES["vote_confirmed"].format(reward=VOTE_REWARD))
        except Exception as e:
            logger.error(f"Xabar yuborishda xato: {e}")
    await callback.answer("✅ Ovoz tasdiqlandi!")
    await callback.message.edit_text(f"✅ Ovoz tasdiqlandi!\n👤 {user.full_name}\n📱 {vote.phone}\n💰 +{VOTE_REWARD} so'm")

# ================= MAIN =================
async def on_startup():
    logger.info("Bot ishga tushdi")
    await bot.send_message(ADMIN_IDS[0], "🟢 Bot ishga tushdi")

async def on_shutdown():
    logger.info("Bot to'xtadi")
    await bot.send_message(ADMIN_IDS[0], "🔴 Bot to'xtadi")

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
