from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .creativity_engine import CreativityEngine
from .models import ContentBrief, CreativityMode, TrendInsight


@dataclass(slots=True)
class FactoryRequest:
    niche: str
    persona: str
    creativity_mode: CreativityMode
    batch_size: int = 3


class ContentFactory:
    def __init__(self, creativity_engine: CreativityEngine):
        self.creativity_engine = creativity_engine

    def build_batch(self, request: FactoryRequest, trends: Iterable[TrendInsight]) -> List[ContentBrief]:
        trend_list = list(trends)
        return [
            self.creativity_engine.generate_brief(
                niche=request.niche,
                persona=request.persona,
                mode=request.creativity_mode,
                trend_insights=trend_list,
            )
            for _ in range(request.batch_size)
        ]
