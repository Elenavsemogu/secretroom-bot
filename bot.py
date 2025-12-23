import os
import json
import telebot
from telebot import types
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- ВЕБ-СЕРВЕР (Нужен для Render, чтобы он считал сервис живым) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- НАСТРОЙКИ ---
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_JSON = os.getenv("GOOGLE_SHEETS_JSON") 
SHEET_NAME = "SecretRoomData" # Если назвала таблицу иначе, поменяй тут

bot = telebot.TeleBot(TOKEN)
users = {}

# --- СОХРАНЕНИЕ В ТАБЛИЦУ ---
def save_to_sheet(user_data):
    try:
        if not GOOGLE_JSON:
            print("Ошибка: Нет ключа Google")
            return
        
        # Превращаем текст ключа обратно в словарь
        creds_dict = json.loads(GOOGLE_JSON)
        scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Открываем таблицу
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
        print(f"Данные {user_data['name']} сохранены.")
    except Exception as e:
        print(f"ОШИБКА ЗАПИСИ: {e}")

# --- КЛАВИАТУРА МЕНЮ ---
def main_menu_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📂 Конференции", "🛠 Сервисы")
    kb.row("💬 Чаты", "👤 Мой профиль")
    return kb

# --- ЛОГИКА БОТА ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    # Сразу спрашиваем согласие
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("✅ Согласен на обработку персональных данных")
    
    text = (
        "👋 <b>Добро пожаловать в Secretroom!</b>\n\n"
        "Для доступа к закрытому клубу iGaming нам нужно задать пару вопросов.\n\n"
        "<i>Нажимая кнопку ниже, вы даете согласие на обработку персональных данных в соответствии с ФЗ-152.</i>"
    )
    bot.send_message(user_id, text, parse_mode="HTML", reply_markup=markup)
    bot.register_next_step_handler(message, check_pd_consent)

def check_pd_consent(message):
    if message.text == "✅ Согласен на обработку персональных данных":
        msg = bot.send_message(message.chat.id, "Отлично! 1️⃣ Как вас зовут? (ФИО)", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_name)
    else:
        bot.send_message(message.chat.id, "Без согласия мы не можем продолжить. Напишите /start, если передумаете.")

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
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text 
    
    users[user_id]["phone"] = phone
    
    bot.send_message(user_id, "⏳ Сохраняем ваши данные...", reply_markup=types.ReplyKeyboardRemove())
    
    # Запись в таблицу
    save_to_sheet(users[user_id])
    
    text = "✅ <b>Регистрация завершена!</b>\nДоступ к базе открыт."
    bot.send_message(user_id, text, parse_mode="HTML", reply_markup=main_menu_kb())

# --- ОБРАБОТЧИК МЕНЮ ---
@bot.message_handler(content_types=['text'])
def handle_menu(message):
    if message.text == "📂 Конференции":
         bot.send_message(message.chat.id, "Список конференций: MAC 2026, SiGMA, AWE...")
    elif message.text == "👤 Мой профиль":
        u = users.get(message.from_user.id)
        if u:
            bot.send_message(message.chat.id, f"👤 <b>{u['name']}</b>\nРоль: {u['role']}", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "Сначала пройдите регистрацию /start")
    elif message.text == "🛠 Сервисы":
        bot.send_message(message.chat.id, "Полезные сервисы: Keitaro, Dolphin...")
    elif message.text == "💬 Чаты":
        bot.send_message(message.chat.id, "Чаты: @example_chat")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
