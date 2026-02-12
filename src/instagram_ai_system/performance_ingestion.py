from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .schema_validation import validate_payload

_REQUIRED_FIELDS = [
    "post_id",
    "observed_at",
    "window",
    "impressions",
    "plays",
    "avg_watch_time",
    "likes",
    "comments",
    "shares",
    "saves",
]


@dataclass(slots=True)
class IngestionResult:
    records: list[dict[str, Any]]
    errors: list[dict[str, Any]]
    summary: dict[str, int]


class PerformanceIngestionService:
    schema_path = "schemas/performance_ingestion_record.schema.json"

    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []

    def ingest_csv(self, csv_payload: str) -> IngestionResult:
        reader = csv.DictReader(io.StringIO(csv_payload))
        rows = list(reader)
        return self._ingest_rows(rows)

    def ingest_json(self, payload: list[dict[str, Any]]) -> IngestionResult:
        return self._ingest_rows(payload)

    def _ingest_rows(self, rows: list[dict[str, Any]]) -> IngestionResult:
        accepted: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []

        for row_num, row in enumerate(rows, start=1):
            try:
                normalized = self._normalize_row(row)
                validate_payload(normalized, self.schema_path)
                accepted.append(normalized)
                self._records.append(normalized)
            except Exception as exc:  # noqa: BLE001
                errors.append({"row": row_num, "post_id": row.get("post_id"), "error": str(exc)})

        return IngestionResult(
            records=accepted,
            errors=errors,
            summary={"processed": len(rows), "succeeded": len(accepted), "failed": len(errors)},
        )

    def query(self, post_id: str, start: datetime, end: datetime) -> list[dict[str, Any]]:
        return [
            record
            for record in self._records
            if record["post_id"] == post_id and start <= datetime.fromisoformat(record["observed_at"]) <= end
        ]

    def _normalize_row(self, row: dict[str, Any]) -> dict[str, Any]:
        missing = [field for field in _REQUIRED_FIELDS if row.get(field) in (None, "")]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        plays = int(row["plays"])
        shares = int(row["shares"])
        saves = int(row["saves"])
        likes = int(row["likes"])
        comments = int(row["comments"])
        watch_time = float(row["avg_watch_time"])
        engagement = likes + comments + shares + saves

        return {
            "post_id": str(row["post_id"]),
            "observed_at": datetime.fromisoformat(str(row["observed_at"])).isoformat(),
            "window": str(row["window"]),
            "impressions": int(row["impressions"]),
            "plays": plays,
            "avg_watch_time": watch_time,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "saves": saves,
            "follower_change": int(row.get("follower_change", 0)),
            "derived_metrics": {
                "engagement_rate": (engagement / plays) if plays else 0,
                "save_rate": (saves / plays) if plays else 0,
                "share_rate": (shares / plays) if plays else 0,
                "watch_through_estimate": min(1.0, watch_time / 30.0),
            },
            "kpi_label": "success" if plays and (shares / plays) >= 0.02 else "needs_iteration",
        }
