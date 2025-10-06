import asyncio
import re
from datetime import datetime, timedelta
import aiohttp
from bs4 import BeautifulSoup
import psycopg2
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InputMediaPhoto
from aiogram.enums import ParseMode
from aiogram import F
import os
from dotenv import load_dotenv

# Konfiguratsiyani yuklash
load_dotenv()

# Sozlamalar
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'job_scraper'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': os.getenv('DB_PORT', '5432')
}

# TELEGRAM_CONFIG = {
#     'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
#     'channel_id': os.getenv('TELEGRAM_CHANNEL_ID'),
#     'admin_id': os.getenv('TELEGRAM_ADMIN_ID')
# }

# Bot va dispatcher yaratish
# bot = Bot(token=TELEGRAM_CONFIG['bot_token'], parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())


async def create_database_tables():
    """Ma'lumotlar bazasi jadvallarini yaratish"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            source VARCHAR(20),
            title VARCHAR(255),
            price VARCHAR(100),
            company VARCHAR(255),
            position VARCHAR(255),
            location VARCHAR(100) DEFAULT 'Bekobod',
            contact VARCHAR(100),
            work_hours VARCHAR(100),
            requirements TEXT,
            description TEXT,
            link TEXT UNIQUE,
            image_url TEXT,
            posted_at TIMESTAMP,
            posted_to_telegram BOOLEAN DEFAULT FALSE,
            scraped_at TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
        """)

        conn.commit()
        print("Ma'lumotlar bazasi jadvallari yaratildi")
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
    finally:
        if conn:
            conn.close()


async def scrape_olx_bekobod_jobs():
    """OLX.uz dan Bekobod vakansiyalarini skreyp qilish"""
    url = "https://www.olx.uz/oz/rabota/bekabad/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')

                listings = soup.find_all('div', {'data-cy': 'l-card'})
                jobs = []

                for listing in listings:
                    # Joylashuvni tekshirish
                    location = listing.find('p', class_='css-15khyzd').text.strip() if listing.find('p',
                                                                                                    class_='css-15khyzd') else ''
                    if 'Bekobod' not in location and 'Бекабад' not in location:
                        continue

                    # Ma'lumotlarni olish
                    title = listing.find('h4', class_='css-amfvow').text.strip() if listing.find('h4',
                                                                                                 class_='css-amfvow') else 'N/A'
                    link = "https://www.olx.uz" + listing.find('a', class_='css-13gxtrp')['href'] if listing.find('a',
                                                                                                                  class_='css-13gxtrp') else 'N/A'
                    price = listing.find('p', class_='css-zgm539').text.strip() if listing.find('p',
                                                                                                class_='css-zgm539') else 'Kelishiladi'

                    # Kompaniya nomini ajratib olish
                    company = 'N/A'
                    if '-' in title:
                        parts = title.split('-')
                        if len(parts) > 1:
                            company = parts[0].strip()
                            title = '-'.join(parts[1:]).strip()

                    # Rasm manzili
                    image_element = listing.find('img')
                    image_url = image_element[
                        'src'] if image_element else 'https://via.placeholder.com/300?text=OLX+Bekobod'

                    jobs.append({
                        'source': 'OLX',
                        'title': title,
                        'price': price,
                        'company': company,
                        'location': 'Bekobod',
                        'link': link,
                        'image_url': image_url,
                        'posted_at': datetime.now().strftime('%Y-%m-%d'),
                        'scraped_at': datetime.now()
                    })

                return jobs

    except Exception as e:
        print(f"OLX skreyp qilishda xatolik: {e}")
        return []


async def scrape_ishkop_bekobod_jobs():
    """Ishkop.uz dan Bekobod vakansiyalarini skreyp qilish"""
    url = "https://ishkop.uz/вакансии/Бекабад-Ташкентская-область"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')

                articles = soup.find_all('article', class_='job')
                jobs = []

                for article in articles:
                    # Arxivlangan vakansiyalarni o'tkazib yuborish
                    if article.find('div', class_='archived'):
                        continue

                    # Sarlavha va havola
                    title_element = article.find('a', class_='job-title')
                    title = title_element.text.strip() if title_element else 'N/A'
                    link = title_element['href'] if title_element else 'N/A'

                    # Kompaniya
                    company = article.find('div', class_='company').text.strip() if article.find('div',
                                                                                                 class_='company') else 'N/A'

                    # Ish haqi
                    salary = article.find('div', class_='salary').text.strip() if article.find('div',
                                                                                               class_='salary') else 'Kelishiladi'
                    salary = salary.replace('&nbsp;', ' ')

                    # Tavsif
                    desc = article.find('div', class_='desc').text.strip() if article.find('div', class_='desc') else ''

                    # Sana
                    posted = article.find('div', class_='from').text.strip() if article.find('div',
                                                                                             class_='from') else ''
                    posted_at = parse_ishkop_date(posted)

                    jobs.append({
                        'source': 'Ishkop',
                        'title': title,
                        'price': salary,
                        'company': company,
                        'location': 'Bekobod',
                        'description': desc,
                        'link': link,
                        'image_url': 'https://via.placeholder.com/300?text=Ishkop.uz',
                        'posted_at': posted_at,
                        'scraped_at': datetime.now()
                    })

                return jobs

    except Exception as e:
        print(f"Ishkop skreyp qilishda xatolik: {e}")
        return []


