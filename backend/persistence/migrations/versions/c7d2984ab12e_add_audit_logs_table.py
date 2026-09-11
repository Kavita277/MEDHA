"""add audit_logs table

Revision ID: c7d2984ab12e
Revises: b3f7e291cc4a
Create Date: 2026-09-11 11:35:00.000000

Adds the audit_logs table for Step 27 Privacy, RBAC & Comprehensive Audit Logging.

Design notes:
  - Persistent, append-only security & compliance audit log.
  - Foreign key to users table with ON DELETE SET NULL to preserve the audit trail if a user is deleted.
  - Indexes on actor_user_id, action, resource_type, resource_id, and created_at for performant querying.
  - NEVER stores sensitive clinical transcripts, raw audio, passwords, or authentication secrets.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c7d2984ab12e"
down_revision: Union[str, Sequence[str], None] = "b3f7e291cc4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("actor_role", sa.String(length=32), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=True),
        sa.Column("resource_id", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="SUCCESS"),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("metadata_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audit_logs_actor_user_id"),
        "audit_logs",
        ["actor_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_action"),
        "audit_logs",
        ["action"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_resource_type"),
        "audit_logs",
        ["resource_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_resource_id"),
        "audit_logs",
        ["resource_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_created_at"),
        "audit_logs",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_audit_logs_created_at"),
        table_name="audit_logs",
    )
    op.drop_index(
        op.f("ix_audit_logs_resource_id"),
        table_name="audit_logs",
    )
    op.drop_index(
        op.f("ix_audit_logs_resource_type"),
        table_name="audit_logs",
    )
    op.drop_index(
        op.f("ix_audit_logs_action"),
        table_name="audit_logs",
    )
    op.drop_index(
        op.f("ix_audit_logs_actor_user_id"),
        table_name="audit_logs",
    )
    op.drop_table("audit_logs")
