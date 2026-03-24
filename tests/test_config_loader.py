"""Tests for configuration loader and system prompt management."""

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest

from smart_agent_arch.config_loader import ConfigLoader, FullConfig, ModelProviderConfig
from smart_agent_arch.system_prompt_manager import SystemPromptManager
from smart_agent_arch.user_api import UserAIFacade, initialize_ai


class TestConfigLoaderFromDict:
    """Test configuration loading from dictionary."""

    def test_load_minimal_config(self) -> None:
        config = ConfigLoader.from_dict({})
        assert config.name == "SmartAgent"
        assert config.model_provider.provider == "openai"
        assert config.io_config.output_format == "text"
        assert config.model_behavior.temperature == 0.7
        assert config.output_style.tone == "neutral"

    def test_load_with_customizations(self) -> None:
        config_dict = {
            "name": "MyAgent",
            "temperature": 0.9,
            "tone": "technical",
            "language": "ru",
            "verbose_level": 2,
            "output_format": "markdown",
            "max_response_length": 6000,
        }
        config = ConfigLoader.from_dict(config_dict)
        
        assert config.name == "MyAgent"
        assert config.model_behavior.temperature == 0.9
        assert config.output_style.tone == "technical"
        assert config.output_style.language == "ru"
        assert config.output_style.verbose_level == 2
        assert config.io_config.output_format == "markdown"
        assert config.io_config.max_response_length == 6000

    def test_load_component_customizations(self) -> None:
        config_dict = {
            "mentor_interval_sec": 3.0,
            "mentor_feedback_focus": "efficiency",
            "deep_thinker_max_iterations": 75,
            "fast_memory_threshold": 0.45,
            "fast_memory_max_hints": 5,
        }
        config = ConfigLoader.from_dict(config_dict)
        
        assert config.mentor_config.interval_sec == 3.0
        assert config.mentor_config.feedback_focus == "efficiency"
        assert config.deep_thinker_config.max_iterations == 75
        assert config.fast_memory_config.matching_threshold == 0.45
        assert config.fast_memory_config.max_hints == 5

    def test_load_memory_configuration(self) -> None:
        config_dict = {
            "memory_retention_days": 90,
            "storage_backend": "sqlite",
            "storage_path": "./agent.db",
        }
        config = ConfigLoader.from_dict(config_dict)
        
        assert config.memory_config.memory_retention_days == 90
        assert config.memory_config.storage_backend == "sqlite"
        assert config.memory_config.storage_path == "./agent.db"

    def test_load_rate_limiting(self) -> None:
        config_dict = {
            "requests_per_minute": 120,
            "requests_per_hour": 5000,
            "burst_allowed": 10,
        }
        config = ConfigLoader.from_dict(config_dict)
        
        assert config.rate_limiting.requests_per_minute == 120
        assert config.rate_limiting.requests_per_hour == 5000
        assert config.rate_limiting.burst_allowed == 10

    def test_load_caching_config(self) -> None:
        config_dict = {
            "enable_caching": True,
            "cache_ttl_sec": 1800,
            "cache_backend": "redis",
        }
        config = ConfigLoader.from_dict(config_dict)
        
        assert config.caching.enable_caching is True
        assert config.caching.cache_ttl_sec == 1800
        assert config.caching.cache_backend == "redis"

    def test_temperature_validation(self) -> None:
        # Valid temperatures
        config1 = ConfigLoader.from_dict({"temperature": 0})
        assert config1.model_behavior.temperature == 0
        
        config2 = ConfigLoader.from_dict({"temperature": 1.0})
        assert config2.model_behavior.temperature == 1.0
        
        config3 = ConfigLoader.from_dict({"temperature": 2.0})
        assert config3.model_behavior.temperature == 2.0

    def test_invalid_output_format_in_dict(self) -> None:
        # Invalid types should raise ConfigurationError
        with pytest.raises(Exception):
            ConfigLoader.from_dict({"output_format": 123})

    def test_to_dict_export(self) -> None:
        config = ConfigLoader.from_dict({
            "name": "TestAgent",
            "temperature": 0.8,
            "language": "ru",
        })
        exported = config.to_dict()
        
        assert exported["name"] == "TestAgent"
        assert exported["model_behavior"]["temperature"] == 0.8
        assert exported["output_style"]["language"] == "ru"


