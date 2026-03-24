from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Literal, Protocol


@dataclass(slots=True)
class MentorReview:
    feedback: str | None = None
    pause_self: bool = False
    assign_thinker_task: str | None = None
    synthesize_tool: dict[str, Any] | None = None


class MentorGateway(Protocol):
    def review(self, runtime_context: dict[str, Any]) -> MentorReview | None:
        ...


class StubMentorGateway:
    def review(self, runtime_context: dict[str, Any]) -> MentorReview | None:
        del runtime_context
        return None


class MentorAIComponent:
    """Background mentor loop that reviews runtime context and emits coaching feedback."""

    def __init__(
        self,
        gateway: MentorGateway,
        context_provider: Callable[[], dict[str, Any]],
        feedback_callback: Callable[[str], None],
        task_callback: Callable[[str], None] | None = None,
        tool_callback: Callable[[dict[str, Any]], None] | None = None,
        interval_sec: float = 5.0,
    ) -> None:
        self._gateway = gateway
        self._context_provider = context_provider
        self._feedback_callback = feedback_callback
        self._task_callback = task_callback
        self._tool_callback = tool_callback
        self._interval_sec = max(0.05, float(interval_sec))
        self._state: Literal["running", "paused", "stopped"] = "running"
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    @property
    def state(self) -> Literal["running", "paused", "stopped"]:
        with self._lock:
            return self._state

    def start(self) -> None:
        with self._lock:
            self._state = "running"
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._loop,
                name="smart-agent-mentor-loop",
                daemon=True,
            )
            self._thread.start()

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

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            with self._lock:
                state = self._state
            if state == "stopped":
                return
            if state == "paused":
                time.sleep(0.05)
                continue

            context = self._context_provider()
            review = self._gateway.review(context)
            if review is not None:
                if review.feedback:
                    self._feedback_callback(review.feedback)
                if review.assign_thinker_task and self._task_callback is not None:
                    self._task_callback(review.assign_thinker_task)
                if review.synthesize_tool and self._tool_callback is not None:
                    self._tool_callback(review.synthesize_tool)
                if review.pause_self:
                    self.pause()

            time.sleep(self._interval_sec)
