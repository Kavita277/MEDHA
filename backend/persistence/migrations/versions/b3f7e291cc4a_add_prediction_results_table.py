"""add prediction_results table

Revision ID: b3f7e291cc4a
Revises: ead3432ccad1
Create Date: 2026-09-10 18:15:00.000000

Adds the prediction_results table for Step 11 Therapist Results API.

Design notes:
  - All specialist prediction columns (struct_pred, text_pred, voice_pred, behav_pred)
    are nullable. null means genuinely unavailable, NOT zero.
  - behav_pred will remain null until Step 10 (Frozen V2 Behaviour Specialist) is
    resolved.
  - session_id is nullable because results can be case-level (not session-specific).
  - ON DELETE CASCADE from cases ensures orphan cleanup.
  - ON DELETE SET NULL from chat_sessions preserves result records if a session
    is deleted (historical auditability).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b3f7e291cc4a"
down_revision: Union[str, Sequence[str], None] = "ead3432ccad1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prediction_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("timepoint", sa.Integer(), nullable=False),
        # Core V2 outputs (all nullable)
        sa.Column("fusion_dds_prediction", sa.Float(), nullable=True),
        sa.Column("temporal_risk_score", sa.Float(), nullable=True),
        sa.Column("future_escalation_flag", sa.Integer(), nullable=True),
        sa.Column("triage_level", sa.String(length=16), nullable=True),
        # Specialist predictions (nullable: missing != zero)
        sa.Column("struct_pred", sa.Float(), nullable=True),
        sa.Column("text_pred", sa.Float(), nullable=True),
        sa.Column("voice_pred", sa.Float(), nullable=True),
        sa.Column("behav_pred", sa.Float(), nullable=True),  # Blocked until Step 10
        # Availability flags
        sa.Column("struct_available", sa.Boolean(), nullable=False),
        sa.Column("text_available", sa.Boolean(), nullable=False),
        sa.Column("voice_available", sa.Boolean(), nullable=False),
        sa.Column("behav_available", sa.Boolean(), nullable=False),
        # Timestamps
        sa.Column("predicted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["chat_sessions.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_prediction_results_case_id"),
        "prediction_results",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prediction_results_session_id"),
        "prediction_results",
        ["session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_prediction_results_session_id"),
        table_name="prediction_results",
    )
    op.drop_index(
        op.f("ix_prediction_results_case_id"),
        table_name="prediction_results",
    )
    op.drop_table("prediction_results")
