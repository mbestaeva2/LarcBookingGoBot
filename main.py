
from telebot import TeleBot, types
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(TOKEN)

ADMIN_ID = 561665893

user_data = {}

def calculate_price(adults, children, animals):
    price_adult = 3000
    price_child = 2000
    price_pet = 500

    usd_rate = 92.0
    gel_rate = 30.0
    eur_rate = 100.0

    total_rub = adults * price_adult + children * price_child + animals * price_pet
    total_passengers = adults + children + animals

    if total_passengers >= 7:
        discount_percent = 15
    elif total_passengers >= 5:
        discount_percent = 10
    elif total_passengers >= 3:
        discount_percent = 5
    else:
        discount_percent = 0

    discount_amount = total_rub * (discount_percent / 100)
    final_total_rub = total_rub - discount_amount

    total_usd = round(final_total_rub / usd_rate, 2)
    total_gel = round(final_total_rub / gel_rate, 2)
    total_eur = round(final_total_rub / eur_rate, 2)

    return {
        "passengers": total_passengers,
        "discount_percent": discount_percent,
         "initial_rub": total_rub,
        "final_rub": round(final_total_rub, 2),
        "final_usd": total_usd,
        "final_gel": total_gel,
        "final_eur": total_eur
    }

@bot.message_handler(commands=['start'])
def handle_start(message):
    show_main_menu(message.chat.id)

def show_main_menu(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("Рассчитать стоимость", callback_data="start_booking"),
        types.InlineKeyboardButton("📄 Информация о документах", callback_data="info"),
        types.InlineKeyboardButton("❓ Задать вопрос", url="https://t.me/TransverTbilisi")
    )
    bot.send_message(chat_id, "Главное меню:", reply_markup=markup)

from telebot import types

def ask_phone(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton("📱 Отправить номер", request_contact=True)
    markup.add(button)
    bot.send_message(chat_id, "📞 Пожалуйста, нажмите кнопку, чтобы отправить свой номер телефона:", reply_markup=markup)
    
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    chat_id = message.chat.id
    if message.contact:
        user_data[chat_id]["phone"] = message.contact.phone_number
        bot.send_message(chat_id, "Спасибо! Номер получен ✅", reply_markup=types.ReplyKeyboardRemove())
        # Переходим к следующему шагу
        ask_location(chat_id)
        
        # Переходим к следующему шагу — выбор локации
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
        finish_booking(chat_id)
        #show_summary(chat_id)

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
        bot.send_message(chat_id, "Для поездки необходимо иметь\n"
                         "*загранпаспорт(обьязательно, внутренний не подойдет)\n"
                        "*Загранпаспорт ребенка, свидетельство о рождении(на границе могут потребовать)\n"
                        "*Для животных: Ветпаспорт с прививкой от бешенства,\n"
                        "Справка формы №1\n"
                        "Наличие чипа(желательно")
        show_main_menu(chat_id)

def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id]["name"] = message.text
    msg = bot.send_message(chat_id, "Введите дату поездки (например, 22.07):")
    bot.register_next_step_handler(msg, get_date)

def get_date(message):
    chat_id = message.chat.id
    user_data[chat_id]["date"] = message.text
    msg = bot.send_message(chat_id, "Сколько взрослых?")
    bot.register_next_step_handler(msg, get_passengers)

def get_passengers(message):
    chat_id = message.chat.id
    user_data[chat_id]["passengers"] = message.text
    msg = bot.send_message(chat_id, "Сколько детей? 👶:")
    bot.register_next_step_handler(msg, get_children)

def get_children(message):
    chat_id = message.chat.id
    user_data[chat_id]["children"] = message.text
    msg = bot.send_message(chat_id, "Сколько животных? 🐶:")
    bot.register_next_step_handler(msg, get_animals)    
