"""Tests for DB integrity — FK pragma enforcement"""

import pytest

from app.db import db
from app.models import Label


class TestSQLiteForeignKeyEnforcement:
    """PRAGMA foreign_keys = ON is active."""

    def test_fk_pragma_is_enabled(self, app) -> None:
        """Verify that foreign_keys pragma is ON for new connections."""
        with app.app_context():
            result = db.session.execute(db.text("PRAGMA foreign_keys")).scalar()
            assert result == 1

    def test_insert_label_with_invalid_fk_fails(self, app) -> None:
        """Inserting a label referencing a non-existent form should raise IntegrityError."""
        from sqlalchemy.exc import IntegrityError

        with app.app_context():
            label = Label(
                product_name="Ghost Label",
                form="nonexistent_form",
                amount=10,
                price=50,
                unit_price=5.0,
            )
            db.session.add(label)
            with pytest.raises(IntegrityError):
                db.session.commit()
            db.session.rollback()
