from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Protocol, Callable

from smart_agent_arch.agent_contract import AgentContract
from smart_agent_arch.command_parser import ConfigCommandParser
from smart_agent_arch.config_loader import ConfigLoader, FullConfig
from smart_agent_arch.deep_thinker_ai import DeepThinkerAIComponent, DeepThinkerGateway, StubDeepThinkerGateway
from smart_agent_arch.event_cache import EventCache
from smart_agent_arch.exceptions import ConfigurationError
from smart_agent_arch.fast_memory_assist import FastMemoryAssist
from smart_agent_arch.long_memory import LongMemory
from smart_agent_arch.mentor_ai import MentorAIComponent, MentorGateway, StubMentorGateway
from smart_agent_arch.system_prompt_manager import SystemPromptManager
from smart_agent_arch.tools_loader import ToolsLoader
from smart_agent_arch.hooks import HookManager, EventKind, FileLogger

MediaType = Literal["text", "image", "video", "audio"]


@dataclass(slots=True)
class InputEnvelope:
    media_type: MediaType
    payload: Any
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RuntimeResponse:
    status: str
    content: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ControlStubResult:
    action: Literal["pause", "stop", "start"]
    implemented: bool
    message: str


class RuntimeGateway(Protocol):
    def send(
        self,
        envelope: InputEnvelope,
        config: dict[str, Any],
        runtime_context: dict[str, Any],
    ) -> RuntimeResponse:
        ...


class StubRuntimeGateway:
    """Temporary runtime that echoes acceptance while internals are under construction."""

    def send(
        self,
        envelope: InputEnvelope,
        config: dict[str, Any],
        runtime_context: dict[str, Any],
    ) -> RuntimeResponse:
        del config
        return RuntimeResponse(
            status="accepted",
            content=f"AI response for {envelope.media_type}: {str(envelope.payload)[:120]}",
            metadata={
                "media_type": envelope.media_type,
                "current_time": runtime_context.get("current_time"),
                "events_count": len(runtime_context.get("event_cache", [])),
                "response_mode": runtime_context.get("agent_contract", {}).get("response_mode"),
                "note": "Stub runtime: internal model pipeline will be attached later.",
            },
        )


