"""create cases table

Revision ID: 002_create_cases
Revises: 001_create_users_and_therapists
Create Date: 2026-09-10 15:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_create_cases'
down_revision: Union[str, None] = '001_create_users_and_therapists'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'cases',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('victim_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('therapist_id', sa.Uuid(), nullable=False),
        sa.Column('current_timepoint', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['therapist_id'], ['therapists.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cases_victim_id', 'cases', ['victim_id'], unique=True)
    op.create_index('ix_cases_user_id', 'cases', ['user_id'], unique=False)
    op.create_index('ix_cases_therapist_id', 'cases', ['therapist_id'], unique=False)
    op.create_index('ix_cases_status', 'cases', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_cases_status', table_name='cases')
    op.drop_index('ix_cases_therapist_id', table_name='cases')
    op.drop_index('ix_cases_user_id', table_name='cases')
    op.drop_index('ix_cases_victim_id', table_name='cases')
    op.drop_table('cases')
