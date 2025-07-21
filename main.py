import telebot
from telebot import types

# Replace 'YOUR_BOT_TOKEN_HERE' with your bot's API token
API_TOKEN = '7606923892:AAFTaq2UnGukug2VJJGZsN1NRrbgFeaICvQ'
# Replace with the Telegram user ID of the admin who will receive transfer requests
ADMIN_ID = 561665893

bot = telebot.TeleBot(API_TOKEN)
user_data = {}

def show_main_menu(chat_id):
    """Display the main menu with options."""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚕 Забронировать поездку", callback_data="book_transfer"))
    markup.add(types.InlineKeyboardButton("ℹ️ Информация о документах", callback_data="info_docs"))
    # This button opens a URL (e.g., a chat with admins or an external FAQ link)
    markup.add(types.InlineKeyboardButton("❓ Задать вопрос", url="https://t.me/TransferTbilisi"))
    bot.send_message(chat_id, "Главное меню:", reply_markup=markup)

def show_back_to_menu_button(chat_id):
    """Send a prompt with a 'Return to menu' button."""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu"))
    bot.send_message(chat_id, "Что дальше?", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start_command(message):
    """Handle the /start command by showing the main menu."""
    show_main_menu(message.chat.id)

# Step-by-step handlers for the booking process
def process_name(message):
    chat_id = message.chat.id
    user_data[chat_id]['name'] = message.text
    bot.send_message(chat_id, "Введите дату:")
    bot.register_next_step_handler(message, process_date)

def process_date(message):
    chat_id = message.chat.id
    user_data[chat_id]['date'] = message.text
    bot.send_message(chat_id, "Введите номер телефона:")
    bot.register_next_step_handler(message, process_phone)

def process_phone(message):
    chat_id = message.chat.id
    user_data[chat_id]['phone'] = message.text
    bot.send_message(chat_id, "Введите маршрут:")
    bot.register_next_step_handler(message, process_route)

def process_route(message):
    chat_id = message.chat.id
    user_data[chat_id]['route'] = message.text
    bot.send_message(chat_id, "Введите количество пассажиров:")
    bot.register_next_step_handler(message, process_passengers)

def process_passengers(message):
    chat_id = message.chat.id
    user_data[chat_id]['passengers'] = message.text
    # After collecting all text fields, prompt for location selection with inline buttons
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Аэропорт", callback_data="loc-airport"),
        types.InlineKeyboardButton("Ж/д вокзал", callback_data="loc-station")
    )
    markup.add(
        types.InlineKeyboardButton("С адреса во Владикавказе", callback_data="loc-address"),
        types.InlineKeyboardButton("Станция метро Дидубе", callback_data="loc-didube")
    )
    markup.add(types.InlineKeyboardButton("Другое", callback_data="loc-other"))
    bot.send_message(chat_id, "Откуда будет выезд? Выберите локацию:", reply_markup=markup)

def finish_booking(call):
    """Compile the request summary and ask for confirmation or cancellation."""
    chat_id = call.message.chat.id
    # Determine the chosen location text from the callback data
    location_key = call.data.split('-', 1)[1]
    loc_names = {
        "airport": "Аэропорт",
        "station": "Ж/д вокзал",
        "address": "С адреса во Владикавказе",
        "didube": "Станция метро Дидубе",
        "other": "Другое"
    }
    user_data[chat_id]['location'] = loc_names.get(location_key, "Неизвестно")
    data = user_data[chat_id]
    # Prepare a summary of the collected data
    summary_text = (
        f"📝 Проверьте данные заявки:\n\n"
        f"Имя: {data['name']}\n"
        f"Дата: {data['date']}\n"
        f"Телефон: {data['phone']}\n"
        f"Маршрут: {data['route']}\n"
        f"Пассажиры: {data['passengers']}\n"
        f"Локация: {data['location']}\n\n"
        f"Отправить заявку?"
    )
    # Inline keyboard for confirmation (submit) or cancellation
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Отправить", callback_data="confirm"),
        types.InlineKeyboardButton("❌ Отменить", callback_data="cancel")
    )
    bot.send_message(chat_id, summary_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Handle all callback queries from inline buttons."""
    chat_id = call.message.chat.id
    if call.data == "book_transfer":
        # User chose to start a transfer booking
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        user_data[chat_id] = {}  # initialize storage for this user
        sent = bot.send_message(chat_id, "Пожалуйста, введите ваше имя:")
        bot.register_next_step_handler(sent, process_name)
    elif call.data.startswith("loc-"):
        # Location selected in the booking process
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        finish_booking(call)
    elif call.data == "confirm":
        # User confirmed the request
        data = user_data.get(chat_id)
        if data:
            # Send the request details to admin
            request_text = (
                f"🆕 Новая заявка на трансфер:\n"
                f"Имя: {data['name']}\n"
                f"Дата: {data['date']}\n"
                f"Телефон: {data['phone']}\n"
                f"Маршрут: {data['route']}\n"
                f"Пассажиры: {data['passengers']}\n"
                f"Локация: {data['location']}"
            )
            bot.send_message(ADMIN_ID, request_text)
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        bot.send_message(chat_id, "Заявка отправлена ✅")
        show_back_to_menu_button(chat_id)
        user_data.pop(chat_id, None)  # clear stored data
    elif call.data == "cancel":
        # User canceled the request
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        bot.send_message(chat_id, "Заявка отменена ❌")
        show_back_to_menu_button(chat_id)
        user_data.pop(chat_id, None)
    elif call.data == "back_to_menu":
        # User wants to return to the main menu
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        show_main_menu(chat_id)
    elif call.data == "info_docs":
        # User requested information about documents
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        bot.send_message(chat_id, "Для поездки необходимо иметь при себе документы, удостоверяющие личность.")
        show_main_menu(chat_id)

# Start the bot
bot.polling(none_stop=True)
