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
def session(uid: int) -> dict:
    return user_data.setdefault(uid, {})
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
def start(message):
    uid, chat_id = message.from_user.id, message.chat.id
    session(uid).clear()  # новая заявка
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("Расчёт стоимости"))
    bot.send_message(chat_id, "Добро пожаловать! Выберите действие:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "Расчёт стоимости")
def start_flow(message):
    uid, chat_id = message.from_user.id, message.chat.id
    session(uid).clear()
    msg = bot.send_message(chat_id, "Как вас зовут?")
    bot.register_next_step_handler(msg, get_name)

def get_name(message):
    uid = message.from_user.id
    session(uid)['name'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Сколько взрослых пассажиров? (числом)")
    bot.register_next_step_handler(msg, get_adults)

def get_adults(message):
    uid = message.from_user.id
    try:
        session(uid)['adults'] = max(0, int(message.text))
    except:
        msg = bot.send_message(message.chat.id, "Введите число. Сколько взрослых?")
        return bot.register_next_step_handler(msg, get_adults)
    msg = bot.send_message(message.chat.id, "Сколько детей? (числом)")
    bot.register_next_step_handler(msg, get_children)

def get_children(message):
    uid = message.from_user.id
    try:
        session(uid)['children'] = max(0, int(message.text))
    except:
        msg = bot.send_message(message.chat.id, "Введите число. Сколько детей?")
        return bot.register_next_step_handler(msg, get_children)
    msg = bot.send_message(message.chat.id, "Сколько животных? (числом)")
    bot.register_next_step_handler(msg, get_animals)

def get_animals(message):
    uid = message.from_user.id
    try:
        session(uid)['animals'] = max(0, int(message.text))
    except:
        msg = bot.send_message(message.chat.id, "Введите число. Сколько животных?")
        return bot.register_next_step_handler(msg, get_animals)
    # показываем выбор маршрута (inline)
    ask_route(message.chat.id)

    # выбор маршрута
from telebot import types

# ===== МАРШРУТ -> ЦЕНА -> "Оформить заявку" =====
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

def show_price(chat_id: int, route: str, total: int):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Оформить заявку", callback_data="apply_booking"))  # <— ВАЖНО: то же самое в хендлере
    bot.send_message(
        chat_id,
        f"Стоимость поездки по маршруту <b>{route}</b>: <b>{total} руб.</b>\n\nНажмите, чтобы оформить заявку:",
        parse_mode="HTML",
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("route_"))
def on_route_selected(call):
    bot.answer_callback_query(call.id)
    uid, chat_id = call.from_user.id, call.message.chat.id
    route = call.data.split("route_", 1)[1]

    s = session(uid)
    s["route"] = route

    adults   = int(s.get("adults", 1))
    children = int(s.get("children", 0))
    animals  = int(s.get("animals", 0))

    # ВАЖНО: распаковываем кортеж из calculate_price!
   total, pa, pc, pp = calculate_price(adults, children, animals, route)
session(uid)["total"] = total
show_price(chat_id, route, total)

    # Показ цены + кнопка "Оформить заявку"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Оформить заявку", callback_data="apply_booking"))
    bot.send_message(
        chat_id,
        f"Стоимость поездки по маршруту <b>{route}</b>: <b>{total} руб.</b>\n\nНажмите, чтобы оформить заявку:",
        parse_mode="HTML",
        reply_markup=kb
    )
# 1) Показ цены + кнопка "Оформить заявку"
def show_price(chat_id, route, total):
    text = f"Стоимость поездки по маршруту <b>{route}</b>: <b>{total} руб.</b>"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Оформить заявку", callback_data="apply_booking"))
    safe_send(chat_id, text + "\n\nНажмите, чтобы оформить заявку:",
              reply_markup=markup, parse_mode="HTML")

# 2) Хендлер кнопки — один!
# ===== ОФОРМЛЕНИЕ ЗАЯВКИ: телефон -> локация =====
@bot.callback_query_handler(func=lambda c: c.data == "apply_booking")
def cb_apply_booking(call):
    bot.answer_callback_query(call.id)
    uid, chat_id = call.from_user.id, call.message.chat.id

    # если телефона ещё нет — просим
    if not session(uid).get("phone"):
        return ask_phone(chat_id, uid)

    # если телефон уже есть — сразу спросим локацию
    return ask_location(chat_id)
def ask_phone(chat_id: int, uid: int):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("Отправить номер телефона", request_contact=True))

    if int(chat_id) < 0:  # группа
        bot.send_message(chat_id, "Чтобы оформить заявку, продолжим в личных сообщениях. Я написал(а) вам в личку.")
        bot.send_message(uid, "Пожалуйста, отправьте номер телефона кнопкой ниже.", reply_markup=kb)
        return

    bot.send_message(chat_id, "Пожалуйста, отправьте номер телефона кнопкой ниже.", reply_markup=kb)
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    uid, chat_id = message.from_user.id, message.chat.id
    if int(chat_id) < 0:
        return bot.send_message(chat_id, "Пожалуйста, отправьте номер телефона мне в личные сообщения.")

    if message.contact and message.contact.phone_number:
        session(uid)["phone"] = message.contact.phone_number
        bot.send_message(chat_id, "Спасибо! Номер получен. Укажите локацию выезда:",
                         reply_markup=types.ReplyKeyboardRemove())
        return ask_location(chat_id)

    bot.send_message(chat_id, "Не вижу номер. Нажмите кнопку «Отправить номер телефона».")

     
   
# ===== ЛОКАЦИЯ (inline) + формирование заявки =====
# ===== ЛОКАЦИЯ (inline) =====
def ask_location(chat_id: int):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("Аэропорт", callback_data="loc_airport"),
        types.InlineKeyboardButton("Ж/д вокзал", callback_data="loc_station"),
    )
    kb.add(
        types.InlineKeyboardButton("С адреса во Владикавказе", callback_data="loc_address"),
        types.InlineKeyboardButton("Метро Дидубе", callback_data="loc_didube"),
    )
    kb.add(types.InlineKeyboardButton("Другое", callback_data="loc_other"))
    bot.send_message(chat_id, "Откуда будет выезд?", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("loc_"))
