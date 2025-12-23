import os
import json
import telebot
from telebot import types
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- ВЕБ-СЕРВЕР (Для Render) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

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
users = {}

# ==========================================
# НОВАЯ БАЗА ДАННЫХ КОНФЕРЕНЦИЙ
# ==========================================
# У каждой конференции теперь есть уникальный 'id', короткий 'title' для кнопки,
# и полное 'details' описание с ссылкой.
CONFERENCES_DB = [
    {
        "id": "mac26",
        "title": "🔥 MAC Yerevan 2026",
        "details": "🇦🇲 <b>MAC Affiliate Conference 2026 (Ереван)</b>\n\nОдна из крупнейших конференций в сфере партнерского маркетинга. Ожидается более 3000 участников, топовые спикеры и легендарные афтепати.\n\n📅 <b>Даты:</b> Май 2026 (Уточняется)\n🔗 <b>Сайт:</b> mac.affiliate"
    },
    {
        "id": "sigma_dubai",
        "title": "💎 SiGMA Eurasia",
        "details": "🇦🇪 <b>SiGMA Eurasia (Дубай)</b>\n\nКрупнейший хаб для iGaming индустрии на Ближнем Востоке. Идеальное место для нетворкинга с операторами и провайдерами.\n\n📅 <b>Даты:</b> Февраль 2026\n🔗 <b>Сайт:</b> sigma.world/eurasia"
    },
    {
        "id": "awe_bcn",
        "title": "🚀 Affiliate World Europe",
        "details": "🇪🇸 <b>Affiliate World Europe (Барселона)</b>\n\nДвухдневное событие мирового масштаба. Фокус на e-commerce, нутре и технологиях.\n\n📅 <b>Даты:</b> Июль 2026\n🔗 <b>Сайт:</b> affiliateworldconferences.com/europe"
    },
    {
        "id": "lac",
        "title": "🇬🇧 London Affiliate Conference",
        "details": "🇬🇧 <b>iGB Affiliate London</b>\n\nСтарейшая и самая уважаемая конференция в нише iGaming. Строгий B2B формат.\n\n📅 <b>Даты:</b> Февраль 2026\n🔗 <b>Сайт:</b> london.igbaffiliate.com"
    },
    # ... Добавляй остальные конференции по аналогии ...
     {
        "id": "spb_cpa",
        "title": "🇷🇺 SPB CPA Life",
        "details": "🇷🇺 <b>SPB CPA Life (Санкт-Петербург)</b>\n\nГлавная арбитражная тусовка России. Атмосфера, нетворкинг и инсайды рынка СНГ.\n\n📅 <b>Даты:</b> Август 2026\n🔗 <b>Сайт:</b> cpalife.su"
    },
]

# (Сервисы пока оставляем простым списком, их тоже можно переделать позже)
SERVICES = [
    "🛠 Keitaro (Трекер)", "🛠 Dolphin{anty} (Антидетект)", "🛠 AdHeart (Spy-сервис)",
    "🛠 Capitalist (Платежка)", "🛠 FBTool (Автозалив)", "🛠 Octo Browser",
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
        row = [user_data.get('id',''), user_data.get('name',''), user_data.get('role',''), user_data.get('company',''), user_data.get('exp',''), user_data.get('phone',''), "ДА"]
        sheet.append_row(row)
    except Exception as e: print(f"Google Sheet Error: {e}")

# --- ГЛАВНОЕ МЕНЮ ---
def main_menu_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📂 Конференции", "🛠 Сервисы")
    kb.row("💬 Чаты", "👤 Мой профиль")
    return kb

# ==========================================
# НОВАЯ ЛОГИКА ОТОБРАЖЕНИЯ СПИСКОВ (INLINE КНОПКИ)
# ==========================================

# Функция создания клавиатуры со списком конференций (с пагинацией)
def get_conferences_keyboard(page=0, items_per_page=4):
    kb = types.InlineKeyboardMarkup()
    total_pages = (len(CONFERENCES_DB) + items_per_page - 1) // items_per_page

    start = page * items_per_page
    end = start + items_per_page
    current_items = CONFERENCES_DB[start:end]

    # 1. Создаем кнопки для каждой конференции на странице
    for item in current_items:
        # callback_data="view_conf_ID" - так мы поймем, на что нажали
        kb.add(types.InlineKeyboardButton(text=item["title"], callback_data=f"view_conf_{item['id']}"))

    # 2. Создаем кнопки пагинации внизу
    btns = []
    if page > 0:
        btns.append(types.InlineKeyboardButton("⬅️", callback_data=f"list_conf_prev_{page}"))
    btns.append(types.InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        btns.append(types.InlineKeyboardButton("➡️", callback_data=f"list_conf_next_{page}"))
    kb.row(*btns)
    return kb, total_pages

# Функция для отображения конкретной конференции
def show_conference_details(call, conf_id):
    # Ищем конференцию по ID
    conf = next((item for item in CONFERENCES_DB if item["id"] == conf_id), None)
    if not conf:
        bot.answer_callback_query(call.id, "Конференция не найдена")
        return

    # Клавиатура с кнопкой "Назад"
    kb = types.InlineKeyboardMarkup()
    # Возвращаемся на 0-ю страницу списка
    kb.add(types.InlineKeyboardButton("⬅️ Назад к списку", callback_data="back_to_list_conf_0"))

    # Редактируем сообщение, показывая детали
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
    if user_id in users and users[user_id].get('registered'):
         bot.send_message(user_id, "С возвращением!", reply_markup=main_menu_kb())
         return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("✅ Согласен на обработку ПД")
    text = "👋 <b>Добро пожаловать в Secretroom!</b>\n\nДля доступа к базе знаний нам нужно познакомиться.\n\n<i>Нажимая кнопку ниже, вы даете согласие на обработку персональных данных (ФЗ-152).</i>"
    bot.send_message(user_id, text, parse_mode="HTML", reply_markup=markup)
    bot.register_next_step_handler(message, check_pd_consent)

def check_pd_consent(message):
    if message.text == "✅ Согласен на обработку ПД":
        msg = bot.send_message(message.chat.id, "Супер! 1️⃣ Как вас зовут? (ФИО)", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_name)
    else:
        bot.send_message(message.chat.id, "Без согласия мы не можем продолжить. /start")

def process_name(message):
    users[message.from_user.id] = {"id": message.from_user.id, "name": message.text}
    msg = bot.send_message(message.from_user.id, "2️⃣ Кто вы по специальности?", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).row("Media Buyer", "Арбитражник").row("Team Lead", "Маркетолог"))
    bot.register_next_step_handler(msg, process_role)

def process_role(message):
    users[message.from_user.id]["role"] = message.text
    msg = bot.send_message(message.from_user.id, "3️⃣ В какой компании работаете?", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).row("Фриланс", "Нет компании"))
    bot.register_next_step_handler(msg, process_company)

