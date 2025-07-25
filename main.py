from telebot import TeleBot, types
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(TOKEN)

user_data = {}

# Валютные курсы
usd_rate = 90
eur_rate = 100
gel_rate = 30

# ---------- ФУНКЦИЯ РАСЧЁТА ---------- #
def calculate_price(adults, children, animals, route):
    # Базовые цены по маршруту
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
        # Для маршрутов Владикавказ—Тбилиси и Тбилиси—Владикавказ
        price_adult = 3000
        price_child = 2000
        price_pet = 500

    # Подсчёт стоимости
    total = adults * price_adult + children * price_child + animals * price_pet
    total_passengers = adults + children + animals

    # Скидки
    if total_passengers >= 7:
        discount = 15
    elif total_passengers >= 5:
        discount = 10
    elif total_passengers >= 3:
        discount = 5
    else:
        discount = 0

    final_rub = int(total * (1 - discount / 100))

    # Конвертация валют (можешь заменить на API)
    usd_rate = 90
    eur_rate = 100
    gel_rate = 32

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
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🚐 Забронировать поездку", callback_data="start_booking"),
        types.InlineKeyboardButton("💰 Рассчитать стоимость", callback_data="calc_price"),
        types.InlineKeyboardButton("📄 Информация о документах", callback_data="info"),
        types.InlineKeyboardButton("❓ Задать вопрос", url="https://t.me/TransverTbilisi")
    )
    bot.send_message(message.chat.id, "Привет! 👋 Выберите действие:", reply_markup=markup)

# ---------- СТАРТ ---------- #
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id

    if call.data == "start_booking":
        user_data[chat_id] = {}
        msg = bot.send_message(chat_id, "Введите имя:")
        bot.register_next_step_handler(msg, get_name)

    elif call.data == "info":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "📄 Для поездки в Грузию вам понадобятся:\n\n"
                                  "🛂 Паспорт РФ или загранпаспорт\n"
                                  "🧾 COVID-сертификат — по ситуации\n"
                                  "🚫 Виза не нужна для граждан РФ\n\n"
                                  "📌 Уточняйте детали у водителя или администратора.")

    elif call.data == "calc_price":
        user_data[chat_id] = {}
        msg = bot.send_message(chat_id, "Сколько взрослых пассажиров?")
        bot.register_next_step_handler(msg, get_adults_for_price)

    elif call.data.startswith("calc_route_"):
        bot.answer_callback_query(call.id)
        route = call.data.split("_", 1)[1]
        user_data[chat_id]["route"] = route

        adults = int(user_data[chat_id].get("adults", 0))
        children = int(user_data[chat_id].get("children", 0))
        animals = int(user_data[chat_id].get("animals", 0))

        result = calculate_price(adults, children, animals, route)
        user_data[chat_id]["price"] = result

        text = f"""💰 Примерная стоимость:

📍 {route}
👤 Взр: {adults} | 🧒 Дет: {children} | 🐶 Жив: {animals}
🎟 Всего: {result['passengers']}
🔻 Скидка: {result['discount_percent']}%
💵 {result['final_rub']} ₽ | {result['final_usd']} $ | {result['final_eur']} € | {result['final_gel']} ₾
"""
        bot.send_message(chat_id, text)

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Да, хочу оформить", callback_data="confirm_booking"),
            types.InlineKeyboardButton("❌ Нет, спасибо", callback_data="cancel_booking")
        )
        bot.send_message(chat_id, "Хотите оформить заявку на поездку?", reply_markup=markup)

    elif call.data == "confirm_booking":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, "Отлично! Введите имя:")
        bot.register_next_step_handler(msg, get_name)

    elif call.data == "cancel_booking":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "Хорошо 😊 Если передумаете — нажмите /start")

    elif call.data.startswith("loc_"):
        bot.answer_callback_query(call.id)
        locs = {
            "airport": "Аэропорт",
            "station": "Ж/д вокзал",
            "address": "С адреса во Владикавказе",
            "didube": "Станция метро Дидубе",
            "other": "Другое"
        }
        loc_key = call.data.split("_", 1)[1]
        user_data[chat_id]["location"] = locs.get(loc_key, "Неизвестно")

        data = user_data[chat_id]
        message_text = f"""📩 Новая заявка:

👤 Имя: {data['name']}
📅 Дата: {data['date']}
📍 Маршрут: {data['route']}
👥 Взр/Дет/Жив: {data['adults']}/{data['children']}/{data['animals']}
📞 Телефон: {data['phone']}
🚗 Локация: {data['location']}
"""
        bot.send_message(561665893, message_text)  # Заменить ID при необходимости
        bot.send_message(chat_id, "✅ Спасибо! Заявка отправлена. Мы с вами скоро свяжемся.")
        
