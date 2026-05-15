"""add product quantity

Revision ID: 2b_add_product_quantity
Revises: 1c6002a1f811
Create Date: 2026-05-11

"""
from alembic import op
import sqlalchemy as sa


revision = "2b_add_product_quantity"
down_revision = "1c6002a1f811"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "product",
        sa.Column("quantity", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )


def downgrade():
    op.drop_column("product", "quantity")
