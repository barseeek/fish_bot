import random
import string
from io import BytesIO

import requests
from environs import Env


def get_cart_id_by_tg_id(host, headers, tg_id):
    response = requests.get(
        f'http://{host}/api/carts',
        headers=headers,
        params={'filters[tg_id][$eq]': tg_id}
    )
    response.raise_for_status()
    if response.status_code == 200:
        carts = response.json().get('data', [])
        if len(carts) > 0:
            return carts[0].get('id', None)
    return None


def get_cart_products(host, headers, cart_id):
    params = {
        'populate[cart_products][populate][0]': 'product'
    }
    response = requests.get(
        f'http://{host}/api/carts/{cart_id}',
        params=params,
        headers=headers
    )
    response.raise_for_status()
    cart_products = response.json()['data']['attributes']['cart_products']['data']
    if len(cart_products) == 0:
        return None

    total_price = 0
    cart_items = []
    for cart_product in cart_products:
        attributes = cart_product['attributes']
        amount = attributes['amount']
        title = attributes['product']['data']['attributes']['Title']
        price = attributes['product']['data']['attributes']['price']
        unit = attributes['product']['data']['attributes']['unit']
        total_unit_price = price * amount
        cart_items.append({
            'id': cart_product['id'],
            'title': title,
            'amount': amount,
            'unit': unit,
            'price': price,
            'total_unit_price': total_unit_price
        })
        total_price += total_unit_price

    result = {
        'items': cart_items,
        'total_price': round(total_price, 2)
    }

    return result


def create_cart(host, headers, tg_id):
    url = f'http://{host}/api/carts/'
    payload = {
        "data": {
            "tg_id": tg_id,
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()['data']['id']


def create_cart_product(host, headers, product_id, quantity):
    url = f'http://{host}/api/cart-products'
    payload = {
        "data": {
            "product": product_id,
            "amount": quantity
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    cart_product_id = response.json().get('data', {}).get('id')
    return cart_product_id


def get_products(host, headers):
    url = f'http://{host}/api/products'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_product(host, headers, product_id):
    url = f'http://{host}/api/products/{product_id}'
    params = {"populate": "picture"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    payload = response.json().get('data').get('attributes')
    description = payload.get('description')
    price = payload.get('price')
    image_url = 'http://{}{}'.format(
        host,
        payload.get('picture').get('data').get('attributes').get('url')
    )
    response = requests.get(image_url, headers=headers)
    response.raise_for_status()
    image_data = BytesIO(response.content)
    return payload, image_data


def add_to_cart(host, headers, cart_id, product_id, quantity=1):
    message = 'Товар добавлен в корзину'
    cart_product_id = create_cart_product(product_id, quantity)
    url = f'http://{host}/api/carts/{cart_id}'
    payload = {
        "data": {
            "cart_products": {
                "connect": [cart_product_id]
            }
        }
    }
    response = requests.put(url, headers=headers, json=payload)
    response.raise_for_status()
    if response.status_code != 200:
        message = 'Произошла ошибка при добавлении в корзину'
    return message


def delete_cart_product(host, headers, cart_product_id):
    message = 'Товар удален из корзины'

    url = f'http://{host}/api/cart-products/{cart_product_id}'
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    if response.status_code != 200:
        message = 'Произошла ошибка при удалении товара'
    return message


def create_user(host, headers, email, username, cart_id):
    url = f'http://{host}/api/users'
    password = generate_password()
    payload = {
        "username": username,
        "email": email,
        "password": password,
        "role": 2,
        "cart": cart_id

    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    user_id = response.json().get('id')
    if not user_id:
        return None
    return email, password


def get_user(host, headers, email):
    url = f'http://{host}/api/users'
    params = {
        "filters[email][$eq]": email
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    users = response.json()
    return users[0] if users else None


def generate_password(length=8):
    characters = ''
    characters += string.ascii_uppercase
    characters += string.ascii_lowercase
    characters += string.digits
    characters += string.punctuation

    password = ''.join(random.choice(characters) for _ in range(length))
    return password
