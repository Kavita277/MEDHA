"""create chat_sessions table

Revision ID: 003_create_sessions
Revises: 002_create_cases
Create Date: 2026-09-10 15:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_create_sessions'
down_revision: Union[str, None] = '002_create_cases'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('session_identifier', sa.String(length=100), nullable=False),
        sa.Column('timepoint', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('state_snapshot', sa.JSON(), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chat_sessions_case_id', 'chat_sessions', ['case_id'], unique=False)
    op.create_index('ix_chat_sessions_session_identifier', 'chat_sessions', ['session_identifier'], unique=True)
    op.create_index('ix_chat_sessions_status', 'chat_sessions', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_chat_sessions_status', table_name='chat_sessions')
    op.drop_index('ix_chat_sessions_session_identifier', table_name='chat_sessions')
    op.drop_index('ix_chat_sessions_case_id', table_name='chat_sessions')
    op.drop_table('chat_sessions')
