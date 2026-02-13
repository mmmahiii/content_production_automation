from __future__ import annotations

import pytest

from instagram_ai_system.production_loop import PipelineWorker

@pytest.mark.skipif(pytest.importorskip("sqlalchemy", reason="sqlalchemy required") is None, reason="sqlalchemy required")
def test_pipeline_worker_end_to_end_and_resume(tmp_path, monkeypatch) -> None:
    db_url = f"sqlite+pysqlite:///{tmp_path / 'pipeline.db'}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    worker = PipelineWorker(db_url=db_url)

    def fake_fetch(topic: str | None = None):
        return [
            {
                "trend_id": "t-1",
                "keyword": "AI workflow automation",
                "source": "reddit",
                "score": 0.8,
                "momentum": 0.7,
                "observed_at": "2025-01-01T00:00:00+00:00",
            }
        ]

    class FakeTrend:
        def fetch(self, topic: str | None = None):
            from instagram_ai_system.production_loop import TrendItem

            return [TrendItem(**fake_fetch(topic)[0])]

    worker.trends = FakeTrend()  # type: ignore[assignment]

    run_id = worker.enqueue(topic="ai")

    # Simulate interrupted run after trend stage.
    worker._stage_trends(run_id)

    from instagram_ai_system.storage import Base, Database
    from instagram_ai_system.storage.models import PipelineRunModel

    db = Database(db_url)
    Base.metadata.create_all(db.engine)
    with db.session_scope() as session:
        model = session.get(PipelineRunModel, run_id)
        assert model is not None
        assert model.trend_payload
        assert not model.publish_payload

    # Resume run; should not duplicate or fail.
    result = worker.process(run_id)
    assert result["status"] == "completed"
    assert result["publish"]["platform_post_id"].startswith("sim-")
    assert result["metrics"]["metrics"]["views"] >= 1

    result2 = worker.process(run_id)
    assert result2["status"] == "completed"
    assert result2["publish"]["platform_post_id"] == result["publish"]["platform_post_id"]
