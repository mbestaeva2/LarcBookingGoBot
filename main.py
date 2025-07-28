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

if __name__ == "__main__":
    bot.polling(none_stop=True)
