"""add play_style and has_microphone to recruitments

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-02-07 23:30:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    play_style_enum = sa.Enum("casual", "competitive", "beginner_welcome", name="playstyle")
    play_style_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "recruitments",
        sa.Column("play_style", play_style_enum, nullable=True),
    )
    op.add_column(
        "recruitments",
        sa.Column("has_microphone", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("recruitments", "has_microphone")
    op.drop_column("recruitments", "play_style")

    play_style_enum = sa.Enum("casual", "competitive", "beginner_welcome", name="playstyle")
    play_style_enum.drop(op.get_bind(), checkfirst=True)
