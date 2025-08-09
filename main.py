import os
from telebot import TeleBot, types
from datetime import datetime

# ===== Конфигурация =====
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Переменная окружения BOT_TOKEN не задана")

# chat_id вашей админ-группы (оставь как у тебя)
ADMIN_GROUP_ID = -4948043121

bot = TeleBot(TOKEN, parse_mode="HTML")

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

    # выбор маршрута
    kb = types.InlineKeyboardMarkup()
    for route in [
        "Владикавказ — Тбилиси",
        "Владикавказ — Степанцминда",
        "Владикавказ — Кутаиси",
        "Владикавказ — Батуми",

]:
        kb.add(types.InlineKeyboardButton(route, callback_data=f"route:{route}"))
    bot.send_message(chat_id, "Выберите маршрут:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("route:"))
def on_route_selected(call):
    chat_id = call.message.chat.id
    route = call.data.split("route:", 1)[1]
    ensure_session(chat_id)
    d = user_data[chat_id]

    d["route"] = route
    total, pa, pc, pp = calculate_price(d["adults"] or 0, d["children"] or 0, d["animals"] or 0, route)
    d["price"] = total

    # кнопка «Оформить заявку»
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Оформить заявку", callback_data="confirm"))
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=f"Стоимость поездки по маршруту <b>{route}</b>: <b>{total} руб.</b>",
        parse_mode="HTML"
    )
    bot.send_message(chat_id, "Нажмите, чтобы оформить заявку:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "confirm")
def ask_phone(call):
    chat_id = call.message.chat.id
    ensure_session(chat_id)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("Отправить номер", request_contact=True))
    bot.send_message(chat_id, "Пожалуйста, отправьте номер телефона для заявки.", reply_markup=kb)

@bot.message_handler(content_types=['contact'])
def got_contact(message):
    chat_id = message.chat.id
    ensure_session(chat_id)
    if message.contact and message.contact.phone_number:
        user_data[chat_id]["phone"] = message.contact.phone_number

    # место выезда
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("Аэропорт", callback_data="loc:airport"),
        types.InlineKeyboardButton("Ж/д вокзал", callback_data="loc:station"),
        types.InlineKeyboardButton("С адреса во Владикавказе", callback_data="loc:address"),
        types.InlineKeyboardButton("Станция метро Дидубе", callback_data="loc:didube"),
        types.InlineKeyboardButton("Другое", callback_data="loc:other"),
    )
    bot.send_message(chat_id, "Откуда будет выезд?", reply_markup=kb)

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
if name == "__main__":
    # На всякий случай убираем вебхук (если раньше где-то включался)
    try:
        bot.remove_webhook()
    except Exception:
        pass

    print("Бот запущен…", datetime.now().isoformat())
    # Один процесс, один инстанс → 409 не будет
    bot.

МВ, [09.08.2025 5:40]
infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
