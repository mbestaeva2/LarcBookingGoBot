
import os
from telebot import TeleBot, types

TOKEN = os.getenv("BOT_TOKEN")
print("TOKEN:", TOKEN)
bot = TeleBot(TOKEN)

ADMIN_ID = 561665893
ADMIN_GROUP_ID = -4948043121

user_data = {}

def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id]["name"] = message.text
    bot.send_message(chat_id, "Сколько взрослых?")

МВ, [08.08.2025 23:51]
def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id]["name"] = message.text
    bot.send_message(chat_id, "Сколько взрослых?")

МВ, [09.08.2025 0:07]
def calculate_price(adults, children, animals, route):
    if "Батуми" in route:
        price_adult = 6000
        price_child = 4000
        price_pet = 1000
    elif "Кутаиси" in route:
        price_adult = 5000
        price_child = 3500
        price_pet = 800
    elif "Степанцминда" in route:
        price_adult = 2000
        price_child = 1500
        price_pet = 500
    else:  # Тбилиси и прочие
        price_adult = 3000
        price_child = 2000
        price_pet = 500
    return adults * price_adult + children * price_child + animals * price_pet


@bot.message_handler(commands=['start'])
def start_command(message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Расчёт стоимости")
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=kb)


@bot.message_handler(func=lambda m: m.text == "Расчёт стоимости")
def handle_calc_button(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    msg = bot.send_message(chat_id, "Как вас зовут?")
    bot.register_next_step_handler(msg, get_name_step)


def get_name_step(message):
    chat_id = message.chat.id
    user_data.setdefault(chat_id, {})
    user_data[chat_id]["name"] = message.text.strip()
    msg = bot.send_message(chat_id, "Сколько взрослых пассажиров?")
    bot.register_next_step_handler(msg, get_adults)


def _parse_int_or_ask_again(message, prompt):
    chat_id = message.chat.id
    try:
        return int(message.text.strip())
    except Exception:
        msg = bot.send_message(chat_id, "Пожалуйста, введите число.")
        bot.register_next_step_handler(msg, prompt)
        return None


def get_adults(message):
    chat_id = message.chat.id
    val = _parse_int_or_ask_again(message, get_adults)
    if val is None:
        return
    user_data[chat_id]["adults"] = val
    msg = bot.send_message(chat_id, "Сколько детей?")
    bot.register_next_step_handler(msg, get_children)


def get_children(message):
    chat_id = message.chat.id
    val = _parse_int_or_ask_again(message, get_children)
    if val is None:
        return
    user_data[chat_id]["children"] = val
    msg = bot.send_message(chat_id, "Сколько животных?")
    bot.register_next_step_handler(msg, get_animals)


def get_animals(message):
    chat_id = message.chat.id
    val = _parse_int_or_ask_again(message, get_animals)
    if val is None:
        return
    user_data[chat_id]["animals"] = val

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
    route = call.data.replace("route_", "")
    d = user_data.get(chat_id, {})
    adults = d.get("adults", 0)
    children = d.get("children", 0)
    animals = d.get("animals", 0)

    price = calculate_price(adults, children, animals, route)
    d["route"] = route
    d["price"] = price
    user_data[chat_id] = d

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Оформить заявку", callback_data="confirm_booking"))
    bot.send_message(chat_id, f"Стоимость поездки по маршруту {route}: {price} руб.", reply_markup=kb)


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
    user_data.setdefault(chat_id, {})

МВ, [08.08.2025 23:51]
def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id]["name"] = message.text
    bot.send_message(chat_id, "Сколько взрослых?")

МВ, [09.08.2025 0:07]
user_data[chat_id]["phone"] = message.contact.phone_number

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
    d = user_data.get(chat_id, {})
    d["location"] = call.data.replace("loc_", "")
    user_data[chat_id] = d

    name = d.get("name", "Не указано")
    route = d.get("route", "-")
    phone = d.get("phone", "-")
    adults = d.get("adults", 0)
    children = d.get("children", 0)
    animals = d.get("animals", 0)
    price = d.get("price", 0)
    location = d.get("location", "-")

    text = (
        f"Новая заявка:\n"
        f"Имя: {name}\n"
        f"Маршрут: {route}\n"
        f"Взрослых: {adults}, Детей: {children}, Животных: {animals}\n"
        f"Телефон: {phone}\n"
        f"Место выезда: {location}\n"
        f"Итоговая стоимость: {price} руб."
    )

    # Админам в группу
    bot.send_message(ADMIN_GROUP_ID, text)
    # Пользователю подтверждение
    bot.send_message(chat_id, "Ваша заявка отправлена администраторам. Мы с вами свяжемся.")


print("Бот запущен…")
bot.polling(none_stop=True)
