from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

MemoryType = str


@dataclass(slots=True)
class MemoryRecord:
    timestamp: str
    summary: str
    importance: float
    source: str
    memory_type: MemoryType


class LongMemory:
    """Stores only important memories and keeps them ranked for model context."""

    def __init__(self, max_items: int = 100, importance_threshold: float = 0.6) -> None:
        self._max_items = max_items
        self._threshold = importance_threshold
        self._items: list[MemoryRecord] = []

    def add(self, summary: str, importance: float, source: str = "ai", at: datetime | None = None) -> bool:
        return self.add_typed(
            summary=summary,
            importance=importance,
            source=source,
            memory_type="memory",
            at=at,
        )

    def add_typed(
        self,
        summary: str,
        importance: float,
        source: str = "ai",
        memory_type: MemoryType = "memory",
        at: datetime | None = None,
    ) -> bool:
        text = summary.strip()
        if not text:
            return False
        score = max(0.0, min(1.0, float(importance)))
        if score < self._threshold:
            return False

        record = MemoryRecord(
            timestamp=self._to_iso(at),
            summary=text,
            importance=score,
            source=source.strip() or "ai",
            memory_type=memory_type.strip() or "memory",
        )
        self._items.append(record)
        self._sort_and_trim()
        return True

    def add_many(self, memories: list[dict[str, Any]]) -> int:
        added = 0
        for item in memories:
            if self.add_typed(
                summary=str(item.get("summary", "")),
                importance=float(item.get("importance", 0.0)),
                source=str(item.get("source", "ai")),
                memory_type=str(item.get("memory_type", "memory")),
            ):
                added += 1
        return added

    def add_preferences(self, preferences: list[dict[str, Any]]) -> int:
        added = 0
        for item in preferences:
            if self.add_typed(
                summary=str(item.get("summary", "")),
                importance=float(item.get("importance", 0.0)),
                source=str(item.get("source", "user")),
                memory_type="preference",
            ):
                added += 1
        return added

    def add_knowledge(self, knowledge_items: list[dict[str, Any]]) -> int:
        added = 0
        for item in knowledge_items:
            if self.add_typed(
                summary=str(item.get("summary", "")),
                importance=float(item.get("importance", 0.0)),
                source=str(item.get("source", "knowledge")),
                memory_type="knowledge",
            ):
                added += 1
        return added

    def items(self) -> list[MemoryRecord]:
        return list(self._items)

    def build_context(self, now: datetime | None = None, limit: int = 20) -> dict[str, Any]:
        selected = self._items[:limit]
        return {
            "current_time": self._to_iso(now),
            "long_memory": [
                {
                    "timestamp": item.timestamp,
                    "summary": item.summary,
                    "importance": item.importance,
                    "source": item.source,
                    "memory_type": item.memory_type,
                }
                for item in selected
            ],
            "user_preferences": [
                {
                    "timestamp": item.timestamp,
                    "summary": item.summary,
                    "importance": item.importance,
                    "source": item.source,
                }
                for item in selected
                if item.memory_type == "preference"
            ],
            "knowledge": [
                {
                    "timestamp": item.timestamp,
                    "summary": item.summary,
                    "importance": item.importance,
                    "source": item.source,
                }
                for item in selected
                if item.memory_type == "knowledge"
            ],
        }

    def _sort_and_trim(self) -> None:
        # Primary sort by importance, secondary by recency via ISO timestamp.
        self._items.sort(key=lambda item: (item.importance, item.timestamp), reverse=True)
        if len(self._items) > self._max_items:
            self._items = self._items[: self._max_items]

    @staticmethod
    def _to_iso(value: datetime | None) -> str:
        current = value or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        return current.astimezone(timezone.utc).isoformat()
