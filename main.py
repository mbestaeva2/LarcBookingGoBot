import os
from telebot import TeleBot, types
from datetime import datetime, timezone, timedelta
import uuid

# === Конфигурация ===
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Переменная окружения BOT_TOKEN не задана")

bot = TeleBot(TOKEN)
# --- Команда /id: показывает chat_id и user_id (работает в личке и группах) ---
@bot.message_handler(commands=['id'])
def chat_id_cmd(message):
    chat = message.chat
    user = message.from_user

    # Базовая инфа
    lines = [
        f"Тип чата: {chat.type}",          # private / group / supergroup / channel
        f"Chat ID: {chat.id}",
        f"User ID: {user.id}",
    ]

    # Доп. данные для групп
    if chat.type in ('group', 'supergroup'):
        lines.append(f"Название чата: {chat.title}")

    bot.reply_to(message, "\n".join(lines))
    
ADMIN_GROUP_ID = -4948043121  # чат админов

# Память на сессию пользователя
user_data = {}

def format_money(n: int) -> str:
    # 23500 -> "23 500 руб."
    return f"{n:,}".replace(",", " ") + " руб."

def build_breakdown(adults, children, animals, price_adult, price_child, price_pet):
    lines = []
    total = adults * price_adult + children * price_child + animals * price_pet
    if adults:
        lines.append(f"Взрослые: {adults} × {format_money(price_adult)} = {format_money(adults * price_adult)}")
    if children:
        lines.append(f"Дети: {children} × {format_money(price_child)} = {format_money(children * price_child)}")
    if animals:
        lines.append(f"Животные: {animals} × {format_money(price_pet)} = {format_money(animals * price_pet)}")
    lines.append(f"Итоговая стоимость: {format_money(total)}")
    return "\n".join(lines), total

def get_local_time_str():
    # Время UTC+3 (Тбилиси/Мск). Если нужен другой пояс — поменяй hours=...
    now = datetime.now(timezone(timedelta(hours=3)))
    return now.strftime("%d.%m.%Y %H:%M (UTC+3)")

def make_request_id():
    # Короткий уникальный ID
    return uuid.uuid4().hex[:8]

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
@bot.callback_query_handler(func=lambda call: call.data.startswith("loc_"))
def finish_booking(call):
    chat_id = call.message.chat.id
    location = call.data.replace("loc_", "")

    # Достаём всё, что собрали раньше
    data = user_data.get(chat_id, {})
    name = data.get("name", "Не указано")
    route = data.get("route", "-")
    phone = data.get("phone", "-")
    adults = int(data.get("adults", 0) or 0)
    children = int(data.get("children", 0) or 0)
    animals = int(data.get("animals", 0) or 0)

    # Тарифы для выбранного маршрута
    # Если у тебя уже есть функция get_tariffs(route) — используем её.
    # ДОЛЖНО возвращать (price_adult, price_child, price_pet).
    price_adult, price_child, price_pet = get_tariffs(route)

    # Сборка разбора и тотала
    breakdown_text, total = build_breakdown(adults, children, animals, price_adult, price_child, price_pet)

    # ID и время заявки
    request_id = make_request_id()
    ts_str = get_local_time_str()

    # Сообщение админу
    admin_text = (
        f"Новая заявка № {request_id}\n"
        f"Время: {ts_str}\n"
        f"Имя: {name}\n"
        f"Маршрут: {route}\n"
        f"Взрослых: {adults}, Детей: {children}, Животных: {animals}\n"
        f"Телефон: {phone}\n"
        f"Место выезда: {location}\n"
        f"{breakdown_text}"
    )
    bot.send_message(ADMIN_GROUP_ID, admin_text)

    # Подтверждение пользователю
    user_text = (
        "Ваша заявка отправлена администраторам. Мы с вами свяжемся.\n\n"
        f"Номер вашей заявки: {request_id}\n"
        f"Время: {ts_str}\n"
        f"{breakdown_text}"
    )
    bot.send_message(chat_id, user_text)

    # очищаем состояние
    user_data.pop(chat_id, None)

# === Запуск ===
if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True, interval=1)
