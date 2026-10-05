"""Persist scan notes and visual features used by the Freshness Passport."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261006_0002"
down_revision: Union[str, None] = "20261006_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("food_scans", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column(
        "vision_predictions",
        sa.Column("confidence_kind", sa.String(length=50), server_default="heuristic_score", nullable=False),
    )
    op.add_column(
        "vision_predictions",
        sa.Column("visual_evidence", sa.Text(), server_default=sa.text("'{}'"), nullable=False),
    )
    op.alter_column("vision_predictions", "confidence_kind", server_default=None)
    op.alter_column("vision_predictions", "visual_evidence", server_default=None)


def downgrade() -> None:
    op.drop_column("vision_predictions", "visual_evidence")
    op.drop_column("vision_predictions", "confidence_kind")
    op.drop_column("food_scans", "notes")