def get_animals(message):
    chat_id = message.chat.id
    user_data[chat_id]["animals"] = message.text
    # Теперь, когда всё собрано — показываем маршрут
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Владикавказ — Тбилиси", callback_data="route_Владикавказ — Тбилиси"),
        types.InlineKeyboardButton("Владикавказ — Степанцминда", callback_data="route_Владикавказ — Степанцминда"),
        types.InlineKeyboardButton("Владикавказ — Кутаиси", callback_data="route_Владикавказ — Кутаиси"),
        types.InlineKeyboardButton("Владикавказ — Батуми", callback_data="route_Владикавказ — Батуми"),
        types.InlineKeyboardButton("Тбилиси — Владикавказ", callback_data="route_Тбилиси — Владикавказ")
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

def get_passengers(message):
    chat_id = message.chat.id
    user_data[chat_id]["passengers"] = message.text
    msg = bot.send_message(chat_id, "Сколько детей? 👶:")
    bot.register_next_step_handler(msg, get_children)

def get_children(message):
    chat_id = message.chat.id
    user_data[chat_id]["children"] = message.text
    msg = bot.send_message(chat_id, "Сколько животных? 🐶:")
    bot.register_next_step_handler(msg, get_animals)    
def get_animals(message):
    chat_id = message.chat.id
    user_data[chat_id]["animals"] = message.text
    # Теперь, когда всё собрано — показываем маршрут
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Владикавказ — Тбилиси", callback_data="route_Владикавказ — Тбилиси"),
        types.InlineKeyboardButton("Владикавказ — Степанцминда", callback_data="route_Владикавказ — Степанцминда"),
        types.InlineKeyboardButton("Владикавказ — Кутаиси", callback_data="route_Владикавказ — Кутаиси"),
        types.InlineKeyboardButton("Владикавказ — Батуми", callback_data="route_Владикавказ — Батуми"),
        types.InlineKeyboardButton("Тбилиси — Владикавказ", callback_data="route_Тбилиси — Владикавказ")
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

def get_passengers(message):
    chat_id = message.chat.id
    user_data[chat_id]["passengers"] = message.text
    msg = bot.send_message(chat_id, "Сколько детей? 👶:")
    bot.register_next_step_handler(msg, get_children)

def get_children(message):
    chat_id = message.chat.id
    user_data[chat_id]["children"] = message.text
    msg = bot.send_message(chat_id, "Сколько животных? 🐶:")
    bot.register_next_step_handler(msg, get_animals)    
def get_animals(message):
    chat_id = message.chat.id
    user_data[chat_id]["animals"] = message.text
    # Теперь, когда всё собрано — показываем маршрут
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
    button = types.KeyboardButton("📱 Отправить номер", request_contact=True)
    markup.add(button)
    bot.send_message(chat_id, "Пожалуйста, нажмите кнопку, чтобы отправить свой номер телефона:", reply_markup=markup)
    
def finish_booking(chat_id):
    data = user_data.get(chat_id, {})

    try:
        adults = int(data.get("passengers", "0"))
        children = int(data.get("children", "0"))
        animals = int(data.get("animals", "0"))

        result = calculate_price(adults, children, animals)

        price_message = f"""
💰 Итоговая стоимость поездки:

👨‍👩‍👧‍👦 Пассажиров: {adults} взрослых, {children} детей
🐶 Животных: {animals}

🎁 Скидка: {result['discount_percent']}%
💵 Сумма без скидки: {result['initial_rub']} ₽
✅ Сумма со скидкой: {result['final_rub']} ₽

💲 В долларах: {result['final_usd']} $
💶 В евро: {result['final_eur']} €
🇬🇪 В лари: {result['final_gel']} ₾
"""
        bot.send_message(chat_id, price_message)

        summary = f"""🔎 Проверьте данные заявки:

👤 Имя: {data.get('name')}
📅 Дата: {data.get('date')}
📍 Маршрут: {data.get('route')}
📞 Телефон: {data.get('phone')}
🧍 Пассажиры: {data.get('passengers')}
👶 Дети: {data.get('children')}
🐾 Животные: {data.get('animals')}
🚗 Локация: {data.get('location')}

Отправить заявку?
"""

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Забронировать", callback_data="confirm_yes"),
            types.InlineKeyboardButton("❌ Отменить", callback_data="confirm_no")
        )

        bot.send_message(chat_id, summary, reply_markup=markup)

    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при расчёте: {e}")


if __name__ == '__main__':
    bot.polling(none_stop=True, timeout=60)
