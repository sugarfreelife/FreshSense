"""Create the initial FreshSense schema."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261006_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "food_scans",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("image_path", sa.String(length=1024), nullable=False),
        sa.Column("food_label", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_food_scans_user_id", "food_scans", ["user_id"], unique=False)

    op.create_table(
        "vision_predictions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("scan_id", sa.String(length=36), nullable=False),
        sa.Column("food_type", sa.String(length=255), nullable=False),
        sa.Column("freshness", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(length=100), nullable=False),
        sa.Column("model_type", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scan_id"], ["food_scans.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scan_id"),
    )

    op.create_table(
        "ocr_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("scan_id", sa.String(length=36), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("date_detected", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scan_id"], ["food_scans.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scan_id"),
    )

    op.create_table(
        "sensor_readings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("scan_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("gas_value", sa.Float(), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("humidity", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scan_id"], ["food_scans.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sensor_readings_scan_id", "sensor_readings", ["scan_id"], unique=False)
    op.create_index("ix_sensor_readings_user_id", "sensor_readings", ["user_id"], unique=False)

    op.create_table(
        "final_assessments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("scan_id", sa.String(length=36), nullable=False),
        sa.Column("freshness", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("recommendation", sa.String(length=100), nullable=False),
        sa.Column("warnings", sa.Text(), nullable=False),
        sa.Column("modalities_used", sa.Text(), nullable=False),
        sa.Column("expiry_status", sa.String(length=50), nullable=False),
        sa.Column("days_remaining", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scan_id"], ["food_scans.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scan_id"),
    )

    op.create_table(
        "model_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=100), nullable=False),
        sa.Column("model_type", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("model_versions")
    op.drop_table("final_assessments")
    op.drop_index("ix_sensor_readings_user_id", table_name="sensor_readings")
    op.drop_index("ix_sensor_readings_scan_id", table_name="sensor_readings")
    op.drop_table("sensor_readings")
    op.drop_table("ocr_results")
    op.drop_table("vision_predictions")
    op.drop_index("ix_food_scans_user_id", table_name="food_scans")
    op.drop_table("food_scans")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
