import os
import requests
from telebot import TeleBot, types
from datetime import datetime
from telebot.apihelper import ApiTelegramException
from telebot import types
from telebot import apihelper
apihelper.READ_TIMEOUT = 60
apihelper.CONNECT_TIMEOUT = 15
apihelper.SESSION_TIME_TO_LIVE = 300

def safe_send(chat_id, text, **kwargs):
    try:
        return bot.send_message(chat_id, text, **kwargs)
    except ApiTelegramException as e:
        print(f"[safe_send] {e}")
        return None

def is_group(chat_id: int) -> bool:
    return int(chat_id) < 0
    
# ===== Конфигурация =====
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Переменная окружения BOT_TOKEN не задана")

# chat_id вашей админ-группы (оставь как у тебя)
ADMIN_GROUP_ID = -4948043121

bot = TeleBot(TOKEN, parse_mode="HTML")
bot.remove_webhook()  # важно перед infinity_polling

# Память на сессию пользователя
user_data = {}  # {chat_id: {"name":..., "adults":..., "children":..., "animals":..., "route":..., "phone":..., "price":...}}

# ===== Утилиты =====
def get_tariffs(route: str):
    """Цены за одного: (adult, child, pet)"""
    if "Батуми" in route:
        return 6000, 4000, 1000
    if "Кутаиси" in route:
        return 5000, 3500, 800
    if "Степанцминда" in route:
        return 2000, 1500, 500
    # Владикавказ — Тбилиси и всё остальное
    return 3000, 2000, 500

def calculate_price(adults, children, animals, route):
    price_adult, price_child, price_pet = get_tariffs(route)
    total = adults * price_adult + children * price_child + animals * price_pet
    return total, price_adult, price_child, price_pet

def ensure_session(chat_id):
    user_data.setdefault(chat_id, {
        "name": None,
        "adults": None,
        "children": None,
        "animals": None,
        "route": None,
        "phone": None,
        "price": None,
    })

# ===== Служебные команды =====
@bot.message_handler(commands=['id'])
def chat_id_cmd(message):
    chat = message.chat
    user = message.from_user
    lines = [
        f"Тип чата: <b>{chat.type}</b>",
        f"Chat ID: <code>{chat.id}</code>",
        f"User ID: <code>{user.id}</code>",
    ]
    if chat.type in ('group', 'supergroup'):
        lines.append(f"Название чата: {chat.title}")
    bot.reply_to(message, "\n".join(lines))

@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    ensure_session(chat_id)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("Расчёт стоимости"))
    bot.send_message(chat_id, "Добро пожаловать! Выберите действие:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "Расчёт стоимости")
def start_flow(message):
    chat_id = message.chat.id
    ensure_session(chat_id)
    msg = bot.send_message(chat_id, "Как вас зовут?")
    bot.register_next_step_handler(msg, get_name)

def get_name(message):
    chat_id = message.chat.id
    ensure_session(chat_id)
    user_data[chat_id]["name"] = (message.text or "").strip() or "Не указано"
    msg = bot.send_message(chat_id, "Сколько взрослых пассажиров? (числом)")
    bot.register_next_step_handler(msg, get_adults)

def get_adults(message):
    chat_id = message.chat.id
    ensure_session(chat_id)
    try:
        user_data[chat_id]["adults"] = max(0, int(message.text))
    except Exception:
        msg = bot.send_message(chat_id, "Пожалуйста, введите число. Сколько взрослых?")
        return bot.register_next_step_handler(msg, get_adults)
    msg = bot.send_message(chat_id, "Сколько детей? (числом)")
    bot.register_next_step_handler(msg, get_children)

def get_children(message):
    chat_id = message.chat.id
    ensure_session(chat_id)
    try:
        user_data[chat_id]["children"] = max(0, int(message.text))
    except Exception:
        msg = bot.send_message(chat_id, "Пожалуйста, введите число. Сколько детей?")
        return bot.register_next_step_handler(msg, get_children)
    msg = bot.send_message(chat_id, "Сколько животных? (числом)")
    bot.register_next_step_handler(msg, get_animals)

def get_animals(message):
    chat_id = message.chat.id
    ensure_session(chat_id)
    try:
        user_data[chat_id]["animals"] = max(0, int(message.text))
    except Exception:
        msg = bot.send_message(chat_id, "Пожалуйста, введите число. Сколько животных?")
        return bot.register_next_step_handler(msg, get_animals)

    return ask_route(chat_id)

    # выбор маршрута
from telebot import types

ROUTES = [
    "Владикавказ — Тбилиси",
    "Владикавказ — Степанцминда",
    "Владикавказ — Кутаиси",
    "Владикавказ — Батуми",
]

def ask_route(chat_id: int):
    kb = types.InlineKeyboardMarkup()
    for r in ROUTES:
        kb.add(types.InlineKeyboardButton(r, callback_data="route_" + r))
    bot.send_message(chat_id, "Выберите маршрут:", reply_markup=kb)
@bot.callback_query_handler(func=lambda c: c.data.startswith("route_"))
def on_route_selected(call):
    chat_id = call.message.chat.id
    route = call.data.split("route_", 1)[1]

    user_data.setdefault(chat_id, {})
    user_data[chat_id]["route"] = route

    adults   = int(user_data[chat_id].get("adults", 1))
    children = int(user_data[chat_id].get("children", 0))
    animals  = int(user_data[chat_id].get("animals", 0))

    total = calculate_price(adults, children, animals, route)
    show_price(chat_id, route, total)  # рисует цену + "Оформить заявку"
    
    # показываем цену + кнопку
    text = f"Стоимость поездки по маршруту <b>{route}</b>: <b>{total} руб.</b>"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Оформить заявку", callback_data="apply_booking"))
    safe_send(chat_id, text + "\n\nНажмите, чтобы оформить заявку:", reply_markup=markup, parse_mode="HTML")
    

# 1) Показ цены + кнопка "Оформить заявку"
def show_price(chat_id, route, total):
    text = f"Стоимость поездки по маршруту <b>{route}</b>: <b>{total} руб.</b>"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Оформить заявку", callback_data="apply_booking"))
    safe_send(chat_id, text + "\n\nНажмите, чтобы оформить заявку:",
              reply_markup=markup, parse_mode="HTML")

# 2) Хендлер кнопки — один!
@bot.callback_query_handler(func=lambda c: c.data == "apply_booking")
def cb_apply_booking(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    ask_phone(chat_id=chat_id, user_id=user_id)   # <— используем одну функцию

# 3) Функция запроса телефона — одна! (без ensure_session)
def ask_phone(chat_id: int, user_id: int):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("Отправить номер телефона", request_contact=True))

    if is_group(chat_id):
        safe_send(chat_id, "Чтобы оформить заявку, продолжим в личных сообщениях. Я написал(а) вам в личку.")
        pm = safe_send(user_id, "Пожалуйста, отправьте номер телефона для заявки кнопкой ниже.", reply_markup=kb)
        if pm is None:
            safe_send(chat_id, "Откройте мой профиль и нажмите «Start», затем вернитесь.")
        return

    safe_send(chat_id, "Пожалуйста, отправьте номер телефона для заявки кнопкой ниже.", reply_markup=kb)

# 4) Обработчик контакта
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if is_group(chat_id):
        safe_send(chat_id, "Пожалуйста, отправьте номер телефона мне в личные сообщения.")
        return

    if message.contact and message.contact.phone_number:
        phone = message.contact.phone_number
        user_data.setdefault(user_id, {})
        user_data[user_id]["phone"] = phone

        hide = types.ReplyKeyboardRemove()
        safe_send(chat_id, "Спасибо! Номер получен. Укажите локацию выезда:", reply_markup=hide)

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Аэропорт", callback_data="loc_airport"),
            types.InlineKeyboardButton("Ж/д вокзал", callback_data="loc_station"),
            types.InlineKeyboardButton("С адреса во Владикавказе", callback_data="loc_address"),
            types.InlineKeyboardButton("Метро Дидубе", callback_data="loc_didube"),
            types.InlineKeyboardButton("Другое", callback_data="loc_other"),
        )
        safe_send(chat_id, "Откуда будет выезд?", reply_markup=markup)
    else:
        safe_send(chat_id, "Не вижу номер. Нажмите кнопку «Отправить номер телефона».")
        
