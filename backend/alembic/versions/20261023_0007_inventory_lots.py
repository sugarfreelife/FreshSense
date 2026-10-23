"""Add user-owned food inventory batches."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261023_0007"
down_revision: Union[str, None] = "20261022_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inventory_items",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_scan_id", sa.String(length=36), sa.ForeignKey("food_scans.id", ondelete="SET NULL"), nullable=True),
        sa.Column("product_name", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("expiry_source", sa.String(length=24), nullable=False, server_default="unknown"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_inventory_quantity_positive"),
    )
    op.create_index("ix_inventory_items_user_id", "inventory_items", ["user_id"])
    op.create_index("ix_inventory_items_source_scan_id", "inventory_items", ["source_scan_id"])


def downgrade() -> None:
    op.drop_index("ix_inventory_items_source_scan_id", table_name="inventory_items")
    op.drop_index("ix_inventory_items_user_id", table_name="inventory_items")
    op.drop_table("inventory_items")
