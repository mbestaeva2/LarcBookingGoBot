import os
from telebot import TeleBot, types

# === Конфигурация ===
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Переменная окружения BOT_TOKEN не задана")

bot = TeleBot(TOKEN)

ADMIN_GROUP_ID = -4948043121  # чат админов

# Память на сессию пользователя
user_data = {}

# === Тарифы и расчёт ===
def get_tariffs(route: str):
    if "Батуми" in route:
        return 6000, 4000, 1000  # взрослый, ребёнок, животное
    elif "Кутаиси" in route:
        return 5000, 3500, 800
    elif "Степанцминда" in route:
        return 2000, 1500, 500
    else:  # Владикавказ — Тбилиси и прочее
        return 3000, 2000, 500

def calculate_price(adults: int, children: int, animals: int, route: str) -> int:
    pa, pc, pp = get_tariffs(route)
    return adults * pa + children * pc + animals * pp

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
def ensure_user(chat_id: int):
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

def parse_int_safe(text: str):
    try:
        return int(text.strip())
    except Exception:
        return None

# === Старт ===
@bot.message_handler(commands=['start'])
def start_command(message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Расчёт стоимости")
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "Расчёт стоимости")
def handle_calc_button(message):
    chat_id = message.chat.id
    d = ensure_user(chat_id)
    # сбрасываем предыдущее состояние
    for k in d.keys():
        d[k] = None
    msg = bot.send_message(chat_id, "Как вас зовут?")
    bot.register_next_step_handler(msg, get_name_step)

# === Шаги опроса ===
def get_name_step(message):
    chat_id = message.chat.id
    d = ensure_user(chat_id)
    d["name"] = (message.text or "").strip() or "Не указано"
    msg = bot.send_message(chat_id, "Сколько взрослых пассажиров?")
    bot.register_next_step_handler(msg, get_adults)

def get_adults(message):
    chat_id = message.chat.id
    n = parse_int_safe(message.text)
    if n is None or n < 0:
        msg = bot.send_message(chat_id, "Пожалуйста, введите целое неотрицательное число взрослых.")
        return bot.register_next_step_handler(msg, get_adults)
    d = ensure_user(chat_id)
    d["adults"] = n
    msg = bot.send_message(chat_id, "Сколько детей?")
    bot.register_next_step_handler(msg, get_children)

def get_children(message):
    chat_id = message.chat.id
    n = parse_int_safe(message.text)
    if n is None or n < 0:
        msg = bot.send_message(chat_id, "Пожалуйста, введите целое неотрицательное число детей.")
        return bot.register_next_step_handler(msg, get_children)
    d = ensure_user(chat_id)
    d["children"] = n
    msg = bot.send_message(chat_id, "Сколько животных?")
    bot.register_next_step_handler(msg, get_animals)

def get_animals(message):
    chat_id = message.chat.id
    n = parse_int_safe(message.text)
    if n is None or n < 0:
        msg = bot.send_message(chat_id, "Пожалуйста, введите целое неотрицательное число животных (0, если нет).")
        return bot.register_next_step_handler(msg, get_animals)
    d = ensure_user(chat_id)
    d["animals"] = n

    # выбор маршрута
    kb = types.InlineKeyboardMarkup()
    for r in [
        "Владикавказ — Тбилиси",
        "Владикавказ — Степанцминда",

МВ, [09.08.2025 3:34]
"Владикавказ — Кутаиси",
        "Владикавказ — Батуми",
    ]:
        kb.add(types.InlineKeyboardButton(r, callback_data=f"route_{r}"))
    bot.send_message(chat_id, "Выберите маршрут:", reply_markup=kb)

# === Выбор маршрута ===
@bot.callback_query_handler(func=lambda c: c.data.startswith("route_"))
def on_route_selected(call):
    chat_id = call.message.chat.id
    route = call.data.replace("route_", "")
    d = ensure_user(chat_id)

    adults  = int(d.get("adults")  or 0)
    children = int(d.get("children") or 0)
    animals  = int(d.get("animals") or 0)

    price = calculate_price(adults, children, animals, route)
    d["route"] = route
    d["price"] = price

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Оформить заявку", callback_data="confirm_booking"))
    bot.send_message(chat_id, f"Стоимость поездки по маршруту {route}: {price} руб.", reply_markup=kb)

# === Оформление заявки: телефон ===
@bot.callback_query_handler(func=lambda c: c.data == "confirm_booking")
def confirm_booking(call):
    chat_id = call.message.chat.id
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

    # выбор места выезда
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

# === Завершение: место выезда и отправка заявки ===
@bot.callback_query_handler(func=lambda c: c.data.startswith("loc_"))
def finish_booking(call):
    chat_id = call.message.chat.id
    location = call.data.replace("loc_", "")
    d = ensure_user(chat_id)
    d["location"] = location

    name = d.get("name", "Не указано")
    route = d.get("route", "-")
    phone = d.get("phone", "-")
    adults = int(d.get("adults") or 0)
    children = int(d.get("children") or 0)
    animals = int(d.get("animals") or 0)

    breakdown, total = format_price_breakdown(adults, children, animals, route)

    # Админам
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

    # Пользователю
    bot.send_message(chat_id, "Ваша заявка отправлена администраторам. Мы с вами свяжемся.\n\n" + breakdown)

    # очищаем состояние
    user_data.pop(chat_id, None)

# === Запуск ===
if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True, interval=1)
