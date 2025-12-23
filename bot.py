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
# ПОЛНАЯ БАЗА ДАННЫХ КОНФЕРЕНЦИЙ (10 шт)
# ==========================================
CONFERENCES_DB = [
    {
        "id": "mac26",
        "title": "🔥 MAC Yerevan 2026",
        "details": "🇦🇲 <b>MAC Affiliate Conference 2026 (Ереван)</b>\n\nЛегендарная конференция, собирающая топов рынка СНГ и Европы. Огромная экспо-зона, крутые спикеры и, конечно, самые масштабные афтепати в индустрии.\n\n📅 <b>Даты:</b> Май 2026\n🔗 <b>Сайт:</b> mac.affiliate"
    },
    {
        "id": "sigma_dubai",
        "title": "💎 SiGMA Eurasia",
        "details": "🇦🇪 <b>SiGMA Eurasia (Дубай)</b>\n\nЦентр притяжения iGaming и крипто-индустрии на Ближнем Востоке. Идеальное место для поиска инвесторов и выхода на рынки Азии и Африки.\n\n📅 <b>Даты:</b> Февраль 2026\n🔗 <b>Сайт:</b> sigma.world/eurasia"
    },
    {
        "id": "awe_bcn",
        "title": "🚀 AW Europe",
        "details": "🇪🇸 <b>Affiliate World Europe (Барселона)</b>\n\nГлавное событие лета. Двухдневный интенсив: e-commerce, нутра, дейтинг и технологии. Сюда едут за трендами мирового масштаба.\n\n📅 <b>Даты:</b> Июль 2026\n🔗 <b>Сайт:</b> affiliateworldconferences.com/europe"
    },
    {
        "id": "lac",
        "title": "🇬🇧 iGB Affiliate (London)",
        "details": "🇬🇧 <b>iGB Affiliate London</b>\n\nСтарейшая и самая респектабельная конференция. Строгий B2B формат, фокус на SEO и партнерских программах в белых нишах.\n\n📅 <b>Даты:</b> Февраль 2026\n🔗 <b>Сайт:</b> london.igbaffiliate.com"
    },
    {
        "id": "igaming_de",
        "title": "🇩🇪 iGaming Germany",
        "details": "🇩🇪 <b>iGaming Germany 2026</b>\n\nСпециализированная конференция по немецкому рынку (DACH). Обсуждение регуляции, лицензий и особенностей работы в Германии.\n\n📅 <b>Даты:</b> Июнь 2026\n🔗 <b>Сайт:</b> igaminggermany.com"
    },
    {
        "id": "spb_cpa",
        "title": "🇷🇺 SPB CPA Life",
        "details": "🇷🇺 <b>SPB CPA Life (Санкт-Петербург)</b>\n\nДушевная и масштабная тусовка в Питере. Акцент на CPA-рынок России и СНГ. Нетворкинг на теплоходах и в лучших клубах города.\n\n📅 <b>Даты:</b> Август 2026\n🔗 <b>Сайт:</b> cpalife.su"
    },
    {
        "id": "was_bkk",
        "title": "🇹🇭 WAS 2026 (Bangkok)",
        "details": "🇹🇭 <b>World Affiliate Show (Бангкок)</b>\n\nМолодая, но шумная конференция в Азии. Отличный повод совместить работу с отдыхом в Таиланде и найти партнеров под бурж.\n\n📅 <b>Даты:</b> Октябрь 2026\n🔗 <b>Сайт:</b> worldaffiliateshow.com"
    },
    {
        "id": "asw_vegas",
        "title": "🇺🇸 Affiliate Summit West",
        "details": "🇺🇸 <b>Affiliate Summit West (Las Vegas)</b>\n\nКрупнейшая конференция в США. Тысячи маркетологов, фокус на лидген, e-com и белые вертикали. Проходит в легендарных отелях Вегаса.\n\n📅 <b>Даты:</b> Январь 2026\n🔗 <b>Сайт:</b> affiliatesummit.com/west"
    },
    {
        "id": "bis_sigma",
        "title": "🇧🇷 BiS SiGMA Americas",
        "details": "🇧🇷 <b>BiS SiGMA Americas (Sao Paulo)</b>\n\nВорота в Латинскую Америку. Бразилия — один из самых горячих рынков сейчас (iGaming, Betting). Обязательно к посещению, если льете на ЛатАм.\n\n📅 <b>Даты:</b> Апрель 2026\n🔗 <b>Сайт:</b> sigma.world/americas"
    },
    {
        "id": "igb_live",
        "title": "🇳🇱 iGB Live! (Amsterdam)",
        "details": "🇳🇱 <b>iGB Live! (Амстердам)</b>\n\nЛетняя встреча топов iGaming индустрии. Более расслабленная атмосфера, чем в Лондоне, но не менее продуктивная.\n\n📅 <b>Даты:</b> Июль 2026\n🔗 <b>Сайт:</b> igblive.com"
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
        row = [user_data.get('id',''), user_data.get('name',''), user_data.get('role',''), user_data.get('company',''), user_data.get('exp',''), user_data.get('phone',''), "ДА"]
        sheet.append_row(row)
    except Exception as e: print(f"Google Sheet Error: {e}")

# --- ГЛАВНОЕ МЕНЮ ---
def main_menu_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📂 Конференции", "🛠 Сервисы")
    kb.row("💬 Чаты", "👤 Мой профиль")
    return kb

# --- ФУНКЦИИ СПИСКОВ (КНОПКИ) ---
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

def show_conference_details(call, conf_id):
    conf = next((item for item in CONFERENCES_DB if item["id"] == conf_id), None)
    if not conf:
        bot.answer_callback_query(call.id, "Конференция не найдена")
        return

    kb = types.InlineKeyboardMarkup()
    # ИСПРАВЛЕНИЕ: изменил callback_data на такой же формат, как у перелистывания страниц
    # Теперь он не будет ломать split()
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
    # Условие проверки регистрации убрал, чтобы ты могла тестировать всегда
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
        kb = get_conferences_keyboard(page=0)
        bot.send_message(message.chat.id, "📅 <b>Выберите конференцию:</b>", parse_mode="HTML", reply_markup=kb)

    elif message.text == "🛠 Сервисы":
        text = "🛠 <b>Полезные сервисы:</b>\n\n" + "\n".join([f"• {s}" for s in SERVICES])
        bot.send_message(message.chat.id, text, parse_mode="HTML")

    elif message.text == "💬 Чаты":
        bot.send_message(message.chat.id, "🔓 <b>Чаты:</b>\n\n🇷🇺 CPA Secret Chat\n🇺🇸 Affiliate World", parse_mode="HTML")
    elif message.text == "👤 Мой профиль":
        u = users.get(message.from_user.id)
        if u: bot.send_message(message.chat.id, f"👤 <b>{u['name']}</b>\n{u['role']}", parse_mode="HTML")

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

        # Теперь сюда попадает и листание, и кнопка "Назад"
        elif call.data.startswith("list_conf_"):
            parts = call.data.split("_")
            # list_conf_next_0 -> parts[2] = "next", parts[3] = "0"
            # list_conf_start_0 -> parts[2] = "start", parts[3] = "0"
            
            action = parts[2]
            current_page = int(parts[3])

            new_page = current_page
            if action == "next": new_page += 1
            elif action == "prev": new_page -= 1
            # Если action "start", то страница остается 0, ничего менять не надо

            kb = get_conferences_keyboard(page=new_page)
            
            # Редактируем сообщение (возвращаем список)
            bot.edit_message_text(
                text="📅 <b>Выберите конференцию:</b>",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=kb
            )

    except Exception as e:
        print(f"Error: {e}")
        bot.answer_callback_query(call.id, "Ошибка навигации")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
