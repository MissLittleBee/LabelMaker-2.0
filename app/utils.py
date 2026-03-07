import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def calculate_unit_price(amount: float, price: float) -> Optional[float]:
    """Calculate unit price given amount and total price."""
    logger.debug(f"Calculating unit price: price={price}, amount={amount}")
    if amount <= 0:
        logger.error(f"Invalid amount for unit price calculation: {amount}")
        return None
    result = round(price / amount, 2)
    logger.info(f"Unit price calculated: {result}")
    return result


FONT_SETTINGS_PATH = (
    Path(__file__).parent.parent / "instance" / "pdf_font_settings.json"
)


def load_font_settings():
    try:
        with open(FONT_SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load font settings: {e}", exc_info=True)
        return {"price_font_size": 32, "text_font_size": 14}


def save_font_settings(price_font_size: int, text_font_size: int):
    with open(FONT_SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {"price_font_size": price_font_size, "text_font_size": text_font_size}, f
        )
