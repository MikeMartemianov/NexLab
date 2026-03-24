from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AgentContract:
    """Operational rules passed to model runtime on every cycle."""

    command_execution_enabled: bool = True
    command_execution_optional: bool = True
    response_mode: str = "direct"
    speed_priority: str = "max"
    internal_thought_style: str = "brief"
    user_output_channel: str = "direct"

    def to_context(self) -> dict[str, Any]:
        return {
            "command_execution": {
                "enabled": self.command_execution_enabled,
                "optional": self.command_execution_optional,
            },
            "response_mode": self.response_mode,
            "speed_priority": self.speed_priority,
            "internal_thought_style": self.internal_thought_style,
            "user_output_channel": self.user_output_channel,
            "policy_text": (
                "Return full final answer directly to the user. "
                "You may emit command words for parser execution when needed. "
                "Prefer fast execution and keep internal reasoning brief."
            ),
        }
