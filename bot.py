import os
import json
import telebot
from telebot import types
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- ВЕБ-СЕРВЕР (Для Render, чтобы не засыпал) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- НАСТРОЙКИ ---
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_JSON = os.getenv("GOOGLE_SHEETS_JSON")
SHEET_NAME = "SecretRoomData"

bot = telebot.TeleBot(TOKEN)
users = {}  # Хранилище в оперативной памяти (очищается при перезапуске)

# ==========================================
# ПОЛНАЯ БАЗА ДАННЫХ КОНФЕРЕНЦИЙ (10 шт)
# ==========================================
CONFERENCES_DB = [
    {
        "id": "mac",
        "title": "🔥 MAC Yerevan",
        "details": "🇦🇲 <b>MAC Affiliate Conference (Ереван)</b>\n\nОдна из самых хардкорных конференций для практиков. Топовые кейсы, огромная экспо-зона и легендарные вечеринки до утра.\n\n📅 <b>Даты:</b> Май 2026\n🔗 <b>Сайт:</b> mac.affiliate"
    },
    {
        "id": "sigma",
        "title": "💎 SiGMA Eurasia",
        "details": "🇦🇪 <b>SiGMA Eurasia (Дубай)</b>\n\nРоскошь и бизнес. Сюда едут за крупными контрактами с прямыми рекламодателями и инвесторами. Идеально для тех, кто работает с криптой и гемблой.\n\n📅 <b>Даты:</b> Февраль 2026\n🔗 <b>Сайт:</b> sigma.world/eurasia"
    },
    {
        "id": "awe",
        "title": "🚀 AW Europe",
        "details": "🇪🇸 <b>Affiliate World Europe (Барселона)</b>\n\nДвухдневный интенсив в сердце Каталонии. Здесь задаются тренды на год вперед. Основные вертикали: E-com, Nutra, Dating.\n\n📅 <b>Даты:</b> Июль 2026\n🔗 <b>Сайт:</b> affiliateworldconferences.com"
    },
    {
        "id": "lac",
        "title": "🇬🇧 iGB Affiliate",
        "details": "🇬🇧 <b>iGB Affiliate (Лондон)</b>\n\nКлассика жанра. Самое уважаемое событие в мире iGaming. Строгий дресс-код, серьезные лица и контракты на миллионы.\n\n📅 <b>Даты:</b> Февраль 2026\n🔗 <b>Сайт:</b> london.igbaffiliate.com"
    },
    {
        "id": "igd",
        "title": "🇩🇪 iGaming Germany",
        "details": "🇩🇪 <b>iGaming Germany (Берлин)</b>\n\nУзкоспециализированная конференция по рынку DACH (Германия, Австрия, Швейцария). Всё о лицензировании и белых методах работы.\n\n📅 <b>Даты:</b> Июнь 2026\n🔗 <b>Сайт:</b> igaminggermany.com"
    },
    {
        "id": "cpa",
        "title": "🇷🇺 SPB CPA Life",
        "details": "🇷🇺 <b>SPB CPA Life (Санкт-Петербург)</b>\n\nГлавный фестиваль арбитража в России. Pre-party, основная часть и after-party, о которых слагают легенды. Атмосфера праздника и нетворкинга.\n\n📅 <b>Даты:</b> Август 2026\n🔗 <b>Сайт:</b> cpalife.su"
    },
    {
        "id": "was",
        "title": "🇹🇭 WAS Bangkok",
        "details": "🇹🇭 <b>World Affiliate Show (Бангкок)</b>\n\nЛучшая точка входа на азиатский рынок. Отличный повод совместить работу с отдыхом в Таиланде.\n\n📅 <b>Даты:</b> Октябрь 2026\n🔗 <b>Сайт:</b> worldaffiliateshow.com"
    },
    {
        "id": "asw",
        "title": "🇺🇸 ASW Las Vegas",
        "details": "🇺🇸 <b>Affiliate Summit West (Лас-Вегас)</b>\n\nГигантская конференция в США (6000+ участников). Если вы льете на Tier-1 и хотите выйти на американский рынок — вам сюда.\n\n📅 <b>Даты:</b> Январь 2026\n🔗 <b>Сайт:</b> affiliatesummit.com"
    },
    {
        "id": "bis",
        "title": "🇧🇷 BiS SiGMA",
        "details": "🇧🇷 <b>BiS SiGMA Americas (Сан-Паулу)</b>\n\nЛатинская Америка сейчас — «золотая жила» гемблинга. Конференция №1 для тех, кто хочет лить на Бразилию.\n\n📅 <b>Даты:</b> Апрель 2026\n🔗 <b>Сайт:</b> sigma.world/americas"
    },
    {
        "id": "igb",
        "title": "🇳🇱 iGB Live!",
        "details": "🇳🇱 <b>iGB Live! (Амстердам)</b>\n\nЛетняя версия лондонской конференции, но более расслабленная. Отличный микс бизнеса и вечеринок в Амстердаме.\n\n📅 <b>Даты:</b> Июль 2026\n🔗 <b>Сайт:</b> igblive.com"
    }
]

SERVICES = [
    "🛠 Keitaro (Трекер)", "🛠 Dolphin{anty} (Антидетект)", "🛠 AdHeart (Spy-сервис)",
    "🛠 Capitalist (Платежка)", "🛠 FBTool (Автозалив)", "🛠 Octo Browser",
    "🛠 Multilogin", "🛠 Poshmark (Accounts)", "🛠 SMS Activate"
]

# --- ЗАПИСЬ В GOOGLE ТАБЛИЦУ ---
def save_to_sheet(user_data):
    try:
        if not GOOGLE_JSON: return
        creds_dict = json.loads(GOOGLE_JSON)
        scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME).sheet1
        
        row = [
            user_data.get('id', ''),
            user_data.get('name', ''),
            user_data.get('role', ''),
            user_data.get('company', ''),
            user_data.get('exp', ''),
            user_data.get('phone', ''),
            "ДА"
        ]
        sheet.append_row(row)
    except Exception as e:
        print(f"Sheet Error: {e}")

# --- КЛАВИАТУРЫ ---
def main_menu_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📂 Конференции", "🛠 Сервисы")
    kb.row("💬 Чаты", "👤 Мой профиль")
    return kb

# Функция генерации кнопок списка конференций
def get_conferences_keyboard(page=0, items_per_page=4):
    kb = types.InlineKeyboardMarkup()
    total_pages = (len(CONFERENCES_DB) + items_per_page - 1) // items_per_page

    start = page * items_per_page
    end = start + items_per_page
    current_items = CONFERENCES_DB[start:end]

    for item in current_items:
        kb.add(types.InlineKeyboardButton(text=item["title"], callback_data=f"view_conf_{item['id']}"))

    btns = []
    if page > 0:
        btns.append(types.InlineKeyboardButton("⬅️", callback_data=f"list_conf_prev_{page}"))
    btns.append(types.InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        btns.append(types.InlineKeyboardButton("➡️", callback_data=f"list_conf_next_{page}"))
    kb.row(*btns)
    return kb

# Функция показа деталей конференции
def show_conference_details(call, conf_id):
    conf = next((item for item in CONFERENCES_DB if item["id"] == conf_id), None)
    if not conf:
        bot.answer_callback_query(call.id, "Конференция не найдена")
        return

    kb = types.InlineKeyboardMarkup()
    # Кнопка НАЗАД возвращает пользователя на ПЕРВУЮ страницу (0)
    kb.add(types.InlineKeyboardButton("⬅️ Назад к списку", callback_data="list_conf_start_0"))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=conf["details"],
        parse_mode="HTML
