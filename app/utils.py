def calculate_unit_price(amount, price):
    """Calculate unit price given amount and total price."""
    if amount <= 0:
        return None
    return round(price / amount, 2)
