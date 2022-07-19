import logging
import os

import redis
from environs import Env
from notifiers.logging import NotificationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from telegram.ext import Filters, Updater

from format_message import create_cart_message, create_product_description
from motlin_tools import get_all_products, get_product_by_id, \
    get_product_image_by_id, add_product_in_cart, get_cart_items, \
    remove_product_from_cart, create_customer

_database = None
logger = logging.getLogger(__name__)


def create_menu_buttons():
    products = get_all_products()
    keyboard = [
        [InlineKeyboardButton(product.name, callback_data=product.id)]
        for product in products]
    keyboard.append(
        [InlineKeyboardButton('Корзина', callback_data='cart')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def create_card_buttons(products):
    keyboard = [
        [InlineKeyboardButton(f"Убрать из корзины {product.name}",
                              callback_data=product.id)]
        for product in products]
    keyboard.append(
        [InlineKeyboardButton('В меню', callback_data='menu'),
         InlineKeyboardButton('Оплатить', callback_data='email')]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def start(bot, update):
    reply_markup = create_menu_buttons()

    update.message.reply_text('Please choose:', reply_markup=reply_markup)
    return "HANDLE_MENU"


def handle_menu(bot, update):
    query = update.callback_query
    if query.data == 'cart':
        products, total_price = get_cart_items(update.effective_user.id)
        message = create_cart_message(products, total_price)
        reply_markup = create_card_buttons(products)
        bot.send_message(text=message,
                         reply_markup=reply_markup,
                         chat_id=query.message.chat_id)
        return "HANDLE_CART"
    product = get_product_by_id(query.data)

    keyboard = [
        [InlineKeyboardButton("1шт.", callback_data=f"1,{product.get('id')}"),
         InlineKeyboardButton("3шт.", callback_data=f"3,{product.get('id')}"),
         InlineKeyboardButton("5шт.", callback_data=f"5,{product.get('id')}")],
        [InlineKeyboardButton("Назад", callback_data="back")],
        [InlineKeyboardButton('Корзина', callback_data='cart')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_photo(
        chat_id=query.message.chat_id,
        photo=get_product_image_by_id(product.get('id')),
        caption=create_product_description(product),
        reply_markup=reply_markup
    )
    bot.delete_message(chat_id=query.message.chat_id,
                       message_id=query.message.message_id)
    return "HANDLE_DESCRIPTION"


def handle_cart(bot, update):
    query = update.callback_query
    if query.data == 'menu':
        reply_markup = create_menu_buttons()

        bot.send_message(text='Please choose:',
                         reply_markup=reply_markup,
                         chat_id=query.message.chat_id)
        bot.delete_message(chat_id=query.message.chat_id,
                           message_id=query.message.message_id)
        return "HANDLE_MENU"
    if query.data == 'email':
        bot.send_message(text="Напишите ваш email",
                         chat_id=query.message.chat_id)
        return "HANDLE_WAITING_EMAIL"
    else:
        remove_product_from_cart(query.data, update.effective_user.id)
        products, total_price = get_cart_items(update.effective_user.id)
        message = create_cart_message(products, total_price)
        reply_markup = create_card_buttons(products)
        bot.send_message(text=message,
                         reply_markup=reply_markup,
                         chat_id=query.message.chat_id)
        return "HANDLE_CART"


def handle_description(bot, update):
    query = update.callback_query
    try:
        command, product_id = query.data.split(",")
    except ValueError:
        command = query.data
        product_id = None

    if command == 'back':
        reply_markup = create_menu_buttons()

        bot.send_message(text='Please choose:',
                         reply_markup=reply_markup,
                         chat_id=query.message.chat_id)
        bot.delete_message(chat_id=query.message.chat_id,
                           message_id=query.message.message_id)
        return "HANDLE_MENU"

    if command == 'cart':
        products, total_price = get_cart_items(update.effective_user.id)
        message = create_cart_message(products, total_price)
        reply_markup = create_card_buttons(products)
        bot.send_message(text=message,
                         reply_markup=reply_markup,
                         chat_id=query.message.chat_id)
        return "HANDLE_CART"

    if command == '1':
        update.callback_query.answer("Товар добавлен в корзину")
        add_product_in_cart(product_id, 1, update.effective_user.id)
        return "HANDLE_DESCRIPTION"
    if command == '3':
        update.callback_query.answer("Товар добавлен в корзину")
        add_product_in_cart(product_id, 3, update.effective_user.id)
        return "HANDLE_DESCRIPTION"
    if command == '5':
        update.callback_query.answer("Товар добавлен в корзину")
        add_product_in_cart(product_id, 5, update.effective_user.id)
        return "HANDLE_DESCRIPTION"
    return "HANDLE_MENU"


def handle_waiting_email(bot, update):
    user = update.effective_user
    name = f"{user.first_name}_tgid-{user.id}"
    email = update.message.text
    create_customer(name, email)
    bot.send_message(
        text=f'Вы прислали мне эту почту: {email}',
        chat_id=update.message.chat_id)


def handle_users_reply(bot, update):
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
        'HANDLE_WAITING_EMAIL': handle_waiting_email,
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(bot, update)
        db.set(chat_id, next_state)
    except Exception as err:
        logging.error(err)


def get_database_connection():
    """
    Возвращает конекшн с базой данных Redis, либо создаёт новый, если он ещё не создан.
    """
    global _database
    if _database is None:
        _database = redis.Redis(host=database_host, port=database_port,
                                password=database_password)
    return _database


def handle_error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning(f'Update {update} caused error {error}', update, error)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s : %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S',
        level=logging.INFO
    )
    env = Env()
    env.read_env()
    telegram_api_token = env("TELEGRAM_API_TOKEN")
    telegram_chat_id = env("TELEGRAM_CHAT_ID")
    database_password = os.getenv("DATABASE_PASSWORD")
    database_host = os.getenv("DATABASE_HOST")
    database_port = os.getenv("DATABASE_PORT")

    params = {
        'token': telegram_api_token,
        'chat_id': telegram_chat_id
    }
    tg_handler = NotificationHandler("telegram", defaults=params)
    logger.addHandler(tg_handler)

    updater = Updater(telegram_api_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    dispatcher.add_error_handler(handle_error)
    updater.start_polling()