@bot.callback_query_handler(func=lambda c: c.data.startswith("loc:"))
def finish_booking(call):
    chat_id = call.message.chat.id
    ensure_session(chat_id)
    d = user_data[chat_id]
    location = call.data.split("loc:", 1)[1]

    # Безопасные значения по умолчанию
    name = d.get("name") or "Не указано"
    route = d.get("route") or "-"
    adults = d.get("adults") or 0
    children = d.get("children") or 0
    animals = d.get("animals") or 0
    phone = d.get("phone") or "-"
    total, pa, pc, pp = calculate_price(adults, children, animals, route)

    # Сообщение админу (в группу)
    admin_text = (
        "🧾 <b>Новая заявка</b>:\n"
        f"Имя: {name}\n"
        f"Маршрут: {route}\n"
        f"Телефон: <a href='tel:{phone}'>{phone}</a>\n"
        f"Место выезда: {location}\n"
        f"Взрослые: {adults} × {pa} = {adults * pa} руб.\n"
        f"Дети: {children} × {pc} = {children * pc} руб.\n"
        f"Животные: {animals} × {pp} = {animals * pp} руб.\n"
        f"<b>Итоговая стоимость: {total} руб.</b>"
    )
    bot.send_message(ADMIN_GROUP_ID, admin_text, disable_web_page_preview=True)

    # Подтверждение пользователю (с тем же разбором)
    user_text = (
        "✅ Ваша заявка отправлена администраторам. Мы с вами свяжемся.\n\n"
        f"Взрослые: {adults} × {pa} = {adults * pa} руб.\n"
        f"Дети: {children} × {pc} = {children * pc} руб.\n"
        f"Животные: {animals} × {pp} = {animals * pp} руб.\n"
        f"<b>Итоговая стоимость: {total} руб.</b>"
    )
    bot.send_message(chat_id, user_text)

# ===== Запуск =====
import time

if __name__ == "__main__":
    bot.remove_webhook()
    while True:
        try:
            print("[polling] bot is running…")
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=50)
        except requests.exceptions.ReadTimeout:
            print("[polling] ReadTimeout — пробую снова через 3с"); time.sleep(3)
        except requests.exceptions.ConnectionError as e:
            print(f"[polling] ConnectionError: {e} — повтор через 5с"); time.sleep(5)
        except ApiTelegramException as e:
            print(f"[polling] API error: {e} — повтор через 5с"); time.sleep(5)
        except Exception as e:
            print(f"[polling] Unhandled: {e} — повтор через 10с"); time.sleep(10)
   


