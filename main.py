import os
from telebot import TeleBot, types

# === Конфиг ===
TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(TOKEN)

ADMIN_GROUP_ID = -4948043121  # твоя админ-группа

# Память по пользователям
user_data = {}

# ===== Тарифы и расчет =====
def get_tariffs(route: str):
    if "Батуми" in route:
        return 6000, 4000, 1000   # adult, child, pet
    elif "Кутаиси" in route:
        return 5000, 3500, 800
    elif "Степанцминда" in route:
        return 2000, 1500, 500
    else:  # Владикавказ — Тбилиси и всё остальное
        return 3000, 2000, 500

def format_price_breakdown(adults: int, children: int, animals: int, route: str):
    pa, pc, pp = get_tariffs(route)
    lines = []
    if adults:
        lines.append(f"Взрослые: {adults} × {pa} = {adults * pa} руб.")
    if children:
        lines.append(f"Дети: {children} × {pc} = {children * pc} руб.")
    if animals:
        lines.append(f"Животные: {animals} × {pp} = {animals * pp} руб.")
    total = adults * pa + children * pc + animals * pp
    lines.append(f"Итоговая стоимость: {total} руб.")
    return "\n".join(lines), total
    
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

# ===== Завершение оформления заявки (выбор локации) =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("loc_"))
def finish_booking(call):
    chat_id = call.message.chat.id
    location = call.data.replace("loc_", "")

    data = user_data.get(chat_id, {})
    name = data.get("name", "Не указано")
    phone = data.get("phone", "-")
    route = data.get("route", "-")
    adults = int(data.get("adults") or 0)
    children = int(data.get("children") or 0)
    animals = int(data.get("animals") or 0)

    breakdown, total = format_price_breakdown(adults, children, animals, route)

    # Сообщение администраторам
    text_admin = (
        "Новая заявка:\n"
        f"Имя: {name}\n"
        f"Маршрут: {route}\n"
        f"Взрослых: {adults}, Детей: {children}, Животных: {animals}\n"
        f"Телефон: {phone}\n"
        f"Место выезда: {location}\n"
        f"{breakdown}"
    )
    bot.send_message(ADMIN_GROUP_ID, text_admin)

    # Подтверждение пользователю
    bot.send_message(
        chat_id,
        "Ваша заявка отправлена администраторам. Мы с вами свяжемся.\n\n" + breakdown
    )

  
    # Очистим состояние, чтобы следующий расчёт начинать с нуля
    user_data[chat_id] = {}

print("Бот запущен...")
bot.polling(none_stop=True)
