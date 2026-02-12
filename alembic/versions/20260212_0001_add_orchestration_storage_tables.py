"""add orchestration storage tables

Revision ID: 20260212_0001
Revises: 
Create Date: 2026-02-12 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260212_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "content_plans",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("objective", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("plan_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_plans_trace_id", "content_plans", ["trace_id"], unique=False)

    op.create_table(
        "brief_assets",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("content_plan_id", sa.String(length=64), nullable=False),
        sa.Column("brief_payload", sa.JSON(), nullable=False),
        sa.Column("asset_payload", sa.JSON(), nullable=False),
        sa.Column("lifecycle_state", sa.String(length=32), nullable=False),
        sa.Column("approval_status", sa.String(length=32), nullable=False),
        sa.Column("approval_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_brief_assets_content_plan_id", "brief_assets", ["content_plan_id"], unique=False)
    op.create_index("ix_brief_assets_trace_id", "brief_assets", ["trace_id"], unique=False)

    op.create_table(
        "publish_attempts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("brief_asset_id", sa.String(length=64), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("response_payload", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_publish_attempts_brief_asset_id", "publish_attempts", ["brief_asset_id"], unique=False)
    op.create_index("ix_publish_attempts_trace_id", "publish_attempts", ["trace_id"], unique=False)

    op.create_table(
        "post_performance_snapshots",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("publish_attempt_id", sa.String(length=64), nullable=False),
        sa.Column("window", sa.String(length=16), nullable=False),
        sa.Column("metrics_payload", sa.JSON(), nullable=False),
        sa.Column("derived_rates", sa.JSON(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_post_performance_snapshots_publish_attempt_id",
        "post_performance_snapshots",
        ["publish_attempt_id"],
        unique=False,
    )
    op.create_index("ix_post_performance_snapshots_trace_id", "post_performance_snapshots", ["trace_id"], unique=False)

    op.create_table(
        "experiment_arm_states",
        sa.Column("arm_key", sa.String(length=128), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("pulls", sa.Integer(), nullable=False),
        sa.Column("reward_sum", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("arm_key"),
    )
    op.create_index("ix_experiment_arm_states_trace_id", "experiment_arm_states", ["trace_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_experiment_arm_states_trace_id", table_name="experiment_arm_states")
    op.drop_table("experiment_arm_states")

    op.drop_index("ix_post_performance_snapshots_trace_id", table_name="post_performance_snapshots")
    op.drop_index("ix_post_performance_snapshots_publish_attempt_id", table_name="post_performance_snapshots")
    op.drop_table("post_performance_snapshots")

    op.drop_index("ix_publish_attempts_trace_id", table_name="publish_attempts")
    op.drop_index("ix_publish_attempts_brief_asset_id", table_name="publish_attempts")
    op.drop_table("publish_attempts")

    op.drop_index("ix_brief_assets_trace_id", table_name="brief_assets")
    op.drop_index("ix_brief_assets_content_plan_id", table_name="brief_assets")
    op.drop_table("brief_assets")

    op.drop_index("ix_content_plans_trace_id", table_name="content_plans")
    op.drop_table("content_plans")