def parse_ishkop_date(date_str):
    """Ishkop sanasini tahlil qilish"""
    today = datetime.now()

    if 'сегодня' in date_str.lower():
        return today.strftime('%Y-%m-%d')
    elif 'вчера' in date_str.lower():
        return (today - timedelta(days=1)).strftime('%Y-%m-%d')
    elif 'день' in date_str.lower() or 'дня' in date_str.lower() or 'дней' in date_str.lower():
        days = int(re.search(r'\d+', date_str).group())
        return (today - timedelta(days=days)).strftime('%Y-%m-%d')
    else:
        return today.strftime('%Y-%m-%d')


async def save_to_database(jobs):
    """Ma'lumotlar bazasiga saqlash"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        for job in jobs:
            # Vakansiya bazada bormi?
            cursor.execute("SELECT 1 FROM jobs WHERE link = %s", (job['link'],))
            exists = cursor.fetchone()

            if not exists:
                cursor.execute("""
                INSERT INTO jobs (
                    source, title, price, company, location, 
                    description, link, image_url, posted_at, scraped_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    job['source'],
                    job['title'],
                    job['price'],
                    job['company'],
                    job['location'],
                    job.get('description', ''),
                    job['link'],
                    job['image_url'],
                    job['posted_at'],
                    job['scraped_at']
                ))

        conn.commit()
        print(f"{len(jobs)} ta yangi vakansiya saqlandi")
    except Exception as e:
        print(f"Ma'lumotlar bazasiga saqlashda xatolik: {e}")
    finally:
        if conn:
            conn.close()


# async def format_telegram_post(job):
#     """Telegram postini tayyorlash"""
#     # Ma'lumotlarni tozalash
#     title = job['title'].replace('в сеть магазинов', '').replace('(г.Бекабад)', '').strip()
#     company = job['company'] if job['company'] != 'N/A' else 'Noma\'lum'
#     salary = job['price'] if job['price'] != 'N/A' else 'Kelishiladi'
#
#     # Kontakt ma'lumoti
#     contact = "Raqam ko'rsatilmagan"
#     if job['source'] == 'OLX' and 'tel:' in job['link']:
#         contact = job['link'].split('tel:')[-1]
#
#     post = f"""
# Xodim kerak
#
# 🏢 Idora: {company}
# 👨‍💻 Yo'nalish: {title}
# 📍 Hudud: {job['location']}
# 👤 Mas'ul shaxs: {contact}
# 🕰 Murojaat vaqti: 9:00-18:00
# ⏰ Ish vaqti: Kelishiladi
# 💸 Maosh: {salary}
# ✔️ Batafsil: {job.get('description', 'Batafsil ma\'lumot uchun manzilda ko\'ring')}
#
# © @bekobod_job
# © @bekobod_jobs_bot
# """
#     return post.strip()


