"""Shared pytest fixtures for LabelMaker tests."""

import pytest

from app.app import create_app
from app.db import db as _db


@pytest.fixture()
def app():
    """Create a Flask application configured for testing with an in-memory SQLite DB."""
    application = create_app()
    application.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_ECHO": False,
        }
    )

    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture()
def db_session(app):
    """Provide a clean database session for each test."""
    with app.app_context():
        yield _db.session


@pytest.fixture()
def seed_form(client):
    """Create a default form and return its dict."""
    resp = client.post(
        "/api/form",
        json={"name": "Tablety", "short_name": "tbl", "unit": "ks"},
    )
    assert resp.status_code == 201
    return resp.get_json()["form"]


@pytest.fixture()
def seed_label(client, seed_form):
    """Create a default label and return its dict."""
    resp = client.post(
        "/labels/api/label",
        json={
            "product_name": "Paralen 500mg",
            "form": "tbl",
            "amount": 24,
            "price": 89.50,
        },
    )
    assert resp.status_code == 201
    return resp.get_json()["label"]
