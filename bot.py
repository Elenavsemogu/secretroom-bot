import os
import telebot
from telebot import types
from dotenv import load_dotenv

# Загружаем настройки
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("ОШИБКА: Токен не найден в файле .env")
    exit()

bot = telebot.TeleBot(TOKEN)

# --- ИМИТАЦИЯ БАЗЫ ДАННЫХ ---
users = {}

# --- КОНТЕНТ (ЗАГЛУШКИ ДЛЯ ДЕМО) ---
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
    """Генератор кнопок пагинации (⬅️ 1/5 ➡️)"""
    kb = types.InlineKeyboardMarkup()
    btns = []
    if current_page > 0:
        btns.append(types.InlineKeyboardButton("⬅️", callback_data=f"{prefix}_prev_{current_page}"))
    
    btns.append(types.InlineKeyboardButton(f"{current_page+1}/{total_pages}", callback_data="noop"))
    
    if current_page < total_pages - 1:
        btns.append(types.InlineKeyboardButton("➡️", callback_data=f"{prefix}_next_{current_page}"))
    
    kb.row(*btns)
    return kb

# --- ЛОГИКА РЕГИСТРАЦИИ ---

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    
    # ПРОВЕРКА НА ДУБЛИ
    if user_id in users:
        bot.send_message(user_id, f"С возвращением, {users[user_id]['name']}! Главное меню:", reply_markup=main_menu_kb())
    else:
        # Начинаем регистрацию
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("🚀 Заполнить профиль и получить доступ")
        
        text = (
            "👋 <b>Добро пожаловать в Secretroom!</b>\n\n"
            "Это закрытый клуб для специалистов iGaming.\n"
            "Чтобы получить доступ к базе конференций и чатов, пройдите короткую анкету."
        )
        msg = bot.send_message(user_id, text, parse_mode="HTML", reply_markup=markup)
        bot.register_next_step_handler(msg, process_registration_start)

def process_registration_start(message):
    if message.text == "🚀 Заполнить профиль и получить доступ":
        msg = bot.send_message(message.chat.id, "1️⃣ Как вас зовут? (ФИО)", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_name)
    else:
        start(message)

def process_name(message):
    user_id = message.from_user.id
    name = message.text
    users[user_id] = {"name": name}
    
    # Шаг 2: Роль
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Media Buyer", "Арбитражник")
    markup.row("Team Lead", "Маркетолог")
    markup.row("Другое")
    
    msg = bot.send_message(user_id, "2️⃣ Кто вы по специальности?", reply_markup=markup)
    bot.register_next_step_handler(msg, process_role)

def process_role(message):
    user_id = message.from_user.id
    users[user_id]["role"] = message.text
    
    # Шаг 3: Компания
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Фриланс", "Нет компании")
    
    msg = bot.send_message(
        user_id, 
        "3️⃣ В какой компании/команде вы работаете?\n(Напишите название или выберите вариант)", 
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_company)

def process_company(message):
    user_id = message.from_user.id
    users[user_id]["company"] = message.text
    
    # Шаг 4: Опыт
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("0-6 мес", "6-12 мес")
    markup.row("1-3 года", "3+ лет")
    
    msg = bot.send_message(user_id, "4️⃣ Ваш опыт в сфере?", reply_markup=markup)
    bot.register_next_step_handler(msg, process_exp)

def process_exp(message):
    user_id = message.from_user.id
    users[user_id]["exp"] = message.text
    
    # Шаг 5: Контакт
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
    
    # Финиш
    text = (
        "✅ <b>Регистрация завершена!</b>\n"
        "Доступ к базе открыт."
    )
    bot.send_message(user_id, text, parse_mode="HTML", reply_markup=main_menu_kb())

# --- ОБРАБОТКА МЕНЮ ---

@bot.message_handler(content_types=['text'])
def handle_menu(message):
    user_id = message.from_user.id
    if user_id not in users:
        bot.send_message(user_id, "Сначала нажмите /start")
        return

    if message.text == "📂 Конференции":
        send_list_page(message.chat.id, "conf", 0)
        
    elif message.text == "🛠 Сервисы":
        send_list_page(message.chat.id, "serv", 0)
        
    elif message.text == "💬 Чаты":
        # ЗДЕСЬ ИЗМЕНЕНИЕ: ВЫДАЕМ СПИСОК СРАЗУ
        text = (
            "🔓 <b>Доступ открыт!</b>\n"
            "Вот список закрытых чатов для участников клуба:\n\n"
            "<b>🇷🇺 RU Community:</b>\n"
            "• <a href='https://t.me/telegram'>CPA Secret Chat</a>\n"
            "• <a href='https://t.me/telegram'>iGaming Insider</a>\n"
            "• <a href='https://t.me/telegram'>Арбитраж Трафика (Private)</a>\n\n"
            "<b>🇺🇸 EN Community:</b>\n"
            "• <a href='https://t.me/telegram'>Affiliate World</a>\n"
            "• <a href='https://t.me/telegram'>Media Buying Global</a>"
        )
        bot.send_message(user_id, text, parse_mode="HTML", disable_web_page_preview=True)
        
    elif message.text == "👤 Мой профиль":
        u = users[user_id]
        text = (
            f"👤 <b>Ваш профиль:</b>\n\n"
            f"<b>Имя:</b> {u['name']}\n"
            f"<b>Роль:</b> {u['role']}\n"
            f"<b>Компания:</b> {u['company']}\n"
            f"<b>Опыт:</b> {u['exp']}\n"
            f"<b>Телефон:</b> {u['phone']}\n"
        )
        bot.send_message(user_id, text, parse_mode="HTML")

# --- ПАГИНАЦИЯ ---

def send_list_page(chat_id, category, page):
    items = CONFERENCES if category == "conf" else SERVICES
    title = "📅 Конференции 2026" if category == "conf" else "🛠 Полезные сервисы"
    
    items_per_page = 3
    total_pages = (len(items) + items_per_page - 1) // items_per_page
    
    start = page * items_per_page
    end = start + items_per_page
    page_items = items[start:end]
    
    text_lines = [f"<b>{title} (Стр. {page+1}/{total_pages})</b>\n"]
    for item in page_items:
        text_lines.append(f"• {item}")
        
    text = "\n".join(text_lines)
    kb = get_pagination_kb(page, total_pages, category)
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.data == "noop": return
            
        category, action, current_page = call.data.split("_")
        current_page = int(current_page)
        
        new_page = current_page
        if action == "next":
            new_page += 1
        elif action == "prev":
            new_page -= 1
            
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_list_page(call.message.chat.id, category, new_page)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()