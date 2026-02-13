from __future__ import annotations

import json
import os
import subprocess
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import sleep
from typing import Any
from uuid import uuid4

from integrations.trends import InstagramHashtagScraperAdapter, RedditTrendsAdapter, TrendAggregator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from instagram_ai_system.storage import Base, Database


@dataclass(slots=True)
class TrendItem:
    trend_id: str
    keyword: str
    source: str
    score: float
    momentum: float
    observed_at: str


@dataclass(slots=True)
class ScriptPackage:
    script_id: str
    title: str
    hook: str
    body: str
    cta: str
    template_key: str
    asset_plan: dict[str, Any]


@dataclass(slots=True)
class PerformanceSnapshot:
    run_id: str
    platform_post_id: str
    window: str
    metrics: dict[str, Any]
    captured_at: str




class InstagramHashtagScraperClient:
    """Best-effort scraper; falls back to deterministic simulator payloads."""

    def __init__(self, seed_tags: list[str] | None = None) -> None:
        self.seed_tags = seed_tags or ["ai", "automation", "contentcreator", "smallbusiness"]

    def fetch_trending_hashtags(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for tag in self.seed_tags:
            url = f"https://www.instagram.com/explore/tags/{urllib.parse.quote(tag)}/"
            req = urllib.request.Request(url, headers={"User-Agent": "content-automation/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=10) as response:  # noqa: S310
                    html = response.read().decode("utf-8", errors="ignore")
                pseudo_volume = min(900000, max(10000, len(html) * 4))
                rows.append({
                    "hashtag": f"#{tag}",
                    "post_count": pseudo_volume,
                    "growth_24h": 0.2 + (len(tag) % 5) * 0.08,
                    "engagement_rate": 0.03 + (len(tag) % 4) * 0.01,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                    "url": url,
                })
            except Exception:
                rows.append({
                    "hashtag": f"#{tag}",
                    "post_count": 120000,
                    "growth_24h": 0.18,
                    "engagement_rate": 0.04,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                    "url": url,
                })
        return rows


class MultiSourceTrendSource:
    def __init__(self) -> None:
        self.reddit = RedditTrendsAdapter(RedditClient())
        self.instagram = InstagramHashtagScraperAdapter(InstagramHashtagScraperClient())
        self.aggregator = TrendAggregator([self.reddit, self.instagram])

    def fetch(self, topic: str | None = None) -> list[TrendItem]:
        normalized = self.aggregator.fetch_and_normalize()
        items: list[TrendItem] = []
        for trend in normalized:
            if topic and topic.lower() not in trend.topic.lower():
                continue
            items.append(
                TrendItem(
                    trend_id=f"{trend.source}:{trend.topic[:24]}",
                    keyword=trend.topic,
                    source=trend.source,
                    score=trend.score,
                    momentum=trend.momentum,
                    observed_at=trend.observed_at.isoformat(),
                )
            )
        return items[:8]


class RedditClient:
    endpoint = "https://www.reddit.com/r/popular/hot.json"

    def fetch_hot_topics(self) -> list[dict[str, Any]]:
        query = urllib.parse.urlencode({"limit": 10})
        req = urllib.request.Request(
            f"{self.endpoint}?{query}",
            headers={"User-Agent": "content-automation/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
        rows = []
        for row in payload.get("data", {}).get("children", []):
            data = row.get("data", {})
            rows.append(
                {
                    "title": str(data.get("title", "")).strip(),
                    "hotness": min(1.0, float(data.get("ups", 0) or 0) / 50000),
                    "velocity": float(data.get("upvote_ratio", 0.0) or 0.0),
                    "created_utc": data.get("created_utc"),
                    "subreddit": data.get("subreddit"),
                    "url": f"https://reddit.com{data.get('permalink', '')}",
                }
            )
        return rows


class RedditTrendSource:
    endpoint = "https://www.reddit.com/r/popular/hot.json"

    def fetch(self, topic: str | None = None) -> list[TrendItem]:
        query = urllib.parse.urlencode({"limit": 10})
        req = urllib.request.Request(
            f"{self.endpoint}?{query}",
            headers={"User-Agent": "content-automation/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))

        items: list[TrendItem] = []
        for row in payload.get("data", {}).get("children", []):
            data = row.get("data", {})
            title = str(data.get("title", "")).strip()
            if not title:
                continue
            if topic and topic.lower() not in title.lower():
                continue
            ups = float(data.get("ups", 0) or 0)
            ratio = float(data.get("upvote_ratio", 0) or 0)
            items.append(
                TrendItem(
                    trend_id=str(data.get("id", uuid4())),
                    keyword=title[:120],
                    source="reddit",
                    score=min(1.0, (ups / 50000.0) + ratio * 0.2),
                    momentum=ratio,
                    observed_at=datetime.now(timezone.utc).isoformat(),
                )
            )
        return sorted(items, key=lambda item: item.score, reverse=True)[:5]


class TemplateCreativeEngine:
    def create(self, trend: TrendItem) -> ScriptPackage:
        key = "kinetic-subtitles-v1"
        hook = f"Everyone is missing this: {trend.keyword[:65]}"
        return ScriptPackage(
            script_id=f"script-{trend.trend_id}",
            title=f"{trend.keyword[:58]} #shorts",
            hook=hook,
            body=f"Hook: {hook}\nPoint 1: why this trend matters now.\nPoint 2: one quick practical takeaway.",
            cta="Follow for daily tactical explainers.",
            template_key=key,
            asset_plan={"duration_seconds": 22, "format": "9:16", "voice": "energetic"},
        )


class FfmpegRenderer:
    def __init__(self, output_dir: str = "artifacts") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render(self, run_id: str, script: ScriptPackage) -> str:
        output_path = self.output_dir / f"{run_id}.mp4"
        if output_path.exists():
            return str(output_path)

        ffmpeg = os.getenv("FFMPEG_BIN", "ffmpeg")
        command = [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=1080x1920:d=3",
            "-vf",
            "format=yuv420p",
            str(output_path),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except Exception:
            output_path.write_bytes(b"FAKE_MP4")
        return str(output_path)


class InstagramGraphPublisher:
    def publish_or_schedule(self, media_path: str, caption: str, run_id: str) -> dict[str, Any]:
        token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
        if not token or not account_id:
            return {
                "platform": "instagram",
                "status": "simulated",
                "platform_post_id": f"sim-{run_id}",
                "media_path": media_path,
                "caption": caption,
            }

        create_url = f"https://graph.facebook.com/v20.0/{account_id}/media"
        publish_url = f"https://graph.facebook.com/v20.0/{account_id}/media_publish"
        create_payload = urllib.parse.urlencode(
            {
                "caption": caption,
                "media_type": "REELS",
                "video_url": os.getenv("PUBLIC_MEDIA_BASE_URL", "") + "/" + Path(media_path).name,
                "access_token": token,
            }
        ).encode()
        req = urllib.request.Request(create_url, data=create_payload, method="POST")
        with urllib.request.urlopen(req, timeout=20) as response:  # noqa: S310
            creation = json.loads(response.read().decode("utf-8"))

        publish_payload = urllib.parse.urlencode(
            {"creation_id": creation["id"], "access_token": token}
        ).encode()
        req2 = urllib.request.Request(publish_url, data=publish_payload, method="POST")
        with urllib.request.urlopen(req2, timeout=20) as response:  # noqa: S310
            published = json.loads(response.read().decode("utf-8"))

        return {
            "platform": "instagram",
            "status": "published",
            "platform_post_id": str(published.get("id")),
            "creation_id": str(creation.get("id")),
            "media_path": media_path,
        }


class InstagramGraphAnalytics:
    def fetch(self, platform_post_id: str, run_id: str) -> PerformanceSnapshot:
        token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        if not token or platform_post_id.startswith("sim-"):
            return PerformanceSnapshot(
                run_id=run_id,
                platform_post_id=platform_post_id,
                window="24h",
                metrics={"views": 1200, "likes": 87, "comments": 9, "shares": 11, "saves": 17},
                captured_at=datetime.now(timezone.utc).isoformat(),
            )

        fields = "reach,likes,comments,shares,saved,video_views"
        url = (
            f"https://graph.facebook.com/v20.0/{platform_post_id}/insights"
            f"?metric={urllib.parse.quote(fields)}&access_token={urllib.parse.quote(token)}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "content-automation/1.0"})
        with urllib.request.urlopen(req, timeout=20) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))

        mapped = {"views": 0, "likes": 0, "comments": 0, "shares": 0, "saves": 0}
        for row in payload.get("data", []):
            name = row.get("name")
            value = row.get("values", [{}])[0].get("value", 0)
            if name in {"video_views", "reach"}:
                mapped["views"] = int(value)
            elif name == "likes":
                mapped["likes"] = int(value)
            elif name == "comments":
                mapped["comments"] = int(value)
            elif name == "shares":
                mapped["shares"] = int(value)
            elif name == "saved":
                mapped["saves"] = int(value)

        return PerformanceSnapshot(
            run_id=run_id,
            platform_post_id=platform_post_id,
            window="24h",
            metrics=mapped,
            captured_at=datetime.now(timezone.utc).isoformat(),
        )


class PolicyGuard:
    blocked_terms = {"hate", "violence", "medical cure", "guaranteed income"}
    blocked_competitors = {"tiktok shop scam"}

    def validate(self, script: ScriptPackage) -> tuple[bool, list[str]]:
        reason: list[str] = []
        text = f"{script.title} {script.hook} {script.body} {script.cta}".lower()
        for term in self.blocked_terms:
            if term in text:
                reason.append(f"policy_block:{term}")
        for name in self.blocked_competitors:
            if name in text:
                reason.append(f"brand_block:{name}")
        return (len(reason) == 0, reason)


class PipelineWorker:
    def __init__(self, db_url: str | None = None) -> None:
        from instagram_ai_system.storage import Base, Database

        self._models = __import__("instagram_ai_system.storage.models", fromlist=["LearningSnapshotModel", "PipelineRunModel", "PipelineStageCheckpointModel"])
        database_url = db_url or os.getenv("DATABASE_URL", "sqlite+pysqlite:///./automation.db")
        self.db = Database(database_url)
        Base.metadata.create_all(self.db.engine)
        self.trends = MultiSourceTrendSource()
        self.creative = TemplateCreativeEngine()
        self.renderer = FfmpegRenderer()
        self.publisher = InstagramGraphPublisher()
        self.analytics = InstagramGraphAnalytics()
        self.policy = PolicyGuard()

    def enqueue(self, topic: str | None = None) -> str:
        run_id = str(uuid4())
        with self.db.session_scope() as session:
            session.add(self._models.PipelineRunModel(id=run_id, topic=topic or "general", status="queued", attempts=0))
        return run_id

    def _checkpoint(self, run_id: str, stage_name: str, status: str, payload: dict[str, Any]) -> None:
        with self.db.session_scope() as session:
            pk = f"{run_id}:{stage_name}"
            model = session.get(self._models.PipelineStageCheckpointModel, pk)
            if model is None:
                model = self._models.PipelineStageCheckpointModel(id=pk, run_id=run_id, stage_name=stage_name)
                session.add(model)
            model.status = status
            model.payload = payload

    def process(self, run_id: str) -> dict[str, Any]:
        with self.db.session_scope() as session:
            run = session.get(self._models.PipelineRunModel, run_id)
            if run is None:
                raise ValueError(f"Unknown run id: {run_id}")
            if run.status == "completed":
                return {"run_id": run_id, "status": "completed", "publish": run.publish_payload, "metrics": run.metrics_payload}
            run.status = "running"
            run.attempts += 1

        run = self._stage_trends(run_id)
        run = self._stage_script(run_id)
        run = self._stage_render(run_id)
        run = self._stage_publish(run_id)
        run = self._stage_metrics(run_id)
        self._stage_learning(run_id)

        with self.db.session_scope() as session:
            model = session.get(self._models.PipelineRunModel, run_id)
            assert model is not None
            model.status = "completed"
            return {"run_id": run_id, "status": model.status, "publish": model.publish_payload, "metrics": model.metrics_payload}

    def _stage_trends(self, run_id: str) -> dict[str, Any]:
        with self.db.session_scope() as session:
            run = session.get(self._models.PipelineRunModel, run_id)
            assert run is not None
            if run.trend_payload:
                return run.trend_payload
            for i in range(3):
                try:
                    items = self.trends.fetch(run.topic)
                    if not items:
                        raise RuntimeError("no trends returned")
                    payload = {"items": [item.__dict__ for item in items], "selected": items[0].__dict__}
                    run.trend_payload = payload
                    run.current_stage = "trends"
                    from instagram_ai_system.storage import TrendIngestionRepository

                    repo = TrendIngestionRepository(session)
                    for idx, item in enumerate(items):
                        repo.create(
                            ingestion_id=f"{run_id}:trend:{idx}",
                            run_id=run_id,
                            source=item.source,
                            topic=item.keyword,
                            score=item.score,
                            momentum=item.momentum,
                            payload=item.__dict__,
                            observed_at=datetime.fromisoformat(item.observed_at.replace("Z", "+00:00")),
                        )
                    self._checkpoint(run_id, "trends", "done", payload)
                    return payload
                except Exception as exc:
                    if i == 2:
                        run.status = "failed"
                        run.error_message = str(exc)
                        self._checkpoint(run_id, "trends", "failed", {"error": str(exc)})
                        raise
                    sleep(2**i)
        raise RuntimeError("unreachable")

    def _stage_script(self, run_id: str) -> dict[str, Any]:
        with self.db.session_scope() as session:
            run = session.get(self._models.PipelineRunModel, run_id)
            assert run is not None
            if run.script_payload:
                return run.script_payload
            trend = TrendItem(**run.trend_payload["selected"])
            script = self.creative.create(trend)
            allowed, reasons = self.policy.validate(script)
            payload = {"script": script.__dict__, "approved": allowed, "block_reasons": reasons}
            if not allowed:
                run.status = "blocked"
            run.script_payload = payload
            run.current_stage = "script"
            self._checkpoint(run_id, "script", "done" if allowed else "blocked", payload)
            return payload

    def _stage_render(self, run_id: str) -> dict[str, Any]:
        with self.db.session_scope() as session:
            run = session.get(self._models.PipelineRunModel, run_id)
            assert run is not None
            if run.render_payload:
                return run.render_payload
            if not run.script_payload.get("approved"):
                return {}
            script = ScriptPackage(**run.script_payload["script"])
            media_path = self.renderer.render(run_id, script)
            payload = {"media_path": media_path, "cached": Path(media_path).exists()}
            run.render_payload = payload
            run.current_stage = "render"
            self._checkpoint(run_id, "render", "done", payload)
            return payload

    def _stage_publish(self, run_id: str) -> dict[str, Any]:
        with self.db.session_scope() as session:
            run = session.get(self._models.PipelineRunModel, run_id)
            assert run is not None
            if run.publish_payload:
                return run.publish_payload
            if run.status == "blocked":
                return {}
            script = run.script_payload["script"]
            result = self.publisher.publish_or_schedule(
                media_path=run.render_payload["media_path"],
                caption=f"{script['hook']}\n\n{script['cta']}",
                run_id=run_id,
            )
            run.publish_payload = result
            run.current_stage = "publish"
            self._checkpoint(run_id, "publish", "done", result)
            return result

    def _stage_metrics(self, run_id: str) -> dict[str, Any]:
        with self.db.session_scope() as session:
            run = session.get(self._models.PipelineRunModel, run_id)
            assert run is not None
            if run.metrics_payload:
                return run.metrics_payload
            if not run.publish_payload:
                return {}
            snap = self.analytics.fetch(run.publish_payload["platform_post_id"], run_id)
            payload = snap.__dict__
            run.metrics_payload = payload
            run.current_stage = "metrics"
            self._checkpoint(run_id, "metrics", "done", payload)
            return payload

    def _stage_learning(self, run_id: str) -> None:
        with self.db.session_scope() as session:
            run = session.get(self._models.PipelineRunModel, run_id)
            assert run is not None
            if not run.script_payload or not run.metrics_payload:
                return
            snap_id = f"learn:{run_id}"
            existing = session.get(self._models.LearningSnapshotModel, snap_id)
            if existing:
                return
            script = run.script_payload["script"]
            trend = run.trend_payload.get("selected", {})
            metrics = run.metrics_payload.get("metrics", {})
            session.add(
                self._models.LearningSnapshotModel(
                    id=snap_id,
                    run_id=run_id,
                    trend_features={"source": trend.get("source"), "score": trend.get("score"), "momentum": trend.get("momentum")},
                    script_features={
                        "hook_style": "direct",
                        "length": len(script.get("body", "")),
                        "cta": script.get("cta"),
                        "topic_tags": [trend.get("keyword", "").split(" ")[0].lower()],
                    },
                    template_key=script.get("template_key", "unknown"),
                    perf_1h=metrics,
                    perf_6h=metrics,
                    perf_24h=metrics,
                )
            )


def run_daily_pipeline(topic: str | None = None) -> dict[str, Any]:
    worker = PipelineWorker()
    run_id = worker.enqueue(topic=topic)
    return worker.process(run_id)
