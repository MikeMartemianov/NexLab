from __future__ import annotations
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Protocol

class EventKind(Enum):
    ON_INPUT = auto()
    ON_TOOL_START = auto()
    ON_TOOL_END = auto()
    ON_RESPONSE = auto()
    ON_ERROR = auto()
    ON_MEMORY_ADD = auto()

class EventCallback(Protocol):
    def __call__(self, event_kind: EventKind, payload: Dict[str, Any]) -> None:
        ...

class HookManager:
    """Manages lifecycle hooks for the AI Agent."""
    
    def __init__(self):
        self._hooks: Dict[EventKind, List[Callable]] = {kind: [] for kind in EventKind}

    def register(self, kind: EventKind, callback: Callable):
        """Register a new callback for a specific event kind."""
        if kind in self._hooks:
            self._hooks[kind].append(callback)

    def trigger(self, kind: EventKind, payload: Dict[str, Any]):
        """Trigger all callbacks for a specific event kind."""
        for callback in self._hooks.get(kind, []):
            try:
                callback(kind, payload)
            except Exception as e:
                # We don't want hooks to break the main execution flow
                print(f"[Hook Error] Failed to execute {callback}: {e}")
