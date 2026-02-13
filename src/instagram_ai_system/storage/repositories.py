from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    AccountExperimentModel,
    BriefAssetModel,
    ContentPlanModel,
    ExperimentArmStateModel,
    ExperimentMetricModel,
    ExperimentPostModel,
    ModelVersionModel,
    NicheCandidateModel,
    NicheScoreModel,
    PerformanceSnapshotModel,
    PublishAttemptModel,
    OperationRunModel,
    TrendIngestionModel,
    DecisionLogModel,
    MonetizationInsightModel,
)


@dataclass(slots=True)
class ArmStateRecord:
    arm_key: str
    pulls: int
    reward_sum: float
    schema_version: str
    trace_id: str


class ContentPlanRepository:
    def __init__(self, session: Session):
        self.session = session

    def upsert_plan(
        self,
        *,
        plan_id: str,
        topic: str,
        objective: str,
        status: str,
        payload: dict[str, Any],
        schema_version: str,
        trace_id: str,
    ) -> ContentPlanModel:
        plan = self.session.get(ContentPlanModel, plan_id)
        if plan is None:
            plan = ContentPlanModel(id=plan_id, topic=topic, objective=objective, status=status)
            self.session.add(plan)
        plan.topic = topic
        plan.objective = objective
        plan.status = status
        plan.plan_payload = payload
        plan.schema_version = schema_version
        plan.trace_id = trace_id
        return plan

    def get_plan(self, plan_id: str) -> ContentPlanModel | None:
        return self.session.get(ContentPlanModel, plan_id)


class BriefAssetRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_brief_asset(
        self,
        *,
        asset_id: str,
        content_plan_id: str,
        brief_payload: dict[str, Any],
        asset_payload: dict[str, Any],
        lifecycle_state: str,
        schema_version: str,
        trace_id: str,
        approval_status: str = "pending",
        approval_payload: dict[str, Any] | None = None,
    ) -> BriefAssetModel:
        model = BriefAssetModel(
            id=asset_id,
            content_plan_id=content_plan_id,
            brief_payload=brief_payload,
            asset_payload=asset_payload,
            lifecycle_state=lifecycle_state,
            approval_status=approval_status,
            approval_payload=approval_payload or {},
            schema_version=schema_version,
            trace_id=trace_id,
        )
        self.session.add(model)
        return model

    def list_for_plan(self, content_plan_id: str) -> list[BriefAssetModel]:
        stmt = select(BriefAssetModel).where(BriefAssetModel.content_plan_id == content_plan_id)
        return list(self.session.scalars(stmt))


class PublishAttemptRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_attempt(
        self,
        *,
        attempt_id: str,
        brief_asset_id: str,
        platform: str,
        status: str,
        attempt_number: int,
        response_payload: dict[str, Any],
        error_message: str | None,
        attempted_at: datetime,
        schema_version: str,
        trace_id: str,
    ) -> PublishAttemptModel:
        model = PublishAttemptModel(
            id=attempt_id,
            brief_asset_id=brief_asset_id,
            platform=platform,
            status=status,
            attempt_number=attempt_number,
            response_payload=response_payload,
            error_message=error_message,
            attempted_at=attempted_at,
            schema_version=schema_version,
            trace_id=trace_id,
        )
        self.session.add(model)
        return model

    def list_for_asset(self, brief_asset_id: str) -> list[PublishAttemptModel]:
        stmt = select(PublishAttemptModel).where(PublishAttemptModel.brief_asset_id == brief_asset_id)
        return list(self.session.scalars(stmt))


class PerformanceSnapshotRepository:
    def __init__(self, session: Session):
        self.session = session

    def record_snapshot(
        self,
        *,
        snapshot_id: str,
        publish_attempt_id: str,
        window: str,
        metrics_payload: dict[str, Any],
        derived_rates: dict[str, Any],
        captured_at: datetime,
        schema_version: str,
        trace_id: str,
    ) -> PerformanceSnapshotModel:
        model = PerformanceSnapshotModel(
            id=snapshot_id,
            publish_attempt_id=publish_attempt_id,
            window=window,
            metrics_payload=metrics_payload,
            derived_rates=derived_rates,
            captured_at=captured_at,
            schema_version=schema_version,
            trace_id=trace_id,
        )
        self.session.add(model)
        return model

    def list_for_attempt(self, publish_attempt_id: str) -> list[PerformanceSnapshotModel]:
        stmt = select(PerformanceSnapshotModel).where(PerformanceSnapshotModel.publish_attempt_id == publish_attempt_id)
        return list(self.session.scalars(stmt))



class OperationRunRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_run(
        self,
        *,
        run_id: str,
        operation_name: str,
        params_payload: dict[str, Any],
        status: str,
        result_payload: dict[str, Any],
        trace_id: str,
        started_at: datetime,
        completed_at: datetime | None = None,
        error_message: str | None = None,
    ) -> OperationRunModel:
        model = OperationRunModel(
            id=run_id,
            operation_name=operation_name,
            params_payload=params_payload,
            status=status,
            result_payload=result_payload,
            trace_id=trace_id,
            started_at=started_at,
            completed_at=completed_at,
            error_message=error_message,
        )
        self.session.add(model)
        return model

    def complete_run(
        self,
        *,
        run_id: str,
        status: str,
        result_payload: dict[str, Any],
        completed_at: datetime,
        error_message: str | None = None,
    ) -> OperationRunModel:
        model = self.session.get(OperationRunModel, run_id)
        if model is None:
            raise ValueError(f"Unknown operation run id: {run_id}")
        model.status = status
        model.result_payload = result_payload
        model.completed_at = completed_at
        model.error_message = error_message
        return model

    def list_failed_runs(self, *, operation_name: str, since: datetime) -> list[OperationRunModel]:
        stmt = (
            select(OperationRunModel)
            .where(OperationRunModel.operation_name == operation_name)
            .where(OperationRunModel.status == "failed")
            .where(OperationRunModel.started_at >= since)
            .order_by(OperationRunModel.started_at.asc())
        )
        return list(self.session.scalars(stmt))

    def was_replayed(self, *, failed_run_id: str) -> bool:
        stmt = select(OperationRunModel).where(
            OperationRunModel.operation_name == "replay-failed",
            OperationRunModel.status == "succeeded",
        )
        for row in self.session.scalars(stmt):
            if (row.params_payload or {}).get("failed_run_id") == failed_run_id:
                return True
        return False

class ExperimentStateRepository:
    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def build_arm_state_record(
        *,
        arm_key: str,
        pulls: int,
        reward_sum: float,
        schema_version: str,
        trace_id: str,
    ) -> ArmStateRecord:
        return ArmStateRecord(
            arm_key=arm_key,
            pulls=pulls,
            reward_sum=reward_sum,
            schema_version=schema_version,
            trace_id=trace_id,
        )

    def load_arm_states(self) -> list[ArmStateRecord]:
        stmt = select(ExperimentArmStateModel)
        rows = self.session.scalars(stmt)
        return [
            ArmStateRecord(
                arm_key=row.arm_key,
                pulls=row.pulls,
                reward_sum=row.reward_sum,
                schema_version=row.schema_version,
                trace_id=row.trace_id,
            )
            for row in rows
        ]

    def upsert_arm_states(
        self,
        arm_states: Iterable[ArmStateRecord],
        *,
        schema_version: str,
        trace_id: str,
    ) -> None:
        for state in arm_states:
            model = self.session.get(ExperimentArmStateModel, state.arm_key)
            if model is None:
                model = ExperimentArmStateModel(arm_key=state.arm_key)
                self.session.add(model)
            model.pulls = state.pulls
            model.reward_sum = state.reward_sum
            model.schema_version = schema_version
            model.trace_id = trace_id


class NicheStrategyRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_niche_candidate(
        self,
        *,
        candidate_id: str,
        niche_name: str,
        target_audience: str,
        candidate_payload: dict[str, Any],
        status: str,
        schema_version: str,
        trace_id: str,
    ) -> NicheCandidateModel:
        model = NicheCandidateModel(
            id=candidate_id,
            niche_name=niche_name,
            target_audience=target_audience,
            candidate_payload=candidate_payload,
            status=status,
            schema_version=schema_version,
            trace_id=trace_id,
        )
        self.session.add(model)
        return model

    def record_niche_score(
        self,
        *,
        score_id: str,
        niche_candidate_id: str,
        score_payload: dict[str, Any],
        success_score: float,
        model_version: str,
        schema_version: str,
        trace_id: str,
    ) -> NicheScoreModel:
        model = NicheScoreModel(
            id=score_id,
            niche_candidate_id=niche_candidate_id,
            score_payload=score_payload,
            success_score=success_score,
            model_version=model_version,
            schema_version=schema_version,
            trace_id=trace_id,
        )
        self.session.add(model)
        return model

    def create_account_experiment(
        self,
        *,
        experiment_id: str,
        niche_candidate_id: str,
        account_handle: str,
        stage: str,
        status: str,
        plan_payload: dict[str, Any],
        schema_version: str,
        trace_id: str,
    ) -> AccountExperimentModel:
        model = AccountExperimentModel(
            id=experiment_id,
            niche_candidate_id=niche_candidate_id,
            account_handle=account_handle,
            stage=stage,
            status=status,
            plan_payload=plan_payload,
            schema_version=schema_version,
            trace_id=trace_id,
        )
        self.session.add(model)
        return model

    def create_experiment_post(
        self,
        *,
        post_id: str,
        account_experiment_id: str,
        content_ref: str,
        status: str,
        schema_version: str,
        trace_id: str,
        published_at: datetime | None = None,
    ) -> ExperimentPostModel:
        model = ExperimentPostModel(
            id=post_id,
            account_experiment_id=account_experiment_id,
            content_ref=content_ref,
            status=status,
            schema_version=schema_version,
            trace_id=trace_id,
            published_at=published_at,
        )
        self.session.add(model)
        return model

    def record_experiment_metric(
        self,
        *,
        metric_id: str,
        experiment_post_id: str,
        metric_payload: dict[str, Any],
        captured_at: datetime,
        schema_version: str,
        trace_id: str,
    ) -> ExperimentMetricModel:
        model = ExperimentMetricModel(
            id=metric_id,
            experiment_post_id=experiment_post_id,
            metric_payload=metric_payload,
            captured_at=captured_at,
            schema_version=schema_version,
            trace_id=trace_id,
        )
        self.session.add(model)
        return model

    def record_model_version(
        self,
        *,
        version_id: str,
        model_name: str,
        version_tag: str,
        parameters_payload: dict[str, Any],
        schema_version: str,
        trace_id: str,
    ) -> ModelVersionModel:
        model = ModelVersionModel(
            id=version_id,
            model_name=model_name,
            version_tag=version_tag,
            parameters_payload=parameters_payload,
            schema_version=schema_version,
            trace_id=trace_id,
        )
        self.session.add(model)
        return model

    def list_ranked_niches(self) -> list[NicheScoreModel]:
        stmt = select(NicheScoreModel).order_by(NicheScoreModel.success_score.desc())
        return list(self.session.scalars(stmt))


class TrendIngestionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        ingestion_id: str,
        run_id: str,
        source: str,
        topic: str,
        score: float,
        momentum: float,
        payload: dict[str, Any],
        observed_at: datetime,
    ) -> TrendIngestionModel:
        model = TrendIngestionModel(
            id=ingestion_id,
            run_id=run_id,
            source=source,
            topic=topic,
            score=score,
            momentum=momentum,
            payload=payload,
            observed_at=observed_at,
        )
        self.session.add(model)
        return model


class DecisionLogRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, *, decision_id: str, run_id: str, decision_type: str, decision_payload: dict[str, Any], trace_id: str) -> DecisionLogModel:
        model = DecisionLogModel(
            id=decision_id,
            run_id=run_id,
            decision_type=decision_type,
            decision_payload=decision_payload,
            trace_id=trace_id,
        )
        self.session.add(model)
        return model


class MonetizationInsightRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, *, insight_id: str, run_id: str, insight_payload: dict[str, Any]) -> MonetizationInsightModel:
        model = MonetizationInsightModel(id=insight_id, run_id=run_id, insight_payload=insight_payload)
        self.session.add(model)
        return model
