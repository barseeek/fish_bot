import random
import string
from io import BytesIO

import requests
from environs import Env


class Strapi:
    env = Env()
    env.read_env()
    host = env.str("STRAPI_HOST", "localhost:1337")
    headers = {'Authorization': f'bearer {env.str("STRAPI_TOKEN")}'}

    @staticmethod
    def get_cart_id_by_tg_id(tg_id):
        response = requests.get(
            f'http://{Strapi.host}/api/carts',
            headers=Strapi.headers,
            params={'filters[tg_id][$eq]': tg_id}
        )
        response.raise_for_status()
        if response.status_code == 200:
            carts = response.json().get('data', [])
            if len(carts) > 0:
                return carts[0].get('id', None)
        return None

    @staticmethod
    def get_cart_products(cart_id):
        params = {
            'populate[cart_products][populate][0]': 'product'
        }
        response = requests.get(
            f'http://{Strapi.host}/api/carts/{cart_id}',
            params=params,
            headers=Strapi.headers
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

    @staticmethod
    def create_cart(tg_id):
        url = f'http://{Strapi.host}/api/carts/'
        payload = {
            "data": {
                "tg_id": tg_id,
            }
        }
        response = requests.post(url, json=payload, headers=Strapi.headers)
        response.raise_for_status()
        return response.json()['data']['id']

    @staticmethod
    def create_cart_product(product_id, quantity):
        url = f'http://{Strapi.host}/api/cart-products'
        payload = {
            "data": {
                "product": product_id,
                "amount": quantity
            }
        }
        response = requests.post(url, json=payload, headers=Strapi.headers)
        response.raise_for_status()
        cart_product_id = response.json().get('data', {}).get('id')
        return cart_product_id

    @staticmethod
    def get_products():
        url = f'http://{Strapi.host}/api/products'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_product(product_id):
        url = f'http://{Strapi.host}/api/products/{product_id}'
        params = {"populate": "picture"}
        response = requests.get(url, headers=Strapi.headers, params=params)
        response.raise_for_status()

        payload = response.json().get('data').get('attributes')
        description = payload.get('description')
        price = payload.get('price')
        image_url = 'http://{}{}'.format(
            Strapi.host,
            payload.get('picture').get('data').get('attributes').get('url')
        )
        response = requests.get(image_url, headers=Strapi.headers)
        response.raise_for_status()
        image_data = BytesIO(response.content)
        return payload, image_data

    @staticmethod
    def add_to_cart(cart_id, product_id, quantity=1):
        message = 'Товар добавлен в корзину'
        cart_product_id = Strapi.create_cart_product(product_id, quantity)
        url = f'http://{Strapi.host}/api/carts/{cart_id}'
        payload = {
            "data": {
                "cart_products": {
                    "connect": [cart_product_id]
                }
            }
        }
        response = requests.put(url, headers=Strapi.headers, json=payload)
        response.raise_for_status()
        if response.status_code != 200:
            message = 'Произошла ошибка при добавлении в корзину'
        return message

    @staticmethod
    def delete_cart_product(cart_product_id):
        message = 'Товар удален из корзины'

        url = f'http://{Strapi.host}/api/cart-products/{cart_product_id}'
        response = requests.delete(url, headers=Strapi.headers)
        response.raise_for_status()
        if response.status_code != 200:
            message = 'Произошла ошибка при удалении товара'
        return message

    @staticmethod
    def create_user(email, username, cart_id):
        url = f'http://{Strapi.host}/api/users'
        password = generate_password()
        payload = {
            "username": username,
            "email": email,
            "password": password,
            "role": 2,
            "cart": cart_id

        }
        response = requests.post(url, json=payload, headers=Strapi.headers)
        response.raise_for_status()
        user_id = response.json().get('id')
        if not user_id:
            return None
        return email, password

    @staticmethod
    def get_user(email):
        url = f'http://{Strapi.host}/api/users'
        params = {
            "filters[email][$eq]": email
        }
        response = requests.get(url, headers=Strapi.headers, params=params)
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
