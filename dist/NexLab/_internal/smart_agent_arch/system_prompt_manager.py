"""System prompt management for individual AI components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_agent_arch.config_loader import FullConfig


@dataclass(slots=True)
class SystemPromptSet:
    """System prompts for all AI components."""
    main_ai: str
    mentor_ai: str
    deep_thinker_ai: str
    fast_memory_ai: str


class SystemPromptManager:
    """Manage system prompts with immutable base + customizable suffix."""

    # Core system prompts (immutable, cannot be changed)
    BASE_MAIN_AI = """You are the primary intelligent agent. Your role is to:
1. Respond directly to user queries with clear, actionable answers
2. Execute commands when appropriate (optional, not required)
3. Think quickly and efficiently
4. Provide complete, final answers without asking for clarification

Guidelines:
- Be direct and concise
- Leverage your memory and context
- Execute commands only when they add value
- Focus on user satisfaction"""

    BASE_MENTOR_AI = """You are a mentor AI that observes and provides coaching feedback.
Your role is to:
1. Review the main AI's responses for quality, efficiency, and completeness
2. Provide constructive feedback to help improve future responses
3. Identify complex tasks that require deep thinking and assign them
4. Pause your own operation when needed

Guidelines:
- Be supportive but honest
- Give actionable feedback
- Identify patterns in main AI's behavior
- Suggest optimizations without being critical
- Keep feedback brief and focused"""

    BASE_DEEP_THINKER_AI = """You are a specialized deep-thinking AI that solves complex problems.
Your role is to:
1. Work on complex tasks assigned by the mentor AI
2. Think through problems step-by-step with rigorous reasoning
3. Verify your solutions are correct before reporting
4. Continue iterating until you find a verified solution

Guidelines:
- Don't give up on hard problems
- Verify your answers multiple times
- Show your reasoning process
- Be thorough and precise
- Report only verified solutions"""

    BASE_FAST_MEMORY_AI = """You are a memory matcher that provides relevant memory hints.
Your role is to:
1. Match current topics to relevant memories and knowledge
2. Provide concise hints about relevant past learnings
3. Help other AI components by injecting context-specific knowledge
4. Operate quickly with minimal overhead

