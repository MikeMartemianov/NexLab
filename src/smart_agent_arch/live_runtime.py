from __future__ import annotations

import json
import re
from typing import Any

from smart_agent_arch.config_loader import ConfigLoader, FullConfig
from smart_agent_arch.deep_thinker_ai import ThinkerOutcome
from smart_agent_arch.mentor_ai import MentorReview
from smart_agent_arch.model_provider import ModelResolver
from smart_agent_arch.user_api import InputEnvelope, RuntimeResponse


class LiveRuntimeGateway:
    """Live runtime gateway that connects to the actual model provider."""

    def send(
        self,
        envelope: InputEnvelope,
        config: dict[str, Any] | FullConfig,
        runtime_context: dict[str, Any],
    ) -> RuntimeResponse:
        full_config = config if isinstance(config, FullConfig) else ConfigLoader.from_dict(config)
        provider = ModelResolver.resolve(full_config)

        system_prompt = str(runtime_context.get("system_prompt", ""))

        # Build context prompt
        events = runtime_context.get("event_cache", [])
        events_text = "\n".join([f"- [{e.get('kind', 'log')}] (Repeats: {e.get('repeats', 1)}): {e.get('summary', '')}" for e in events[-15:]])
        
        mentor_fb = "\n".join([f"- {fb}" for fb in runtime_context.get("mentor_feedback", [])[-5:]])
        hints = "\n".join([f"- {h}" for hint_pack in runtime_context.get("fast_memory_hints", [])[-3:] for h in hint_pack.get("memories", [])])

        prompt = f"Recent Context Events:\n{events_text}\n"
        if mentor_fb:
            prompt += f"\nMentor Feedback to heed:\n{mentor_fb}\n"
        if hints:
            prompt += f"\nDeep Memory Hints:\n{hints}\n"

        prompt += f"\nUser Input ({envelope.media_type}):\n{envelope.payload}"

        try:
            # We use complete_sync since we are running in a dedicated thread inside the UserAIFacade loop
            content = provider.complete_sync(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=full_config.model_behavior.temperature,
                top_p=full_config.model_behavior.top_p,
            )
            return RuntimeResponse(
                status="completed", 
                content=content.strip(), 
                metadata={"media_type": envelope.media_type, "provider": full_config.model_provider.provider}
            )
        except Exception as e:
            msg = str(e)
            if "404" in msg:
                msg += " (Hint: Double check if 'provider' matches your 'base_url'. Cerebras/Groq/etc. use 'openai' provider, not 'ollama')"
            return RuntimeResponse(
                status="error", 
                content=f"Model Gateway Error: {msg}", 
                metadata={"error": msg, "media_type": envelope.media_type}
            )


class LiveMentorGateway:
    """Mentor AI that observes the Runtime context and emits coaching feedback."""

    def __init__(self, full_config: FullConfig) -> None:
        override = None
        if full_config.mentor_config and full_config.mentor_config.model_provider_override:
            from smart_agent_arch.config_loader import ModelProviderConfig
            override = ModelProviderConfig(**full_config.mentor_config.model_provider_override)
        self._provider = ModelResolver.resolve(full_config, override=override)

    def review(self, runtime_context: dict[str, Any]) -> MentorReview | None:
        events = runtime_context.get("event_cache", [])
        if not events:
            return None

        system_prompt = (
            "You are a Mentor AI silently observing a main AI agent inside a system runtime. "
            "Analyze the last few events and provide concise, constructive feedback or assign a background task. "
            "If you notice repetitive CLI commands or Python routines, you can synthesize a new Tool "
            "for the main AI to use. Output STRICTLY in JSON format:\n"
            "{\n  \"feedback\": \"Your brief advice or null\",\n"
            "  \"pause_self\": false,\n"
            "  \"assign_thinker_task\": \"A problem to ponder or null\",\n"
            "  \"synthesize_tool\": {\n"
            "    \"name\": \"function_name\",\n"
            "    \"pattern\": \"RUN_FUNCTION_NAME arg1=(?P<arg1>\\\\w+)\",\n"
            "    \"triggers\": [\"RUN_FUNCTION_NAME\"],\n"
            "    \"casts\": {\"arg1\": \"str\"},\n"
            "    \"arg_descriptions\": {\"arg1\": \"desc\"},\n"
            "    \"output_description\": \"what it returns\",\n"
            "    \"description\": \"purpose\",\n"
            "    \"code\": \"def function_name(arg1):\\n    return arg1\"\n"
            "  } // or null\n"
            "}"
        )

        events_text = "\n".join([f"- [{e.get('kind', 'log')}]: {e.get('summary', '')}" for e in events[-20:]])
        prompt = f"Recent System Events:\n{events_text}\n\nProvide JSON review:"

        try:
            content = self._provider.complete_sync(prompt=prompt, system_prompt=system_prompt, temperature=0.3)
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return MentorReview(
                    feedback=data.get("feedback"),
                    pause_self=bool(data.get("pause_self", False)),
                    assign_thinker_task=data.get("assign_thinker_task"),
                    synthesize_tool=data.get("synthesize_tool")
                )
        except Exception:
            pass
        return None


class LiveDeepThinkerGateway:
    """Deep Thinker AI that solves complex assigned tasks with chain-of-thought."""

    def __init__(self, full_config: FullConfig) -> None:
        override = None
        if full_config.deep_thinker_config and full_config.deep_thinker_config.model_provider_override:
            from smart_agent_arch.config_loader import ModelProviderConfig
            override = ModelProviderConfig(**full_config.deep_thinker_config.model_provider_override)
        self._provider = ModelResolver.resolve(full_config, override=override)

    def think(self, task_text: str, runtime_context: dict[str, Any]) -> ThinkerOutcome | None:
        system_prompt = (
            "You are a Deep Thinker AI assigned a complex background task. "
            "Analyze the task deeply, provide step-by-step reasoning. "
            "If you have solved the task and verified it, set \"solved\" and \"verified\" to true in your JSON output. "
            "Output STRICTLY in JSON format:\n"
            "{\n  \"solved\": true/false,\n  \"verified\": true/false,\n"
            "  \"insight\": \"Your final verified solution or current chain of thought\",\n"
            "  \"pause_self\": false\n}"
        )

        prompt = f"Background Task:\n{task_text}\n\nProvide JSON thinking update:"

        try:
            content = self._provider.complete_sync(prompt=prompt, system_prompt=system_prompt, temperature=0.5)
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return ThinkerOutcome(
                    solved=bool(data.get("solved", False)),
                    verified=bool(data.get("verified", False)),
                    insight=data.get("insight"),
                    pause_self=bool(data.get("pause_self", False))
                )
        except Exception:
            pass
        return None
