"""add_missing_indexes

Revision ID: a1b2c3d4e5f6
Revises: eeb1ca6bfe11
Create Date: 2026-02-07 20:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'eeb1ca6bfe11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(op.f('ix_messages_user_id'), 'messages', ['user_id'], unique=False)
    op.create_index(op.f('ix_room_members_user_id'), 'room_members', ['user_id'], unique=False)
    op.create_index(op.f('ix_blocks_blocked_id'), 'blocks', ['blocked_id'], unique=False)
    op.create_index(op.f('ix_reports_reporter_id'), 'reports', ['reporter_id'], unique=False)
    op.create_index(op.f('ix_reports_reported_id'), 'reports', ['reported_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_reports_reported_id'), table_name='reports')
    op.drop_index(op.f('ix_reports_reporter_id'), table_name='reports')
    op.drop_index(op.f('ix_blocks_blocked_id'), table_name='blocks')
    op.drop_index(op.f('ix_room_members_user_id'), table_name='room_members')
    op.drop_index(op.f('ix_messages_user_id'), table_name='messages')
