import requests
from environs import Env
from telegram import InlineKeyboardMarkup, InlineKeyboardButton


def get_products_keyboard():
    env = Env()
    env.read_env()
    url = f'http://{env.str("STRAPI_HOST", "localhost:1337")}/api/products'
    headers = {'Authorization': f'bearer {env.str("STRAPI_TOKEN")}'}
    response = requests.get(url, headers=headers)

    keyboard = []
    for product in response.json()['data']:
        keyboard.append([InlineKeyboardButton(product['attributes']['Title'], callback_data=product['id'])])

    return InlineKeyboardMarkup(keyboard, row_width=1)

PRODUCTS_KEYBOARD = get_products_keyboard()


if __name__ == '__main__':
    env = Env()
    env.read_env()
    get_products_keyboard()