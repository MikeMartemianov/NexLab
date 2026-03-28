import time
from pathlib import Path

import pytest

from smart_agent_arch import initialize_ai
from smart_agent_arch.deep_thinker_ai import ThinkerOutcome
from smart_agent_arch.exceptions import ConfigurationError
from smart_agent_arch.mentor_ai import MentorReview
from smart_agent_arch.user_api import InputEnvelope, RuntimeResponse, UserAIFacade


class RecorderRuntime:
    def __init__(self) -> None:
        self.envelopes: list[InputEnvelope] = []
        self.contexts: list[dict[str, object]] = []

    def send(
        self,
        envelope: InputEnvelope,
        config: dict[str, object],
        runtime_context: dict[str, object],
    ) -> RuntimeResponse:
        del config
        self.envelopes.append(envelope)
        self.contexts.append(runtime_context)
        return RuntimeResponse(status="ok", metadata={"media_type": envelope.media_type})


class ScriptRuntime:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = outputs
        self.envelopes: list[InputEnvelope] = []
        self.contexts: list[dict[str, object]] = []

    def send(
        self,
        envelope: InputEnvelope,
        config: dict[str, object],
        runtime_context: dict[str, object],
    ) -> RuntimeResponse:
        del config
        self.envelopes.append(envelope)
        self.contexts.append(runtime_context)
        if self.outputs:
            return RuntimeResponse(status="ok", content=self.outputs.pop(0), metadata={})
        return RuntimeResponse(status="ok", content="", metadata={})


class ScriptMentorRuntime:
    def __init__(self, reviews: list[MentorReview | None]) -> None:
        self.reviews = reviews
        self.contexts: list[dict[str, object]] = []

    def review(self, runtime_context: dict[str, object]) -> MentorReview | None:
        self.contexts.append(runtime_context)
        if self.reviews:
            return self.reviews.pop(0)
        return None


class ScriptThinkerRuntime:
    def __init__(self, outcomes: list[ThinkerOutcome | None]) -> None:
        self.outcomes = outcomes
        self.calls = 0

    def think(self, task_text: str, runtime_context: dict[str, object]) -> ThinkerOutcome | None:
        import time
        time.sleep(0.15)
        del task_text, runtime_context
        self.calls += 1
        if self.outcomes:
            return self.outcomes.pop(0)
        return None


def test_initialize_ai_accepts_config_dict() -> None:
    ai = initialize_ai({"model": "demo"})
    assert isinstance(ai, UserAIFacade)


def test_initialize_ai_rejects_empty_dict() -> None:
    with pytest.raises(ConfigurationError):
        initialize_ai({})


def test_send_text_image_video_forwarded_to_runtime() -> None:
    runtime = RecorderRuntime()
    ai = UserAIFacade(config={"model": "demo"}, runtime_gateway=runtime)

    ai.send_text("hello")
    ai.send_image(b"img-bytes")
    ai.send_video("video.mp4")

    assert [e.media_type for e in runtime.envelopes] == ["text", "image", "video"]
    assert runtime.envelopes[0].payload == "hello"
    assert runtime.envelopes[1].payload == b"img-bytes"
    assert runtime.envelopes[2].payload == "video.mp4"


def test_pause_and_stop_are_stubs() -> None:
    ai = initialize_ai({"model": "demo"})

    pause_result = ai.pause()
    stop_result = ai.stop()

    assert pause_result.implemented is True
    assert stop_result.implemented is True
    assert pause_result.action == "pause"
    assert stop_result.action == "stop"


def test_runtime_context_contains_current_time_and_event_cache() -> None:
    runtime = RecorderRuntime()
    ai = UserAIFacade(config={"model": "demo"}, runtime_gateway=runtime)

    ai.send_text("hello")

    context = runtime.contexts[0]
    assert "current_time" in context
    assert "event_cache" in context
    assert "long_memory" in context
    assert "user_preferences" in context
    assert "knowledge" in context
    assert "runtime_state" in context
    assert "agent_contract" in context
    assert "command_parser" in context
    assert "system_prompt" in context
    assert isinstance(context["event_cache"], list)
    assert len(context["event_cache"]) >= 2


