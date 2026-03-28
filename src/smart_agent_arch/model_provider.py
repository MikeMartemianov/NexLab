"""Model provider resolution and connection management."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from smart_agent_arch.config_loader import FullConfig, ModelProviderConfig
from smart_agent_arch.exceptions import ConfigurationError

def _sanitize_base_url(url: str | None) -> str | None:
    """Strip redundant suffixes from base_url to prevent double-appends."""
    if not url:
        return url
    
    url = url.rstrip("/")
    # We DO NOT strip /v1 because many providers (Cerebras, Groq, OpenAI) expect it in base_url
    suffixes = ["/chat/completions", "/api/chat"]
    
    changed = True
    while changed:
        changed = False
        for s in suffixes:
            if url.endswith(s):
                url = url[:-len(s)].rstrip("/")
                changed = True
                break
    return url


class ModelProvider(ABC):
    """Abstract base for model provider implementations."""
    pass

class GlobalProviderCache:
    """Cache for ModelProvider instances to avoid redundant SDK client overhead."""
    _instances: dict[int, ModelProvider] = {}

    @classmethod
    def get(cls, config: ModelProviderConfig) -> ModelProvider | None:
        # Create a stable hash based on core config fields
        config_key = hash((
            config.provider, 
            config.model, 
            config.api_key, 
            config.base_url,
            config.timeout_sec,
            config.custom_module_path,
            config.custom_function_name
        ))
        return cls._instances.get(config_key)

    @classmethod
    def set(cls, config: ModelProviderConfig, provider: ModelProvider) -> None:
        config_key = hash((
            config.provider, 
            config.model, 
            config.api_key, 
            config.base_url,
            config.timeout_sec,
            config.custom_module_path,
            config.custom_function_name
        ))
        cls._instances[config_key] = provider

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
        self.base_url = _sanitize_base_url(config.base_url) or "https://api.openai.com/v1"
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


class OpenRouterProvider(OpenAIProvider):
    """OpenRouter API provider (uses OpenAI compatible endpoints)."""
    def __init__(self, config: ModelProviderConfig) -> None:
        super().__init__(config)
        self.base_url = _sanitize_base_url(config.base_url) or "https://openrouter.ai/api/v1"
        if not self.model:
            self.model = "google/gemma-3-4b-it:free"

class OllamaProvider(ModelProvider):
    """Ollama local model provider."""

    def __init__(self, config: ModelProviderConfig) -> None:
        self.config = config
        self.model = config.model
        self.base_url = _sanitize_base_url(config.base_url) or "http://localhost:11434"

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
        "openrouter": OpenRouterProvider,
    }

    @staticmethod
    def resolve(config: FullConfig | dict[str, Any], override: ModelProviderConfig | None = None) -> ModelProvider:
        """Resolve model provider from configuration."""
        if isinstance(config, dict):
            from smart_agent_arch.config_loader import ConfigLoader
            config = ConfigLoader.from_dict(config)

        provider_config = override or config.model_provider
        
        # Check cache first to avoid redundant SDK client overhead
        cached = GlobalProviderCache.get(provider_config)
        if cached:
            return cached

        provider_name = provider_config.provider.lower()
        provider = None

        if provider_name == "custom" and provider_config.custom_module_path:
            provider = ModelResolver._resolve_custom_file(provider_config, config)
        elif provider_name == "custom_function":
            if config.model_provider_function:
                provider = CustomProvider(config.model_provider_function, config)
            else:
                raise ConfigurationError("provider='custom_function' specified but no function pointer provided in config")
        elif provider_name in ModelResolver.PROVIDERS:
            provider_class = ModelResolver.PROVIDERS[provider_name]
            provider = provider_class(provider_config)
        else:
            raise ConfigurationError(
                f"Unknown provider: {provider_name}. "
                f"Available: {list(ModelResolver.PROVIDERS.keys()) + ['custom', 'custom_function']}"
            )
        
        if provider:
            GlobalProviderCache.set(provider_config, provider)
            return provider
            
        raise ConfigurationError(f"Could not resolve provider: {provider_name}")

    @staticmethod
    def _resolve_custom_file(provider_config: ModelProviderConfig, config: FullConfig) -> ModelProvider:
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
        raise ConfigurationError(f"Failed to load custom provider from {path}")

    @staticmethod
    def register_provider(name: str, provider_class: type[ModelProvider]) -> None:
        """Register a custom provider implementation."""
        ModelResolver.PROVIDERS[name.lower()] = provider_class
