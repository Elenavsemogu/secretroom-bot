import os
import telebot
from telebot import types
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# --- НАСТРОЙКА ДЛЯ RENDER (ЧТОБЫ НЕ УСНУЛ) ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ---------------------------------------------

load_dotenv()
# Render сам подставит токен, если не найдет .env
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("ERROR: No token found")
else:
    print("Token found, starting bot...")

bot = telebot.TeleBot(TOKEN)
users = {}

# --- ДАННЫЕ ---
CONFERENCES = [
    "🔥 MAC Affiliate Conference 2026 (Ереван)",
    "💎 SiGMA Eurasia (Дубай)",
    "🚀 Affiliate World Europe (Барселона)",
    "🇬🇧 London Affiliate Conference", 
    "🇩🇪 iGaming Germany 2026",
    "🇷🇺 SPB CPA Life (Санкт-Петербург)",
    "🇹🇭 WAS 2026 (Бангкок)"
]

SERVICES = [
    "🛠 Keitaro (Трекер)",
    "🛠 Dolphin{anty} (Антидетект)",
    "🛠 AdHeart (Spy-сервис)",
    "🛠 Capitalist (Платежка)",
    "🛠 FBTool (Автозалив)",
    "🛠 Indigo Browser"
]

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

# --- ЛОГИКА ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id in users:
        bot.send_message(user_id, f"С возвращением, {users[user_id]['name']}! Главное меню:", reply_markup=main_menu_kb())
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("🚀 Заполнить профиль и получить доступ")
        text = "👋 <b>Добро пожаловать в Secretroom!</b>\n\nЭто закрытый клуб для специалистов iGaming.\nЧтобы получить доступ, пройдите анкету."
        bot.send_message(user_id, text, parse_mode="HTML", reply_markup=markup)
        bot.register_next_step_handler(message, process_registration_start)

def process_registration_start(message):
    if message.text == "🚀 Заполнить профиль и получить доступ":
        msg = bot.send_message(message.chat.id, "1️⃣ Как вас зовут? (ФИО)", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_name)
    else:
        start(message)

def process_name(message):
    user_id = message.from_user.id
    users[user_id] = {"name": message.text}
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
    msg = bot.send_message(user_id, "3️⃣ В какой компании/команде вы работаете?", reply_markup=markup)
    bot.register_next_step_handler(msg, process_company)

def process_company(message):
    user_id = message.from_user.id
    users[user_id]["company"] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("0-6 мес", "6-12 мес")
    markup.row("1-3 года", "3+ лет")
    msg = bot.send_message(user_id, "4️⃣ Ваш опыт в сфере?", reply_markup=markup)
    bot.register_next_step_handler(msg, process_exp)

def process_exp(message):
    user_id = message.from_user.id
    users[user_id]["exp"] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("📱 Поделиться телефоном", request_contact=True)
    btn2 = types.KeyboardButton("Пропустить")
    markup.add(btn1, btn2)
    msg = bot.send_message(user_id, "5️⃣ Контакт для связи (опционально):", reply_markup=markup)
    bot.register_next_step_handler(msg, process_phone_finish)

def process_phone_finish(message):
    user_id = message.from_user.id
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = "Не указан"
    users[user_id]["phone"] = phone
    text = "✅ <b>Регистрация завершена!</b>\nДоступ к базе открыт."
    bot.send_message(user_id, text, parse_mode="HTML", reply_markup=main_menu_kb())

@bot.message_handler(content_types=['text'])
def handle_menu(message):
    user_id = message.from_user.id
    if user_id not in users:
        # Если бота перезагрузили, а пользователь пишет - не требуем регистрацию заново, просто пускаем в меню
        # (в идеале нужна база данных, но пока так)
        start(message)
        return

    if message.text == "📂 Конференции":
        send_list_page(message.chat.id, "conf", 0)
    elif message.text == "🛠 Сервисы":
        send_list_page(message.chat.id, "serv", 0)
    elif message.text == "💬 Чаты":
        text = "🔓 <b>Доступ открыт!</b>\nСписок чатов:\n\n<b>🇷🇺 RU Community:</b>\n• CPA Secret Chat\n• iGaming Insider\n\n<b>🇺🇸 EN Community:</b>\n• Affiliate World"
        bot.send_message(user_id, text, parse_mode="HTML")
    elif message.text == "👤 Мой профиль":
        u = users[user_id]
        text = f"👤 <b>Ваш профиль:</b>\n\n<b>Имя:</b> {u['name']}\n<b>Роль:</b> {u['role']}\n<b>Компания:</b> {u['company']}\n<b>Опыт:</b> {u['exp']}\n<b>Телефон:</b> {u['phone']}"
        bot.send_message(user_id, text, parse_mode="HTML")

def send_list_page(chat_id, category, page):
    items = CONFERENCES if category == "conf" else SERVICES
    title = "📅 Конференции 2026" if category == "conf" else "🛠 Полезные сервисы"
    items_per_page = 3
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
        new_page = current_page + 1 if action == "next" else current_page - 1
        bot.edit_message_text(call.message.text, call.message.chat.id, call.message.message_id, reply_markup=get_pagination_kb(new_page, (len(CONFERENCES if category=="conf" else SERVICES)+2)//3, category))
        # Упрощенная логика пагинации для примера, чтобы не усложнять код
        send_list_page(call.message.chat.id, category, new_page)
        bot.delete_message(call.message.chat.id, call.message.message_id) # Удаляем старое, чтобы не дублировать
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    keep_alive() # Запускаем веб-сервер
    bot.infinity_polling()
