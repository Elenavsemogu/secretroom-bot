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
SHEET_NAME = "SecretRoomData" # Имя твоей таблицы

bot = telebot.TeleBot(TOKEN)
users = {}

# --- СПИСКИ ДАННЫХ (ВЕРНУЛ ВСЁ НА МЕСТО) ---
CONFERENCES = [
    "🔥 MAC Affiliate Conference 2026 (Ереван)",
    "💎 SiGMA Eurasia (Дубай)",
    "🚀 Affiliate World Europe (Барселона)",
    "🇬🇧 London Affiliate Conference", 
    "🇩🇪 iGaming Germany 2026",
    "🇷🇺 SPB CPA Life (Санкт-Петербург)",
    "🇹🇭 WAS 2026 (Бангкок)",
    "🇺🇸 Affiliate Summit West (Las Vegas)",
    "🇧🇷 BiS SiGMA Americas (Sao Paulo)",
    "🇳🇱 iGB Lived (Amsterdam)"
]

SERVICES = [
    "🛠 Keitaro (Трекер)",
    "🛠 Dolphin{anty} (Антидетект)",
    "🛠 AdHeart (Spy-сервис)",
    "🛠 Capitalist (Платежка)",
    "🛠 FBTool (Автозалив)",
    "🛠 Indigo Browser",
    "🛠 Octo Browser",
    "🛠 Multilogin",
    "🛠 Poshmark (Accounts)",
    "🛠 SMS Activate"
]

# --- ЗАПИСЬ В GOOGLE ТАБЛИЦУ ---
def save_to_sheet(user_data):
    try:
        if not GOOGLE_JSON:
            print("Ошибка: Нет ключа Google")
            return
        
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
            "ДА" # Согласие
        ]
        sheet.append_row(row)
        print(f"User {user_data['name']} saved to sheet.")
    except Exception as e:
        print(f"Google Sheet Error: {e}")

# --- КЛАВИАТУРЫ ---
def main_menu_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📂 Конференции", "🛠 Сервисы")
    kb.row("💬 Чаты", "👤 Мой профиль")
    return kb

def get_pagination_kb(current_page, total_pages, prefix):
    kb = types.InlineKeyboardMarkup()
    btns = []
    if current_page > 0:
        btns.append(types.InlineKeyboardButton("⬅️", callback_data=f"{prefix}_prev_{current_page}"))
    btns.append(types.InlineKeyboardButton(f"{current_page+1}/{total_pages}", callback_data="noop"))
    if current_page < total_pages - 1:
        btns.append(types.InlineKeyboardButton("➡️", callback_data=f"{prefix}_next_{current_page}"))
    kb.row(*btns)
    return kb

# --- ЛОГИКА РЕГИСТРАЦИИ (С ПД) ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    # Если пользователь уже есть (в памяти), сразу даем меню. 
    # (Для надежности можно убрать условие, если хочешь всегда опрашивать)
    if user_id in users and users[user_id].get('registered'):
         bot.send_message(user_id, "С возвращением!", reply_markup=main_menu_kb())
         return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("✅ Согласен на обработку персональных данных")
    
    text = (
        "👋 <b>Добро пожаловать в Secretroom!</b>\n\n"
        "Для доступа к базе знаний нам нужно познакомиться.\n\n"
        "<i>Нажимая кнопку ниже, вы даете согласие на обработку персональных данных (ФЗ-152).</i>"
    )
    bot.send_message(user_id, text, parse_mode="HTML", reply_markup=markup)
    bot.register_next_step_handler(message, check_pd_consent)

def check_pd_consent(message):
    if message.text == "✅ Согласен на обработку персональных данных":
        msg = bot.send_message(message.chat.id, "Супер! 1️⃣ Как вас зовут? (ФИО)", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_name)
    else:
        bot.send_message(message.chat.id, "Без согласия мы не можем продолжить. Жмите /start, если передумаете.")

def process_name(message):
    user_id = message.from_user.id
    users[user_id] = {"id": user_id, "name": message.text}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Media Buyer", "Арбитражник")
    markup.row("Team Lead", "Маркетолог")
    markup.row("Другое")
    msg = bot.send_message(user_id, "2️⃣ Кто вы по специальности?", reply_markup=markup)
    bot.register_next_step_handler(msg, process_role)

