"""add product brand and ingredients (optional)

Revision ID: 3d_add_brand_ingredients
Revises: 3c_add_manufacturing_date
Create Date: 2026-05-11

"""
from alembic import op
import sqlalchemy as sa


revision = "3d_add_brand_ingredients"
down_revision = "3c_add_manufacturing_date"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("product", sa.Column("brand", sa.String(length=255), nullable=True))
    op.add_column("product", sa.Column("ingredients", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("product", "ingredients")
    op.drop_column("product", "brand")
