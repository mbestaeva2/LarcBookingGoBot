from telebot import TeleBot, types
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(TOKEN)
user_data = {}

usd_rate = 90
eur_rate = 100
gel_rate = 32

def calculate_price(adults, children, animals, route):
    if "Батуми" in route:
        price_adult, price_child, price_pet = 6000, 4000, 1000
    elif "Кутаиси" in route:
        price_adult, price_child, price_pet = 5000, 3500, 800
    elif "Степанцминда" in route:
        price_adult, price_child, price_pet = 2000, 1500, 500
    else:
        price_adult, price_child, price_pet = 3000, 2000, 500

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
        types.InlineKeyboardButton("Забронировать поездку", callback_data="start_booking"),
        types.InlineKeyboardButton("Рассчитать стоимость", callback_data="calc_price"),
        types.InlineKeyboardButton("Информация о документах", callback_data="info"),
        types.InlineKeyboardButton("Задать вопрос", url="https://t.me/TransverTbilisi")
    )
    bot.send_message(message.chat.id, "Привет! Выберите действие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    data = user_data.setdefault(chat_id, {})

    if call.data == "start_booking":
        if "adults" in data and "children" in data and "animals" in data and "route" in data:
            bot.send_message(chat_id, "Вы уже рассчитали стоимость. Оформляем заявку.")
            ask_name(chat_id)
        else:
            bot.send_message(chat_id, "Введите количество взрослых пассажиров:")
            bot.register_next_step_handler(call.message, get_adults)

    elif call.data == "calc_price":
        data.clear()
        bot.send_message(chat_id, "Сколько взрослых пассажиров?")
        bot.register_next_step_handler(call.message, get_adults)

    elif call.data == "info":
bot.send_message(chat_id, """Для поездки в Грузию вам понадобятся:

🛂 Паспорт РФ или загранпаспорт
🧾 COVID-сертификат — по ситуации
🚫 Виза не нужна для граждан РФ

📌 Уточняйте детали у водителя или администратора.""")
    elif call.data.startswith("route_"):
        route = call.data.split("_", 1)[1]
        data["route"] = route
        if all(k in data for k in ["adults", "children", "animals"]):
            result = calculate_price(data["adults"], data["children"], data["animals"], route)
            data["price"] = result
            message_text = (
                "Примерная стоимость:
"
                + route + "
"
                + "Взр: " + str(data["adults"]) + " | Дет: " + str(data["children"]) + " | Жив: " + str(data["animals"]) + "
"
                + "Всего: " + str(result["passengers"]) + "
"
                + "Скидка: " + str(result["discount_percent"]) + "%
"
                + str(result["final_rub"]) + " RUB | " + str(result["final_usd"]) + " USD | " + str(result["final_eur"]) + " EUR | " + str(result["final_gel"]) + " GEL"
            )
            bot.send_message(chat_id, message_text)
            ask_name(chat_id)

def get_adults(message):
    chat_id = message.chat.id
    try:
        user_data[chat_id]["adults"] = int(message.text)
        bot.send_message(chat_id, "Сколько детей?")
        bot.register_next_step_handler(message, get_children)
    except:
        bot.send_message(chat_id, "Ошибка! Введите число взрослых:")
        bot.register_next_step_handler(message, get_adults)

def get_children(message):
    chat_id = message.chat.id
    try:
        user_data[chat_id]["children"] = int(message.text)
        bot.send_message(chat_id, "Сколько животных?")
        bot.register_next_step_handler(message, get_animals)
    except:
        bot.send_message(chat_id, "Ошибка! Введите число детей:")
        bot.register_next_step_handler(message, get_children)

def get_animals(message):
    chat_id = message.chat.id
    try:
        user_data[chat_id]["animals"] = int(message.text)
        markup = types.InlineKeyboardMarkup()
        for route in ["Владикавказ — Тбилиси", "Владикавказ — Степанцминда", "Владикавказ — Кутаиси", "Владикавказ — Батуми", "Тбилиси — Владикавказ"]:
            markup.add(types.InlineKeyboardButton(route, callback_data="route_" + route))
        bot.send_message(chat_id, "Выберите маршрут:", reply_markup=markup)
    except:
        bot.send_message(chat_id, "Ошибка! Введите число животных:")
        bot.register_next_step_handler(message, get_animals)

def ask_name(chat_id):
    msg = bot.send_message(chat_id, "Введите ваше имя:")
    bot.register_next_step_handler(msg, get_name)

def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id]["name"] = message.text
    msg = bot.send_message(chat_id, "Введите дату поездки (например, 28.07):")
    bot.register_next_step_handler(msg, get_date)

def get_date(message):
    chat_id = message.chat.id
    user_data[chat_id]["date"] = message.text
    msg = bot.send_message(chat_id, "Введите номер телефона:")
    bot.register_next_step_handler(msg, get_phone)

def get_phone(message):
    chat_id = message.chat.id
    user_data[chat_id]["phone"] = message.text
    summary = user_data[chat_id]
    message_text = (
        "Заявка оформлена!

"
        + "Имя: " + summary["name"] + "
"
        + "Дата: " + summary["date"] + "
"
        + "Маршрут: " + summary["route"] + "
"
        + "Телефон: " + summary["phone"] + "
"
        + "Взр: " + str(summary["adults"]) + " | Дет: " + str(summary["children"]) + " | Жив: " + str(summary["animals"]) + "
"
        + "Сумма: " + str(summary["price"]["final_rub"]) + " RUB (" + str(summary["price"]["final_usd"]) + " USD)"
    )
    bot.send_message(561665893, message_text)
    bot.send_message(chat_id, "Ваша заявка отправлена! Мы свяжемся с вами в ближайшее время.")

if __name__ == "__main__":
    bot.polling(none_stop=True)