def test_agent_contract_requires_fast_tool_only_execution() -> None:
    ai = initialize_ai({"model": "demo"})

    contract = ai.runtime_context()["agent_contract"]
    assert contract["command_execution"]["enabled"] is True
    assert contract["command_execution"]["optional"] is True
    assert contract["speed_priority"] == "max"
    assert contract["response_mode"] == "direct"
    assert contract["internal_thought_style"] == "brief"
    assert contract["user_output_channel"] == "direct"


def test_repetitive_ai_events_are_compacted() -> None:
    ai = initialize_ai({"model": "demo"})

    ai.append_ai_events([
        {"kind": "log", "summary": "heartbeat"},
        {"kind": "log", "summary": "heartbeat"},
        {"kind": "log", "summary": "heartbeat"},
    ])

    cache = ai.runtime_context()["event_cache"]
    compacted = [item for item in cache if item["kind"] == "log" and item["summary"] == "heartbeat"]
    assert len(compacted) == 1
    assert compacted[0]["repeats"] == 3


def test_long_memory_keeps_only_important_items() -> None:
    ai = initialize_ai({"model": "demo"})

    added = ai.append_ai_memories([
        {"summary": "Critical user preference", "importance": 0.95, "source": "ai"},
        {"summary": "Low signal debug note", "importance": 0.3, "source": "ai"},
    ])

    assert added == 1
    context = ai.runtime_context()
    summaries = [item["summary"] for item in context["long_memory"]]
    assert "Critical user preference" in summaries
    assert "Low signal debug note" not in summaries


def test_stop_interrupts_until_start_is_called() -> None:
    runtime = RecorderRuntime()
    ai = UserAIFacade(config={"model": "demo"}, runtime_gateway=runtime, tick_interval_sec=0.05)

    ai.stop()
    blocked = ai.send_text("hello while stopped")

    assert blocked.status == "stopped"
    assert len(runtime.envelopes) == 0

    ai.start()
    resumed = ai.send_text("hello after start")

    assert resumed.status == "ok"
    assert len(runtime.envelopes) == 1


def test_pause_auto_resumes_on_next_input() -> None:
    runtime = RecorderRuntime()
    ai = UserAIFacade(config={"model": "demo"}, runtime_gateway=runtime, tick_interval_sec=0.05)

    ai.pause()
    paused_context = ai.runtime_context()
    paused_state = paused_context["runtime_state"]
    assert paused_state == "paused"
    assert paused_context["mentor_state"] == "paused"

    response = ai.send_text("resume me")
    assert response.status == "ok"
    resumed_context = ai.runtime_context()
    assert resumed_context["runtime_state"] == "running"
    assert resumed_context["mentor_state"] == "running"


def test_background_cycle_runs_after_start_every_second_like_interval() -> None:
    ai = UserAIFacade(config={"model": "demo"}, tick_interval_sec=0.05)
    ai.stop()
    ai.start()

    time.sleep(0.16)
    ticks = [
        item for item in ai.runtime_context()["event_cache"]
        if item["kind"] == "tick" and item["summary"] == "Background cycle executed"
    ]

    assert len(ticks) >= 1


def test_user_preferences_are_saved_to_long_memory() -> None:
    ai = initialize_ai({"model": "demo"})

    added = ai.append_user_preferences([
        {"summary": "User prefers concise responses", "importance": 0.9},
        {"summary": "Low-priority preference", "importance": 0.2},
    ])

    assert added == 1
    context = ai.runtime_context()
    preferences = context["user_preferences"]
    assert len(preferences) == 1
    assert preferences[0]["summary"] == "User prefers concise responses"


def test_knowledge_items_are_saved_to_long_memory() -> None:
    ai = initialize_ai({"model": "demo"})

    added = ai.append_knowledge([
        {"summary": "Project uses UTC timestamps", "importance": 0.85},
        {"summary": "Unimportant note", "importance": 0.1},
    ])

    assert added == 1
    context = ai.runtime_context()
    knowledge = context["knowledge"]
    assert len(knowledge) == 1
    assert knowledge[0]["summary"] == "Project uses UTC timestamps"