class UserAIFacade:
    """Stable user-facing API. Internal architecture can evolve behind this facade."""

    def __init__(
        self,
        config: dict[str, Any] | FullConfig,
        runtime_gateway: RuntimeGateway | None = None,
        mentor_gateway: MentorGateway | None = None,
        thinker_gateway: DeepThinkerGateway | None = None,
        tick_interval_sec: float | None = None,
        mentor_interval_sec: float | None = None,
    ) -> None:
        # Convert FullConfig to dict if needed
        if isinstance(config, FullConfig):
            full_config = config
            config_dict = config.to_dict()
        else:
            self._validate_config(config)
            config_dict = dict(config)
            # Try to load FullConfig for better type safety
            try:
                full_config = ConfigLoader.from_dict(config_dict)
            except Exception:
                full_config = None

        self._config = config_dict
        self._full_config = full_config

        # Autowire real gateways if not specifically overriden by tests
        if runtime_gateway is None:
            from smart_agent_arch.live_runtime import LiveRuntimeGateway
            runtime_gateway = LiveRuntimeGateway()
        self._runtime = runtime_gateway
        
        # Apply memory configuration
        memory_config = full_config.memory_config if full_config else None
        memory_max_items = int(config_dict.get("memory_max_items", 100))
        memory_threshold = float(config_dict.get("importance_threshold", 0.65))
        if memory_config:
            memory_max_items = memory_config.max_items
            memory_threshold = memory_config.importance_threshold
        
        self._event_cache = EventCache(max_events=200)
        self._long_memory = LongMemory(max_items=memory_max_items, importance_threshold=memory_threshold)
        
        # Initialize command parser
        self._agent_contract = AgentContract()
        self._command_parser = ConfigCommandParser.from_config(config_dict)
        self._max_command_hops = int(config_dict.get("max_command_hops", 1))
        
        # State management
        self._state: Literal["running", "paused", "stopped"] = "running"
        self._mentor_feedback: list[str] = []
        self._thinker_insights: list[str] = []
        self._fast_memory_hints: list[dict[str, Any]] = []
        self._fast_assist = FastMemoryAssist()
        
        # Apply timing configuration
        if tick_interval_sec is None:
            tick_interval_sec = float(config_dict.get("tick_interval_sec", 1.0))
        self._tick_interval_sec = max(0.05, float(tick_interval_sec))
        
        if mentor_interval_sec is None:
            mentor_interval_sec_config = float(config_dict.get("mentor_interval_sec", 5.0))
            if full_config and hasattr(full_config, 'mentor_config'):
                mentor_interval_sec_config = full_config.mentor_config.interval_sec
            mentor_interval_sec = mentor_interval_sec_config
        
        self._worker_stop_event = threading.Event()
        self._worker_thread: threading.Thread | None = None
        self._lock = threading.Lock()
        
        # Initialize Hooks
        self._hooks = HookManager()

        # Attach file logger if configured
        if self._full_config and self._full_config.logging.log_file:
            logger = FileLogger(self._full_config.logging.log_file)
            for kind in EventKind:
                self._hooks.subscribe(kind, logger)
        self._detailed_diagnostics = bool(config_dict.get("detailed_diagnostics", False))
        
        # Initialize custom tools loader
        project_root = Path(__file__).resolve().parent.parent.parent
        self._tools_dir = project_root / "utils" / "custom_tools"
        self._tools_loader = ToolsLoader(self._tools_dir)
        self.refresh_custom_tools()
        
        # Initialize component gateways
        if mentor_gateway is None and full_config:
            from smart_agent_arch.live_runtime import LiveMentorGateway
            mentor_gateway = LiveMentorGateway(full_config)
            
        if thinker_gateway is None and full_config:
            from smart_agent_arch.live_runtime import LiveDeepThinkerGateway
            thinker_gateway = LiveDeepThinkerGateway(full_config)

        self._mentor = MentorAIComponent(
            gateway=mentor_gateway or StubMentorGateway(),
            context_provider=self.runtime_context,
            feedback_callback=self._on_mentor_feedback,
            task_callback=self._on_mentor_task,
            tool_callback=self._on_mentor_synthesize_tool,
            interval_sec=float(mentor_interval_sec),
        )
        self._deep_thinker = DeepThinkerAIComponent(
            gateway=thinker_gateway or StubDeepThinkerGateway(),
            context_provider=self.runtime_context,
            insight_callback=self._on_thinker_insight,
        )
        
        # Build and store system prompts
        if full_config:
            self._system_prompts = SystemPromptManager.build_prompts(full_config)
        else:
            self._system_prompts = SystemPromptManager.build_prompts(
                ConfigLoader.from_dict(config_dict)
            )
        
        # Log initialization
        self._event_cache.add(kind="system", summary="AI facade initialized with advanced config")
        self._event_cache.add(
            kind="system",
            summary=f"Command parser enabled: {self._command_parser.enabled}",
        )
        self._event_cache.add(
            kind="system",
            summary=f"Config: provider={config_dict.get('provider', '?')}, "
                    f"model={config_dict.get('model', '?')}, "
                    f"output_format={config_dict.get('output_format', 'text')}, "
                    f"temperature={config_dict.get('temperature', '?')}",
        )
        self._long_memory.add(
            summary="Facade initialized with full customization support",
            importance=0.8,
            source="system",
        )
        
        self._start_worker_if_needed()
        self._components_started = False
        self._start_components()

    def _start_components(self) -> None:
        """Explicitly start all background workers."""
        with self._lock:
            if not self._components_started:
                self._mentor.start()
                self._deep_thinker.start()
                self._components_started = True
                self._event_cache.add(kind="system", summary="Background components started")

    def _ensure_active(self) -> None:
        """Helper to lazy-start components on first use without changing logical state."""
        if not self._components_started:
            self._start_components()

    def diagnostics(self, last_n: int = 20) -> list[dict[str, Any]]:
        """Returns a list of recent diagnostic events for UI display."""
        events = self._event_cache.events()[-last_n:]
        results = []
        for e in events:
            results.append({
                "timestamp": getattr(e, "timestamp", str(time.time())),
                "kind": getattr(e, "kind", "system"),
                "summary": getattr(e, "summary", "No details"),
                "repeats": getattr(e, "repeats", 1)
            })
        return results

    def print_diagnostics(self, last_n: int = 20) -> None:
        """Prints a beautiful diagnostic report of recent events."""
        try:
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
        except ImportError:
            print("Rich library not installed. Cannot show beautiful diagnostics.")
            return

        console = Console()
        table = Table(title="💎 NexLab Agent Diagnostics", show_lines=True)
        table.add_column("Time", style="dim")
        table.add_column("Component", style="cyan")
        table.add_column("Event", style="magenta")
        table.add_column("Details", style="white")

        events = self.diagnostics(last_n)
        for e in events:
            ts = e["timestamp"].split("T")[-1][:8] if "T" in e["timestamp"] else str(e["timestamp"])
            table.add_row(
                ts,
                e["kind"],
                e["summary"],
                f"x{e['repeats']}" if e["repeats"] > 1 else ""
            )

        console.print(Panel(table, title="[bold green]System Health Status[/bold green]", expand=False))

    def register_hook(self, kind: EventKind, callback: Callable) -> None:
        """Register a custom hook for agent lifecycle events."""
        self._hooks.subscribe(kind, callback)

    @property
    def config(self) -> dict[str, Any]:
        return dict(self._config)

    def send_text(self, text: str, metadata: dict[str, Any] | None = None) -> RuntimeResponse:
        blocked = self._prepare_input_flow()
        if blocked is not None:
            return blocked
        self._event_cache.add(kind="input", summary="Received text input")
        self._assist_with_fast_memory(topic=text, source_component="first_ai")
        envelope = InputEnvelope(
            media_type="text",
            payload=text,
            metadata=metadata or {},
        )
        self._hooks.trigger(EventKind.ON_INPUT, {"envelope": envelope})
        response = self._send_with_command_pipeline(envelope)
        self._event_cache.add(kind="runtime", summary=f"Runtime status: {response.status}")
        return response

    def send_image(self, image: Any, metadata: dict[str, Any] | None = None) -> RuntimeResponse:
        blocked = self._prepare_input_flow()
        if blocked is not None:
            return blocked
        self._event_cache.add(kind="input", summary="Received image input")
        theme = str((metadata or {}).get("theme", str(image)[:120]))
        self._assist_with_fast_memory(topic=theme, source_component="first_ai")
        envelope = InputEnvelope(
            media_type="image",
            payload=image,
            metadata=metadata or {},
        )
        response = self._send_with_command_pipeline(envelope)
        self._event_cache.add(kind="runtime", summary=f"Runtime status: {response.status}")
        return response

    def send_video(self, video: Any, metadata: dict[str, Any] | None = None) -> RuntimeResponse:
        blocked = self._prepare_input_flow()
        if blocked is not None:
            return blocked
        self._event_cache.add(kind="input", summary="Received video input")
        theme = str((metadata or {}).get("theme", str(video)[:120]))
        self._assist_with_fast_memory(topic=theme, source_component="first_ai")
        envelope = InputEnvelope(
            media_type="video",
            payload=video,
            metadata=metadata or {},
        )
        response = self._send_with_command_pipeline(envelope)
        self._event_cache.add(kind="runtime", summary=f"Runtime status: {response.status}")
        return response

    def send_audio(self, audio: Any, metadata: dict[str, Any] | None = None) -> RuntimeResponse:
        blocked = self._prepare_input_flow()
        if blocked is not None:
            return blocked
        self._event_cache.add(kind="input", summary="Received audio input")
        theme = str((metadata or {}).get("theme", str(audio)[:120]))
        self._assist_with_fast_memory(topic=theme, source_component="first_ai")
        envelope = InputEnvelope(
            media_type="audio",
            payload=audio,
            metadata=metadata or {},
        )
        response = self._send_with_command_pipeline(envelope)
        self._event_cache.add(kind="runtime", summary=f"Runtime status: {response.status}")
        return response

    def append_ai_events(self, events: list[dict[str, str]]) -> None:
        """Adds summarized AI-generated events to cache without storing raw chat logs."""
        self._event_cache.add_many(events)

    def append_ai_memories(self, memories: list[dict[str, Any]]) -> int:
        """Adds important AI-selected memories into long-term memory."""
        added = self._long_memory.add_many(memories)
        if added:
            self._event_cache.add(kind="memory", summary=f"Stored {added} long-memory items")
        return added

    def append_user_preferences(self, preferences: list[dict[str, Any]]) -> int:
        """Stores important user preferences in long-term memory."""
        added = self._long_memory.add_preferences(preferences)
        if added:
            self._event_cache.add(kind="memory", summary=f"Stored {added} user preferences")
        return added

    def append_knowledge(self, knowledge_items: list[dict[str, Any]]) -> int:
        """Stores important knowledge items in long-term memory."""
        added = self._long_memory.add_knowledge(knowledge_items)
        if added:
            self._event_cache.add(kind="memory", summary=f"Stored {added} knowledge items")
        return added

    def submit_deep_task(self, task_text: str, source: str = "manual") -> None:
        """Submit a complex task for deep-thinker AI to solve in background until verified."""
        self._assist_with_fast_memory(topic=task_text, source_component="third_ai")
        self._deep_thinker.submit_task(task_text=task_text, source=source)
        self._event_cache.add(kind="thinker", summary=f"Deep task assigned by {source}")

    def refresh_custom_tools(self) -> int:
        """Reload all tools from the custom tools directory."""
        specs = self._tools_loader.load_all()
        for spec in specs:
            self._command_parser.add_command(spec)
        
        count = len(specs)
        if count > 0:
            self._event_cache.add(kind="system", summary=f"Loaded {count} custom tools from {self._tools_dir}")
        return count

    def runtime_context(self) -> dict[str, Any]:
        """Returns current time plus compact event list for model-side context."""
        event_context = self._event_cache.build_model_context()
        memory_context = self._long_memory.build_context()
        contract = self._agent_contract.to_context()
        parser_info = self._command_parser.describe()
        system_prompt = self._build_system_prompt(
            policy_text=str(contract.get("policy_text", "")),
            parser_addendum=str(parser_info.get("system_prompt_addendum", "")),
            current_time=str(event_context["current_time"]),
        )
        return {
            "current_time": event_context["current_time"],
            "event_cache": event_context["event_cache"],
            "long_memory": memory_context["long_memory"],
            "user_preferences": memory_context["user_preferences"],
            "knowledge": memory_context["knowledge"],
            "mentor_feedback": list(self._mentor_feedback),
            "mentor_state": self._mentor.state,
            "deep_thinker_state": self._deep_thinker.state,
            "deep_thinker_task": self._deep_thinker.task_snapshot(),
            "deep_thinker_insights": list(self._thinker_insights),
            "fast_memory_hints": list(self._fast_memory_hints),
            "runtime_state": self._state,
            "agent_contract": contract,
            "command_parser": parser_info,
            "system_prompt": system_prompt,
        }

    def pause(self) -> ControlStubResult:
        with self._lock:
            self._state = "paused"
        self._mentor.pause()
        self._deep_thinker.pause()
        self._event_cache.add(kind="control", summary="Runtime paused")
        return ControlStubResult(
            action="pause",
            implemented=True,
            message="Runtime paused. It will auto-resume on next input.",
        )

    def stop(self) -> ControlStubResult:
        with self._lock:
            self._state = "stopped"
        self._mentor.stop()
        self._deep_thinker.stop()
        # Persistent behavior: unfinished deep task auto-resumes even after global stop.
        self._deep_thinker.ensure_running_for_pending_task()
        self._promote_critical_cache_to_long_memory()
        self._event_cache.add(kind="control", summary="Runtime stopped")
        return ControlStubResult(
            action="stop",
            implemented=True,
            message="Runtime stopped. Call start() to resume processing.",
        )

    def start(self) -> ControlStubResult:
        with self._lock:
            self._state = "running"
        self._start_worker_if_needed()
        self._mentor.start()
        self._deep_thinker.start()
        self._event_cache.add(kind="control", summary="Runtime started")
        return ControlStubResult(
            action="start",
            implemented=True,
            message="Runtime started.",
        )

    @staticmethod
    def _validate_config(config: dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise ConfigurationError("config must be a dictionary")
        if not config:
            raise ConfigurationError("config dictionary must not be empty")

    def _prepare_input_flow(self) -> RuntimeResponse | None:
        with self._lock:
            current = self._state
            if current == "paused":
                self._state = "running"
        if current == "paused":
            self._event_cache.add(kind="control", summary="Runtime auto-resumed by input")
            self._start_worker_if_needed()
            self._mentor.resume()
            self._mentor.start()
            self._deep_thinker.resume()
            self._deep_thinker.start()
            return None
        if current == "stopped":
            self._event_cache.add(kind="control", summary="Input ignored while runtime is stopped")
            return RuntimeResponse(
                status="stopped",
                metadata={
                    "reason": "Runtime is stopped. Call start() before sending input.",
                },
            )
        self._start_worker_if_needed()
        return None

    def _start_worker_if_needed(self) -> None:
        with self._lock:
            if self._worker_thread is not None and self._worker_thread.is_alive():
                return
            self._worker_stop_event.clear()
            self._worker_thread = threading.Thread(
                target=self._worker_loop,
                name="smart-agent-runtime-loop",
                daemon=True,
            )
            self._worker_thread.start()

    def _worker_loop(self) -> None:
        while not self._worker_stop_event.is_set():
            with self._lock:
                current = self._state
            if current == "running":
                self._event_cache.add(kind="tick", summary="Background cycle executed")
                time.sleep(self._tick_interval_sec)
                continue
            time.sleep(0.05)

    def _send_with_command_pipeline(self, envelope: InputEnvelope) -> RuntimeResponse:
        context = self.runtime_context()
        # Use FullConfig if available to preserve function pointers
        config_to_pass = self._full_config if self._full_config else self._config
        response = self._runtime.send(envelope, config_to_pass, context)

        # The AI response is returned directly to user; parser is optional and can refine via follow-up hops.
        hops = 0
        while (
            self._command_parser.enabled
            and isinstance(response.content, str)
            and hops < max(0, self._max_command_hops)
        ):
            match = self._command_parser.match(response.content)
            if match is None:
                break

            command_result = self._command_parser.execute(match)
            self._hooks.trigger(EventKind.ON_TOOL_END, {"command": match.spec.name, "result": command_result})
            self._event_cache.add(kind="command", summary=f"Executed command: {match.spec.name}")
            self._long_memory.add(
                summary=f"Command {match.spec.name} executed successfully",
                importance=0.7,
                source="runtime",
            )

            followup_envelope = InputEnvelope(
                media_type="text",
                payload=(
                    "Command execution result available. "
                    f"Command: {match.spec.name}. "
                    f"Arguments: {match.args}. "
                    f"Result: {command_result}. "
                    "Generate final response for user."
                ),
                metadata={
                    "command_name": match.spec.name,
                    "command_args": match.args,
                    "command_result": command_result,
                },
            )
            response = self._runtime.send(followup_envelope, self._config, self.runtime_context())
            hops += 1

        return response

    @staticmethod
    def _build_system_prompt(policy_text: str, parser_addendum: str, current_time: str) -> str:
        return (
            "System instructions for model runtime:\n"
            f"- Current UTC time: {current_time}\n"
            f"- Core policy: {policy_text}\n"
            f"- Command parser policy:\n{parser_addendum}"
        )

    def _on_mentor_feedback(self, feedback: str) -> None:
        text = feedback.strip()
        if not text:
            return
        self._assist_with_fast_memory(topic=text, source_component="second_ai")
        self._mentor_feedback.append(text)
        if len(self._mentor_feedback) > 50:
            self._mentor_feedback = self._mentor_feedback[-50:]
        self._event_cache.add(kind="mentor", summary=text)

    def _on_mentor_task(self, task_text: str) -> None:
        text = task_text.strip()
        if not text:
            return
        self._assist_with_fast_memory(topic=text, source_component="second_ai")
        self.submit_deep_task(task_text=text, source="mentor")

    def _on_mentor_synthesize_tool(self, tool_def: dict[str, Any]) -> None:
        try:
            name = tool_def.get("name")
            code = tool_def.get("code")
            if not name or not code:
                return

            from pathlib import Path
            generated_dir = Path("utils/generated_tools")
            generated_dir.mkdir(parents=True, exist_ok=True)

            file_path = generated_dir / f"{name}.py"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

            from smart_agent_arch.command_parser import CommandSpec
            spec = CommandSpec(
                name=name,
                triggers=tool_def.get("triggers", [f"RUN_{name.upper()}"]),
                pattern=tool_def.get("pattern", f"RUN_{name.upper()}"),
                function_file=str(file_path.absolute()),
                function_name=name,
                casts=tool_def.get("casts", {}),
                arg_descriptions=tool_def.get("arg_descriptions", {}),
                output_description=tool_def.get("output_description", "Returns generic output"),
                description=tool_def.get("description", f"Autogenerated tool {name}"),
            )
            self._command_parser.add_command(spec)
            self._event_cache.add(kind="tool", summary=f"Mentor synthesized new tool: {name}")
            self.append_ai_memories([{
                "summary": f"Synthesized new tool '{name}'. Trigger: {spec.pattern}",
                "importance": 0.85,
                "source": "mentor"
            }])
        except Exception as e:
            self._event_cache.add(kind="error", summary=f"Failed to synthesize tool: {str(e)}")

    def _on_thinker_insight(self, insight: str) -> None:
        text = insight.strip()
        if not text:
            return
        self._thinker_insights.append(text)
        if len(self._thinker_insights) > 100:
            self._thinker_insights = self._thinker_insights[-100:]

        # Simulate internal "write" tool: save verified thinker insight to long memory.
        self.append_ai_memories([
            {
                "summary": f"Deep thinker solution: {text}",
                "importance": 0.9,
                "source": "deep_thinker",
            }
        ])
        self._event_cache.add(kind="tool", summary="Executed tool: write_long_memory")

    def _assist_with_fast_memory(self, topic: str, source_component: str) -> None:
        hits = self._fast_assist.find_related(topic=topic, memories=self._long_memory.items())
        if not hits:
            return

        previous_runtime = self._state
        previous_mentor = self._mentor.state
        previous_thinker = self._deep_thinker.state

        # Brief global pause while broadcasting relevant deep memory hints.
        with self._lock:
            self._state = "paused"
        self._mentor.pause()
        self._deep_thinker.pause()

        hint = {
            "topic": topic,
            "source_component": source_component,
            "memories": [
                {
                    "summary": hit.summary,
                    "source": hit.source,
                    "memory_type": hit.memory_type,
                    "importance": hit.importance,
                    "score": hit.score,
                }
                for hit in hits
            ],
        }
        self._fast_memory_hints.append(hint)
        if len(self._fast_memory_hints) > 30:
            self._fast_memory_hints = self._fast_memory_hints[-30:]
        self._event_cache.add(
            kind="fast_memory",
            summary=(
                f"Injected {len(hits)} deep-memory hints for {source_component}"
            ),
        )

        self._restore_component_state(previous_runtime, previous_mentor, previous_thinker)

    def _restore_component_state(
        self,
        runtime_state: Literal["running", "paused", "stopped"],
        mentor_state: Literal["running", "paused", "stopped"],
        thinker_state: Literal["running", "paused", "stopped"],
    ) -> None:
        with self._lock:
            self._state = runtime_state

        if runtime_state == "running":
            self._start_worker_if_needed()

        if mentor_state == "running":
            self._mentor.start()
        elif mentor_state == "paused":
            self._mentor.pause()
        else:
            self._mentor.stop()

        if thinker_state == "running":
            self._deep_thinker.start()
        elif thinker_state == "paused":
            self._deep_thinker.pause()
        else:
            self._deep_thinker.stop()

    def _promote_critical_cache_to_long_memory(self) -> None:
        events = self._event_cache.events()
        knowledge_items: list[dict[str, Any]] = []
        memory_items: list[dict[str, Any]] = []

        for event in events:
            # Strictly save only AI Knowledge and User Preferences
            if event.kind == "mentor":
                importance = min(1.0, 0.9 + min(event.repeats, 5) * 0.01)
                knowledge_items.append(
                    {
                        "summary": f"AI Knowledge/Insight: {event.summary}",
                        "importance": importance,
                        "source": "mentor",
                    }
                )
            elif event.kind == "preference" or "preference" in event.summary.lower():
                memory_items.append(
                    {
                        "summary": f"User Preference: {event.summary}",
                        "importance": 0.85,
                        "source": "cache_stop",
                    }
                )

        if knowledge_items:
            self.append_knowledge(knowledge_items)
        if memory_items:
            self.append_ai_memories(memory_items)
        if knowledge_items or memory_items:
            self._event_cache.add(
                kind="memory",
                summary=(
                    "Promoted cache items to long memory on stop: "
                    f"knowledge={len(knowledge_items)}, preferences={len(memory_items)}"
                ),
            )


    def load_knowledge_file(self, file_path: str) -> int:
        """Load a single text file into long memory as knowledge chunks."""
        try:
            path = Path(file_path)
            content = path.read_text(encoding="utf-8")
            if not content.strip():
                return 0
            
            chunks = [content[i:i+4000] for i in range(0, len(content), 4000)]
            memories: list[dict[str, Any]] = []
            for i, chunk in enumerate(chunks):
                memories.append({
                    "summary": f"Knowledge from {path.name} (Part {i+1}): {chunk[:100]}...",
                    "importance": 0.9,
                    "source": "document_loader",
                    "content": chunk
                })
            self.append_ai_memories(memories)
            self._event_cache.add(kind="system", summary=f"Loaded {len(chunks)} knowledge chunks from {path.name}")
            return len(chunks)
        except Exception as e:
            self._event_cache.add(kind="error", summary=f"Failed to load knowledge file {file_path}: {e}")
            return 0

    def load_knowledge_directory(self, dir_path: str) -> int:
        """Scan a directory for text/markdown/python files and load them into memory."""
        try:
            path = Path(dir_path)
            if not path.exists() or not path.is_dir():
                return 0
                
            count = 0
            for ext in ["*.txt", "*.md", "*.py"]:
                for file_path in path.rglob(ext):
                    count += self.load_knowledge_file(str(file_path))
            
            self._event_cache.add(kind="system", summary=f"Loaded total {count} knowledge chunks from {dir_path}")
            return count
        except Exception as e:
            self._event_cache.add(kind="error", summary=f"Failed to load knowledge directory {dir_path}: {e}")
            return 0

def initialize_ai(config: dict[str, Any] | FullConfig | str | Path, runtime_gateway: RuntimeGateway | None = None) -> UserAIFacade:
    """Single entrypoint for config from dict, FullConfig, or file path.

    Supported path formats:
    - .yaml / .yml
    - .json
    - .py (CONFIG or get_config + optional create_model_provider)
    """

    if isinstance(config, FullConfig):
        return UserAIFacade(config=config, runtime_gateway=runtime_gateway)

    if isinstance(config, dict):
        return UserAIFacade(config=config, runtime_gateway=runtime_gateway)

    if isinstance(config, (str, Path)):
        from smart_agent_arch.config_loader import ConfigLoader
        full_config = ConfigLoader.from_file(config)
        return UserAIFacade(config=full_config, runtime_gateway=runtime_gateway)

    raise ConfigurationError(f"Unsupported config type: {type(config)}")
