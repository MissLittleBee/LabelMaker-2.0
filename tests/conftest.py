"""Shared pytest fixtures for LabelMaker tests."""

from __future__ import annotations

from typing import Generator, cast

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.app import create_app
from app.db import db as _db
from app.models import FormDict, LabelDict


@pytest.fixture(scope="session")
def app() -> Generator[Flask, None, None]:
    """Create a Flask application once for the entire test session."""
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
        _db.drop_all()


@pytest.fixture(autouse=True)
def _clean_tables(app: Flask) -> Generator[None, None, None]:
    """Delete all row data after each test while keeping the schema."""
    yield
    with app.app_context():
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    """Flask test client."""
    return app.test_client()


@pytest.fixture()
def db_session(app: Flask) -> Generator[object, None, None]:
    """Provide a clean database session for each test."""
    with app.app_context():
        yield _db.session


@pytest.fixture()
def seed_form(client: FlaskClient) -> FormDict:
    """Create a default form and return its dict."""
    resp = client.post(
        "/api/form",
        json={"name": "Tablety", "short_name": "tbl", "unit": "ks"},
    )
    assert resp.status_code == 201
    return cast(FormDict, resp.get_json()["form"])


@pytest.fixture()
def seed_label(client: FlaskClient, seed_form: FormDict) -> LabelDict:
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
    return cast(LabelDict, resp.get_json()["label"])
