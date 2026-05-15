from extensions import db


class Product(db.Model):
    """
    An item with an expiry date, owned by a user and optionally placed in a category.
    """

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("category.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    barcode = db.Column(db.String(128), nullable=True, index=True)
    # Optional enrichment (Open Food Facts or manual). Nullable for backward compatibility.
    brand = db.Column(db.String(255), nullable=True)
    ingredients = db.Column(db.Text, nullable=True)
    # Optional: used for shelf-life % in get_product_status. Old rows stay NULL.
    manufacturing_date = db.Column(db.Date, nullable=True, index=True)
    expiry_date = db.Column(db.Date, nullable=False, index=True)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"<Product {self.name!r} expires={self.expiry_date}>"
