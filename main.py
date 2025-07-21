import telebot
from telebot import types

TOKEN = "7606923892:AAFTaq2UnGukug2VJJGZsN1NRrbgFeaICvQ"
ADMIN_ID = 561665893
bot = telebot.TeleBot(TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def handle_start(message):
    show_main_menu(message.chat.id)

def show_main_menu(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🚐 Забронировать поездку", callback_data="start_booking"),
        types.InlineKeyboardButton("📄 Информация о документах", callback_data="info"),
        types.InlineKeyboardButton("❓ Задать вопрос", url="https://t.me/TransverTbilisi")
    )
    bot.send_message(chat_id, "Главное меню:", reply_markup=markup)

def show_back_to_menu_button(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Вернуться в меню", callback_data="back_to_menu"))
    bot.send_message(chat_id, "Что дальше?", reply_markup=markup)

def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    user_data[chat_id]["name"] = message.text
    bot.send_message(chat_id, "Введите дату поездки (например, 22.07):")
    bot.register_next_step_handler(message, get_date)

def get_date(message):
    chat_id = message.chat.id
    user_data[chat_id]["date"] = message.text
    send_route_options(chat_id)

def send_route_options(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    routes = [
        "Владикавказ — Тбилиси",
        "Владикавказ — Степанцминда",
        "Владикавказ — Кутаиси",
        "Владикавказ — Батуми",
        "Тбилиси — Владикавказ"
    ]
    for route in routes:
        markup.add(types.InlineKeyboardButton(route, callback_data=f"route_{route}"))
    bot.send_message(chat_id, "Выберите маршрут:", reply_markup=markup)

def get_phone(message):
    chat_id = message.chat.id
    user_data[chat_id]["phone"] = message.text
    send_passenger_count(chat_id)

def send_passenger_count(chat_id):
    markup = types.InlineKeyboardMarkup()
    for i in range(1, 6):
        markup.add(types.InlineKeyboardButton(f"{i} человек", callback_data=f"pass_{i}"))
    bot.send_message(chat_id, "Сколько пассажиров?", reply_markup=markup)

def send_location_options(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Аэропорт", callback_data="loc_airport"),
        types.InlineKeyboardButton("Ж/д вокзал", callback_data="loc_station"),
        types.InlineKeyboardButton("С адреса во Владикавказе", callback_data="loc_address"),
        types.InlineKeyboardButton("Станция метро Дидубе", callback_data="loc_didube"),
        types.InlineKeyboardButton("Другое", callback_data="loc_other")
    )
    bot.send_message(chat_id, "Откуда будет выезд?", reply_markup=markup)

def finish_booking_preview(call):
    chat_id = call.message.chat.id
    location = call.data.split("_", 1)[1]
    loc_names = {
        "airport": "Аэропорт",
        "station": "Ж/д вокзал",
        "address": "С адреса во Владикавказе",
        "didube": "Станция метро Дидубе",
        "other": "Другое"
    }
    user_data[chat_id]["location"] = loc_names.get(location, "Неизвестно")
    data = user_data[chat_id]
    summary = f"""📝 Проверьте данные заявки:

Имя: {data['name']}
Дата: {data['date']}
Маршрут: {data['route']}
Телефон: {data['phone']}
Пассажиры: {data['passengers']}
Локация: {data['location']}

Отправить заявку?
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Отправить", callback_data="confirm_yes"),
        types.InlineKeyboardButton("❌ Отменить", callback_data="confirm_no")
    )
    bot.send_message(chat_id, summary, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    if call.data == "start_booking":
        bot.send_message(chat_id, "Введите ваше имя:")
        bot.register_next_step_handler(call.message, get_name)
    elif call.data.startswith("route_"):
        user_data[chat_id]["route"] = call.data.split("_", 1)[1]
        bot.send_message(chat_id, "Введите номер телефона:")
        bot.register_next_step_handler(call.message, get_phone)
    elif call.data.startswith("pass_"):
        user_data[chat_id]["passengers"] = call.data.split("_", 1)[1]
        send_location_options(chat_id)
    elif call.data.startswith("loc_"):
        finish_booking_preview(call)
    elif call.data == "confirm_yes":
        data = user_data.get(chat_id)
        if data:
            text = f"""🚨 Новая заявка!

Имя: {data['name']}
Дата: {data['date']}
Маршрут: {data['route']}
Телефон: {data['phone']}
Пассажиры: {data['passengers']}
Локация: {data['location']}
"""
            bot.send_message(ADMIN_ID, text)
            bot.send_message(chat_id, "Заявка отправлена ✅")
        show_back_to_menu_button(chat_id)
        user_data.pop(chat_id, None)
    elif call.data == "confirm_no":
        bot.send_message(chat_id, "Заявка отменена ❌")
        show_back_to_menu_button(chat_id)
        user_data.pop(chat_id, None)
    elif call.data == "back_to_menu":
        show_main_menu(chat_id)
    elif call.data == "info":
        bot.send_message(chat_id, "Для поездки необходимо иметь документы, удостоверяющие личность.")
        show_back_to_menu_button(chat_id)

if __name__ == '__main__':
    bot.polling(none_stop=True)
