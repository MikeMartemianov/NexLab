from __future__ import annotations

import importlib.util
import inspect
import re
from pathlib import Path
from typing import Any, Callable, Type, get_type_hints

from smart_agent_arch.command_parser import CommandSpec


def export_tool(func: Callable) -> Callable:
    """Decorator to mark a function as a tool for the AI."""
    func._is_ai_tool = True
    return func


class ToolsLoader:
    """Dynamically loads Python functions as CommandSpecs for the AI."""

    def __init__(self, search_dir: str | Path) -> None:
        self.search_dir = Path(search_dir).resolve()
        self.search_dir.mkdir(parents=True, exist_ok=True)

    def load_all(self) -> list[CommandSpec]:
        """Scans the directory and returns a list of CommandSpecs."""
        specs: list[CommandSpec] = []
        for py_file in self.search_dir.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue
            specs.extend(self._load_from_file(py_file))
        return specs

    def _load_from_file(self, file_path: Path) -> list[CommandSpec]:
        """Loads all exported tools from a single Python file."""
        specs: list[CommandSpec] = []
        module_name = f"dynamic_tools_{file_path.stem}_{abs(hash(str(file_path)))}"
        
        try:
            spec = importlib.util.spec_from_file_location(module_name, str(file_path))
            if spec is None or spec.loader is None:
                return []
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            for name, obj in inspect.getmembers(module):
                if inspect.isfunction(obj) and getattr(obj, "_is_ai_tool", False):
                    specs.append(self._create_spec(name, obj, file_path))
                    
        except Exception as e:
            print(f"Error loading tools from {file_path}: {e}")
            
        return specs

    def _create_spec(self, name: str, func: Callable, file_path: Path) -> CommandSpec:
        """Extracts metadata from a function and creates a CommandSpec."""
        doc = inspect.getdoc(func) or f"Auto-generated tool {name}"
        
        # Split docstring into purpose and arg descriptions
        # Simple heuristic: first paragraph is purpose, lines starting with :param are args
        doc_lines = doc.splitlines()
        purpose = doc_lines[0] if doc_lines else doc
        
        arg_descriptions: dict[str, str] = {}
        for line in doc_lines:
            match = re.search(r":param (\w+): (.+)", line)
            if match:
                arg_descriptions[match.group(1)] = match.group(2).strip()

        # Get type hints for casts
        type_hints = get_type_hints(func)
        casts: dict[str, str] = {}
        for arg_name, arg_type in type_hints.items():
            if arg_name == "return":
                continue
            if arg_type is int:
                casts[arg_name] = "int"
            elif arg_type is float:
                casts[arg_name] = "float"
            elif arg_type is bool:
                casts[arg_name] = "bool"
            else:
                casts[arg_name] = "str"

        # Build pattern: name(arg1="...", arg2="...")
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        
        # Enhanced pattern that matches name(arg1="val", arg2=123)
        # We need a regex that can pick up named groups for command_parser.match
        pattern_parts = []
        for p in params:
            # Match arg="value" or arg=value
            pattern_parts.append(rf'{p}\s*=\s*["\']?(?P<{p}>[^,"\']+)["\']?')
        
        pattern = rf"{name}\s*\(\s*" + r"\s*,\s*".join(pattern_parts) + r"\s*\)"
        
        # If no params, just name()
        if not params:
            pattern = rf"{name}\s*\(\s*\)"

        return CommandSpec(
            name=name,
            triggers=[f"{name}("],
            pattern=pattern,
            function_file=str(file_path.absolute()),
            function_name=name,
            casts=casts,
            arg_descriptions=arg_descriptions,
            output_description="Returns function output",
            description=purpose,
        )
