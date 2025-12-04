from datetime import datetime

from app.db import db


class Label(db.Model):
    """Model for storing generated labels."""

    product_name = db.Column(db.String(255), nullable=False, primary_key=True)
    form = db.Column(db.String(50), nullable=False, primary_key=True)
    amount = db.Column(db.Float, nullable=False, primary_key=True)
    price = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=True)
    marked_to_print = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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

    def to_dict(self):
        return {
            "name": self.name,
            "short_name": self.short_name,
            "unit": self.unit,
        }