def test_mentor_feedback_is_visible_to_first_ai_and_cached() -> None:
    mentor = ScriptMentorRuntime([MentorReview(feedback="Use shorter tool path")])
    ai = UserAIFacade(
        config={"model": "demo"},
        mentor_gateway=mentor,
        mentor_interval_sec=0.05,
    )

    time.sleep(0.12)
    context = ai.runtime_context()

    assert context["mentor_state"] in {"running", "paused"}
    assert any("Use shorter tool path" in item for item in context["mentor_feedback"])
    mentor_events = [item for item in context["event_cache"] if item["kind"] == "mentor"]
    assert len(mentor_events) >= 1


def test_mentor_can_pause_itself() -> None:
    mentor = ScriptMentorRuntime([MentorReview(feedback="Pausing self", pause_self=True)])
    ai = UserAIFacade(
        config={"model": "demo"},
        mentor_gateway=mentor,
        mentor_interval_sec=0.05,
    )

    time.sleep(0.12)
    assert ai.runtime_context()["mentor_state"] == "paused"


def test_stop_promotes_mentor_insights_to_long_memory() -> None:
    mentor = ScriptMentorRuntime([MentorReview(feedback="Remember to validate edge cases")])
    ai = UserAIFacade(
        config={"model": "demo"},
        mentor_gateway=mentor,
        mentor_interval_sec=0.05,
    )

    time.sleep(0.12)
    ai.stop()
    context = ai.runtime_context()

    assert context["runtime_state"] == "stopped"
    assert context["mentor_state"] == "stopped"
    knowledge_summaries = [item["summary"] for item in context["knowledge"]]
    assert any("AI Knowledge/Insight: Remember to validate edge cases" in x for x in knowledge_summaries)


def test_start_restores_all_components_to_running() -> None:
    ai = UserAIFacade(config={"model": "demo"}, mentor_interval_sec=0.05)

    ai.pause()
    paused = ai.runtime_context()
    assert paused["runtime_state"] == "paused"
    assert paused["mentor_state"] == "paused"

    ai.start()
    running = ai.runtime_context()
    assert running["runtime_state"] == "running"
    assert running["mentor_state"] == "running"
    assert running["deep_thinker_state"] == "running"


def test_direct_model_response_is_returned_to_user() -> None:
    runtime = ScriptRuntime(["This is full AI response for user"])
    ai = UserAIFacade(config={"model": "demo"}, runtime_gateway=runtime)

    response = ai.send_text("hello")
    assert response.content == "This is full AI response for user"


def test_command_parser_executes_function_and_returns_second_pass_answer(tmp_path: Path) -> None:
    fn_file = tmp_path / "user_commands.py"
    fn_file.write_text(
        "def sum_numbers(a, b):\n"
        "    return a + b\n",
        encoding="utf-8",
    )

    config = {
        "model": "demo",
        "command_parser": {
            "enabled": True,
            "commands": [
                {
                    "name": "sum",
                    "triggers": ["RUN_SUM"],
                    "pattern": r"RUN_SUM a=(?P<a>\d+) b=(?P<b>\d+)",
                    "casts": {"a": "int", "b": "int"},
                    "arg_descriptions": {
                        "a": "First integer value",
                        "b": "Second integer value",
                    },
                    "output_description": "Returns integer sum of a and b",
                    "function": {
                        "file": str(fn_file),
                        "name": "sum_numbers",
                    },
                    "description": "Adds two integers",
                }
            ],
        },
        "max_command_hops": 1,
    }

    runtime = ScriptRuntime([
        "RUN_SUM a=2 b=3",
        "Final answer: 5",
    ])
    ai = UserAIFacade(config=config, runtime_gateway=runtime)

    response = ai.send_text("calculate")

    assert response.content == "Final answer: 5"
    assert len(runtime.envelopes) == 2
    assert "Result: 5" in str(runtime.envelopes[1].payload)
    system_prompt = str(runtime.contexts[0]["system_prompt"])
    assert "RUN_SUM a=(?P<a>\\d+) b=(?P<b>\\d+)" in system_prompt
    assert "a (int): First integer value" in system_prompt
    assert "b (int): Second integer value" in system_prompt
    assert "function_output: Returns integer sum of a and b" in system_prompt


