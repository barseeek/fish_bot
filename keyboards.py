from environs import Env
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

import api_functions


def get_products_keyboard(host, headers):
    payload = api_functions.get_products(host, headers)
    keyboard = [[InlineKeyboardButton(text='Моя корзина', callback_data='my_cart')]]
    for product in payload['data']:
        keyboard.append([InlineKeyboardButton(product['attributes']['Title'], callback_data=product['id'])])

    return InlineKeyboardMarkup(keyboard, row_width=1)


PRODUCT_KEYBOARD = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton('Добавить в корзину', callback_data='add_to_cart'),
            InlineKeyboardButton('Моя корзина', callback_data='my_cart')
        ],
        [InlineKeyboardButton('Назад', callback_data='back')]
    ]
)
CART_KEYBOARD = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton('Оформить заказ', callback_data='order'),
            InlineKeyboardButton('В меню', callback_data='to_menu')
        ],
        [
            InlineKeyboardButton('Удалить товар из корзины', callback_data='delete_product')
        ]
    ]
)
EMPTY_CART_KEYBOARD = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton('В меню', callback_data='to_menu'),
        ]
    ]
)


