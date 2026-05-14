"""create vocalizations table

Revision ID: 6a064155
Revises:
Create Date: 2026-05-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "6a064155"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vocalizations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("speaker", sa.Text(), nullable=False),
        sa.Column("record_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", sa.Text(), nullable=False),
        sa.Column("vocalization", sa.Text(), nullable=False),
        sa.Column("audio_file", sa.Text(), nullable=False),
        sa.Column("audio_number", sa.Text(), nullable=True),
        sa.Column("segment", sa.Text(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "validated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_table("vocalizations")
