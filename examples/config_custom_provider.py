"""
Python configuration example with custom model provider.

Load this config with:
    config = ConfigLoader.from_python_module("config_custom_provider.py")
"""

from typing import Any


def create_model_provider(
    prompt: str,
    system_prompt: str = "",
    config: Any = None,
    **kwargs: Any,
) -> str:
    """
    Custom model provider function that can be defined in config.
    
    This example shows how to:
    - Connect to a custom LLM backend
    - Use environment-specific logic
    - Implement specialized behaviors
    
    Args:
        prompt: The user prompt
        system_prompt: System instructions
        config: The full FullConfig object
        **kwargs: Additional parameters (temperature, etc.)
    
    Returns:
        Generated text response
    """
    # Example: Connect to a local fine-tuned model
    import requests
    
    # Build the request
    payload = {
        "prompt": prompt,
        "system_prompt": system_prompt,
        "temperature": kwargs.get("temperature", 0.7),
        "max_tokens": kwargs.get("max_tokens"),
    }
    
    # Send to custom backend
    response = requests.post(
        "http://localhost:8000/generate",
        json=payload,
        timeout=config.model_provider.timeout_sec if config else 60,
    )
    
    result = response.json()
    return result.get("text", "")


# Configuration dictionary
CONFIG = {
    "name": "CustomProviderAgent",
    "version": "1.0",
    "description": "Smart agent with custom model provider function",
    
    # Use custom provider function instead of built-in providers
    "provider": "custom_function",
    "model": "local-llama-70b",
    
    # Input/Output - CUSTOMIZATION #1-2
    "input_formats": ["text"],
    "output_format": "markdown",
    "max_response_length": 6000,
    
    # Model behavior - CUSTOMIZATION #3-5
    "temperature": 0.6,
    "top_p": 0.9,
    "max_tokens": 2000,
    "frequency_penalty": 0.1,
    
    # Output style - CUSTOMIZATION #6-8
    "language": "en",
    "tone": "academic",
    "verbose_level": 2,
    "include_citations": True,
    "include_reasoning": True,
    
    # Memory - CUSTOMIZATION #9-10
    "memory_retention_days": 60,
    "storage_backend": "sqlite",
    "storage_path": "./smart_agent_memory.db",
    
    # Components - CUSTOMIZATION #11
    "mentor_interval_sec": 4.0,
    "deep_thinker_max_iterations": 75,
    "fast_memory_threshold": 0.45,
    "fast_memory_max_hints": 4,
    
    # Tools - CUSTOMIZATION #12
    "enable_commands": True,
    "max_command_hops": 2,
    
    # Rate limiting - CUSTOMIZATION #13
    "requests_per_minute": 100,
    "enable_throttling": True,
    
    # Caching - CUSTOMIZATION #14
    "enable_caching": True,
    "cache_ttl_sec": 1800,
    
    # Logging - CUSTOMIZATION #15
    "enable_logging": True,
    "log_level": "INFO",
    "capture_all_inputs": True,
    
    # Custom system prompts
    "system_prompts": {
        "main_ai_suffix": """You are an expert researcher AI specialized in computer science.
        
Your domain expertise:
- Machine learning and neural networks
- Distributed systems and concurrency
- Performance optimization
- Research paper analysis

Communication style:
- Use academic rigor and precision
- Cite papers and sources
- Explain complex concepts clearly
- Include mathematical notation when appropriate""",
        
        "mentor_ai_suffix": """You specialize in academic rigor.
Review responses for:
- Technical correctness
- Clarity of explanation
- Proper citations and sources
- Completeness of analysis""",
        
        "deep_thinker_ai_suffix": """You solve research problems through systematic analysis.
Process:
1. Formalize the problem statement
2. Review relevant literature
3. Develop theoretical framework
4. Propose solutions with proofs
5. Validate through analysis""",
    }
}


# Alternative: Load from environment
def get_config() -> dict[str, Any]:
    """
    Dynamic configuration from environment.
    Allows runtime customization without reloading config file.
    """
    import os
    
    config = dict(CONFIG)
    
    # Override from environment variables
    if os.getenv("AGENT_TEMPERATURE"):
        config["temperature"] = float(os.getenv("AGENT_TEMPERATURE"))
    
    if os.getenv("AGENT_STORAGE_PATH"):
        config["storage_path"] = os.getenv("AGENT_STORAGE_PATH")
    
    if os.getenv("AGENT_LOG_LEVEL"):
        config["log_level"] = os.getenv("AGENT_LOG_LEVEL")
    
    return config