def process_company(message):
    users[message.from_user.id]["company"] = message.text
    msg = bot.send_message(message.from_user.id, "4️⃣ Ваш опыт?", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).row("0-6 мес", "6-12 мес").row("1-3 года", "3+ лет"))
    bot.register_next_step_handler(msg, process_exp)

def process_exp(message):
    users[message.from_user.id]["exp"] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📱 Поделиться телефоном", request_contact=True), types.KeyboardButton("Пропустить"))
    msg = bot.send_message(message.from_user.id, "5️⃣ Контакт для связи:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_phone_finish)

def process_phone_finish(message):
    uid = message.from_user.id
    users[uid]["phone"] = message.contact.phone_number if message.contact else message.text
    users[uid]["registered"] = True
    bot.send_message(uid, "⏳ Сохраняю данные...", reply_markup=types.ReplyKeyboardRemove())
    save_to_sheet(users[uid])
    bot.send_message(uid, "✅ <b>Регистрация завершена!</b>\nДоступ открыт.", parse_mode="HTML", reply_markup=main_menu_kb())

# --- ОБРАБОТЧИК МЕНЮ ---
@bot.message_handler(content_types=['text'])
def handle_menu(message):
    if message.text == "📂 Конференции":
        # Отправляем сообщение с инлайн-клавиатурой конференций (1-я страница)
        kb, total = get_conferences_keyboard(page=0)
        bot.send_message(message.chat.id, "📅 <b>Выберите конференцию:</b>", parse_mode="HTML", reply_markup=kb)

    elif message.text == "🛠 Сервисы":
        # Сервисы пока оставляем простым текстом для примера
        text = "🛠 <b>Полезные сервисы:</b>\n\n" + "\n".join([f"• {s}" for s in SERVICES])
        bot.send_message(message.chat.id, text, parse_mode="HTML")

    elif message.text == "💬 Чаты":
        bot.send_message(message.chat.id, "🔓 <b>Чаты:</b>\n\n🇷🇺 CPA Secret Chat\n🇺🇸 Affiliate World", parse_mode="HTML")
    elif message.text == "👤 Мой профиль":
        u = users.get(message.from_user.id)
        if u: bot.send_message(message.chat.id, f"👤 <b>{u['name']}</b>\n{u['role']}", parse_mode="HTML")

# ==========================================
# НОВЫЙ ОБРАБОТЧИК ВСЕХ НАЖАТИЙ НА КНОПКИ
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.data == "noop":
            bot.answer_callback_query(call.id) # Просто убираем часики
            return

        # 1. Нажали на конкретную конференцию ("view_conf_id")
        if call.data.startswith("view_conf_"):
            conf_id = call.data.split("_")[2]
            show_conference_details(call, conf_id)

        # 2. Нажали пагинацию списка конференций ("list_conf_next_1" или "back_to_list_conf_0")
        elif call.data.startswith("list_conf_") or call.data.startswith("back_to_list_"):
            parts = call.data.split("_")
            action = parts[2] # "prev", "next" или "conf" (если back_to_list)
            current_page = int(parts[3])

            new_page = current_page
            if action == "next": new_page += 1
            elif action == "prev": new_page -= 1
            # Если action "conf", то new_page уже равен нужной странице (например, 0 при возврате)

            # Генерируем новую клавиатуру для новой страницы
            new_kb, total_pages = get_conferences_keyboard(page=new_page)

            # Редактируем сообщение, возвращая список
            bot.edit_message_text(
                text="📅 <b>Выберите конференцию:</b>",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=new_kb
            )

    except Exception as e:
        print(f"Callback error: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
