
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
    else:
        price_adult = 3000
        price_child = 2000
        price_pet = 500

    total = adults * price_adult + children * price_child + animals * price_pet
    return total

@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Расчёт стоимости")
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "Расчёт стоимости")
def handle_calc_button(message):
    chat_id = message.from_user.id
    user_data[chat_id] = {}
    msg = bot.send_message(chat_id, "Как вас зовут?")
    bot.register_next_step_handler(msg, get_name)
    
def handle_calc_button(message):
    chat_id = message.from_user.id
    user_data[chat_id] = {}
    msg = bot.send_message(chat_id, "Сколько взрослых пассажиров?")
    bot.register_next_step_handler(msg, get_adults)

def get_adults(message):
    chat_id = message.from_user.id
    try:
        user_data[chat_id]['adults'] = int(message.text)
    except:
        return bot.send_message(chat_id, "Пожалуйста, введите число.")
    msg = bot.send_message(chat_id, "Сколько детей?")
    bot.register_next_step_handler(msg, get_children)

def get_children(message):
    chat_id = message.from_user.id
    try:
        user_data[chat_id]['children'] = int(message.text)
    except:
        return bot.send_message(chat_id, "Пожалуйста, введите число.")
    msg = bot.send_message(chat_id, "Сколько животных?")
    bot.register_next_step_handler(msg, get_animals)

def get_animals(message):
    chat_id = message.from_user.id
    try:
        user_data[chat_id]['animals'] = int(message.text)
    except:
        return bot.send_message(chat_id, "Пожалуйста, введите число.")

    markup = types.InlineKeyboardMarkup()
    routes = [
        "Владикавказ — Тбилиси",
        "Владикавказ — Степанцминда",
        "Владикавказ — Кутаиси",
        "Владикавказ — Батуми"
    ]
    for route in routes:
        markup.add(types.InlineKeyboardButton(route, callback_data=f"route_{route}"))

    bot.send_message(chat_id, "Выберите маршрут:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("route_"))
def on_route_selected(call):
    chat_id = call.from_user.id
    route = call.data.replace("route_", "")
    data = user_data.get(chat_id, {})
    adults = data.get('adults', 0)
    children = data.get('children', 0)
    animals = data.get('animals', 0)

    price = calculate_price(adults, children, animals, route)
    user_data[chat_id]['route'] = route
    user_data[chat_id]['price'] = price

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Оформить заявку", callback_data="confirm_booking"))
    bot.send_message(chat_id, f"Стоимость поездки по маршруту {route}: {price} руб.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "confirm_booking")
def confirm_booking(call):
    chat_id = call.from_user.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton("Отправить номер", request_contact=True)
    markup.add(button)
    bot.send_message(chat_id, "Пожалуйста, отправьте номер телефона для заявки.", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    chat_id = message.from_user.id
    if message.contact:
        user_data[chat_id]["phone"] = message.contact.phone_number

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Аэропорт", callback_data="loc_airport"),
            types.InlineKeyboardButton("Ж/д вокзал", callback_data="loc_station"),
            types.InlineKeyboardButton("С адреса во Владикавказе", callback_data="loc_address"),
            types.InlineKeyboardButton("Станция метро Дидубе", callback_data="loc_didube"),
            types.InlineKeyboardButton("Другое", callback_data="loc_other")
        )
        bot.send_message(chat_id, "Откуда будет выезд?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("loc_"))
def finish_booking(call):
    chat_id = call.from_user.id
    location = call.data.replace("loc_", "")
    data = user_data.get(chat_id, {})
    route = data.get("route", "-")
    phone = data.get("phone", "-")
    adults = data.get("adults", 0)
    children = data.get("children", 0)
    animals = data.get("animals", 0)
    price = data.get("price", 0)

  text = (
    f"Новая заявка:\n"
    f"Имя: {user_data[chat_id]['name']}\n"
    f"Маршрут: {route}\n"
    f"Телефон: {phone}\n"
    f"Место выезда: {location}\n"
    f"Стоимость: {price} руб."
)

    bot.send_message(ADMIN_GROUP_ID, text)
    bot.send_message(chat_id, "Ваша заявка отправлена администраторам. Мы с вами свяжемся.")

print("Бот запущен...")
bot.polling(none_stop=True)
