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

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    if call.data == "start_booking":
        user_data[chat_id] = {}
        msg = bot.send_message(chat_id, "Введите имя:")
        bot.register_next_step_handler(msg, get_name)

    elif call.data.startswith("route_"):
        user_data[chat_id]["route"] = call.data.split("_", 1)[1]
        msg = bot.send_message(chat_id, "Введите номер телефона:")
        bot.register_next_step_handler(msg, get_phone)

    elif call.data.startswith("loc_"):
        locs = {
            "airport": "Аэропорт",
            "station": "Ж/д вокзал",
            "address": "С адреса во Владикавказе",
            "didube": "Станция метро Дидубе",
            "other": "Другое"
        }
        user_data[chat_id]["location"] = locs.get(call.data.split("_", 1)[1], "Неизвестно")
        show_summary(chat_id)

    elif call.data == "confirm_yes":
        data = user_data.get(chat_id, {})
        text = f"""🚨 Новая заявка!
Имя: {data.get('name')}
Дата: {data.get('date')}
Маршрут: {data.get('route')}
Телефон: {data.get('phone')}
Пассажиры: {data.get('passengers')}
Локация: {data.get('location')}
"""
        bot.send_message(ADMIN_ID, text)
        bot.send_message(chat_id, "Заявка отправлена ✅")
        show_main_menu(chat_id)

    elif call.data == "confirm_no":
        bot.send_message(chat_id, "Заявка отменена ❌")
        show_main_menu(chat_id)

    elif call.data == "info":
        bot.send_message(chat_id, "Для поездки необходимо иметь паспорт и ПЦР-тест.")
        show_main_menu(chat_id)

def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id]["name"] = message.text
    msg = bot.send_message(chat_id, "Введите дату поездки (например, 22.07):")
    bot.register_next_step_handler(msg, get_date)

def get_date(message):
    chat_id = message.chat.id
    user_data[chat_id]["date"] = message.text
    msg = bot.send_message(chat_id, "Сколько пассажиров?")
    bot.register_next_step_handler(msg, get_passengers)

def get_passengers(message):
    chat_id = message.chat.id
    user_data[chat_id]["passengers"] = message.text
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Владикавказ — Тбилиси", callback_data="route_Владикавказ — Тбилиси"),
        types.InlineKeyboardButton("Владикавказ — Степанцминда", callback_data="route_Владикавказ — Степанцминда"),
        types.InlineKeyboardButton("Владикавказ — Кутаиси", callback_data="route_Владикавказ — Кутаиси"),
        types.InlineKeyboardButton("Владикавказ — Батуми", callback_data="route_Владикавказ — Батуми"),
        types.InlineKeyboardButton("Тбилиси — Владикавказ", callback_data="route_Тбилиси — Владикавказ"),
    )
    bot.send_message(chat_id, "Выберите маршрут:", reply_markup=markup)

def get_phone(message):
    chat_id = message.chat.id
    user_data[chat_id]["phone"] = message.text
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Аэропорт", callback_data="loc_airport"),
        types.InlineKeyboardButton("Ж/д вокзал", callback_data="loc_station"),
        types.InlineKeyboardButton("С адреса во Владикавказе", callback_data="loc_address"),
        types.InlineKeyboardButton("Станция метро Дидубе", callback_data="loc_didube"),
        types.InlineKeyboardButton("Другое", callback_data="loc_other"),
    )
    bot.send_message(chat_id, "Откуда будет выезд?", reply_markup=markup)

def show_summary(chat_id):
    data = user_data[chat_id]
    summary = f"""🔎 Проверьте данные заявки:

Имя: {data.get('name')}
Дата: {data.get('date')}
Маршрут: {data.get('route')}
Телефон: {data.get('phone')}
Пассажиры: {data.get('passengers')}
Локация: {data.get('location')}

Отправить заявку?"""
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_yes"),
        types.InlineKeyboardButton("❌ Отменить", callback_data="confirm_no"),
    )
    bot.send_message(chat_id, summary, reply_markup=markup)

if __name__ == '__main__':
    bot.polling(none_stop=True)
