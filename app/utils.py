import json
import logging
import re
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


# Patterns for translating common DB errors to user-friendly Czech messages
_ERROR_PATTERNS: list[Tuple[str, str]] = [
    (
        r"UNIQUE constraint failed: label\.product_name.*label\.form.*label\.amount",
        "Cenovka se stejným názvem, formou a množstvím již existuje.",
    ),
    (
        r"UNIQUE constraint failed: form\.short_name",
        "Forma s touto zkratkou již existuje.",
    ),
    (
        r"UNIQUE constraint failed: form\.name",
        "Forma s tímto názvem již existuje.",
    ),
    (
        r"FOREIGN KEY constraint",
        "Odkazovaný záznam neexistuje.",
    ),
]

_FALLBACK_MESSAGE = "Došlo k neočekávané chybě. Zkuste to prosím znovu."

# Font size bounds
PRICE_FONT_SIZE_MIN = 12
PRICE_FONT_SIZE_MAX = 48
TEXT_FONT_SIZE_MIN = 8
TEXT_FONT_SIZE_MAX = 24


def translate_db_error(error: Exception) -> Tuple[str, int]:
    """Translate a database exception into a user-friendly message and HTTP status code.

    Args:
        error: The caught exception.

    Returns:
        Tuple of (user-friendly message, HTTP status code).
    """
    error_str = str(error)
    for pattern, message in _ERROR_PATTERNS:
        if re.search(pattern, error_str):
            return message, 409
    return _FALLBACK_MESSAGE, 500


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


def save_font_settings(price_font_size: int, text_font_size: int) -> None:
    """Persist font size settings after clamping to valid bounds.

    Args:
        price_font_size: Desired price font size (clamped to PRICE_FONT_SIZE_MIN..MAX).
        text_font_size: Desired text font size (clamped to TEXT_FONT_SIZE_MIN..MAX).
    """
    price_font_size = max(
        PRICE_FONT_SIZE_MIN, min(PRICE_FONT_SIZE_MAX, price_font_size)
    )
    text_font_size = max(TEXT_FONT_SIZE_MIN, min(TEXT_FONT_SIZE_MAX, text_font_size))
    with open(FONT_SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {"price_font_size": price_font_size, "text_font_size": text_font_size}, f
        )
