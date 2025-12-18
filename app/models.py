import logging
from datetime import datetime

from app.db import db

logger = logging.getLogger(__name__)


class Label(db.Model):
    """Model for storing generated labels."""

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_name = db.Column(db.String(255), nullable=False)
    form = db.Column(db.String(50), db.ForeignKey("form.short_name"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=True)
    marked_to_print = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Unique constraint on combination
    __table_args__ = (
        db.UniqueConstraint("product_name", "form", "amount", name="unique_label"),
    )

    def __repr__(self):
        return f"<Label(id={self.id}, product='{self.product_name}', form='{self.form}', marked={self.marked_to_print})>"

    def to_dict(self):
        return {
            "id": self.id,
            "product_name": self.product_name,
            "price": self.price,
            "form": self.form,
            "amount": self.amount,
            "unit_price": self.unit_price,
            "marked_to_print": self.marked_to_print,
            "created_at": self.created_at.isoformat(),
        }


class Form(db.Model):
    """Model for storing product forms."""

    name = db.Column(db.String(100), primary_key=True)
    short_name = db.Column(db.String(100), unique=True, nullable=False)
    unit = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"<Form(name='{self.name}', short_name='{self.short_name}', unit='{self.unit}')>"

    def to_dict(self):
        return {
            "name": self.name,
            "short_name": self.short_name,
            "unit": self.unit,
        }
