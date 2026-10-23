"""Record whether sensor values were entered or supplied as demo estimates."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261022_0005"
down_revision: Union[str, None] = "20261022_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sensor_readings",
        sa.Column("source", sa.String(length=30), nullable=False, server_default="legacy"),
    )
    with op.batch_alter_table("sensor_readings") as batch_op:
        batch_op.alter_column("source", server_default=None)


def downgrade() -> None:
    op.drop_column("sensor_readings", "source")
