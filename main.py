
import os
from telebot import TeleBot, types

# === Конфиг ===
TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(TOKEN)

ADMIN_GROUP_ID = -4948043121  # твоя админ-группа

# Память по пользователям
user_data = {}

# === Прайс ===
def calculate_price(adults, children, animals, route):
    if "Батуми" in route:
        price_adult, price_child, price_pet = 6000, 4000, 1000
    elif "Кутаиси" in route:
        price_adult, price_child, price_pet = 5000, 3500, 800
    elif "Степанцминда" in route:
        price_adult, price_child, price_pet = 2000, 1500, 500
    else:  # Тбилиси и все прочее
        price_adult, price_child, price_pet = 3000, 2000, 500
    return adults * price_adult + children * price_child + animals * price_pet

# === Хелперы ===
def ensure_user(chat_id):
    # Создаем каркас, если его ещё нет
    user_data.setdefault(chat_id, {
        "name": None,
        "adults": None,
        "children": None,
        "animals": None,
        "route": None,
        "price": None,
        "phone": None,
        "location": None
    })
    return user_data[chat_id]

def ask_int(chat_id, text, next_handler):
    msg = bot.send_message(chat_id, text)
    bot.register_next_step_handler(msg, next_handler)

def parse_int_or_repeat(message, repeat_handler):
    chat_id = message.chat.id
    try:
        return int(message.text.strip())
    except Exception:
        msg = bot.send_message(chat_id, "Пожалуйста, введите число.")
        bot.register_next_step_handler(msg, repeat_handler)
        return None

# === Старт/меню ===
@bot.message_handler(commands=['start'])
def start_command(message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Расчёт стоимости")
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "Расчёт стоимости")
def handle_calc_button(message):
    chat_id = message.chat.id
    d = ensure_user(chat_id)
    # начинаем заново каждый раз
    for k in d.keys():
        d[k] = None
    msg = bot.send_message(chat_id, "Как вас зовут?")
    bot.register_next_step_handler(msg, get_name_step)

# === Шаги опроса ===
def get_name_step(message):
    chat_id = message.chat.id
    d = ensure_user(chat_id)
    d["name"] = message.text.strip() if message.text else "Не указано"
    ask_int(chat_id, "Сколько взрослых пассажиров?", get_adults)

def get_adults(message):
    chat_id = message.chat.id
    val = parse_int_or_repeat(message, get_adults)
    if val is None:
        return
    d = ensure_user(chat_id)
    d["adults"] = val
    ask_int(chat_id, "Сколько детей?", get_children)

def get_children(message):
    chat_id = message.chat.id
    val = parse_int_or_repeat(message, get_children)
    if val is None:
        return
    d = ensure_user(chat_id)
    d["children"] = val
    ask_int(chat_id, "Сколько животных?", get_animals)

def get_animals(message):
    chat_id = message.chat.id
    val = parse_int_or_repeat(message, get_animals)
    if val is None:
        return
    d = ensure_user(chat_id)
    d["animals"] = val

    kb = types.InlineKeyboardMarkup()
    routes = [
        "Владикавказ — Тбилиси",
        "Владикавказ — Степанцминда",
        "Владикавказ — Кутаиси",
        "Владикавказ — Батуми",
    ]
    for r in routes:
        kb.add(types.InlineKeyboardButton(r, callback_data=f"route_{r}"))
    bot.send_message(chat_id, "Выберите маршрут:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("route_"))
def on_route_selected(call):
    chat_id = call.message.chat.id
    d = ensure_user(chat_id)

    # если вдруг пользователь перескочил шаги
    for key in ("adults", "children", "animals"):
        if d.get(key) is None:
            bot.answer_callback_query(call.id, "Пожалуйста, сначала ответьте на все вопросы.")
            return

    route = call.data.replace("route_", "")
    d["route"] = route
    d["price"] = calculate_price(d["adults"], d["children"], d["animals"], route)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.
           InlineKeyboardButton("Оформить заявку", callback_data="confirm_booking"))
    bot.send_message(chat_id, f"Стоимость поездки по маршруту {route}: {d['price']} руб.", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "confirm_booking")
def confirm_booking(call):
    chat_id = call.message.chat.id
    d = ensure_user(chat_id)

    if not d.get("route") or d.get("price") is None:
        bot.answer_callback_query(call.id, "Сначала выберите маршрут.")
        return

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("Отправить номер", request_contact=True))
    bot.send_message(chat_id, "Пожалуйста, отправьте номер телефона для заявки.", reply_markup=kb)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    chat_id = message.chat.id
    if not message.contact:
        return
    d = ensure_user(chat_id)
    d["phone"] = message.contact.phone_number

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("Аэропорт", callback_data="loc_airport"),
        types.InlineKeyboardButton("Ж/д вокзал", callback_data="loc_station"),
    )
    kb.add(
        types.InlineKeyboardButton("С адреса во Владикавказе", callback_data="loc_address"),
        types.InlineKeyboardButton("Станция метро Дидубе", callback_data="loc_didube"),
    )
    kb.add(types.InlineKeyboardButton("Другое", callback_data="loc_other"))
    bot.send_message(chat_id, "Откуда будет выезд?", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("loc_"))
def finish_booking(call):
    chat_id = call.message.chat.id
    d = ensure_user(chat_id)
    d["location"] = call.data.replace("loc_", "")

    # Контроль: все обязательные поля должны быть заполнены
    missing = [k for k in ("name", "adults", "children", "animals", "route", "price", "phone", "location") if d.get(k) in (None, "")]
    if missing:
        bot.send_message(chat_id, "Не все данные заполнены. Пожалуйста, начните заново командой «Расчёт стоимости».")
        return

    # Формируем текст заявки — всегда полный
    text = (
        f"Новая заявка:\n"
        f"Имя: {d['name']}\n"
        f"Маршрут: {d['route']}\n"
        f"Взрослых: {d['adults']}, Детей: {d['children']}, Животных: {d['animals']}\n"
        f"Телефон: +{d['phone'] if not d['phone'].startswith('+') else d['phone']}\n"
        f"Место выезда: {d['location']}\n"
        f"Итоговая стоимость: {d['price']} руб."
    )

    # Админам
    bot.send_message(ADMIN_GROUP_ID, text)
    # Пользователю
    bot.send_message(chat_id, "Ваша заявка отправлена администраторам. Мы с вами свяжемся.")

    # Очистим состояние, чтобы следующий расчёт начинать с нуля
    user_data[chat_id] = {}

print("Бот запущен...")
bot.polling(none_stop=True)
