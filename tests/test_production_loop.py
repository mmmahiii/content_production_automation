from __future__ import annotations

import pytest

from instagram_ai_system.production_loop import InstagramGraphPublisher, PipelineWorker

@pytest.mark.skipif(__import__("importlib").util.find_spec("sqlalchemy") is None, reason="sqlalchemy required")
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



def test_publish_defaults_to_simulation_even_with_credentials(monkeypatch) -> None:
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "token")
    monkeypatch.setenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "acct")
    monkeypatch.delenv("ALLOW_AUTONOMOUS_PUBLISH", raising=False)
    monkeypatch.delenv("PUBLISH_APPROVAL_GRANTED", raising=False)
    monkeypatch.delenv("GOVERNANCE_APPROVED", raising=False)

    result = InstagramGraphPublisher().publish_or_schedule("artifact.mp4", "caption", "run-1")

    assert result["status"] == "simulated"
    assert result["platform_post_id"] == "sim-run-1"
    assert "ALLOW_AUTONOMOUS_PUBLISH" in result["reason"]


def test_publish_allows_live_path_with_explicit_override_and_approvals(monkeypatch) -> None:
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "token")
    monkeypatch.setenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "acct")
    monkeypatch.setenv("ALLOW_AUTONOMOUS_PUBLISH", "true")
    monkeypatch.setenv("PUBLISH_APPROVAL_GRANTED", "true")
    monkeypatch.setenv("GOVERNANCE_APPROVED", "true")

    class FakeResponse:
        def __init__(self, payload: dict[str, str]) -> None:
            self._payload = payload

        def read(self) -> bytes:
            import json

            return json.dumps(self._payload).encode()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    calls: list[str] = []

    def fake_urlopen(req, timeout=0):
        url = req.full_url
        calls.append(url)
        if url.endswith("/media"):
            return FakeResponse({"id": "creation-1"})
        return FakeResponse({"id": "post-1"})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    result = InstagramGraphPublisher().publish_or_schedule("artifact.mp4", "caption", "run-2")

    assert result["status"] == "published"
    assert result["platform_post_id"] == "post-1"
    assert len(calls) == 2


def test_publish_blocks_without_approval_signals(monkeypatch) -> None:
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "token")
    monkeypatch.setenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "acct")
    monkeypatch.setenv("ALLOW_AUTONOMOUS_PUBLISH", "true")
    monkeypatch.delenv("PUBLISH_APPROVAL_GRANTED", raising=False)
    monkeypatch.delenv("GOVERNANCE_APPROVED", raising=False)

    result = InstagramGraphPublisher().publish_or_schedule("artifact.mp4", "caption", "run-3")

    assert result["status"] == "simulated"
    assert result["platform_post_id"] == "sim-run-3"
    assert "PUBLISH_APPROVAL_GRANTED" in result["reason"]
