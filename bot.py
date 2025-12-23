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
        parse_mode="HTML",
        reply_markup=kb
    )

# --- ЛОГИКА РЕГИСТРАЦИИ ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("✅ Согласен на обработку ПД")
    
    text = (
        "👋 <b>Добро пожаловать в Secretroom!</b>\n\n"
        "Для доступа к базе знаний нам нужно познакомиться.\n\n"
        "<i>Нажимая кнопку ниже, вы даете согласие на обработку персональных данных (ФЗ-152).</i>"
    )
    bot.send_message(user_id, text, parse_mode="HTML", reply_markup=markup)
    bot.register_next_step_handler(message, check_pd_consent)

def check_pd_consent(message):
    if message.text == "✅ Согласен на обработку ПД":
        msg = bot.send_message(message.chat.id, "Супер! 1️⃣ Как вас зовут? (ФИО)", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_name)
    else:
        bot.send_message(message.chat.id, "Без согласия мы не можем продолжить. Нажмите /start, если передумаете.")

def process_name(message):
    user_id = message.from_user.id
    users[user_id] = {"id": user_id, "name": message.text}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True).row("Media Buyer", "Арбитражник").row("Team Lead", "Маркетолог")
    msg = bot.send_message(user_id, "2️⃣ Кто вы по специальности?", reply_markup=markup)
    bot.register_next_step_handler(msg, process_role)

def process_role(message):
    users[message.from_user.id]["role"] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True).row("Фриланс", "Нет компании")
    msg = bot.send_message(message.from_user.id, "3️⃣ В какой компании работаете?", reply_markup=markup)
    bot.register_next_step_handler(msg, process_company)

def process_company(message):
    users[message.from_user.id]["company"] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True).row("0-6 мес", "6-12 мес").row("1-3 года", "3+ лет")
    msg = bot.send_message(message.from_user.id, "4️⃣ Ваш опыт?", reply_markup=markup)
    bot.register_next_step_handler(msg, process_exp)

def process_exp(message):
    users[message.from_user.id]["exp"] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📱 Поделиться телефоном", request_contact=True), types.KeyboardButton("Пропустить"))
    msg = bot.send_message(message.from_user.id, "5️⃣ Контакт для связи:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_phone_finish)

def process_phone_finish(message):
    uid = message.from_user.id
    phone = message.contact.phone_number if message.contact else message.text
    users[uid]["phone"] = phone
    users[uid]["registered"] = True # Отметка, что регистрация пройдена
    
    bot.send_message(uid, "⏳ Сохраняю данные...", reply_markup=types.ReplyKeyboardRemove())
    save_to_sheet(users[uid])
    
    bot.send_message(uid, "✅ <b>Регистрация завершена!</b>\nДоступ открыт.", parse_mode="HTML", reply_markup=main_menu_kb())

# --- ОБРАБОТЧИК МЕНЮ ---
@bot.message_handler(content_types=['text'])
def handle_menu(message):
    user_id = message.from_user.id
    
    if message.text == "📂 Конференции":
        kb = get_conferences_keyboard(page=0)
        bot.send_message(message.chat.id, "📅 <b>Выберите конференцию:</b>", parse_mode="HTML", reply_markup=kb)

    elif message.text == "🛠 Сервисы":
        text = "🛠 <b>Полезные сервисы:</b>\n\n" + "\n".join([f"• {s}" for s in SERVICES])
        bot.send_message(message.chat.id, text, parse_mode="HTML")

    elif message.text == "💬 Чаты":
        bot.send_message(message.chat.id, "🔓 <b>Чаты:</b>\n\n🇷🇺 CPA Secret Chat\n🇺🇸 Affiliate World", parse_mode="HTML")

    elif message.text == "👤 Мой профиль":
        # ИСПРАВЛЕНО: Проверка наличия пользователя в памяти
        u = users.get(user_id)
        if u:
            text = f"👤 <b>Ваш профиль:</b>\n\nName: {u['name']}\nRole: {u['role']}\nCompany: {u['company']}"
            bot.send_message(message.chat.id, text, parse_mode="HTML")
        else:
            # Если бот перезагружался, он забыл данные. Просим обновить.
            bot.send_message(message.chat.id, "⚠️ Данные не найдены (бот был обновлен).\nПожалуйста, нажмите /start для входа.")

# --- ОБРАБОТЧИК КНОПОК ---
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.data == "noop":
            bot.answer_callback_query(call.id)
            return

        if call.data.startswith("view_conf_"):
            conf_id = call.data.split("_")[2]
            show_conference_details(call, conf_id)

        elif call.data.startswith("list_conf_"):
            parts = call.data.split("_")
            action = parts[2]
            current_page = int(parts[3])

            new_page = current_page
            if action == "next": new_page += 1
            elif action == "prev": new_page -= 1
            # Если action "start", страница просто станет 0

            kb = get_conferences_keyboard(page=new_page)
            
            bot.edit_message_text(
                text="📅 <b>Выберите конференцию:</b>",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=kb
            )

    except Exception as e:
        print(f"Error: {e}")
        bot.answer_callback_query(call.id, "Ошибка")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