# ---------- ШАГИ АНКЕТЫ ---------- #
def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id]["name"] = message.text
    msg = bot.send_message(chat_id, "Введите дату поездки:")
    bot.register_next_step_handler(msg, get_date)
def get_date(message):
    chat_id = message.chat.id
    try:
        user_data[chat_id]["date"] = message.text  # здесь нет необходимости в try, но оставим на всякий
        msg = bot.send_message(chat_id, "Сколько взрослых?")
        bot.register_next_step_handler(msg, get_adults)
    except Exception:
        msg = bot.send_message(chat_id, "Произошла ошибка. Введите дату ещё раз:")
        bot.register_next_step_handler(msg, get_date)

def get_adults_for_price(message):
    chat_id = message.chat.id
    try:
        user_data[chat_id]["adults"] = int(message.text)
        msg = bot.send_message(chat_id, "Сколько детей?")
        bot.register_next_step_handler(msg, get_children_for_price)
    except ValueError:
        msg = bot.send_message(chat_id, "Пожалуйста, введите число (например: 2)")
        bot.register_next_step_handler(msg, get_adults_for_price)

def get_children_for_price(message):
    chat_id = message.chat.id
    try:
        user_data[chat_id]["children"] = int(message.text)
        msg = bot.send_message(chat_id, "Сколько животных?")
        bot.register_next_step_handler(msg, get_animals_for_price)
    except ValueError:
        msg = bot.send_message(chat_id, "❗️ Пожалуйста, введите число (например: 1)")
        bot.register_next_step_handler(msg, get_children_for_price)


def get_animals_for_price(message):
    chat_id = message.chat.id
    try:
        user_data[chat_id]["animals"] = int(message.text)

        # Далее предложим выбрать маршрут
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Владикавказ → Тбилиси", callback_data="calc_route_Владикавказ — Тбилиси"),
            types.InlineKeyboardButton("Тбилиси → Владикавказ", callback_data="calc_route_Тбилиси — Владикавказ"),
            types.InlineKeyboardButton("Владикавказ → Батуми", callback_data="calc_route_Владикавказ — Батуми"),
            types.InlineKeyboardButton("Владикавказ → Кутаиси", callback_data="calc_route_Владикавказ — Кутаиси"),
            types.InlineKeyboardButton("Владикавказ → Степанцминда", callback_data="calc_route_Владикавказ — Степанцминда")
        )
        bot.send_message(chat_id, "Выберите маршрут для расчёта стоимости:", reply_markup=markup)

    except ValueError:
        msg = bot.send_message(chat_id, "❗ Пожалуйста, введите число (например: 0)")
        bot.register_next_step_handler(msg, get_animals_for_price)

# ---------- ЗАПРОС ТЕЛЕФОНА ---------- #
def ask_phone(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton("📱 Отправить номер", request_contact=True)
    markup.add(button)
    msg = bot.send_message(chat_id, "Отправьте номер телефона:", reply_markup=markup)
    bot.register_next_step_handler(msg, handle_contact)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    chat_id = message.chat.id
    user_data[chat_id]["phone"] = message.contact.phone_number

    # Убираем клавиатуру
    hide_markup = types.ReplyKeyboardRemove()

    # Выбор места выезда
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Аэропорт", callback_data="loc_airport"),
        types.InlineKeyboardButton("Ж/д вокзал", callback_data="loc_station"),
        types.InlineKeyboardButton("С адреса во Владикавказе", callback_data="loc_address"),
        types.InlineKeyboardButton("Станция метро Дидубе", callback_data="loc_didube"),
        types.InlineKeyboardButton("Другое", callback_data="loc_other")
    )
    bot.send_message(chat_id, "Откуда будет выезд?", reply_markup=markup)

# ---------- ЗАПУСК ---------- #
if __name__ == '__main__':
    bot.polling(non_stop=True, timeout=60)
