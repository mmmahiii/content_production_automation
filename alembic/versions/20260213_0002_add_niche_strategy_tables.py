"""add niche strategy engine tables

Revision ID: 20260213_0002
Revises: 20260212_0001
Create Date: 2026-02-13 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260213_0002"
down_revision = "20260212_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "niche_candidates",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("niche_name", sa.String(length=255), nullable=False),
        sa.Column("target_audience", sa.String(length=255), nullable=False),
        sa.Column("candidate_payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niche_candidates_trace_id", "niche_candidates", ["trace_id"], unique=False)
    op.create_index("ix_niche_candidates_niche_name", "niche_candidates", ["niche_name"], unique=False)

    op.create_table(
        "niche_scores",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("niche_candidate_id", sa.String(length=64), nullable=False),
        sa.Column("score_payload", sa.JSON(), nullable=False),
        sa.Column("success_score", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niche_scores_trace_id", "niche_scores", ["trace_id"], unique=False)
    op.create_index("ix_niche_scores_niche_candidate_id", "niche_scores", ["niche_candidate_id"], unique=False)
    op.create_index("ix_niche_scores_success_score", "niche_scores", ["success_score"], unique=False)

    op.create_table(
        "account_experiments",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("niche_candidate_id", sa.String(length=64), nullable=False),
        sa.Column("account_handle", sa.String(length=128), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("plan_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_account_experiments_trace_id", "account_experiments", ["trace_id"], unique=False)
    op.create_index(
        "ix_account_experiments_niche_candidate_id",
        "account_experiments",
        ["niche_candidate_id"],
        unique=False,
    )

    op.create_table(
        "experiment_posts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("account_experiment_id", sa.String(length=64), nullable=False),
        sa.Column("content_ref", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_experiment_posts_trace_id", "experiment_posts", ["trace_id"], unique=False)
    op.create_index("ix_experiment_posts_account_experiment_id", "experiment_posts", ["account_experiment_id"], unique=False)

    op.create_table(
        "experiment_metrics",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("experiment_post_id", sa.String(length=64), nullable=False),
        sa.Column("metric_payload", sa.JSON(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_experiment_metrics_trace_id", "experiment_metrics", ["trace_id"], unique=False)
    op.create_index("ix_experiment_metrics_experiment_post_id", "experiment_metrics", ["experiment_post_id"], unique=False)

    op.create_table(
        "model_versions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("version_tag", sa.String(length=64), nullable=False),
        sa.Column("parameters_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_model_versions_trace_id", "model_versions", ["trace_id"], unique=False)
    op.create_index("ix_model_versions_model_name", "model_versions", ["model_name"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_model_versions_model_name", table_name="model_versions")
    op.drop_index("ix_model_versions_trace_id", table_name="model_versions")
    op.drop_table("model_versions")

    op.drop_index("ix_experiment_metrics_experiment_post_id", table_name="experiment_metrics")
    op.drop_index("ix_experiment_metrics_trace_id", table_name="experiment_metrics")
    op.drop_table("experiment_metrics")

    op.drop_index("ix_experiment_posts_account_experiment_id", table_name="experiment_posts")
    op.drop_index("ix_experiment_posts_trace_id", table_name="experiment_posts")
    op.drop_table("experiment_posts")

    op.drop_index("ix_account_experiments_niche_candidate_id", table_name="account_experiments")
    op.drop_index("ix_account_experiments_trace_id", table_name="account_experiments")
    op.drop_table("account_experiments")

    op.drop_index("ix_niche_scores_success_score", table_name="niche_scores")
    op.drop_index("ix_niche_scores_niche_candidate_id", table_name="niche_scores")
    op.drop_index("ix_niche_scores_trace_id", table_name="niche_scores")
    op.drop_table("niche_scores")

    op.drop_index("ix_niche_candidates_niche_name", table_name="niche_candidates")
    op.drop_index("ix_niche_candidates_trace_id", table_name="niche_candidates")
    op.drop_table("niche_candidates")
