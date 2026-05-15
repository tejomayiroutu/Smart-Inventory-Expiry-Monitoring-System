"""add product manufacturing_date (nullable)

Revision ID: 3c_add_manufacturing_date
Revises: 2b_add_product_quantity
Create Date: 2026-05-11

"""
from alembic import op
import sqlalchemy as sa


revision = "3c_add_manufacturing_date"
down_revision = "2b_add_product_quantity"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "product",
        sa.Column("manufacturing_date", sa.Date(), nullable=True),
    )
    with op.batch_alter_table("product", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_product_manufacturing_date"),
            ["manufacturing_date"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("product", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_product_manufacturing_date"))
    op.drop_column("product", "manufacturing_date")
