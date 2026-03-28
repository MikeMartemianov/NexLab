from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class EventRecord:
    timestamp: str
    kind: str
    summary: str
    repeats: int = 1


class EventCache:
    """Compact event cache for model context, separate from full chat history."""

    def __init__(self, max_events: int = 100) -> None:
        self._max_events = max_events
        self._events: list[EventRecord] = []

    def add(self, kind: str, summary: str, at: datetime | None = None) -> None:
        event = EventRecord(
            timestamp=self._to_iso(at),
            kind=kind.strip() or "generic",
            summary=summary.strip() or "(empty summary)",
        )

        # Compress consecutive identical events to avoid noisy repetitive logs.
        if self._events and self._is_same_event(self._events[-1], event):
            last = self._events[-1]
            last.repeats += 1
            last.timestamp = event.timestamp
            return

        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events :]

    def add_many(self, events: list[dict[str, str]]) -> None:
        for item in events:
            self.add(kind=item.get("kind", "ai_event"), summary=item.get("summary", ""))

    def events(self) -> list[EventRecord]:
        return list(self._events)

    def build_model_context(self, now: datetime | None = None) -> dict[str, Any]:
        return {
            "current_time": self._to_iso(now),
            "event_cache": [
                {
                    "timestamp": event.timestamp,
                    "kind": event.kind,
                    "summary": event.summary,
                    "repeats": event.repeats,
                }
                for event in self._events
            ],
        }

    @staticmethod
    def _is_same_event(left: EventRecord, right: EventRecord) -> bool:
        return left.kind == right.kind and left.summary == right.summary

    @staticmethod
    def _to_iso(value: datetime | None) -> str:
        current = value or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        return current.astimezone(timezone.utc).isoformat()
