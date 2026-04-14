"""Tests for app/utils.py — translate_db_error, calculate_unit_price, font settings."""

import json
from pathlib import Path
from unittest.mock import patch

from app.constants import PRICE_FONT_SIZE_MAX, TEXT_FONT_SIZE_MIN
from app.utils import calculate_unit_price, save_font_settings, translate_db_error

# ── translate_db_error ──────────────────────────────────────────────────────────


class TestTranslateDbError:
    """Bug 3: User-friendly error translation."""

    def test_unique_label_constraint(self) -> None:
        """UNIQUE constraint on label combo returns Czech message + 409."""
        exc = Exception(
            "(sqlite3.IntegrityError) UNIQUE constraint failed: "
            "label.product_name, label.form, label.amount"
        )
        msg, code = translate_db_error(exc)
        assert code == 409
        assert "Cenovka se stejným" in msg

    def test_unique_form_short_name(self) -> None:
        exc = Exception("UNIQUE constraint failed: form.short_name")
        msg, code = translate_db_error(exc)
        assert code == 409
        assert "zkratkou" in msg

    def test_unique_form_name(self) -> None:
        exc = Exception("UNIQUE constraint failed: form.name")
        msg, code = translate_db_error(exc)
        assert code == 409
        assert "názvem" in msg

    def test_foreign_key_constraint(self) -> None:
        exc = Exception("FOREIGN KEY constraint failed")
        msg, code = translate_db_error(exc)
        assert code == 409
        assert "neexistuje" in msg

    def test_unknown_error_returns_fallback(self) -> None:
        exc = Exception("something completely unexpected")
        msg, code = translate_db_error(exc)
        assert code == 500
        assert "neočekávané" in msg


# ── calculate_unit_price ────────────────────────────────────────────────────────


class TestCalculateUnitPrice:
    def test_normal_calculation(self) -> None:
        assert calculate_unit_price(10, 100) == 10.0

    def test_rounds_to_two_decimals(self) -> None:
        assert calculate_unit_price(3, 10) == 3.33

    def test_zero_amount_returns_none(self) -> None:
        assert calculate_unit_price(0, 50) is None

    def test_negative_amount_returns_none(self) -> None:
        assert calculate_unit_price(-5, 50) is None


# ── save_font_settings (clamping) ───────────────────────────────────────────────


class TestSaveFontSettings:
    """Bug 7: Font size bounds are enforced on save."""

    def test_clamps_too_large_price_font(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.json"
        with patch("app.utils.FONT_SETTINGS_PATH", path):
            save_font_settings(999, 14)
        data = json.loads(path.read_text())
        assert data["price_font_size"] == PRICE_FONT_SIZE_MAX

    def test_clamps_too_small_text_font(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.json"
        with patch("app.utils.FONT_SETTINGS_PATH", path):
            save_font_settings(20, 1)
        data = json.loads(path.read_text())
        assert data["text_font_size"] == TEXT_FONT_SIZE_MIN

    def test_valid_values_unchanged(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.json"
        with patch("app.utils.FONT_SETTINGS_PATH", path):
            save_font_settings(30, 16)
        data = json.loads(path.read_text())
        assert data["price_font_size"] == 30
        assert data["text_font_size"] == 16
