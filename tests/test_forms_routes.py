"""Tests for form routes — CRUD + delete protection (Bugs 2, 3, 6)."""


class TestCreateForm:
    """POST /api/form."""

    def test_create_form_success(self, client) -> None:
        resp = client.post(
            "/api/form",
            json={"name": "Kapsle", "short_name": "cps", "unit": "ks"},
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["form"]["short_name"] == "cps"

    def test_create_form_missing_fields(self, client) -> None:
        resp = client.post("/api/form", json={"name": "Kapsle"})
        assert resp.status_code == 400
        assert "short_name" in resp.get_json()["error"]

    def test_create_duplicate_name_returns_friendly_error(
        self, client, seed_form
    ) -> None:
        """Bug 3: Duplicate form name returns Czech error, not raw SQL."""
        resp = client.post(
            "/api/form",
            json={"name": "Tablety", "short_name": "tbl2", "unit": "ks"},
        )
        assert resp.status_code == 409
        error = resp.get_json()["error"]
        # Must NOT contain raw SQL
        assert "UNIQUE constraint" not in error
        assert "názvem" in error

    def test_create_duplicate_short_name_returns_friendly_error(
        self, client, seed_form
    ) -> None:
        """Bug 3: Duplicate short_name returns Czech error."""
        resp = client.post(
            "/api/form",
            json={"name": "Jiná forma", "short_name": "tbl", "unit": "ml"},
        )
        assert resp.status_code == 409
        assert "zkratkou" in resp.get_json()["error"]

    def test_create_form_no_json(self, client) -> None:
        resp = client.post("/api/form", content_type="application/json", data="{}")
        assert resp.status_code == 400


class TestUpdateForm:
    """PUT /api/form."""

    def test_update_form_success(self, client, seed_form) -> None:
        resp = client.put(
            "/api/form",
            json={"name": "Tablety", "short_name": "tab", "unit": "ks"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["form"]["short_name"] == "tab"

    def test_update_form_not_found(self, client) -> None:
        resp = client.put(
            "/api/form",
            json={"name": "Nonexistent", "short_name": "x", "unit": "x"},
        )
        assert resp.status_code == 404


class TestDeleteForm:
    """DELETE /api/form — Bug 2: dependency protection."""

    def test_delete_form_success(self, client, seed_form) -> None:
        resp = client.delete("/api/form", json={"name": "Tablety"})
        assert resp.status_code == 200

    def test_delete_form_not_found(self, client) -> None:
        resp = client.delete("/api/form", json={"name": "Ghost"})
        assert resp.status_code == 404

    def test_delete_form_blocked_when_labels_exist(self, client, seed_label) -> None:
        """Bug 2: Cannot delete a form that is used by labels."""
        resp = client.delete("/api/form", json={"name": "Tablety"})
        assert resp.status_code == 409
        error = resp.get_json()["error"]
        assert "Nelze smazat" in error
        assert "1" in error  # at least 1 label

    def test_delete_form_allowed_after_label_removed(self, client, seed_label) -> None:
        """After removing the label, form deletion should succeed."""
        label_id = seed_label["id"]
        del_label_resp = client.delete(f"/labels/api/label/{label_id}")
        assert del_label_resp.status_code == 200

        resp = client.delete("/api/form", json={"name": "Tablety"})
        assert resp.status_code == 200


class TestGetForms:
    """GET /api/form."""

    def test_get_forms_empty(self, client) -> None:
        resp = client.get("/api/form")
        assert resp.status_code == 200
        assert resp.get_json()["forms"] == []

    def test_get_forms_with_data(self, client, seed_form) -> None:
        resp = client.get("/api/form")
        assert resp.status_code == 200
        assert len(resp.get_json()["forms"]) == 1

    def test_get_forms_sorted_by_short(self, client, seed_form) -> None:
        client.post(
            "/api/form",
            json={"name": "Ampule", "short_name": "amp", "unit": "ml"},
        )
        resp = client.get("/api/form?sort=short")
        assert resp.status_code == 200
        forms = resp.get_json()["forms"]
        assert forms[0]["short_name"] == "amp"
