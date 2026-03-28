"""Advanced configuration loader with full customization support."""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal

from smart_agent_arch.exceptions import ConfigurationError


@dataclass(slots=True)
class ModelProviderConfig:
    """LLM provider configuration."""
    provider: str  # "openai", "anthropic", "ollama", "custom_function"
    model: str
    api_key: str | None = None
    base_url: str | None = None
    timeout_sec: int = 60
    max_retries: int = 3
    model_kwargs: dict[str, Any] = field(default_factory=dict)
    custom_module_path: str | None = None
    custom_function_name: str | None = None


@dataclass(slots=True)
class InputOutputConfig:
    """Input/output format configuration."""
    input_formats: list[str] = field(default_factory=lambda: ["text"])
    output_format: str = "text"  # "text", "json", "markdown", "html", "latex"
    max_response_length: int = 8000
    enable_streaming: bool = False


@dataclass(slots=True)
class ModelBehaviorConfig:
    """Model behavior tuning parameters."""
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int | None = None
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    max_tokens: int | None = None
    stop_sequences: list[str] = field(default_factory=list)


@dataclass(slots=True)
class OutputStyleConfig:
    """Output style and tone configuration."""
    language: str = "en"  # Language code (en, ru, etc.)
    tone: str = "neutral"  # "formal", "casual", "technical", "friendly", "academic"
    verbose_level: int = 1  # 0 = very concise, 1 = balanced, 2 = detailed, 3 = verbose
    include_citations: bool = False
    include_reasoning: bool = False


@dataclass(slots=True)
class MemoryConfig:
    """Memory storage and retention configuration."""
    max_items: int = 100
    importance_threshold: float = 0.65
    memory_retention_days: int = 30
    storage_backend: str = "memory"  # "memory", "sqlite", "redis"
    storage_path: str | None = None
    enable_compression: bool = True


@dataclass(slots=True)
class ComponentConfig:
    """Configuration for individual AI components."""
    enabled: bool = True
    system_prompt_suffix: str = ""  # Additional custom prompt for this component
    response_format: str = "text"
    max_iterations: int | None = None
    timeout_sec: int = 30
    model_provider_override: dict[str, Any] | None = None


@dataclass(slots=True)
class MentorConfig(ComponentConfig):
    """Mentor AI specific configuration."""
    interval_sec: float = 5.0
    feedback_focus: str = "quality"  # "quality", "efficiency", "completeness", "all"
    max_feedback_length: int = 500


@dataclass(slots=True)
class DeepThinkerConfig(ComponentConfig):
    """Deep thinker AI specific configuration."""
    max_thinking_iterations: int = 50
    verification_required: bool = True
    persistence_enabled: bool = True


@dataclass(slots=True)
class FastMemoryConfig(ComponentConfig):
    """Fast memory assist specific configuration."""
    matching_threshold: float = 0.34
    max_hints: int = 3
    hint_format: str = "inline"  # "inline", "separate", "structured"


