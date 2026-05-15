from flask_login import UserMixin

from extensions import db


class User(UserMixin, db.Model):
    """
    One row per person who can sign up and log in.
    Stores credentials and links to their categories and products.
    """

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    categories = db.relationship(
        "Category",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    products = db.relationship(
        "Product",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<User {self.email}>"
