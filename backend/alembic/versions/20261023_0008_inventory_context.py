"""Add pantry storage context and reminder preferences."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261023_0008"
down_revision: Union[str, None] = "20261023_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("inventory_items", sa.Column("reminder_days_before", sa.Integer(), nullable=True))
    op.add_column("inventory_items", sa.Column("storage_location", sa.String(length=40), nullable=False, server_default="unknown"))
    op.add_column("inventory_items", sa.Column("opened_date", sa.Date(), nullable=True))
    op.add_column("inventory_items", sa.Column("storage_notes", sa.Text(), nullable=True))
    with op.batch_alter_table("inventory_items") as batch_op:
        batch_op.create_check_constraint(
            "ck_inventory_reminder_days",
            "reminder_days_before IS NULL OR reminder_days_before IN (1, 3, 7)",
        )


def downgrade() -> None:
    with op.batch_alter_table("inventory_items") as batch_op:
        batch_op.drop_constraint("ck_inventory_reminder_days", type_="check")
    op.drop_column("inventory_items", "storage_notes")
    op.drop_column("inventory_items", "opened_date")
    op.drop_column("inventory_items", "storage_location")
    op.drop_column("inventory_items", "reminder_days_before")