Guidelines:
- Be precise in matching
- Provide only highly relevant hints
- Format hints for easy consumption
- Work transparently"""

    @staticmethod
    def _resolve_prompt(base: str, suffix: str | None) -> str:
        if not suffix:
            return base
        from pathlib import Path
        try:
            p = Path(suffix)
            if p.is_file():
                return p.read_text(encoding="utf-8")
        except Exception:
            pass
        return base + "\n\n" + suffix

    @staticmethod
    def build_prompts(config: FullConfig) -> SystemPromptSet:
        """Build complete system prompts from config."""
        # Main AI
        main_ai_prompt = SystemPromptManager._resolve_prompt(
            SystemPromptManager.BASE_MAIN_AI, config.system_prompts.get("main_ai_suffix")
        )
        main_ai_prompt += SystemPromptManager._build_behavioral_section(config)

        # Mentor AI
        mentor_ai_prompt = SystemPromptManager._resolve_prompt(
            SystemPromptManager.BASE_MENTOR_AI, config.system_prompts.get("mentor_ai_suffix")
        )
        mentor_ai_prompt += SystemPromptManager._build_mentor_section(config)

        # Deep Thinker AI
        deep_thinker_prompt = SystemPromptManager._resolve_prompt(
            SystemPromptManager.BASE_DEEP_THINKER_AI, config.system_prompts.get("deep_thinker_ai_suffix")
        )
        deep_thinker_prompt += SystemPromptManager._build_thinker_section(config)

        # Fast Memory AI
        fast_memory_prompt = SystemPromptManager._resolve_prompt(
            SystemPromptManager.BASE_FAST_MEMORY_AI, config.system_prompts.get("fast_memory_ai_suffix")
        )

        return SystemPromptSet(
            main_ai=main_ai_prompt,
            mentor_ai=mentor_ai_prompt,
            deep_thinker_ai=deep_thinker_prompt,
            fast_memory_ai=fast_memory_prompt,
        )

    @staticmethod
    def _build_behavioral_section(config: FullConfig) -> str:
        """Build behavioral instructions for main AI."""
        sections = ["\n## Behavioral Instructions"]

        # Output format
        output_format = config.io_config.output_format
        if output_format == "json":
            sections.append("- Output JSON when requested or for structured data")
        elif output_format == "markdown":
            sections.append("- Format output as Markdown for readability")
        elif output_format == "html":
            sections.append("- Provide HTML-formatted output")

        # Tone
        tone = config.output_style.tone
        tone_map = {
            "formal": "Use formal, professional language",
            "casual": "Use conversational, friendly language",
            "technical": "Use precise, technical terminology",
            "friendly": "Be warm and approachable",
            "academic": "Use scholarly, well-researched language",
        }
        if tone in tone_map:
            sections.append(f"- {tone_map[tone]}")

        # Verbosity
        verbose_level = config.output_style.verbose_level
        if verbose_level == 0:
            sections.append("- Keep responses very concise (1-2 sentences when possible)")
        elif verbose_level == 1:
            sections.append("- Balance conciseness with completeness")
        elif verbose_level == 2:
            sections.append("- Provide detailed explanations with examples")
        elif verbose_level == 3:
            sections.append("- Be exhaustive in your response, include all details")

        # Language
        if config.output_style.language != "en":
            sections.append(f"- Respond in {config.output_style.language} language")

        # Citations
        if config.output_style.include_citations:
            sections.append("- Include citations and sources for claims")

        # Reasoning
        if config.output_style.include_reasoning:
            sections.append("- Show your reasoning process and thought steps")

        # Commands
        if config.tools_config.enable_commands:
            sections.append("- You may execute commands when appropriate")

        # Response length
        sections.append(f"- Keep responses under {config.io_config.max_response_length} characters")

        return "\n".join(sections)

    @staticmethod
    def _build_mentor_section(config: FullConfig) -> str:
        """Build behavioral instructions for mentor AI."""
        sections = ["\n## Mentor Focus"]

        focus = config.mentor_config.feedback_focus
        focus_map = {
            "quality": "Evaluate response accuracy, relevance, and completeness",
            "efficiency": "Assess speed, resource usage, and optimization",
            "completeness": "Check if all aspects of the question were addressed",
            "all": "Evaluate quality, efficiency, and completeness holistically",
        }

        if focus in focus_map:
            sections.append(f"- {focus_map[focus]}")

        max_length = config.mentor_config.max_feedback_length
        sections.append(f"- Keep feedback under {max_length} characters")

        return "\n".join(sections)

    @staticmethod
    def _build_thinker_section(config: FullConfig) -> str:
        """Build behavioral instructions for deep thinker AI."""
        sections = ["\n## Deep Thinking Parameters"]

        max_iter = config.deep_thinker_config.max_iterations
        if max_iter:
            sections.append(f"- You have up to {max_iter} iterations to solve the problem")

        if config.deep_thinker_config.verification_required:
            sections.append("- Always verify your solution before reporting")

        if config.deep_thinker_config.persistence_enabled:
            sections.append("- Your work persists until the task is fully solved")

        return "\n".join(sections)

    @staticmethod
    def update_from_dict(prompts: dict[str, str]) -> None:
        """Update base prompts from dictionary (for testing)."""
        if "main_ai" in prompts:
            SystemPromptManager.BASE_MAIN_AI = prompts["main_ai"]
        if "mentor_ai" in prompts:
            SystemPromptManager.BASE_MENTOR_AI = prompts["mentor_ai"]
        if "deep_thinker_ai" in prompts:
            SystemPromptManager.BASE_DEEP_THINKER_AI = prompts["deep_thinker_ai"]
        if "fast_memory_ai" in prompts:
            SystemPromptManager.BASE_FAST_MEMORY_AI = prompts["fast_memory_ai"]