def on_location_selected(call):
    bot.answer_callback_query(call.id)
    uid, chat_id = call.from_user.id, call.message.chat.id

    loc_map = {
        "loc_airport": "Аэропорт",
        "loc_station": "Ж/д вокзал",
        "loc_address": "С адреса во Владикавказе",
        "loc_didube": "Метро Дидубе",
        "loc_other": "Другое",
    }
    s = session(uid)
    s["location"] = loc_map.get(call.data, "Другое")

    name     = s.get('name', '—')
    phone    = s.get('phone', '—')
    route    = s.get('route', '—')
    adults   = int(s.get('adults', 0))
    children = int(s.get('children', 0))
    animals  = int(s.get('animals', 0))

    # total уже считали после выбора маршрута
    total = s.get('total')
    if total is None:
        total, _, _, _ = calculate_price(adults, children, animals, route)

    admin_text = (
        "🆕 Новая заявка:\n"
        f"Имя: {name}\n"
        f"Маршрут: {route}\n"
        f"Телефон: {phone}\n"
        f"Место выезда: {s['location']}\n"
        f"Взрослые: {adults}\nДети: {children}\nЖивотные: {animals}\n"
        f"Итоговая стоимость: {total} руб."
    )
    bot.send_message(ADMIN_GROUP_ID, admin_text, disable_web_page_preview=True)
    bot.send_message(chat_id, "Заявка отправлена администраторам. Мы свяжемся с вами в ближайшее время.")
# ===== Запуск =====
import time

if __name__ == "__main__":  # <-- исправили name -> name
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

@bot.message_handler(commands=['ping'])
def _ping(m):
    bot.reply_to(m, "pong")

