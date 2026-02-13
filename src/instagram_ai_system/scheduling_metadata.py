from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .contracts_envelope import extract_payload, wrap_payload
from .schema_validation import validate_payload

_ALLOWED_KPI_OBJECTIVES = {"reach", "saves", "shares", "watch-through"}


@dataclass(slots=True)
class SchedulingRequest:
    script_packages: list[dict]
    date_start: datetime
    date_end: datetime
    timezone: str
    cadence: str = "daily"


class SchedulingMetadataService:
    schema_path = "contracts/scheduling_metadata.schema.json"

    def generate(self, request: SchedulingRequest) -> dict:
        tz = ZoneInfo(request.timezone)
        if request.date_end <= request.date_start:
            raise ValueError("date_end must be after date_start")

        scheduled_items: list[dict] = []
        current = request.date_start.astimezone(tz)
        step = timedelta(days=1 if request.cadence == "daily" else 2)
        slot_labels = ["morning", "afternoon", "evening"]
        kpi_tags = sorted(_ALLOWED_KPI_OBJECTIVES)

        for idx, script_package in enumerate(request.script_packages):
            script = extract_payload(script_package)
            publish_dt = current + step * idx
            slot = slot_labels[idx % len(slot_labels)]
            item = {
                "schedule_id": f"schedule-{script['script_id']}",
                "script_id": script["script_id"],
                "publish_datetime": publish_dt.isoformat(),
                "timezone": request.timezone,
                "slot_label": slot,
                "kpi_objective": kpi_tags[idx % len(kpi_tags)],
                "platform_metadata": {
                    "caption": script["caption_variants"]["short"],
                    "hashtags": script["hashtags"],
                    "thumbnail_text": " / ".join(script["segments"][0]["on_screen_text"].split()[:3]),
                    "hook_text": script["segments"][0]["voiceover"],
                },
            }
            scheduled_items.append(item)

        payload = {"items": scheduled_items}
        enveloped_payload = wrap_payload(payload)
        validate_payload(enveloped_payload, self.schema_path)
        return enveloped_payload
