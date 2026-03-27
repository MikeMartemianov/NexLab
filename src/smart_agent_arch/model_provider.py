"""Model provider resolution and connection management."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from smart_agent_arch.config_loader import FullConfig, ModelProviderConfig
from smart_agent_arch.exceptions import ConfigurationError


class ModelProvider(ABC):
    """Abstract base for model provider implementations."""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        """Generate completion from the model."""
        ...

    @abstractmethod
    def complete_sync(
        self,
        prompt: str,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        """Synchronous completion (for compatibility)."""
        ...


class OpenAIProvider(ModelProvider):
    """OpenAI API provider."""

    def __init__(self, config: ModelProviderConfig) -> None:
        self.config = config
        self.api_key = config.api_key
        self.model = config.model
        self.base_url = config.base_url or "https://api.openai.com/v1"
        self._client = None

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        """Generate completion using OpenAI API."""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ConfigurationError("openai package not installed")

        if not self.api_key and "api.openai.com" in self.base_url:
            raise ConfigurationError("OpenAI API key not configured")

        client = AsyncOpenAI(api_key=self.api_key or "dummy", base_url=self.base_url)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=kwargs.get("temperature", self.config.model_kwargs.get("temperature", 0.7)),
            top_p=kwargs.get("top_p", self.config.model_kwargs.get("top_p", 0.9)),
            max_tokens=kwargs.get("max_tokens"),
            timeout=self.config.timeout_sec,
        )

        return response.choices[0].message.content or ""

    def complete_sync(
        self,
        prompt: str,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        """Synchronous completion using OpenAI."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ConfigurationError("openai package not installed")

        if not self.api_key and "api.openai.com" in self.base_url:
            raise ConfigurationError("OpenAI API key not configured")

        client = OpenAI(api_key=self.api_key or "dummy", base_url=self.base_url)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=kwargs.get("temperature", self.config.model_kwargs.get("temperature", 0.7)),
            top_p=kwargs.get("top_p", self.config.model_kwargs.get("top_p", 0.9)),
            max_tokens=kwargs.get("max_tokens"),
            timeout=self.config.timeout_sec,
        )

        return response.choices[0].message.content or ""


class OllamaProvider(ModelProvider):
    """Ollama local model provider."""

    def __init__(self, config: ModelProviderConfig) -> None:
        self.config = config
        self.model = config.model
        self.base_url = config.base_url or "http://localhost:11434"

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        """Generate completion using Ollama."""
        import aiohttp

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get("temperature", 0.7),
                        "top_p": kwargs.get("top_p", 0.9),
                    },
                },
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_sec),
            ) as resp:
                result = await resp.json()
                return result.get("message", {}).get("content", "")

    def complete_sync(
        self,
        prompt: str,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        """Synchronous completion using Ollama."""
        import requests

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "top_p": kwargs.get("top_p", 0.9),
                },
            },
            timeout=self.config.timeout_sec,
        )
        response.raise_for_status()
        result = response.json()
        return result.get("message", {}).get("content", "")


class AnthropicProvider(ModelProvider):
    """Anthropic Claude API provider."""

    def __init__(self, config: ModelProviderConfig) -> None:
        self.config = config
        self.api_key = config.api_key
        self.model = config.model

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        """Generate completion using Anthropic."""
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ConfigurationError("anthropic package not installed")

        if not self.api_key:
            raise ConfigurationError("Anthropic API key not configured")

        client = AsyncAnthropic(api_key=self.api_key)

        response = await client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 1024),
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", self.config.model_kwargs.get("temperature", 0.7)),
        )

        return response.content[0].text if response.content else ""

    def complete_sync(
        self,
        prompt: str,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        """Synchronous completion using Anthropic."""
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ConfigurationError("anthropic package not installed")

        if not self.api_key:
            raise ConfigurationError("Anthropic API key not configured")

        client = Anthropic(api_key=self.api_key)

        response = client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 1024),
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", self.config.model_kwargs.get("temperature", 0.7)),
        )

        return response.content[0].text if response.content else ""


class CustomProvider(ModelProvider):
    """Custom user-provided provider function."""

    def __init__(self, provider_func: callable, config: FullConfig) -> None:
        self.provider_func = provider_func
        self.config = config

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        """Generate completion using custom provider."""
        # Call async version if available
        if hasattr(self.provider_func, "__call__"):
            result = self.provider_func(
                prompt=prompt,
                system_prompt=system_prompt,
                config=self.config,
                **kwargs,
            )
            if hasattr(result, "__await__"):
                return await result
            return result
        raise ConfigurationError("Custom provider function not callable")

    def complete_sync(
        self,
        prompt: str,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        """Synchronous completion using custom provider."""
        return self.provider_func(
            prompt=prompt,
            system_prompt=system_prompt,
            config=self.config,
            **kwargs,
        )


class ModelResolver:
    """Resolve and instantiate model providers from configuration."""

    PROVIDERS = {
        "openai": OpenAIProvider,
        "ollama": OllamaProvider,
        "anthropic": AnthropicProvider,
    }

    @staticmethod
    def resolve(config: FullConfig, override: ModelProviderConfig | None = None) -> ModelProvider:
        """Resolve model provider from configuration."""
        # Check for custom provider function first (if initialized directly from Python)
        if config.model_provider_function:
            return CustomProvider(config.model_provider_function, config)

        # Resolve built-in or dynamically loaded provider
        provider_config = override if override else config.model_provider
        provider_name = provider_config.provider.lower()
        
        if provider_name == "custom" and provider_config.custom_module_path:
            import importlib.util
            from pathlib import Path
            path = Path(provider_config.custom_module_path).resolve()
            spec = importlib.util.spec_from_file_location("custom_provider_mod", str(path))
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                func_name = provider_config.custom_function_name or "complete_fn"
                if hasattr(module, func_name):
                    return CustomProvider(getattr(module, func_name), config)
            raise ConfigurationError(f"Failed to load custom provider '{func_name}' from {path}")
        
        if provider_name == "custom_function":
            if config.model_provider_function:
                return CustomProvider(config.model_provider_function, config)
            raise ConfigurationError("provider='custom_function' specified but no function pointer provided in config")

        if provider_name not in ModelResolver.PROVIDERS:
            raise ConfigurationError(
                f"Unknown provider: {provider_name}. "
                f"Available: {list(ModelResolver.PROVIDERS.keys()) + ['custom', 'custom_function']}"
            )

        provider_class = ModelResolver.PROVIDERS[provider_name]
        return provider_class(provider_config)

    @staticmethod
    def register_provider(name: str, provider_class: type[ModelProvider]) -> None:
        """Register a custom provider implementation."""
        ModelResolver.PROVIDERS[name.lower()] = provider_class
