import logging
from typing import Optional

logger = logging.getLogger(__name__)


def calculate_unit_price(amount: float, price: float) -> Optional[float]:
    """Calculate unit price given amount and total price."""
    logger.debug(f"Calculating unit price: price={price}, amount={amount}")
    if amount <= 0:
        logger.warning(f"Invalid amount for unit price calculation: {amount}")
        return None
    result = round(price / amount, 2)
    logger.debug(f"Unit price calculated: {result}")
    return result
