"""Store partial package expiry stamp text without inventing a year."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261022_0006"
down_revision: Union[str, None] = "20261022_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ocr_results", sa.Column("expiry_text", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("ocr_results", "expiry_text")
