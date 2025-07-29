from telebot import TeleBot, types
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(TOKEN)

ADMIN_ID = 561665893
ADMIN_GROUP_ID = -4948043121

user_data = {}

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
    total_passengers = adults + children + animals

    if total_passengers >= 7:
        discount = 15
    elif total_passengers >= 5:
        discount = 10
    elif total_passengers >= 3:
        discount = 5
    else:
        discount = 0

    final_rub = int(total * (1 - discount / 100))
    usd_rate, eur_rate, gel_rate = 90, 100, 32

    return {
        "final_rub": final_rub,
        "final_usd": round(final_rub / usd_rate, 2),
        "final_eur": round(final_rub / eur_rate, 2),
        "final_gel": round(final_rub / gel_rate, 2),
        "discount_percent": discount,
        "passengers": total_passengers
    }

@bot.message_handler(commands=['start'])
def show_main_menu(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🚐 Забронировать поездку", callback_data="start_booking"),
        types.InlineKeyboardButton("💰 Рассчитать стоимость", callback_data="calc_price"),
        types.InlineKeyboardButton("📄 Информация о документах", callback_data="info"),
        types.InlineKeyboardButton("❓ Задать вопрос", url="https://t.me/TransverTbilisi")
    )
    bot.send_message(message.chat.id, "Привет! 👋 Выберите действие:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    chat_id = message.chat.id
    if message.contact:
        user_data[chat_id]["phone"] = message.contact.phone_number
        bot.send_message(chat_id, "Спасибо! Номер получен. Теперь выберите место выезда:",
                         reply_markup=types.ReplyKeyboardRemove())
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Аэропорт", callback_data="loc_airport"),
            types.InlineKeyboardButton("Ж/д вокзал", callback_data="loc_station"),
            types.InlineKeyboardButton("С адреса во Владикавказе", callback_data="loc_address"),
            types.InlineKeyboardButton("Станция метро Дидубе", callback_data="loc_didube"),
            types.InlineKeyboardButton("Другое", callback_data="loc_other")
        )
        bot.send_message(chat_id, "Откуда будет выезд?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id

    if call.data == "start_booking":
        user_data[chat_id] = {}
        msg = bot.send_message(chat_id, "Введите имя:")
        bot.register_next_step_handler(msg, get_name)

    elif call.data.startswith("route_"):
        user_data[chat_id]["route"] = call.data.split("_", 1)[1]
        ask_phone(chat_id)

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
        summary = f"""🚨 Новая заявка!
Имя: {data.get('name')}
Дата: {data.get('date')}
Маршрут: {data.get('route')}
Телефон: {data.get('phone')}
Пассажиры: {data.get('passengers')}
Локация: {data.get('location')}
"""
        bot.send_message(ADMIN_GROUP_ID, summary)
        bot.send_message(chat_id, "Заявка отправлена ✅")
        show_main_menu(call.message)

    elif call.data == "confirm_no":
        bot.send_message(chat_id, "Заявка отменена ❌")
        show_main_menu(call.message)

    elif call.data == "info":
        bot.send_message(chat_id, "📄 Для поездки необходимо иметь паспорт и ПЦР-тест.")
        show_main_menu(call.message)
        
def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id]["name"] = message.text
    msg = bot.send_message(chat_id, "Введите дату поездки (например, 29.07):")
    bot.register_next_step_handler(msg, get_date)

def get_date(message):
    chat_id = message.chat.id
    user_data[chat_id]["date"] = message.text
    msg = bot.send_message(chat_id, "Сколько взрослых?")
    bot.register_next_step_handler(msg, get_passengers)

def get_passengers(message):
    chat_id = message.chat.id
    user_data[chat_id]["passengers"] = message.text
    msg = bot.send_message(chat_id, "Сколько детей?")
    bot.register_next_step_handler(msg, get_children)

def get_children(message):
    chat_id = message.chat.id
    user_data[chat_id]["children"] = message.text
    msg = bot.send_message(chat_id, "Сколько животных?")
    bot.register_next_step_handler(msg, get_animals)

def get_animals(message):
    chat_id = message.chat.id
    user_data[chat_id]["animals"] = message.text
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Владикавказ — Тбилиси", callback_data="route_Владикавказ — Тбилиси"),
        types.InlineKeyboardButton("Владикавказ — Степанцминда", callback_data="route_Владикавказ — Степанцминда"),
        types.InlineKeyboardButton("Владикавказ — Кутаиси", callback_data="route_Владикавказ — Кутаиси"),
        types.InlineKeyboardButton("Владикавказ — Батуми", callback_data="route_Владикавказ — Батуми"),
        types.InlineKeyboardButton("Тбилиси — Владикавказ", callback_data="route_Тбилиси — Владикавказ")
    )
    bot.send_message(chat_id, "Выберите маршрут:", reply_markup=markup)

def ask_phone(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = types.KeyboardButton("📱 Отправить номер", request_contact=True)
    markup.add(btn)
    bot.send_message(chat_id, "Пожалуйста, нажмите кнопку, чтобы отправить свой номер телефона:", reply_markup=markup)

def show_summary(chat_id):
    data = user_data.get(chat_id, {})
    summary = f"""🔍 Проверьте данные заявки:

👤 Имя: {data.get('name')}
📅 Дата: {data.get('date')}
🚗 Маршрут: {data.get('route')}
📞 Телефон: {data.get('phone')}
👨‍👩‍👧 Пассажиры: {data.get('passengers')}
👶 Дети: {data.get('children')}
🐾 Животные: {data.get('animals')}
📍 Локация: {data.get('location')}
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_yes"),
        types.InlineKeyboardButton("❌ Отменить", callback_data="confirm_no")
    )
    bot.send_message(chat_id, summary, reply_markup=markup)

if __name__ == "__main__":
    bot.polling(none_stop=True)