@dataclass(slots=True)
class RateLimitingConfig:
    """Rate limiting and resource management."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_allowed: int = 5
    enable_throttling: bool = False


@dataclass(slots=True)
class CachingConfig:
    """Response caching configuration."""
    enable_caching: bool = False
    cache_ttl_sec: int = 3600
    cache_backend: str = "memory"  # "memory", "redis", "disk"
    cache_max_size_mb: int = 100


@dataclass(slots=True)
class ToolsConfig:
    """Tools and command execution configuration."""
    enable_commands: bool = True
    commands_optional: bool = True
    max_command_hops: int = 1
    command_timeout_sec: int = 30
    allowed_functions: set[str] | None = None  # None = all allowed


@dataclass(slots=True)
class LoggingConfig:
    """Logging and diagnostics configuration."""
    enable_logging: bool = True
    log_level: str = "INFO"  # "DEBUG", "INFO", "WARNING", "ERROR"
    log_file: str | None = None
    log_format: str = "structured"  # "structured", "text"
    capture_all_inputs: bool = False
    capture_all_outputs: bool = False


@dataclass(slots=True)
class FullConfig:
    """Complete system configuration."""
    # Core configuration
    name: str = "SmartAgent"
    version: str = "1.0"
    description: str = ""

    # Model provider
    model_provider: ModelProviderConfig = field(default_factory=ModelProviderConfig)
    model_provider_function: Callable[..., Any] | None = None

    # Input/output
    io_config: InputOutputConfig = field(default_factory=InputOutputConfig)
    model_behavior: ModelBehaviorConfig = field(default_factory=ModelBehaviorConfig)
    output_style: OutputStyleConfig = field(default_factory=OutputStyleConfig)

    # Memory and storage
    memory_config: MemoryConfig = field(default_factory=MemoryConfig)

    # Components
    mentor_config: MentorConfig = field(default_factory=MentorConfig)
    deep_thinker_config: DeepThinkerConfig = field(default_factory=DeepThinkerConfig)
    fast_memory_config: FastMemoryConfig = field(default_factory=FastMemoryConfig)

    # Operations
    tools_config: ToolsConfig = field(default_factory=ToolsConfig)
    rate_limiting: RateLimitingConfig = field(default_factory=RateLimitingConfig)
    caching: CachingConfig = field(default_factory=CachingConfig)

    # Logging
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # System prompts (per component)
    system_prompts: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Export as dictionary for runtime inspection."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "model_provider": {
                "provider": self.model_provider.provider,
                "model": self.model_provider.model,
                "timeout_sec": self.model_provider.timeout_sec,
                "max_retries": self.model_provider.max_retries,
            },
            "io": {
                "input_formats": self.io_config.input_formats,
                "output_format": self.io_config.output_format,
                "max_response_length": self.io_config.max_response_length,
            },
            "model_behavior": {
                "temperature": self.model_behavior.temperature,
                "top_p": self.model_behavior.top_p,
                "max_tokens": self.model_behavior.max_tokens,
            },
            "output_style": {
                "language": self.output_style.language,
                "tone": self.output_style.tone,
                "verbose_level": self.output_style.verbose_level,
            },
            "memory": {
                "max_items": self.memory_config.max_items,
                "retention_days": self.memory_config.memory_retention_days,
            },
            "rate_limiting": {
                "requests_per_minute": self.rate_limiting.requests_per_minute,
            },
        }


class ConfigLoader:
    """Load and validate configuration from various sources."""

    # Default values for all 12+ customizations
    DEFAULTS = {
        # Model and provider
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "top_p": 0.9,

        # Input/output
        "input_formats": ["text"],
        "output_format": "text",
        "max_response_length": 8000,
        "enable_streaming": False,

        # Output style
        "language": "en",
        "tone": "neutral",
        "verbose_level": 1,
        "include_citations": False,
        "include_reasoning": False,

        # Memory
        "memory_retention_days": 30,
        "storage_backend": "memory",
        "enable_compression": True,

        # Component intervals
        "mentor_interval_sec": 5.0,
        "deep_thinker_max_iterations": 50,
        "fast_memory_threshold": 0.34,

        # Operations
        "requests_per_minute": 60,
        "enable_caching": False,
        "cache_ttl_sec": 3600,

        # Tools
        "enable_commands": True,
        "commands_optional": True,
        "max_command_hops": 1,

        # Logging
        "enable_logging": True,
        "log_level": "INFO",
    }

    @staticmethod
    def from_file(file_path: str | Path) -> FullConfig:
        """Load configuration from file, determining format by extension."""
        path = Path(file_path)
        ext = path.suffix.lower()
        if ext in (".yaml", ".yml"):
            return ConfigLoader.from_yaml(path)
        if ext == ".json":
            return ConfigLoader.from_json(path)
        if ext == ".py":
            return ConfigLoader.from_python_module(path)
        raise ConfigurationError(f"Unsupported configuration format: {ext}")

    @staticmethod
    def from_dict(config_dict: dict[str, Any]) -> FullConfig:
        """Load configuration from dictionary."""
        validated = ConfigLoader._validate_config(config_dict)
        return ConfigLoader._build_config_object(validated)

    @staticmethod
    def from_yaml(yaml_path: str | Path) -> FullConfig:
        """Load configuration from YAML file."""
        try:
            import yaml
        except ImportError:
            raise ConfigurationError(
                "PyYAML not installed. Install with: pip install pyyaml"
            )

        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            raise ConfigurationError(f"Configuration file not found: {yaml_path}")

        with open(yaml_path, encoding="utf-8") as f:
            config_dict = yaml.safe_load(f) or {}

        return ConfigLoader.from_dict(config_dict)

    @staticmethod
    def from_json(json_path: str | Path) -> FullConfig:
        """Load configuration from JSON file."""
        import json

        json_path = Path(json_path)
        if not json_path.exists():
            raise ConfigurationError(f"Configuration file not found: {json_path}")

        with open(json_path, encoding="utf-8") as f:
            config_dict = json.load(f)

        return ConfigLoader.from_dict(config_dict)

    @staticmethod
    def from_python_module(module_path: str | Path) -> FullConfig:
        """Load configuration from Python module with custom provider function."""
        module_path = Path(module_path)
        if not module_path.exists():
            raise ConfigurationError(f"Module not found: {module_path}")

        spec = importlib.util.spec_from_file_location("config_module", module_path)
        if not spec or not spec.loader:
            raise ConfigurationError(f"Cannot load module: {module_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules["config_module"] = module
        spec.loader.exec_module(module)

        # Extract CONFIG dict or get_config function
        if hasattr(module, "get_config"):
            config_dict = module.get_config()
        elif hasattr(module, "CONFIG"):
            config_dict = module.CONFIG
        else:
            raise ConfigurationError(
                "Module must define CONFIG dict or get_config() function"
            )

        config = ConfigLoader.from_dict(config_dict)

        # Check for provider function
        if hasattr(module, "create_model_provider"):
            config.model_provider_function = module.create_model_provider

        return config

    @staticmethod
    def _validate_config(config_dict: dict[str, Any]) -> dict[str, Any]:
        """Validate configuration structure and types."""
        if not isinstance(config_dict, dict):
            raise ConfigurationError("Configuration must be a dictionary")

        # Merge with defaults
        validated = dict(ConfigLoader.DEFAULTS)
        validated.update(config_dict)

        # Validate types
        if not isinstance(validated.get("output_format"), str):
            raise ConfigurationError("output_format must be string")

        if not isinstance(validated.get("temperature"), (int, float)):
            raise ConfigurationError("temperature must be number")

        temp = float(validated["temperature"])
        if not 0 <= temp <= 2:
            raise ConfigurationError("temperature must be between 0 and 2")

        if not isinstance(validated.get("max_response_length"), int):
            raise ConfigurationError("max_response_length must be integer")

        return validated

    @staticmethod
    def _build_config_object(validated: dict[str, Any]) -> FullConfig:
        """Build FullConfig object from validated dictionary."""
        # Model provider
        provider_config = ModelProviderConfig(
            provider=validated.get("provider", "openai"),
            model=validated.get("model", "gpt-3.5-turbo"),
            api_key=validated.get("api_key"),
            base_url=validated.get("base_url"),
            timeout_sec=int(validated.get("model_timeout_sec", 60)),
            max_retries=int(validated.get("model_max_retries", 3)),
            model_kwargs=validated.get("model_kwargs", {}),
            custom_module_path=validated.get("custom_module_path"),
            custom_function_name=validated.get("custom_function_name"),
        )

        # Input/output
        io_config = InputOutputConfig(
            input_formats=validated.get("input_formats", ["text"]),
            output_format=validated.get("output_format", "text"),
            max_response_length=int(validated.get("max_response_length", 8000)),
            enable_streaming=bool(validated.get("enable_streaming", False)),
        )

        # Model behavior
        model_behavior = ModelBehaviorConfig(
            temperature=float(validated.get("temperature", 0.7)),
            top_p=float(validated.get("top_p", 0.9)),
            top_k=validated.get("top_k"),
            frequency_penalty=float(validated.get("frequency_penalty", 0.0)),
            presence_penalty=float(validated.get("presence_penalty", 0.0)),
            max_tokens=validated.get("max_tokens"),
            stop_sequences=validated.get("stop_sequences", []),
        )

        # Output style
        output_style = OutputStyleConfig(
            language=validated.get("language", "en"),
            tone=validated.get("tone", "neutral"),
            verbose_level=int(validated.get("verbose_level", 1)),
            include_citations=bool(validated.get("include_citations", False)),
            include_reasoning=bool(validated.get("include_reasoning", False)),
        )

        # Memory
        memory_config = MemoryConfig(
            max_items=int(validated.get("memory_max_items", 100)),
            importance_threshold=float(validated.get("importance_threshold", 0.65)),
            memory_retention_days=int(validated.get("memory_retention_days", 30)),
            storage_backend=validated.get("storage_backend", "memory"),
            storage_path=validated.get("storage_path"),
            enable_compression=bool(validated.get("enable_compression", True)),
        )

        # Mentor
        mentor_config = MentorConfig(
            enabled=bool(validated.get("mentor_enabled", True)),
            system_prompt_suffix=validated.get("mentor_system_prompt_suffix", ""),
            response_format=validated.get("mentor_response_format", "text"),
            interval_sec=float(validated.get("mentor_interval_sec", 5.0)),
            feedback_focus=validated.get("mentor_feedback_focus", "quality"),
            max_feedback_length=int(validated.get("mentor_max_feedback_length", 500)),
            model_provider_override=validated.get("mentor_model_provider_override"),
        )

        # Deep thinker
        deep_thinker_config = DeepThinkerConfig(
            enabled=bool(validated.get("deep_thinker_enabled", True)),
            system_prompt_suffix=validated.get("deep_thinker_system_prompt_suffix", ""),
            response_format=validated.get("deep_thinker_response_format", "text"),
            max_iterations=int(validated.get("deep_thinker_max_iterations", 50)),
            verification_required=bool(validated.get("verification_required", True)),
            persistence_enabled=bool(validated.get("persistence_enabled", True)),
            model_provider_override=validated.get("deep_thinker_model_provider_override"),
        )

        # Fast memory
        fast_memory_config = FastMemoryConfig(
            enabled=bool(validated.get("fast_memory_enabled", True)),
            system_prompt_suffix=validated.get("fast_memory_system_prompt_suffix", ""),
            matching_threshold=float(validated.get("fast_memory_threshold", 0.34)),
            max_hints=int(validated.get("fast_memory_max_hints", 3)),
            hint_format=validated.get("fast_memory_hint_format", "inline"),
        )

        # Rate limiting
        rate_limiting = RateLimitingConfig(
            requests_per_minute=int(validated.get("requests_per_minute", 60)),
            requests_per_hour=int(validated.get("requests_per_hour", 1000)),
            burst_allowed=int(validated.get("burst_allowed", 5)),
            enable_throttling=bool(validated.get("enable_throttling", False)),
        )

        # Caching
        caching = CachingConfig(
            enable_caching=bool(validated.get("enable_caching", False)),
            cache_ttl_sec=int(validated.get("cache_ttl_sec", 3600)),
            cache_backend=validated.get("cache_backend", "memory"),
            cache_max_size_mb=int(validated.get("cache_max_size_mb", 100)),
        )

        # Tools
        tools_config = ToolsConfig(
            enable_commands=bool(validated.get("enable_commands", True)),
            commands_optional=bool(validated.get("commands_optional", True)),
            max_command_hops=int(validated.get("max_command_hops", 1)),
            command_timeout_sec=int(validated.get("command_timeout_sec", 30)),
            allowed_functions=set(validated.get("allowed_functions", [])) or None,
        )

        # Logging
        logging_config = LoggingConfig(
            enable_logging=bool(validated.get("enable_logging", True)),
            log_level=validated.get("log_level", "INFO"),
            log_file=validated.get("log_file"),
            log_format=validated.get("log_format", "structured"),
            capture_all_inputs=bool(validated.get("capture_all_inputs", False)),
            capture_all_outputs=bool(validated.get("capture_all_outputs", False)),
        )

        # System prompts
        system_prompts = validated.get("system_prompts", {})

        return FullConfig(
            name=validated.get("name", "SmartAgent"),
            version=validated.get("version", "1.0"),
            description=validated.get("description", ""),
            model_provider=provider_config,
            io_config=io_config,
            model_behavior=model_behavior,
            output_style=output_style,
            memory_config=memory_config,
            mentor_config=mentor_config,
            deep_thinker_config=deep_thinker_config,
            fast_memory_config=fast_memory_config,
            rate_limiting=rate_limiting,
            caching=caching,
            tools_config=tools_config,
            logging=logging_config,
            system_prompts=system_prompts,
        )
