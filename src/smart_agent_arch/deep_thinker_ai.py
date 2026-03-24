from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Literal, Protocol


@dataclass(slots=True)
class ThinkerOutcome:
    solved: bool = False
    verified: bool = False
    insight: str | None = None
    pause_self: bool = False


@dataclass(slots=True)
class ThinkerTask:
    text: str
    source: str
    attempts: int = 0


class DeepThinkerGateway(Protocol):
    def think(self, task_text: str, runtime_context: dict[str, Any]) -> ThinkerOutcome | None:
        ...


class StubDeepThinkerGateway:
    def think(self, task_text: str, runtime_context: dict[str, Any]) -> ThinkerOutcome | None:
        del task_text, runtime_context
        return None


class DeepThinkerAIComponent:
    """Persistent background thinker for complex tasks until solved and verified."""

    def __init__(
        self,
        gateway: DeepThinkerGateway,
        context_provider: Callable[[], dict[str, Any]],
        insight_callback: Callable[[str], None],
    ) -> None:
        self._gateway = gateway
        self._context_provider = context_provider
        self._insight_callback = insight_callback
        self._state: Literal["running", "paused", "stopped"] = "running"
        self._task: ThinkerTask | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    @property
    def state(self) -> Literal["running", "paused", "stopped"]:
        with self._lock:
            return self._state

    def submit_task(self, task_text: str, source: str = "mentor") -> None:
        text = task_text.strip()
        if not text:
            return
        with self._lock:
            self._task = ThinkerTask(text=text, source=source)
            if self._state != "stopped":
                self._state = "running"
        self.start()

    def task_snapshot(self) -> dict[str, Any]:
        with self._lock:
            task = self._task
            if task is None:
                return {"has_task": False}
            return {
                "has_task": True,
                "text": task.text,
                "source": task.source,
                "attempts": task.attempts,
            }

    def start(self) -> None:
        old_thread: threading.Thread | None = None
        with self._lock:
            self._state = "running"
            if self._thread is not None and self._thread.is_alive() and not self._stop_event.is_set():
                return
            if self._thread is not None and self._thread.is_alive() and self._stop_event.is_set():
                old_thread = self._thread
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._loop,
                name="smart-agent-deep-thinker-loop",
                daemon=True,
            )
            self._thread.start()
        if old_thread is not None:
            old_thread.join(timeout=0.1)

    def pause(self) -> None:
        with self._lock:
            self._state = "paused"

    def resume(self) -> None:
        with self._lock:
            if self._state != "stopped":
                self._state = "running"

    def stop(self) -> None:
        with self._lock:
            self._state = "stopped"
        self._stop_event.set()

    def ensure_running_for_pending_task(self) -> None:
        with self._lock:
            has_pending = self._task is not None
            current_state = self._state
        if has_pending and current_state == "stopped":
            with self._lock:
                self._state = "running"
            self.start()

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            with self._lock:
                state = self._state
                task = self._task

            if state == "stopped":
                return
            if state == "paused":
                time.sleep(0.05)
                continue
            if task is None:
                time.sleep(0.05)
                continue

            with self._lock:
                if self._task is not None:
                    self._task.attempts += 1

            outcome = self._gateway.think(task.text, self._context_provider())
            if outcome is None:
                continue

            if outcome.pause_self:
                self.pause()
                continue

            if outcome.solved and outcome.verified:
                if outcome.insight:
                    self._insight_callback(outcome.insight)
                with self._lock:
                    self._task = None
                continue
