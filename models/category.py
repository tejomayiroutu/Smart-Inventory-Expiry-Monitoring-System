from extensions import db


class Category(db.Model):
    """
    Groups products (e.g. Dairy, Medicine). Each category belongs to one user
    so users do not see each other's labels.
    """

    __tablename__ = "category"
    __table_args__ = (db.UniqueConstraint("user_id", "name", name="uq_user_category_name"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(120), nullable=False)

    products = db.relationship(
        "Product",
        backref="category",
        lazy="dynamic",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<Category {self.name!r}>"
