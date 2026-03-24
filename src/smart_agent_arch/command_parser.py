from __future__ import annotations

import importlib.util
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(slots=True)
class CommandSpec:
    name: str
    triggers: list[str]
    pattern: str
    function_file: str
    function_name: str
    casts: dict[str, str]
    arg_descriptions: dict[str, str]
    output_description: str
    description: str


@dataclass(slots=True)
class CommandMatch:
    spec: CommandSpec
    args: dict[str, Any]
    raw_text: str


class ConfigCommandParser:
    """Parses AI text commands from config and executes mapped local functions."""

    def __init__(self, enabled: bool, commands: list[CommandSpec]) -> None:
        self.enabled = enabled
        self._commands = commands
        self._callable_cache: dict[tuple[str, str], Callable[..., Any]] = {}

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> ConfigCommandParser:
        raw = config.get("command_parser", {})
        if not isinstance(raw, dict):
            return cls(enabled=False, commands=[])

        enabled = bool(raw.get("enabled", False))
        command_items = raw.get("commands", [])
        if not isinstance(command_items, list):
            return cls(enabled=enabled, commands=[])

        parsed: list[CommandSpec] = []
        for item in command_items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            pattern = str(item.get("pattern", "")).strip()
            function = item.get("function", {})
            if not name or not pattern or not isinstance(function, dict):
                continue

            function_file = str(function.get("file", "")).strip()
            function_name = str(function.get("name", "")).strip()
            if not function_file or not function_name:
                continue

            triggers_raw = item.get("triggers", [])
            triggers = [str(x) for x in triggers_raw] if isinstance(triggers_raw, list) else []
            casts = item.get("casts", {})
            arg_descriptions = cls._read_arg_descriptions(item)
            parsed.append(
                CommandSpec(
                    name=name,
                    triggers=triggers,
                    pattern=pattern,
                    function_file=function_file,
                    function_name=function_name,
                    casts=casts if isinstance(casts, dict) else {},
                    arg_descriptions=arg_descriptions,
                    output_description=str(item.get("output_description", "")).strip(),
                    description=str(item.get("description", "")).strip(),
                )
            )

        return cls(enabled=enabled, commands=parsed)

    def add_command(self, spec: CommandSpec) -> None:
        self._commands.append(spec)
        self.enabled = True

    def describe(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "commands": [
                {
                    "name": spec.name,
                    "triggers": spec.triggers,
                    "pattern": spec.pattern,
                    "description": spec.description,
                    "arg_descriptions": spec.arg_descriptions,
                    "output_description": spec.output_description,
                }
                for spec in self._commands
            ],
            "system_prompt_addendum": self.system_prompt_addendum(),
        }

    def system_prompt_addendum(self) -> str:
        if not self.enabled or not self._commands:
            return "Command parser is disabled."

        lines: list[str] = [
            "Command parser instructions:",
            "When needed, emit one command that matches a configured pattern exactly.",
            "Available commands:",
        ]
        for spec in self._commands:
            lines.append(f"- name: {spec.name}")
            lines.append(f"  pattern: {spec.pattern}")
            if spec.description:
                lines.append(f"  purpose: {spec.description}")
            if spec.arg_descriptions:
                lines.append("  arguments:")
                for arg_name, arg_description in spec.arg_descriptions.items():
                    cast_type = spec.casts.get(arg_name, "str")
                    lines.append(f"    - {arg_name} ({cast_type}): {arg_description}")
            if spec.output_description:
                lines.append(f"  function_output: {spec.output_description}")
        return "\n".join(lines)

    def match(self, text: str) -> CommandMatch | None:
        if not self.enabled:
            return None

        for spec in self._commands:
            if spec.triggers and not any(trigger in text for trigger in spec.triggers):
                continue

            found = re.search(spec.pattern, text)
            if found is None:
                continue

            args = {key: value for key, value in found.groupdict().items()}
            typed_args = self._apply_casts(args, spec.casts)
            return CommandMatch(spec=spec, args=typed_args, raw_text=text)

        return None

    def execute(self, match: CommandMatch) -> Any:
        target = self._load_callable(match.spec.function_file, match.spec.function_name)
        return target(**match.args)

    def _load_callable(self, file_path: str, fn_name: str) -> Callable[..., Any]:
        key = (file_path, fn_name)
        if key in self._callable_cache:
            return self._callable_cache[key]

        resolved = Path(file_path)
        if not resolved.is_absolute():
            resolved = Path.cwd() / resolved
        resolved = resolved.resolve()

        module_name = f"smart_agent_user_fn_{resolved.stem}_{abs(hash(str(resolved)))}"
        spec = importlib.util.spec_from_file_location(module_name, str(resolved))
        if spec is None or spec.loader is None:
            raise ValueError(f"Unable to load module from file: {resolved}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        candidate = getattr(module, fn_name, None)
        if not callable(candidate):
            raise ValueError(f"Function not found or not callable: {fn_name} in {resolved}")

        self._callable_cache[key] = candidate
        return candidate

    @staticmethod
    def _apply_casts(values: dict[str, Any], casts: dict[str, str]) -> dict[str, Any]:
        converted: dict[str, Any] = {}
        for key, value in values.items():
            cast_type = casts.get(key)
            if cast_type == "int":
                converted[key] = int(value)
            elif cast_type == "float":
                converted[key] = float(value)
            elif cast_type == "bool":
                converted[key] = str(value).lower() in {"1", "true", "yes", "on"}
            else:
                converted[key] = value
        return converted

    @staticmethod
    def _read_arg_descriptions(item: dict[str, Any]) -> dict[str, str]:
        raw = item.get("arg_descriptions", {})
        if isinstance(raw, dict):
            return {str(k): str(v) for k, v in raw.items()}

        # Alternative schema for explicit rich command config.
        arguments = item.get("arguments", [])
        if isinstance(arguments, list):
            result: dict[str, str] = {}
            for arg in arguments:
                if not isinstance(arg, dict):
                    continue
                name = str(arg.get("name", "")).strip()
                desc = str(arg.get("description", "")).strip()
                if name and desc:
                    result[name] = desc
            return result
        return {}
