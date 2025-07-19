
from telebot import TeleBot, types

bot = TeleBot("7606923892:AAHXgO5n0xnNE6HpEeNmwWAbJCLnnQtGoGA")

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🚐 Забронировать поездку", callback_data="start_booking")
    )
    bot.send_message(message.chat.id, "Привет! Что вы хотите сделать?", reply_markup=markup)

user_data = {}

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id

    if call.data == "start_booking":
        user_data[chat_id] = {}
        bot.send_message(chat_id, "Введите ваше имя:")
        bot.register_next_step_handler(call.message, get_name)

def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id]["name"] = message.text

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Владикавказ — Тбилиси", callback_data="route1"),
        types.InlineKeyboardButton("Тбилиси — Владикавказ", callback_data="route2")
    )
    bot.send_message(chat_id, "Выберите маршрут:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("route"))
def get_route(call):
    chat_id = call.message.chat.id
    user_data[chat_id]["route"] = "Владикавказ — Тбилиси" if call.data == "route1" else "Тбилиси — Владикавказ"

    markup = types.InlineKeyboardMarkup()
    times = ["09:00", "10:00", "11:00", "15:00", "19:00"]
    for time in times:
        markup.add(types.InlineKeyboardButton(time, callback_data=f"time_{time}"))
    bot.send_message(chat_id, "Выберите время выезда:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("time_"))
def get_time(call):
    chat_id = call.message.chat.id
    time = call.data.split("_")[1]
    user_data[chat_id]["time"] = time

    markup = types.InlineKeyboardMarkup(row_width=4)
    markup.add(
        types.InlineKeyboardButton("1", callback_data="pax_1"),
        types.InlineKeyboardButton("2", callback_data="pax_2"),
        types.InlineKeyboardButton("3", callback_data="pax_3"),
        types.InlineKeyboardButton("4+", callback_data="pax_4")
    )
    bot.send_message(chat_id, "Сколько пассажиров?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pax_"))
def get_passengers(call):
    chat_id = call.message.chat.id
    user_data[chat_id]["passengers"] = call.data.split("_")[1]

    markup = types.InlineKeyboardMarkup()
    locations = [
        ("✈️ Аэропорт", "loc_airport"),
        ("🚉 Ж/д вокзал", "loc_station"),
        ("🏠 С адреса во Владикавказе", "loc_address"),
        ("❓ Другое", "loc_other"),
        ("🚇 Станция метро Дидубе", "loc_didube")
    ]
    for label, callback in locations:
        markup.add(types.InlineKeyboardButton(label, callback_data=callback))
    bot.send_message(chat_id, "Выберите точку отправления:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("loc_"))
def finish_booking(call):
    chat_id = call.message.chat.id
    location = call.data.split("_")[1]
    loc_names = {
        "airport": "Аэропорт",
        "station": "Ж/д вокзал",
        "address": "С адреса во Владикавказе",
        "other": "Другое",
        "didube": "Станция метро Дидубе"
    }
    user_data[chat_id]["location"] = loc_names.get(location, "Неизвестно")

    data = user_data[chat_id]
    text = (
        f"🚐 Новая заявка!
"
        f"👤 Имя: {data['name']}
"
        f"🗺️ Маршрут: {data['route']}
"
        f"🕘 Время: {data['time']}
"
        f"👥 Пассажиров: {data['passengers']}
"
        f"📍 Отправление: {data['location']}"
    )

    bot.send_message("@TransverTbilisi", text)
    bot.send_message(chat_id, "Ваша заявка отправлена админам.
[Чат с админами](https://t.me/TransverTbilisi)", parse_mode="Markdown")

if __name__ == '__main__':
    bot.polling(none_stop=True)
