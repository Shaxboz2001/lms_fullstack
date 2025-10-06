import asyncio
import time
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command

API_TOKEN = "8372128823:AAFyRzgls_kvqyOpN3ef_qy79Rb7PDVwuPU"
ADMIN_ID = 1661832397  # <-- o'zingizning Telegram ID'ingizni yozing

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

quiz = [
    {
        "savol": "🇺🇿 O‘zbekiston poytaxti qaysi?",
        "variantlar": ["Buxoro", "Toshkent", "Samarqand", "Xiva"],
        "javob": 2
    },
    {
        "savol": "🐍 Python dasturlash tilida list qanday belgilanadi?",
        "variantlar": ["{}", "[]", "()", "<>"],
        "javob": 2
    },
    {
        "savol": "📱 Telegram asoschisi kim?",
        "variantlar": ["Mark Zuckerberg", "Elon Musk", "Pavel Durov", "Bill Gates"],
        "javob": 3
    }
]

users_data = {}


@dp.message(Command("start"))
async def start_quiz(message: types.Message):
    users_data[message.from_user.id] = {
        "ism": message.from_user.full_name,
        "ball": 0,
        "index": 0,
        "start": time.time(),
        "finish": None
    }
    await message.answer(
        "🎉 <b>Quizga xush kelibsiz!</b>\n\n"
        "❗ Savollarga tez va to‘g‘ri javob bering.\n"
        "🏆 Oxirida TOP 3 faqat admin ko‘radi."
    )
    await send_question(message.from_user.id)


async def send_question(user_id: int):
    user = users_data[user_id]
    index = user["index"]

    if index >= len(quiz):
        user["finish"] = time.time()
        duration = round(user["finish"] - user["start"], 1)
        await bot.send_message(
            user_id,
            f"✅ Test tugadi!\n"
            f"⭐ Sizning ballingiz: <b>{user['ball']}</b>\n"
            f"⏱ Sarflangan vaqt: <b>{duration} soniya</b>"
        )
        await show_top3()
        return

    savol_data = quiz[index]
    buttons = [
        [types.InlineKeyboardButton(text=variant, callback_data=str(i + 1))]
        for i, variant in enumerate(savol_data["variantlar"])
    ]
    markup = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.send_message(
        user_id,
        f"❓ <b>{savol_data['savol']}</b>\n\n"
        "Variantlardan birini tanlang 👇",
        reply_markup=markup
    )


@dp.callback_query()
async def handle_answer(call: types.CallbackQuery):
    user = users_data[call.from_user.id]
    index = user["index"]
    tanlangan = int(call.data)
    togri = quiz[index]["javob"]

    if tanlangan == togri:
        user["ball"] += 1
        await call.message.answer("✅ <b>To‘g‘ri!</b>")
    else:
        await call.message.answer(
            f"❌ <b>Noto‘g‘ri!</b>\n"
            f"🔑 To‘g‘ri javob: <b>{quiz[index]['variantlar'][togri - 1]}</b>"
        )

    user["index"] += 1
    await send_question(call.from_user.id)
    await call.answer()


async def show_top3():
    finished = [u for u in users_data.values() if u["finish"]]
    if not finished:
        return

    sorted_users = sorted(
        finished,
        key=lambda x: (-x["ball"], x["finish"] - x["start"])
    )
    top3 = sorted_users[:3]

    text = "🏆 <b>TOP 3 Ishtirokchi</b>\n\n"
    for i, user in enumerate(top3, start=1):
        vaqt = round(user["finish"] - user["start"], 1)
        text += (
            f"{i}. <b>{user['ism']}</b>\n"
            f"   ⭐ Ball: <b>{user['ball']}</b>\n"
            f"   ⏱ Vaqt: <b>{vaqt} soniya</b>\n\n"
        )

    # faqat admin ko‘radi
    await bot.send_message(ADMIN_ID, text)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
