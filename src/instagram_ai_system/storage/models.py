from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ContentPlanModel(Base):
    __tablename__ = "content_plans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    objective: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    plan_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class BriefAssetModel(Base):
    __tablename__ = "brief_assets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    content_plan_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    brief_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    asset_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    lifecycle_state: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    approval_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    approval_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class PublishAttemptModel(Base):
    __tablename__ = "publish_attempts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    brief_asset_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    response_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class PerformanceSnapshotModel(Base):
    __tablename__ = "post_performance_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    publish_attempt_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    window: Mapped[str] = mapped_column(String(16), nullable=False, default="24h")
    metrics_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    derived_rates: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class ExperimentArmStateModel(Base):
    __tablename__ = "experiment_arm_states"

    arm_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    pulls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reward_sum: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class NicheCandidateModel(Base):
    __tablename__ = "niche_candidates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    niche_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    target_audience: Mapped[str] = mapped_column(String(255), nullable=False)
    candidate_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="generated")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class NicheScoreModel(Base):
    __tablename__ = "niche_scores"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    niche_candidate_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    score_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    success_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, index=True)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False, default="rules-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class AccountExperimentModel(Base):
    __tablename__ = "account_experiments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    niche_candidate_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    account_handle: Mapped[str] = mapped_column(String(128), nullable=False)
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default="stage_1")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned")
    plan_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class ExperimentPostModel(Base):
    __tablename__ = "experiment_posts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    account_experiment_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    content_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class ExperimentMetricModel(Base):
    __tablename__ = "experiment_metrics"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    experiment_post_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    metric_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class ModelVersionModel(Base):
    __tablename__ = "model_versions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    version_tag: Mapped[str] = mapped_column(String(64), nullable=False)
    parameters_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class OperationRunModel(Base):
    __tablename__ = "operation_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    operation_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    params_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    result_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