class TestConfigLoaderFromFiles:
    """Test loading configuration from files."""

    def test_load_from_json(self) -> None:
        config_dict = {
            "name": "JsonAgent",
            "temperature": 0.6,
            "tone": "academic",
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_dict, f)
            json_path = f.name
        
        try:
            config = ConfigLoader.from_json(json_path)
            assert config.name == "JsonAgent"
            assert config.model_behavior.temperature == 0.6
            assert config.output_style.tone == "academic"
        finally:
            Path(json_path).unlink()

    def test_load_from_yaml(self) -> None:
        yaml_content = """
name: YamlAgent
temperature: 0.9
tone: technical
verbose_level: 2
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name
        
        try:
            config = ConfigLoader.from_yaml(yaml_path)
            assert config.name == "YamlAgent"
            assert config.model_behavior.temperature == 0.9
            assert config.output_style.tone == "technical"
            assert config.output_style.verbose_level == 2
        finally:
            Path(yaml_path).unlink()

    def test_missing_file_raises_error(self) -> None:
        with pytest.raises(Exception):
            ConfigLoader.from_json("/nonexistent/path/config.json")


class TestSystemPromptManager:
    """Test system prompt generation and management."""

    def test_build_base_prompts(self) -> None:
        config = ConfigLoader.from_dict({})
        prompts = SystemPromptManager.build_prompts(config)
        
        assert "primary intelligent agent" in prompts.main_ai.lower()
        assert "mentor" in prompts.mentor_ai.lower()
        assert "deep-thinking" in prompts.deep_thinker_ai.lower()
        assert "memory matcher" in prompts.fast_memory_ai.lower()

    def test_prompts_include_behavioral_instructions(self) -> None:
        config = ConfigLoader.from_dict({
            "tone": "technical",
            "verbose_level": 2,
            "language": "ru",
            "include_reasoning": True,
        })
        prompts = SystemPromptManager.build_prompts(config)
        
        # Should include tone instruction
        assert "technical" in prompts.main_ai.lower()
        # Should include verbosity instruction
        assert "detailed" in prompts.main_ai.lower()
        # Should include language instruction
        assert "ru" in prompts.main_ai.lower()

    def test_prompts_with_custom_suffixes(self) -> None:
        config = ConfigLoader.from_dict({
            "system_prompts": {
                "main_ai_suffix": "Custom main AI instruction",
                "mentor_ai_suffix": "Custom mentor instruction",
            }
        })
        prompts = SystemPromptManager.build_prompts(config)
        
        assert "Custom main AI instruction" in prompts.main_ai
        assert "Custom mentor instruction" in prompts.mentor_ai


class TestUserAIFacadeWithConfig:
    """Test UserAIFacade with configuration."""

    def test_initialize_with_dict_config(self) -> None:
        config_dict = {
            "name": "TestAgent",
            "temperature": 0.75,
            "mentor_interval_sec": 3.0,
        }
        ai = UserAIFacade(config_dict)
        
        assert ai.config["name"] == "TestAgent"
        assert ai.config["temperature"] == 0.75
        assert ai.config["mentor_interval_sec"] == 3.0

    def test_initialize_with_fullconfig_object(self) -> None:
        full_config = ConfigLoader.from_dict({
            "name": "ConfigObjectAgent",
            "temperature": 0.8,
        })
        ai = UserAIFacade(full_config)
        
        # When loading via to_dict(), structure is nested
        assert ai._full_config.name == "ConfigObjectAgent"
        assert ai._full_config.model_behavior.temperature == 0.8

    def test_memory_configuration_applied(self) -> None:
        config_dict = {
            "memory_max_items": 250,
            "importance_threshold": 0.75,
        }
        ai = UserAIFacade(config_dict)
        
        assert ai._long_memory._max_items == 250
        assert ai._long_memory._threshold == 0.75

    def test_mentor_interval_from_config(self) -> None:
        config_dict = {"mentor_interval_sec": 2.5}
        ai = UserAIFacade(config_dict)
        
        # Mentor component has the interval stored
        assert hasattr(ai._mentor, '_interval_sec')
        assert ai._mentor._interval_sec == 2.5

    def test_system_prompts_generated(self) -> None:
        config_dict = {
            "tone": "friendly",
            "verbose_level": 1,
        }
        ai = UserAIFacade(config_dict)
        
        # Check that system prompts were generated
        assert hasattr(ai, '_system_prompts')
        assert ai._system_prompts.main_ai
        assert ai._system_prompts.mentor_ai
        assert ai._system_prompts.deep_thinker_ai


class TestCustomizationDimensions:
    """Test the 15+ customization dimensions."""

    def test_all_customizations_in_defaults(self) -> None:
        """Verify all customization keys have defaults."""
        defaults = ConfigLoader.DEFAULTS
        
        # Customization #1-2: Response format
        assert "output_format" in defaults
        assert "max_response_length" in defaults
        
        # Customization #3-5: Model behavior
        assert "temperature" in defaults
        assert "top_p" in defaults
        
        # Customization #6-8: Output style
        assert "tone" in defaults
        assert "language" in defaults
        assert "verbose_level" in defaults
        
        # Customization #9-10: Memory
        assert "memory_retention_days" in defaults
        assert "storage_backend" in defaults
        
        # Customization #11: Component intervals
        assert "mentor_interval_sec" in defaults
        assert "deep_thinker_max_iterations" in defaults
        assert "fast_memory_threshold" in defaults
        
        # Customization #12-13: Tools/Commands
        assert "enable_commands" in defaults
        assert "max_command_hops" in defaults
        
        # Customization #14: Rate limiting
        assert "requests_per_minute" in defaults
        
        # Customization #15: Caching
        assert "enable_caching" in defaults
        assert "cache_ttl_sec" in defaults

    def test_minimal_agent_respects_all_customizations(self) -> None:
        """Create agent with each customization and verify it's applied."""
        config_dict = {
            # Customization #1: Response format
            "output_format": "json",
            # Customization #2: Max length
            "max_response_length": 3000,
            # Customization #3: Temperature
            "temperature": 1.2,
            # Customization #4: Top-P
            "top_p": 0.85,
            # Customization #5: Top-K (implies other model params)
            "top_k": 30,
            # Customization #6: Tone
            "tone": "formal",
            # Customization #7: Verbosity
            "verbose_level": 0,
            # Customization #8: Language
            "language": "de",
            # Customization #9: Memory retention
            "memory_retention_days": 14,
            # Customization #10: Storage backend
            "storage_backend": "sqlite",
            # Customization #11: Component intervals
            "mentor_interval_sec": 2.0,
            "deep_thinker_max_iterations": 100,
            "fast_memory_threshold": 0.50,
            # Customization #12: Tools
            "enable_commands": True,
            # Customization #13: Rate limiting
            "requests_per_minute": 80,
            # Customization #14: Caching
            "enable_caching": True,
            "cache_ttl_sec": 2400,
            # Customization #15: Logging
            "enable_logging": True,
        }
        
        config = ConfigLoader.from_dict(config_dict)
        ai = UserAIFacade(config_dict)
        
        # Verify all customizations are present
        assert config.io_config.output_format == "json"
        assert config.io_config.max_response_length == 3000
        assert config.model_behavior.temperature == 1.2
        assert config.model_behavior.top_p == 0.85
        assert config.model_behavior.top_k == 30
        assert config.output_style.tone == "formal"
        assert config.output_style.verbose_level == 0
        assert config.output_style.language == "de"
        assert config.memory_config.memory_retention_days == 14
        assert config.memory_config.storage_backend == "sqlite"
        assert config.mentor_config.interval_sec == 2.0
        assert config.deep_thinker_config.max_iterations == 100
        assert config.fast_memory_config.matching_threshold == 0.50
        assert config.tools_config.enable_commands is True
        assert config.rate_limiting.requests_per_minute == 80
        assert config.caching.enable_caching is True
        assert config.caching.cache_ttl_sec == 2400
        assert config.logging.enable_logging is True


class TestInitializationConvenience:
    """Test unified initialization with file path configs."""

    def test_initialize_from_yaml_file(self) -> None:
        yaml_content = """
name: ConvenienceAgent
temperature: 0.5
tone: casual
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name
        
        try:
            ai = initialize_ai(yaml_path)
            assert ai._full_config.name == "ConvenienceAgent"
            assert ai._full_config.model_behavior.temperature == 0.5
            assert ai._full_config.output_style.tone == "casual"
        finally:
            Path(yaml_path).unlink()

    def test_initialize_from_json_file(self) -> None:
        config_dict = {
            "name": "JsonConvenienceAgent",
            "temperature": 0.4,
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_dict, f)
            json_path = f.name
        
        try:
            ai = initialize_ai(json_path)
            assert ai._full_config.name == "JsonConvenienceAgent"
            assert ai._full_config.model_behavior.temperature == 0.4
        finally:
            Path(json_path).unlink()
