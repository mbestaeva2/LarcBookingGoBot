
import telebot
from telebot import types
import qrcode
import os
from datetime import datetime

from keep_alive import keep_alive
keep_alive()

TOKEN = '7606923892:AAHvULF2JRwijXQfY80BCp1fceCFNBzvCO0'
ADMIN_ID = 561665893

bot = telebot.TeleBot(TOKEN)
user_data = {}

def get_greeting():
    now = datetime.now().hour
    if 5 <= now < 12:
        return "Доброе утро! 🌞"
    elif 12 <= now < 17:
        return "Добрый день! ☀️"
    elif 17 <= now < 22:
        return "Добрый вечер! 🌛"
    else:
        return "Доброй ночи! 🌙"

# Создание QR-кода, если файла ещё нет
qr_path = "driver_chat_qr.png"
if not os.path.exists(qr_path):
    img = qrcode.make("https://t.me/TransverTbilisi")
    img.save(qr_path)

@bot.message_handler(commands=['start'])
def show_main_menu(message):
    user_data[message.chat.id] = {'step': 'start'}
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🚐 Забронировать поездку", callback_data="start_booking"),
        types.InlineKeyboardButton("📄 Информация о документах", callback_data="info"),
        types.InlineKeyboardButton("❓ Задать вопрос", url="https://t.me/TransverTbilisi")
    )
    bot.send_message(
        message.chat.id,
        "👋 Добро пожаловать! Мы очень рады, что вы заглянули к нам 😊\n\n"
        "Если хотите просто задать вопрос — просто напишите его ✍️\n\n"
        "А если вы хотите забронировать поездку — нажмите кнопку ниже 👇",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "start_booking")
def start_booking(call):
    user_data[call.message.chat.id] = {'step': 'get_name'}
    bot.send_message(call.message.chat.id, "🙋 Напишите, как к вам обращаться?")

@bot.callback_query_handler(func=lambda call: call.data == "info")
def info_message(call):
    bot.send_message(call.message.chat.id,
        "📄 Документы для пересечения границы:\n– Загранпаспорт\n– Виза (если требуется)\n– Приглашение (если нужно)\n\n"
        "📩 Подробнее: https://t.me/TransverTbilisi")

@bot.message_handler(func=lambda msg: msg.chat.id in user_data)
def handle_user_message(message):
    chat_id = message.chat.id
    data = user_data[chat_id]
    step = data.get('step')

    if message.text.lower() in ['привет', 'здравствуйте', 'хай']:
        bot.send_message(chat_id, "Привет, как дела? 😊")
        return
    if message.text.lower() in ['спасибо', 'благодарю']:
        bot.send_message(chat_id, "Пожалуйста! Рады помочь 🙌")
        return

    if step == 'get_name':
        data['name'] = message.text
        data['step'] = 'get_date'
        markup = types.InlineKeyboardMarkup(row_width=3)
        for dt in ['18 July', '19 July', '20 July', '21 July']:
            markup.add(types.InlineKeyboardButton(text=dt, callback_data='date_' + dt))
        markup.add(types.InlineKeyboardButton("Ввести вручную", callback_data='date_manual'))
        bot.send_message(chat_id, "📅 Выберите дату поездки:", reply_markup=markup)
    elif step == 'get_date_manual':
        data['date'] = message.text
        data['step'] = 'get_route'
        send_route_selection(chat_id)
    elif step == 'get_route_manual':
        data['route'] = message.text
        data['step'] = 'get_phone'
        bot.send_message(chat_id, "📱 Укажите номер телефона:")
    elif step == 'get_phone':
        data['phone'] = message.text
        data['step'] = 'confirm'
        show_confirmation(chat_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("date_"))
def handle_date_selection(call):
    chat_id = call.message.chat.id
    value = call.data.replace("date_", "")
    if value == "manual":
        user_data[chat_id]['step'] = 'get_date_manual'
        bot.send_message(chat_id, "Введите дату вручную:")
    else:
        user_data[chat_id]['date'] = value
        user_data[chat_id]['step'] = 'get_route'
        send_route_selection(chat_id)

def send_route_selection(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for route in ['Владикавказ — Тбилиси', 'Владикавказ — Степанцминда', 'Владикавказ — Кутаиси', 'Владикавказ — Батуми', 'Тбилиси — Владикавказ']:
        markup.add(types.InlineKeyboardButton(text=route, callback_data='route_' + route))
    markup.add(types.InlineKeyboardButton("Свой маршрут", callback_data='route_manual'))
    bot.send_message(chat_id, "🗺 Выберите маршрут:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("route_"))
def handle_route_selection(call):
    chat_id = call.message.chat.id
    value = call.data.replace("route_", "")
    if value == "manual":
        user_data[chat_id]['step'] = 'get_route_manual'
        bot.send_message(chat_id, "Введите маршрут вручную:")
    else:
        user_data[chat_id]['route'] = value
        user_data[chat_id]['step'] = 'get_phone'
        bot.send_message(chat_id, "📱 Укажите номер телефона:")

def show_confirmation(chat_id):
    data = user_data[chat_id]
    text = (
        f"📋 Ваша заявка:\n"
        f"👤 Имя: {data['name']}\n"
        f"📅 Дата: {data['date']}\n"
        f"🛣 Маршрут: {data['route']}\n"
        f"📞 Телефон: {data['phone']}"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data="confirm"),
        types.InlineKeyboardButton("❌ Отменить", callback_data="cancel")
    )
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["confirm", "cancel"])
def handle_final_confirmation(call):
    chat_id = call.message.chat.id
    data = user_data.get(chat_id, {})
    if call.data == "confirm":
        bot.send_message(chat_id, "✅ Ваша заявка принята! Ожидайте подтверждения.")
        text = (
            f"🆕 Новая заявка:\n"
            f"👤 Имя: {data['name']}\n"
            f"📅 Дата: {data['date']}\n"
            f"🛣 Маршрут: {data['route']}\n"
            f"📞 Телефон: {data['phone']}\n"
            f"🔗 Написать: https://t.me/{call.from_user.username or 'username'}"
        )
        bot.send_message(ADMIN_ID, text)
        with open("driver_chat_qr.png", "rb") as qr:
            bot.send_photo(chat_id, qr, caption="📲 Вот чат с водителем. Нажмите или отсканируйте QR-код, чтобы задать вопрос.")
    else:
        bot.send_message(chat_id, "❌ Заявка отменена.")
    user_data.pop(chat_id, None)

@bot.message_handler(func=lambda msg: True)
def fallback_message(message):
    text = message.text.lower()
    chat_id = message.chat.id

    if text in ["привет", "здравствуйте", "хай"]:
        bot.send_message(chat_id, f"{get_greeting()} Напишите, если хотите забронировать. 🚐")
    elif text in ["спасибо", "благодарю"]:
        bot.send_message(chat_id, "Пожалуйста! Обращайтесь 🙂")
    else:
        bot.send_message(chat_id, "Если вы хотите забронировать поездку, нажмите /start.")

if __name__ == '__main__':
    bot.polling(none_stop=True)

1