"""add user suspension and report status

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-02-08 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_banned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "users",
        sa.Column("suspended_until", sa.DateTime(timezone=True), nullable=True),
    )

    report_status_enum = sa.Enum("pending", "reviewed", "dismissed", name="reportstatus")
    report_status_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "reports",
        sa.Column("status", report_status_enum, nullable=False, server_default="pending"),
    )


def downgrade() -> None:
    op.drop_column("reports", "status")
    report_status_enum = sa.Enum("pending", "reviewed", "dismissed", name="reportstatus")
    report_status_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_column("users", "suspended_until")
    op.drop_column("users", "is_banned")
