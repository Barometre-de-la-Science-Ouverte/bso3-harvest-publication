"""added harvesting_date column

Revision ID: e5e88b8f9fe5
Revises: 3512e0c83cf0
Create Date: 2022-07-04 17:25:29.338722

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
from config import DB_HARVESTING_DATE_COLUMN_NAME, DB_DATASTET_VERSION_COLUMN_NAME, DB_HARVESTED_STATUS_TABLE_NAME

revision = 'e5e88b8f9fe5'
down_revision = '3512e0c83cf0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        DB_HARVESTED_STATUS_TABLE_NAME,
        sa.Column(DB_HARVESTING_DATE_COLUMN_NAME, sa.DateTime)
    )

    op.add_column(
        DB_HARVESTED_STATUS_TABLE_NAME,
        sa.Column(DB_DATASTET_VERSION_COLUMN_NAME, sa.String)
    )


def downgrade() -> None:
    op.drop_column(DB_HARVESTED_STATUS_TABLE_NAME, DB_HARVESTING_DATE_COLUMN_NAME)
    op.drop_column(DB_HARVESTED_STATUS_TABLE_NAME, DB_DATASTET_VERSION_COLUMN_NAME)