# async def post_to_telegram():
#     """Telegram kanaliga post jo'natish"""
#     conn = None
#     try:
#         conn = psycopg2.connect(**DB_CONFIG)
#         cursor = conn.cursor()
#
#         # Telegramga jo'natilmagan 5 ta vakansiyani olish
#         cursor.execute("""
#         SELECT * FROM jobs
#         WHERE posted_to_telegram = FALSE
#         AND location = 'Bekobod'
#         ORDER BY scraped_at DESC
#         LIMIT 5
#         """)
#
#         jobs = cursor.fetchall()
#
#         if not jobs:
#             print("Telegramga jo'natish uchun yangi vakansiyalar yo'q")
#             return
#
#         for job in jobs:
#             job_id, source, title, price, company, position, location, contact, work_hours, requirements, desc, link, image_url, posted_at, posted_to_telegram, scraped_at, is_active = job
#
#             job_data = {
#                 'title': title,
#                 'price': price,
#                 'company': company,
#                 'location': location,
#                 'description': desc,
#                 'link': link,
#                 'source': source
#             }
#
#             message = await format_telegram_post(job_data)
#
#             try:
#                 # Rasm bilan post jo'natish
#                 if image_url.startswith('http'):
#                     await bot.send_photo(
#                         chat_id=TELEGRAM_CONFIG['channel_id'],
#                         photo=image_url,
#                         caption=message
#                     )
#                 else:
#                     await bot.send_message(
#                         chat_id=TELEGRAM_CONFIG['channel_id'],
#                         text=message
#                     )
#
#                 # Bazada yangilash
#                 cursor.execute("""
#                 UPDATE jobs SET posted_to_telegram = TRUE
#                 WHERE id = %s
#                 """, (job_id,))
#                 conn.commit()
#
#                 print(f"{job_id} ID li vakansiya Telegramga jo'natildi")
#                 await asyncio.sleep(3)  # Limitdan qochish uchun
#
#             except Exception as e:
#                 print(f"Vakansiyani jo'natishda xatolik: {e}")
#                 continue
#
#     except Exception as e:
#         print(f"Telegramga jo'natishda xatolik: {e}")
#     finally:
#         if conn:
#             conn.close()


async def scheduled_scraper():
    """Vaqt bo'yicha skreyp qilish"""
    while True:
        print("Vakansiyalarni skreyp qilish boshlandi...")

        # OLX va Ishkopdan vakansiyalarni olish
        olx_jobs, ishkop_jobs = await asyncio.gather(
            scrape_olx_bekobod_jobs(),
            scrape_ishkop_bekobod_jobs()
        )

        all_jobs = olx_jobs + ishkop_jobs

        if all_jobs:
            # Bazaga saqlash
            await save_to_database(all_jobs)

            # Telegramga jo'natish
            # await post_to_telegram()
        else:
            print("Yangi Bekobod vakansiyalari topilmadi")

        # 12 soatdan keyin qayta ishlash
        await asyncio.sleep(12 * 60 * 60)


# @dp.message(F.text == '/start')
# async def cmd_start(message: types.Message):
#     """Start komandasi uchun handler"""
#     await message.answer("Bekobod vakansiyalari boti ishga tushdi!")
#
#
# @dp.message(F.text == '/stats')
# async def cmd_stats(message: types.Message):
#     """Statistika komandasi uchun handler"""
#     if str(message.from_user.id) != TELEGRAM_CONFIG['admin_id']:
#         await message.answer("Sizga ruxsat yo'q!")
#         return
#
#     conn = None
#     try:
#         conn = psycopg2.connect(**DB_CONFIG)
#         cursor = conn.cursor()
#
#         cursor.execute("SELECT COUNT(*) FROM jobs")
#         total = cursor.fetchone()[0]
#
#         cursor.execute("SELECT COUNT(*) FROM jobs WHERE posted_to_telegram = TRUE")
#         posted = cursor.fetchone()[0]
#
#         cursor.execute("SELECT COUNT(*) FROM jobs WHERE source = 'OLX'")
#         olx = cursor.fetchone()[0]
#
#         cursor.execute("SELECT COUNT(*) FROM jobs WHERE source = 'Ishkop'")
#         ishkop = cursor.fetchone()[0]
#
#         stats = f"""
# 📊 Bot statistikasi:
#
# 🔢 Jami vakansiyalar: {total}
# 📤 Telegramga jo'natilgan: {posted}
# 🛒 OLX vakansiyalari: {olx}
# 💼 Ishkop vakansiyalari: {ishkop}
# """
#         await message.answer(stats)
#
#     except Exception as e:
#         await message.answer(f"Statistika olishda xatolik: {e}")
#     finally:
#         if conn:
#             conn.close()
#
#
# async def on_startup():
#     """Bot ishga tushganda"""
#     await create_database_tables()
#     await bot.send_message(TELEGRAM_CONFIG['admin_id'], "Bot ishga tushdi! Bekobod vakansiyalari skreyp qilinmoqda...")
#     asyncio.create_task(scheduled_scraper())
#
#
# async def on_shutdown():
#     """Bot to'xtaganda"""
#     await bot.send_message(TELEGRAM_CONFIG['admin_id'], "Bot to'xtatildi!")
#
#
async def main():
    """Asosiy dastur"""
    # await on_startup()
    # await dp.start_polling(bot)
    # await on_shutdown()


if __name__ == '__main__':
    asyncio.run(main())