import os
import telebot
from telebot import types
from datetime import datetime

TOKEN = "7606923892:AAFTaq2UnGukug2VJJGZsN1NRrbgFeaICvQ"  
ADMIN_ID = 561665893
print("TOKEN = ", TOKEN)
bot = telebot.TeleBot(TOKEN)
user_data = {}

def get_greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Доброе утро! 🌞"
    elif hour < 17:
        return "Добрый день! 🌤"
    elif hour < 22:
        return "Добрый вечер! 🌇"
    else:
        return "Доброй ночи! 🌙"

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🚐 Забронировать поездку", callback_data="start_booking"),
        types.InlineKeyboardButton("📄 Информация о документах", callback_data="info"),
        types.InlineKeyboardButton("❓ Задать вопрос", url="https://t.me/TransverTbilisi")
    )
    bot.send_message(message.chat.id, f"{get_greeting()} Добро пожаловать!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    if call.data == "start_booking":
        user_data[chat_id] = {}
        bot.send_message(chat_id, "Введите ваше имя:")
        bot.register_next_step_handler(call.message, get_name)
    elif call.data.startswith("route_"):
        route = call.data.split("_", 1)[1]
        user_data[chat_id]["route"] = route
        send_location_options(chat_id)
    elif call.data.startswith("loc_"):
        finish_booking(call)
    elif call.data.startswith("pass_"):
        user_data[chat_id]["passengers"] = call.data.split("_", 1)[1]
        send_route_options(chat_id)

def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id]["name"] = message.text
    bot.send_message(chat_id, "Введите дату поездки (например, 21.07):")
    bot.register_next_step_handler(message, get_date)

def get_date(message):
    chat_id = message.chat.id
    user_data[chat_id]["date"] = message.text
    bot.send_message(chat_id, "Введите номер телефона:")
    bot.register_next_step_handler(message, get_phone)

def get_phone(message):
    chat_id = message.chat.id
    user_data[chat_id]["phone"] = message.text
    send_passenger_count(chat_id)

def send_passenger_count(chat_id):
    markup = types.InlineKeyboardMarkup()
    for i in range(1, 6):
        markup.add(types.InlineKeyboardButton(f"{i} человек", callback_data=f"pass_{i}"))
    bot.send_message(chat_id, "Сколько пассажиров?", reply_markup=markup)

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

def finish_booking(call):
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
    message_text = f"""🚨 Новая заявка!

Имя: {data['name']}
Дата: {data['date']}
Маршрут: {data['route']}
Телефон: {data['phone']}
    Пассажиры: {data['passengers']}
Локация: {data['location']}
"""
    bot.send_message("@TransverTbilisi", message_text)
    bot.send_message(chat_id, "Ваша заявка отправлена администраторам. [Чат с админами](https://t.me/TransverTbilisi)", parse_mode="Markdown")

if __name__ == "__main__":
    bot.polling(non_stop=True)
    