def test_mentor_can_assign_deep_task_and_solution_goes_to_long_memory() -> None:
    mentor = ScriptMentorRuntime([
        MentorReview(assign_thinker_task="Prove and verify best path for workflow")
    ])
    thinker = ScriptThinkerRuntime([
        ThinkerOutcome(solved=False, verified=False),
        ThinkerOutcome(solved=True, verified=True, insight="Use two-phase validation path"),
    ])
    ai = UserAIFacade(
        config={"model": "demo"},
        mentor_gateway=mentor,
        thinker_gateway=thinker,
        mentor_interval_sec=0.05,
    )

    time.sleep(0.25)
    context = ai.runtime_context()
    summaries = [item["summary"] for item in context["long_memory"]]

    assert any("Deep thinker solution: Use two-phase validation path" in s for s in summaries)
    assert context["deep_thinker_task"]["has_task"] is False
    assert any("Executed tool: write_long_memory" in x["summary"] for x in context["event_cache"] if x["kind"] == "tool")


def test_deep_thinker_persists_after_stop_until_task_done() -> None:
    thinker = ScriptThinkerRuntime([
        ThinkerOutcome(solved=False, verified=False),
        ThinkerOutcome(solved=False, verified=False),
        ThinkerOutcome(solved=True, verified=True, insight="Final verified deep solution"),
    ])
    ai = UserAIFacade(
        config={"model": "demo"},
        thinker_gateway=thinker,
        mentor_interval_sec=0.05,
    )

    ai.submit_deep_task("Solve hard architecture issue", source="manual")
    ai.stop()

    time.sleep(0.3)
    context = ai.runtime_context()
    summaries = [item["summary"] for item in context["long_memory"]]

    assert context["runtime_state"] == "stopped"
    assert context["deep_thinker_state"] in {"running", "paused"}
    assert thinker.calls >= 2
    assert any("Deep thinker solution: Final verified deep solution" in s for s in summaries)


def test_fast_memory_assist_injects_related_memory_hint_for_first_ai() -> None:
    runtime = RecorderRuntime()
    ai = UserAIFacade(config={"model": "demo"}, runtime_gateway=runtime)
    ai.append_ai_memories([
        {
            "summary": "Use two-phase validation path for architecture migrations",
            "importance": 0.95,
            "source": "knowledge-base",
        }
    ])

    ai.send_text("Need a validation path for architecture updates")
    context = runtime.contexts[-1]

    hints = context["fast_memory_hints"]
    assert len(hints) >= 1
    assert any("two-phase validation path" in h["memories"][0]["summary"].lower() for h in hints)
    assert any(item["kind"] == "fast_memory" for item in context["event_cache"])


def test_fast_memory_assist_restores_component_states_after_pause() -> None:
    mentor = ScriptMentorRuntime([])
    thinker = ScriptThinkerRuntime([])
    ai = UserAIFacade(
        config={"model": "demo"},
        mentor_gateway=mentor,
        thinker_gateway=thinker,
        mentor_interval_sec=0.05,
    )
    ai.append_knowledge([
        {
            "summary": "Database schema migration checklist and rollback",
            "importance": 0.9,
        }
    ])

    before = ai.runtime_context()
    assert before["runtime_state"] == "running"
    assert before["mentor_state"] == "running"
    assert before["deep_thinker_state"] == "running"

    ai.submit_deep_task("Need schema migration checklist", source="manual")
    after = ai.runtime_context()

    assert after["runtime_state"] == "running"
    assert after["mentor_state"] == "running"
    assert after["deep_thinker_state"] == "running"
    assert len(after["fast_memory_hints"]) >= 1
