"""Keep image food recognition and label details with each scan."""
from alembic import op
import sqlalchemy as sa

revision = "20261027_0011"
down_revision = "20261027_0010"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("food_scans", sa.Column("product_recognition", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("food_scans", "product_recognition")
