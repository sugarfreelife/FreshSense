"""Add tracked food items and profile names for longitudinal passports."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261022_0003"
down_revision: Union[str, None] = "20261006_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("name", sa.String(length=100), nullable=True))
    op.create_table(
        "tracked_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tracked_items_user_id", "tracked_items", ["user_id"], unique=False)
    op.add_column("food_scans", sa.Column("tracked_item_id", sa.String(length=36), nullable=True))
    with op.batch_alter_table("food_scans") as batch_op:
        batch_op.create_foreign_key(
            "fk_food_scans_tracked_item_id_tracked_items",
            "tracked_items",
            ["tracked_item_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index("ix_food_scans_tracked_item_id", "food_scans", ["tracked_item_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_food_scans_tracked_item_id", table_name="food_scans")
    with op.batch_alter_table("food_scans") as batch_op:
        batch_op.drop_constraint("fk_food_scans_tracked_item_id_tracked_items", type_="foreignkey")
    op.drop_column("food_scans", "tracked_item_id")
    op.drop_index("ix_tracked_items_user_id", table_name="tracked_items")
    op.drop_table("tracked_items")
    op.drop_column("users", "name")