def process_role(message):
    user_id = message.from_user.id
    users[user_id]["role"] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Фриланс", "Нет компании")
    msg = bot.send_message(user_id, "3️⃣ В какой компании работаете?", reply_markup=markup)
    bot.register_next_step_handler(msg, process_company)

def process_company(message):
    user_id = message.from_user.id
    users[user_id]["company"] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("0-6 мес", "6-12 мес")
    markup.row("1-3 года", "3+ лет")
    msg = bot.send_message(user_id, "4️⃣ Ваш опыт?", reply_markup=markup)
    bot.register_next_step_handler(msg, process_exp)

def process_exp(message):
    user_id = message.from_user.id
    users[user_id]["exp"] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("📱 Поделиться телефоном", request_contact=True)
    btn2 = types.KeyboardButton("Пропустить")
    markup.add(btn1, btn2)
    msg = bot.send_message(user_id, "5️⃣ Контакт для связи:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_phone_finish)

def process_phone_finish(message):
    user_id = message.from_user.id
    phone = message.contact.phone_number if message.contact else message.text
    users[user_id]["phone"] = phone
    users[user_id]["registered"] = True
    
    bot.send_message(user_id, "⏳ Сохраняю данные...", reply_markup=types.ReplyKeyboardRemove())
    
    # Сохраняем в Google
    save_to_sheet(users[user_id])
    
    text = "✅ <b>Регистрация завершена!</b>\nДоступ открыт."
    bot.send_message(user_id, text, parse_mode="HTML", reply_markup=main_menu_kb())

# --- ЛОГИКА МЕНЮ (СПИСКИ ВЕРНУЛИСЬ!) ---
@bot.message_handler(content_types=['text'])
def handle_menu(message):
    if message.text == "📂 Конференции":
        send_list_page(message.chat.id, "conf", 0)
    elif message.text == "🛠 Сервисы":
        send_list_page(message.chat.id, "serv", 0)
    elif message.text == "💬 Чаты":
        text = "🔓 <b>Полезные чаты:</b>\n\n<b>🇷🇺 RU:</b>\n• CPA Secret Chat\n• iGaming Insider\n\n<b>🇺🇸 EN:</b>\n• Affiliate World"
        bot.send_message(message.chat.id, text, parse_mode="HTML")
    elif message.text == "👤 Мой профиль":
        u = users.get(message.from_user.id)
        if u:
            text = f"👤 <b>Профиль:</b>\n{u['name']}\n{u['role']} | {u['company']}"
            bot.send_message(message.chat.id, text, parse_mode="HTML")
        else:
             bot.send_message(message.chat.id, "Нажмите /start")

def send_list_page(chat_id, category, page):
    items = CONFERENCES if category == "conf" else SERVICES
    title = "📅 Конференции 2026" if category == "conf" else "🛠 Полезные сервисы"
    items_per_page = 4
    total_pages = (len(items) + items_per_page - 1) // items_per_page
    
    if page < 0: page = 0
    if page >= total_pages: page = total_pages - 1
    
    start = page * items_per_page
    page_items = items[start:start + items_per_page]
    
    text_lines = [f"<b>{title} (Стр. {page+1}/{total_pages})</b>\n"]
    for item in page_items:
        text_lines.append(f"• {item}")
    
    kb = get_pagination_kb(page, total_pages, category)
    bot.send_message(chat_id, "\n".join(text_lines), parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.data == "noop": return
        category, action, current_page = call.data.split("_")
        current_page = int(current_page)
        
        items = CONFERENCES if category == "conf" else SERVICES
        items_per_page = 4
        total_pages = (len(items) + items_per_page - 1) // items_per_page
        
        new_page = current_page + 1 if action == "next" else current_page - 1
        
        if 0 <= new_page < total_pages:
            start = new_page * items_per_page
            page_items = items[start:start + items_per_page]
            title = "📅 Конференции 2026" if category == "conf" else "🛠 Полезные сервисы"
            
            text_lines = [f"<b>{title} (Стр. {new_page+1}/{total_pages})</b>\n"]
            for item in page_items:
                text_lines.append(f"• {item}")
            
            bot.edit_message_text(
                "\n".join(text_lines),
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=get_pagination_kb(new_page, total_pages, category)
            )
    except Exception as e:
        print(f"Callback error: {e}")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
