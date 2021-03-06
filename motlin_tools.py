from dataclasses import dataclass
from datetime import datetime
from typing import NamedTuple

import requests

motlin_token, token_expires_timestamp = None, None


class Token(NamedTuple):
    access_token: str
    expires: int


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


def get_motlin_access_token(motlin_client_id: str,
                            motlin_client_secret: str) -> str:
    """Return motlin access token"""
    global motlin_token, token_expires_timestamp
    if (motlin_token is None) or (not is_valid_token(token_expires_timestamp)):
        motlin_token, token_expires_timestamp = make_authorization(
            motlin_client_id, motlin_client_secret)
    return motlin_token


def make_authorization(motlin_client_id: str,
                       motlin_client_secret: str) -> Token:
    """Return created access_token and expires of token"""
    data = {
        'client_id': motlin_client_id,
        'client_secret': motlin_client_secret,
        'grant_type': 'client_credentials',
    }

    response = requests.post('https://api.moltin.com/oauth/access_token',
                             data=data)
    response.raise_for_status()
    authorization = response.json()
    return Token(access_token=authorization.get("access_token"),
                 expires=authorization.get("expires"))


def get_all_products(motlin_client_id: str,
                     motlin_client_secret: str) -> [Product]:
    """Return list if Product class with product's id and name"""
    motlin_access_token = get_motlin_access_token(motlin_client_id,
                                                  motlin_client_secret)
    headers = {
        'Authorization': f'Bearer {motlin_access_token}',
    }

    response = requests.get('https://api.moltin.com/v2/products',
                            headers=headers)
    response.raise_for_status()
    store = response.json().get("data")
    return [Product(product.get("id"),
                    product.get("name")) for product in store]


def get_product_by_id(product_id: str, motlin_client_id: str,
                      motlin_client_secret: str) -> dict:
    """Return product serialized dict from moltin"""
    motlin_access_token = get_motlin_access_token(motlin_client_id,
                                                  motlin_client_secret)
    headers = {
        'Authorization': f'Bearer {motlin_access_token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/products/{product_id}',
                            headers=headers)
    response.raise_for_status()
    return response.json().get("data")


def get_product_image_by_id(product_id: str, motlin_client_id: str,
                            motlin_client_secret: str) -> str:
    """Return href product's image from moltin"""
    motlin_access_token = get_motlin_access_token(motlin_client_id,
                                                  motlin_client_secret)
    product_file_id = get_product_by_id(
        product_id,
        motlin_client_id,
        motlin_client_secret
    ).get("relationships").get("main_image").get("data").get("id")

    headers = {
        'Authorization': f'Bearer {motlin_access_token}',
    }

    response = requests.get(
        f'https://api.moltin.com/v2/files/{product_file_id}',
        headers=headers)
    response.raise_for_status()
    return response.json().get("data").get("link").get("href")


def add_product_in_cart(product_id: str, amount: int, customer_id: int,
                        motlin_client_id: str,
                        motlin_client_secret: str) -> None:
    """Add product with his amount in user cart"""
    motlin_access_token = get_motlin_access_token(motlin_client_id,
                                                  motlin_client_secret)
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

    response = requests.post(
        f'https://api.moltin.com/v2/carts/{customer_id}/items',
        headers=headers,
        json=json_data)
    response.raise_for_status()


def get_cart_items(customer_id, motlin_client_id: str,
                   motlin_client_secret: str) -> ([Product], str):
    """Return list if Product class with products in cart and total price"""
    motlin_access_token = get_motlin_access_token(motlin_client_id,
                                                  motlin_client_secret)
    headers = {
        'Authorization': f'Bearer {motlin_access_token}',
    }

    response = requests.get(
        f'https://api.moltin.com/v2/carts/{customer_id}/items',
        headers=headers)
    response.raise_for_status()
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


def remove_product_from_cart(product_id: str, customer_id: int,
                             motlin_client_id: str,
                             motlin_client_secret: str) -> None:
    """Remove product from user cart"""
    motlin_access_token = get_motlin_access_token(motlin_client_id,
                                                  motlin_client_secret)
    headers = {
        'Authorization': f'Bearer {motlin_access_token}',
    }

    response = requests.delete(
        f'https://api.moltin.com/v2/carts/{customer_id}/items/{product_id}',
        headers=headers)
    response.raise_for_status()


def create_customer(name: str, email: str, motlin_client_id: str,
                    motlin_client_secret: str) -> None:
    """Create customer"""
    motlin_access_token = get_motlin_access_token(motlin_client_id,
                                                  motlin_client_secret)
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
    response = requests.post('https://api.moltin.com/v2/customers',
                             headers=headers, json=json_data)
    response.raise_for_status()


def get_customer_by_id(customer_id: str, motlin_client_id: str,
                       motlin_client_secret: str) -> dict:
    """Get serialize dict with customer by id from motlin"""
    motlin_access_token = get_motlin_access_token(motlin_client_id,
                                                  motlin_client_secret)
    headers = {
        'Authorization': f'Bearer {motlin_access_token}',
    }

    response = requests.get(
        f'https://api.moltin.com/v2/customers/{customer_id}',
        headers=headers)
    response.raise_for_status()
    return response.json()
