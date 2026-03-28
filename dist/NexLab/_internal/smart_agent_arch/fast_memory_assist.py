from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from smart_agent_arch.long_memory import MemoryRecord


@dataclass(slots=True)
class FastMemoryHit:
    summary: str
    source: str
    memory_type: str
    importance: float
    score: float


class FastMemoryAssist:
    """Very fast lexical matcher to inject relevant deep memories into active contexts."""

    def __init__(self, min_score: float = 0.34, limit: int = 3) -> None:
        self._min_score = min_score
        self._limit = limit

    def find_related(self, topic: str, memories: Iterable[MemoryRecord]) -> list[FastMemoryHit]:
        normalized_topic = topic.strip().lower()
        if not normalized_topic:
            return []

        topic_tokens = self._tokens(normalized_topic)
        if not topic_tokens:
            return []

        hits: list[FastMemoryHit] = []
        for item in memories:
            summary_text = item.summary.strip()
            if not summary_text:
                continue

            summary_norm = summary_text.lower()
            summary_tokens = self._tokens(summary_norm)
            if not summary_tokens:
                continue

            overlap = len(topic_tokens & summary_tokens)
            base = overlap / max(1, len(topic_tokens))
            bonus = 0.15 if normalized_topic in summary_norm or summary_norm in normalized_topic else 0.0
            score = min(1.0, base + bonus)
            if score < self._min_score:
                continue

            hits.append(
                FastMemoryHit(
                    summary=summary_text,
                    source=item.source,
                    memory_type=item.memory_type,
                    importance=item.importance,
                    score=score,
                )
            )

        hits.sort(key=lambda hit: (hit.score, hit.importance), reverse=True)
        return hits[: self._limit]

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[0-9A-Za-zА-Яа-я_]+", text)
            if len(token) >= 3
        }
