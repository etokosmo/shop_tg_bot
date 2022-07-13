from motlin_tools import Product


def create_cart_message(products: [Product], total_price: str) -> str:
    """Create message with products in user's cart and total price"""
    message = ""
    for product in products:
        message += f"""
        Product: {product.name}
        Description: {product.description}
        Amount: {product.amount}
        Price: {product.price}
        """
    message += f"Total: {total_price}"
    return message


def create_product_description(product: dict) -> str:
    """Create message with product description"""
    message = f"""{product.get('name')}\n
    {product.get('description')}
    Price: {product.get('meta').get('display_price').get('with_tax').get('formatted')}"""
    return message
