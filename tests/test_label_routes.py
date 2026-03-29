"""Tests for label routes — CRUD + form validation + error translation + font bounds (Bugs 3, 6, 7)."""

import pytest


class TestCreateLabel:
    """POST /labels/api/label."""

    def test_create_label_success(self, client, seed_form) -> None:
        resp = client.post(
            "/labels/api/label",
            json={
                "product_name": "Ibuprofen 400mg",
                "form": "tbl",
                "amount": 30,
                "price": 65.0,
            },
        )
        assert resp.status_code == 201
        label = resp.get_json()["label"]
        assert label["product_name"] == "Ibuprofen 400mg"
        assert label["unit_price"] == pytest.approx(2.17, abs=0.01)

    def test_create_label_missing_fields(self, client, seed_form) -> None:
        resp = client.post(
            "/labels/api/label",
            json={"product_name": "X"},
        )
        assert resp.status_code == 400
        assert "form" in resp.get_json()["error"]

    def test_create_label_invalid_amount(self, client, seed_form) -> None:
        resp = client.post(
            "/labels/api/label",
            json={
                "product_name": "Test",
                "form": "tbl",
                "amount": -5,
                "price": 100,
            },
        )
        assert resp.status_code == 400

    def test_create_label_nonexistent_form(self, client, seed_form) -> None:
        """Bug 6: Creating a label with a non-existent form returns 400."""
        resp = client.post(
            "/labels/api/label",
            json={
                "product_name": "Test",
                "form": "nonexistent",
                "amount": 10,
                "price": 50,
            },
        )
        assert resp.status_code == 400
        assert "neexistuje" in resp.get_json()["error"]

    def test_create_duplicate_label_returns_friendly_error(
        self, client, seed_label
    ) -> None:
        """Bug 3: Duplicate label returns Czech message, not raw SQL."""
        resp = client.post(
            "/labels/api/label",
            json={
                "product_name": "Paralen 500mg",
                "form": "tbl",
                "amount": 24,
                "price": 99.0,
            },
        )
        assert resp.status_code == 409
        error = resp.get_json()["error"]
        assert "UNIQUE constraint" not in error
        assert "již existuje" in error


class TestUpdateLabel:
    """PUT /labels/api/label/<id>."""

    def test_update_label_success(self, client, seed_label) -> None:
        label_id = seed_label["id"]
        resp = client.put(
            f"/labels/api/label/{label_id}",
            json={"price": 100.0},
        )
        assert resp.status_code == 200
        assert resp.get_json()["label"]["price"] == 100.0

    def test_update_label_not_found(self, client, seed_form) -> None:
        resp = client.put(
            "/labels/api/label/99999",
            json={"price": 10},
        )
        assert resp.status_code == 404

    def test_update_label_nonexistent_form(self, client, seed_label) -> None:
        """Bug 6: Updating label to a non-existent form returns 400."""
        label_id = seed_label["id"]
        resp = client.put(
            f"/labels/api/label/{label_id}",
            json={"form": "ghost_form"},
        )
        assert resp.status_code == 400
        assert "neexistuje" in resp.get_json()["error"]


class TestDeleteLabel:
    """DELETE /labels/api/label/<id>."""

    def test_delete_label_success(self, client, seed_label) -> None:
        label_id = seed_label["id"]
        resp = client.delete(f"/labels/api/label/{label_id}")
        assert resp.status_code == 200

    def test_delete_label_not_found(self, client) -> None:
        resp = client.delete("/labels/api/label/99999")
        assert resp.status_code == 404


class TestTogglePrintMark:
    """POST /labels/api/label/<id>/toggle-print."""

    def test_toggle_print_mark(self, client, seed_label) -> None:
        label_id = seed_label["id"]
        resp = client.post(f"/labels/api/label/{label_id}/toggle-print")
        assert resp.status_code == 200
        assert resp.get_json()["marked_to_print"] is True

        resp2 = client.post(f"/labels/api/label/{label_id}/toggle-print")
        assert resp2.get_json()["marked_to_print"] is False


class TestGetLabels:
    """GET /labels/api/labels."""

    def test_get_labels_empty(self, client) -> None:
        resp = client.get("/labels/api/labels")
        assert resp.status_code == 200
        assert resp.get_json()["count"] == 0

    def test_get_labels_with_data(self, client, seed_label) -> None:
        resp = client.get("/labels/api/labels")
        assert resp.status_code == 200
        assert resp.get_json()["count"] == 1


class TestFontSettings:
    """POST /labels/api/pdf-font-settings — Bug 7: bounded validation."""

    def test_valid_font_settings(self, client) -> None:
        resp = client.post(
            "/labels/api/pdf-font-settings",
            json={"price_font_size": 30, "text_font_size": 14},
        )
        assert resp.status_code == 200

    def test_price_font_too_large(self, client) -> None:
        resp = client.post(
            "/labels/api/pdf-font-settings",
            json={"price_font_size": 100, "text_font_size": 14},
        )
        assert resp.status_code == 400
        assert "musí být" in resp.get_json()["error"]

    def test_price_font_too_small(self, client) -> None:
        resp = client.post(
            "/labels/api/pdf-font-settings",
            json={"price_font_size": 5, "text_font_size": 14},
        )
        assert resp.status_code == 400

    def test_text_font_too_large(self, client) -> None:
        resp = client.post(
            "/labels/api/pdf-font-settings",
            json={"price_font_size": 30, "text_font_size": 50},
        )
        assert resp.status_code == 400

    def test_text_font_too_small(self, client) -> None:
        resp = client.post(
            "/labels/api/pdf-font-settings",
            json={"price_font_size": 30, "text_font_size": 2},
        )
        assert resp.status_code == 400
