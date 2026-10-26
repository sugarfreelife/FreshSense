"""Add shared business workspaces and membership."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261026_0009"
down_revision: Union[str, None] = "20261023_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "business_workspaces",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_business_workspaces_created_by_user_id", "business_workspaces", ["created_by_user_id"])
    op.create_table(
        "workspace_memberships",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["business_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_membership_user"),
    )
    op.create_index("ix_workspace_memberships_workspace_id", "workspace_memberships", ["workspace_id"])
    op.create_index("ix_workspace_memberships_user_id", "workspace_memberships", ["user_id"])
    op.add_column("inventory_items", sa.Column("workspace_id", sa.String(length=36), nullable=True))
    op.add_column("inventory_items", sa.Column("stock_location", sa.String(length=120), nullable=True))
    op.add_column("food_scans", sa.Column("workspace_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(
        "fk_food_scans_workspace_id_business_workspaces",
        "food_scans",
        "business_workspaces",
        ["workspace_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_food_scans_workspace_id", "food_scans", ["workspace_id"])
    op.create_foreign_key(
        "fk_inventory_items_workspace_id_business_workspaces",
        "inventory_items",
        "business_workspaces",
        ["workspace_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_inventory_items_workspace_id", "inventory_items", ["workspace_id"])


def downgrade() -> None:
    op.drop_index("ix_food_scans_workspace_id", table_name="food_scans")
    op.drop_constraint("fk_food_scans_workspace_id_business_workspaces", "food_scans", type_="foreignkey")
    op.drop_column("food_scans", "workspace_id")
    op.drop_column("inventory_items", "stock_location")
    op.drop_index("ix_inventory_items_workspace_id", table_name="inventory_items")
    op.drop_constraint("fk_inventory_items_workspace_id_business_workspaces", "inventory_items", type_="foreignkey")
    op.drop_column("inventory_items", "workspace_id")
    op.drop_index("ix_workspace_memberships_user_id", table_name="workspace_memberships")
    op.drop_index("ix_workspace_memberships_workspace_id", table_name="workspace_memberships")
    op.drop_table("workspace_memberships")
    op.drop_index("ix_business_workspaces_created_by_user_id", table_name="business_workspaces")
    op.drop_table("business_workspaces")
