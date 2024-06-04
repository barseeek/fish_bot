import logging

import redis
from environs import Env
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from telegram.ext import Filters, Updater

import api_functions
from keyboards import PRODUCT_KEYBOARD, CART_KEYBOARD, EMPTY_CART_KEYBOARD, get_products_keyboard
from log import TelegramLogsHandler

_database = None

logger = logging.getLogger('bot')


def start(update, context):
    """
    Хэндлер для состояния START.

    Бот отвечает пользователю фразой "Привет!" и переводит его в состояние HANDLE_MENU.
    Теперь в ответ на его команды будет запускается хэндлер echo.
    """

    update.message.reply_text(
        text='Привет!',
        reply_markup=get_products_keyboard(context.bot_data.get('host'), context.bot_data.get('headers'))
    )
    return "HANDLE_DESCRIPTION"


def handle_cart(update, context):
    query = update.callback_query
    query.answer()
    host = context.bot_data.get('host')
    headers = context.bot_data.get('headers')

    if query.data == "back" or query.data == "to_menu":
        show_menu(update, context)
        context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.callback_query.message.message_id,
        )
        return "HANDLE_DESCRIPTION"

    cart_id = api_functions.get_cart_id_by_tg_id(host, headers, query.from_user.id)
    if not cart_id:
        cart_id = api_functions.create_cart(host, headers, query.from_user.id)
    context.user_data["cart_id"] = cart_id

    if query.data == "my_cart":
        show_cart(update, context)

    elif query.data == "order":
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Укажите вашу почту:",
        )
        return "WAITING_EMAIL"
    elif query.data == "delete_product":
        cart_products = api_functions.get_cart_products(host, headers, cart_id)
        delete_product_keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=f"🛒{cart_product['title']} 🔢{cart_product['amount']} {cart_product['unit']}",
                        callback_data='delete_product_{}'.format(cart_product['id'])
                    )
                ]
                for cart_product in cart_products["items"]
            ])
        delete_product_keyboard.inline_keyboard.append([InlineKeyboardButton('Назад', callback_data='my_cart')])
        query.message.reply_text(text='Выберите товар для удаления', reply_markup=delete_product_keyboard)
        context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

    elif query.data == "add_to_cart":
        product_id = context.user_data.get('product_id')
        if not product_id:
            query.message.reply_text(text='Не могу найти товар, обратитесь в поддержку')

        message = api_functions.add_to_cart(host, headers, cart_id, product_id)
        query.message.reply_text(text=message)
        show_menu(update, context)
        context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        return 'HANDLE_DESCRIPTION'
    else:
        cart_product_id = query.data.replace('delete_product_', '')
        message = api_functions.delete_cart_product(host, headers, cart_product_id)
        query.message.reply_text(text=message)
        show_menu(update, context)
        context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        return 'HANDLE_MENU'

    return 'HANDLE_CART'


def show_menu(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Выберите позицию:',
        reply_markup=get_products_keyboard(context.bot_data.get('host'), context.bot_data.get('headers'))
    )


def handle_menu(update, context):
    query = update.callback_query
    query.answer()
    query.message.reply_text(
        text='Выберите позицию:',
        reply_markup=get_products_keyboard(context.bot_data.get('host'), context.bot_data.get('headers'))
    )
    context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    return "HANDLE_DESCRIPTION"


def show_cart(update, context):
    query = update.callback_query
    cart_id = api_functions.get_cart_id_by_tg_id(host, headers, query.from_user.id)
    if not cart_id:
        cart_id = api_functions.create_cart(host, headers, query.from_user.id)
    context.user_data["cart_id"] = cart_id
    message = 'Ваша корзина:\n'
    cart_products = api_functions.get_cart_products(host, headers, cart_id)

    if not cart_products:
        query.message.reply_text(text='Ваша корзина пуста', reply_markup=EMPTY_CART_KEYBOARD)

    for cart_product in cart_products["items"]:
        message += f"""🛒{cart_product['title']} 🔢{cart_product['amount']} {cart_product['unit']} 💰{cart_product['total_unit_price']} руб.\n"""
    message += f"Общая сумма: {round(cart_products['total_price'], 2)} руб."

    query.message.reply_text(text=message, reply_markup=CART_KEYBOARD)
    context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)


def handle_description(update, context):
    query = update.callback_query
    query.answer()
    host = context.bot_data.get('host')
    headers = context.bot_data.get('headers')

    if query.data == "my_cart":
        show_cart(update, context)
        return "HANDLE_CART"

    product_id = query.data
    context.user_data["product_id"] = product_id
    product, image_data = api_functions.get_product(host, headers, product_id)
    message = f"{product.get('description')}\n\nЦена - {product.get('price')} руб. за {product.get('unit')}"
    context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=image_data,
        caption=message,
        reply_markup=PRODUCT_KEYBOARD
    )
    context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

    return "HANDLE_CART"


def handle_email(update, context):
    email = update.message.text
    host = context.bot_data.get('host')
    headers = context.bot_data.get('headers')

    if not api_functions.get_user(host, headers, email):
        email, password = api_functions.create_user(host, headers, email, update.message.from_user.username,
                                                    context.user_data["cart_id"])
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Ваш логин от ЛК Strapi: {email}\n Пароль: {password}",
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Аккаунт с таким email уже создан"
        )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Заказ передан менеджеру, он свяжется с вами в ближайшее время.",
    )

    return "START"


def handle_users_reply(update, context):
    """
    Функция, которая запускается при любом сообщении от пользователя и решает как его обработать.
    Эта функция запускается в ответ на эти действия пользователя:
        * Нажатие на inline-кнопку в боте
        * Отправка сообщения боту
        * Отправка команды боту
    Она получает стейт пользователя из базы данных и запускает соответствующую функцию-обработчик (хэндлер).
    Функция-обработчик возвращает следующее состояние, которое записывается в базу данных.
    Если пользователь только начал пользоваться ботом, Telegram форсит его написать "/start",
    поэтому по этой фразе выставляется стартовое состояние.
    Если пользователь захочет начать общение с ботом заново, он также может воспользоваться этой командой.
    """
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode("utf-8")

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': handle_email

    }
    state_handler = states_functions[user_state]

    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception as err:
        logger.error('Возникла ошибка {0}'.format(err))


def get_database_connection():
    """
    Возвращает конекшн с базой данных Redis, либо создаёт новый, если он ещё не создан.
    """
    global _database
    if _database is None:
        database_password = env.str("REDIS_PASSWORD")
        database_host = env.str("REDIS_HOST")
        database_port = env.int("REDIS_PORT")
        _database = redis.Redis(host=database_host, port=database_port, password=database_password)
    return _database


if __name__ == '__main__':
    env = Env()
    env.read_env()
    token = env.str("TELEGRAM_BOT_TOKEN")
    chat_id = env.str('TELEGRAM_CHAT_ID')
    telegram_log_token = env.str('TELEGRAM_LOG_BOT_TOKEN')
    host = env.str("STRAPI_HOST", "localhost:1337")
    headers = {'Authorization': f'bearer {env.str("STRAPI_TOKEN")}'}

    tg_handler = TelegramLogsHandler(chat_id, telegram_log_token)
    logger.addHandler(tg_handler)
    logger.setLevel(env.str('LOG_LEVEL', 'INFO'))

    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data['host'] = host
    dispatcher.bot_data['headers'] = headers
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    updater.start_polling()
    logger.info('Fish TG бот запущен')

    updater.idle()
