"""Store the OCR engine and its text-recognition score."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261022_0004"
down_revision: Union[str, None] = "20261022_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ocr_results",
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="legacy"),
    )
    op.add_column("ocr_results", sa.Column("confidence", sa.Float(), nullable=True))
    op.add_column("ocr_results", sa.Column("expiry_label", sa.String(length=50), nullable=True))
    with op.batch_alter_table("ocr_results") as batch_op:
        batch_op.alter_column("provider", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("ocr_results") as batch_op:
        batch_op.drop_column("confidence")
        batch_op.drop_column("expiry_label")
        batch_op.drop_column("provider")
