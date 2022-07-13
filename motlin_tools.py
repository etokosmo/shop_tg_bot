from dataclasses import dataclass
from datetime import datetime

import requests
from environs import Env

motlin_token, token_expires_timestamp = None, None


@dataclass()
class Product:
    id: str
    name: str
    description: str = None
    amount: int = None
    price: str = None


def is_valid_token(token_expires_timestamp: int) -> bool:
    """Return whether token has expired"""
    now_datetime = datetime.now()
    token_expires_datetime = datetime.fromtimestamp(token_expires_timestamp)
    return now_datetime < token_expires_datetime


def get_motlin_access_token() -> str:
    """Return motlin access token"""
    global motlin_token, token_expires_timestamp
    if motlin_token is None:
        motlin_token, token_expires_timestamp = make_authorization()
    elif not is_valid_token(token_expires_timestamp):
        motlin_token, token_expires_timestamp = make_authorization()
    return motlin_token


def make_authorization() -> (str, int):
    """Return created access_token and expires of token"""
    env = Env()
    env.read_env()
    motlin_client_id = env("MOTLIN_CLIENT_ID")
    motlin_client_secret = env("MOTLIN_CLIENT_SECRET")
    data = {
        'client_id': motlin_client_id,
        'client_secret': motlin_client_secret,
        'grant_type': 'client_credentials',
    }

    response = requests.post('https://api.moltin.com/oauth/access_token',
                             data=data)
    authorization = response.json()
    return authorization.get("access_token"), authorization.get("expires")


def get_all_products() -> [Product]:
    """Return list if Product class with product's id and name"""
    motlin_access_token = get_motlin_access_token()
    headers = {
        'Authorization': f'Bearer {motlin_access_token}',
    }

    response = requests.get('https://api.moltin.com/v2/products',
                            headers=headers)

    store = response.json().get("data")
    return [Product(product.get("id"),
                    product.get("name")) for product in store]


def get_product_by_id(product_id: str) -> dict:
    """Return product serialized dict from moltin"""
    motlin_access_token = get_motlin_access_token()
    headers = {
        'Authorization': f'Bearer {motlin_access_token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/products/{product_id}',
                            headers=headers)
    return response.json().get("data")


def get_product_image_by_id(product_id: str) -> str:
    """Return href product's image from moltin"""
    motlin_access_token = get_motlin_access_token()
    product_file_id = get_product_by_id(product_id).get("relationships").get(
        "main_image").get("data").get("id")

    headers = {
        'Authorization': f'Bearer {motlin_access_token}',
    }

    response = requests.get(
        f'https://api.moltin.com/v2/files/{product_file_id}',
        headers=headers)
    return response.json().get("data").get("link").get("href")


def add_product_in_cart(product_id: str, amount: int,
                        customer_id: int) -> None:
    """Add product with his amount in user cart"""
    motlin_access_token = get_motlin_access_token()
    headers = {
        'Authorization': f'Bearer {motlin_access_token}',
    }

    json_data = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': amount,
        },
    }

    requests.post(
        f'https://api.moltin.com/v2/carts/{customer_id}/items',
        headers=headers,
        json=json_data)


def get_cart_items(customer_id) -> ([Product], str):
    """Return list if Product class with products in cart and total price"""
    motlin_access_token = get_motlin_access_token()
    headers = {
        'Authorization': f'Bearer {motlin_access_token}',
    }

    response = requests.get(
        f'https://api.moltin.com/v2/carts/{customer_id}/items',
        headers=headers)
    cart = response.json()
    products = [Product(product.get("id"),
                        product.get("name"),
                        product.get("description"),
                        product.get("quantity"),
                        product.get("meta").get("display_price").get(
                            "with_tax").get("value").get("formatted"),
                        ) for product in cart.get("data")]
    total_price = cart.get("meta").get("display_price").get("with_tax").get(
        "formatted")
    return products, total_price


def remove_product_from_cart(product_id: str, customer_id: int) -> None:
    """Remove product from user cart"""
    motlin_access_token = get_motlin_access_token()
    headers = {
        'Authorization': f'Bearer {motlin_access_token}',
    }

    requests.delete(
        f'https://api.moltin.com/v2/carts/{customer_id}/items/{product_id}',
        headers=headers)


def create_customer(name: str, email: str) -> None:
    """Create customer"""
    motlin_access_token = get_motlin_access_token()
    headers = {
        'Authorization': f'Bearer {motlin_access_token}',
    }

    json_data = {
        'data': {
            'type': 'customer',
            'name': f'{name}',
            'email': f'{email}',
        },
    }
    requests.post('https://api.moltin.com/v2/customers',
                  headers=headers, json=json_data)


def get_customer_by_id(customer_id: str) -> dict:
    """Get serialize dict with customer by id from motlin"""
    motlin_access_token = get_motlin_access_token()
    headers = {
        'Authorization': f'Bearer {motlin_access_token}',
    }

    response = requests.get(
        f'https://api.moltin.com/v2/customers/{customer_id}',
        headers=headers)
    return response.json()
