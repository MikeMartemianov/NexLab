# SmartAgent Configuration Guide - All 12+ Customizations

## Overview

SmartAgent has been enhanced with **17 powerful customization dimensions** that control every aspect of agent behavior. Each customization is **optional and configurable** through YAML, JSON, or Python config files.

---

## The 17 Core Customizations

### **1. Response Format Control** (`output_format`)
Define how the AI structures its outputs.

```yaml
output_format: "markdown"  # text | json | markdown | html | latex
```

**Use Cases:**
- `json`: For programmatic parsing or API integration
- `markdown`: For documentation and readability
- `html`: For web display
- `latex`: For scientific publishing

**Example:**
```yaml
output_format: "json"
```

---

### **2. Maximum Response Length** (`max_response_length`)
Control output verbosity and token usage.

```yaml
max_response_length: 4000  # characters
```

**Benefit:** Prevents overly long responses, reduces latency and cost.

**Smart Defaults:**
- 4000 for quick responses
- 8000 for detailed explanations
- 16000 for research/analysis

---

### **3. Temperature (Randomness)** (`temperature`)
Control creativity vs determinism (0-2 range).

```yaml
temperature: 0.7
```

**Scale:**
- `0.0`: Deterministic, always the same answer
- `0.7`: Balanced (recommended default)
- `1.5`: Creative, varied responses
- `2.0`: Maximum randomness

**Use Cases:**
- 0.0: Fact retrieval, code generation, consistent Q&A
- 0.7: Balanced analysis, explanations
- 1.2: Brainstorming, creative writing
- 1.8: Artistic content, novel ideas

---

### **4. Nucleus Sampling** (`top_p`)
Control diversity of token selection (0-1).

```yaml
top_p: 0.9
```

**Guidance:**
- `0.5`: Conservative, typical responses
- `0.9`: Balanced (default)
- `0.99`: Very diverse

**Works with:** Often used alongside temperature for fine-tuning.

---

### **5. Top-K Sampling** (`top_k`)
Limit to top K most likely next tokens.

```yaml
top_k: 40
```

**Effect:** Prevents low-probability "crazy" tokens while maintaining diversity.

---

### **6. Output Tone** (`tone`)
Set the communicative style of responses.

```yaml
tone: "technical"  # formal | casual | technical | friendly | academic
```

**Tone Options:**
1. **formal**: Professional, structured, serious
   - Target: Corporate, legal, business contexts
   
2. **casual**: Conversational, relaxed, approachable
   - Target: Friendly support, casual learning
   
3. **technical**: Precise, jargon-rich, professional
   - Target: Engineers, scientists, advanced users
   
4. **friendly**: Warm, encouraging, supportive
   - Target: Mentoring, customer service
   
5. **academic**: Scholarly, research-oriented, detailed
   - Target: Research, papers, thorough analysis

---

### **7. Verbosity Level** (`verbose_level`)
Control how detailed responses are (0-3).

```yaml
verbose_level: 1  # 0=terse, 1=balanced, 2=detailed, 3=exhaustive
```

**Levels:**
- `0`: One sentence answers, summary only
- `1`: Balance of conciseness and completeness (default)
- `2`: Full explanations with examples
- `3`: Exhaustive, include all edge cases and details

---

### **8. Language** (`language`)
Set the response language.

```yaml
language: "ru"  # "en", "ru", "es", "fr", "de", "ja", "zh", etc.
```

**Supported:** Any ISO 639-1 language code.

---

### **9. Memory Retention Period** (`memory_retention_days`)
Auto-expire old memories to manage storage.

```yaml
memory_retention_days: 30  # days
```

**Smart Values:**
- 7: Short-term, single session focus
- 30: Monthly retention (default)
- 90: Quarterly learning
- 365: Annual knowledge base

---

### **10. Storage Backend** (`storage_backend`)
Choose where to persist memories.

```yaml
storage_backend: "sqlite"  # "memory" | "sqlite" | "redis"
```

**Backend Options:**
1. **memory**: Fast, ephemeral, ideal for testing
2. **sqlite**: Persistent local database, no external dependencies
3. **redis**: Distributed cache, multi-instance support

**Configuration per backend:**
```yaml
# SQLite
storage_backend: "sqlite"
storage_path: "./agent_memory.db"

# Redis
storage_backend: "redis"
storage_path: "redis://localhost:6379/0"
```

---

### **11. Component Intervals** (`*_interval_sec`)
Control how frequently background components run.

```yaml
mentor_interval_sec: 5.0  # How often mentor reviews main AI
```

**Component Timings:**
- **mentor_interval_sec**: Review frequency (0.5s = very responsive, 10s = batch reviews)
- **deep_thinker_max_iterations**: Maximum thinking steps (50-200)
- **fast_memory_threshold**: Matching sensitivity (0.2-0.8)

**Tuning Guide:**
- Fast response needed? Lower interval: 1-2 seconds
- Batch processing? Higher interval: 10-30 seconds
- High volume? Disable: Set enabled=false

---

### **12. Rate Limiting** (`requests_per_minute`)
Prevent API overload and manage resource usage.

```yaml
requests_per_minute: 60
requests_per_hour: 1000
burst_allowed: 5  # Temporary peak requests
enable_throttling: true
```

**Strategies:**
- **Strict**: requests_per_minute=10, burst_allowed=0
- **Balanced**: requests_per_minute=120, burst_allowed=5 (default)
- **High throughput**: requests_per_minute=500, burst_allowed=20

---

### **13. Query Caching** (`enable_caching`)
Cache responses to improve latency and reduce API calls.

```yaml
enable_caching: true
cache_ttl_sec: 3600  # Cache duration in seconds
cache_backend: "redis"  # "memory" | "redis" | "disk"
cache_max_size_mb: 100
```

**When to Use:**
- Similar queries arrive frequently → cache
- User asks same question multiple times → cache
- Real-time data requirements → disable

**Cost Savings:** Up to 90% reduction in API calls for cached queries.

---

### **14. Logging & Diagnostics** (`enable_logging`, `log_level`)
Capture behavior for debugging and auditing.

```yaml
enable_logging: true
log_level: "INFO"  # "DEBUG" | "INFO" | "WARNING" | "ERROR"
log_file: "./agent.log"
capture_all_inputs: true   # Log user queries
capture_all_outputs: false # Don't log model responses (privacy)
```

**Log Levels:**
- `DEBUG`: Verbose, everything including internal state
- `INFO`: High-level events and decisions
- `WARNING`: Issues that don't break functionality
- `ERROR`: Failures that require attention

---

### **15. Allowed Functions** (`allowed_functions`)
Security: Whitelist which external functions can be executed.

```yaml
enable_commands: true
allowed_functions:
  - "write_file"
  - "execute_code"
  - "search_docs"
```

**Security Model:**
- Empty list `[]` = all functions allowed
- Populated list = only listed functions executable
- `enabled: false` = no commands at all

---

### **16. Dynamic Tool Creation** (`utils/custom_tools`)
Extend agent capabilities by writing simple Python functions.

**How it works:**
The system automatically scans `utils/custom_tools/*.py`. Any function decorated with `@export_tool` is automatically registered as a command.

**Example Tool (`utils/custom_tools/my_tools.py`):**
```python
from smart_agent_arch.tools_loader import export_tool

@export_tool
def get_disk_usage(path: str) -> str:
    """
    Returns the disk usage for a specific path.
    :param path: The directory path to check.
    """
    import shutil
    total, used, free = shutil.disk_usage(path)
    return f"Total: {total // (2**30)}GB, Used: {used // (2**30)}GB, Free: {free // (2**30)}GB"
```

**Configuration:**
To use these tools, the command parser must be enabled:
```yaml
command_parser:
  enabled: true
max_command_hops: 1  # Allow AI to use tools and then respond
```

**Benefits:**
- **Zero-config**: Just drop a `.py` file
- **Auto-metadata**: Descriptions and arguments are extracted from docstrings
- **Safety**: Functions must be explicitly decorated with `@export_tool`

---

### **17. Self-Update System** (`update_from_github`)
Easily update the `smart-agent-arch` package to the latest version from GitHub.

**How it works:**
The system includes a pre-configured tool `update_from_github()` available in `utils/custom_tools/system_tools.py`. It performs a safely managed `git pull` from the main repository.

**Key Features:**
- **Preserves Customizations**: Does not overwrite your `utils/custom_tools/` or local config files.
- **One-Command Update**: Can be triggered directly by the AI assistant.

**Example Usage (via AI):**
> "Please update yourself from GitHub."

---

## Advanced: Component-Specific Customizations

### **Main AI Customizations**
```yaml
main_ai_timeout_sec: 30
main_ai_system_prompt_suffix: "You are..."
```

### **Mentor AI Customizations**
```yaml
mentor_enabled: true
mentor_interval_sec: 5.0
mentor_feedback_focus: "quality"  # "quality" | "efficiency" | "completeness" | "all"
mentor_max_feedback_length: 500
mentor_response_format: "text"
mentor_system_prompt_suffix: "You review..."
```

### **Deep Thinker Customizations**
```yaml
deep_thinker_enabled: true
deep_thinker_max_iterations: 50
verification_required: true  # Must verify before reporting
persistence_enabled: true    # Continue after restart
deep_thinker_response_format: "markdown"
deep_thinker_system_prompt_suffix: "You solve..."
```

### **Fast Memory Customizations**
```yaml
fast_memory_enabled: true
fast_memory_threshold: 0.34      # Match sensitivity (0-1)
fast_memory_max_hints: 3          # How many memories to inject
fast_memory_hint_format: "inline" # "inline" | "separate" | "structured"
```

---

## Complete Configuration Examples

### **Example 1: Fast, Concise API**
```yaml
temperature: 0.3
verbose_level: 0
max_response_length: 500
enable_caching: true
requests_per_minute: 200
mentor_interval_sec: 10.0
```

### **Example 2: Research & Analysis**
```yaml
temperature: 0.7
verbose_level: 2
tone: "academic"
include_citations: true
include_reasoning: true
deep_thinker_max_iterations: 100
memory_retention_days: 365
```

### **Example 3: Real-time Chat**
```yaml
temperature: 0.8
verbose_level: 1
enable_streaming: true
mentor_interval_sec: 2.0
enable_caching: false
requests_per_minute: 100
```

### **Example 4: Secure Production**
```yaml
enable_logging: true
capture_all_inputs: true
allowed_functions: ["safe_function_1", "safe_function_2"]
enable_caching: true
cache_ttl_sec: 1800
enable_throttling: true
requests_per_minute: 50
```

---

## Dynamic Configuration

### Load from YAML
```python
from smart_agent_arch.config_loader import ConfigLoader

config = ConfigLoader.from_yaml("config.yaml")
agent = UserAIFacade(config.to_dict())
```

### Load from Python Module
```python
config = ConfigLoader.from_python_module("config_custom_provider.py")
agent = UserAIFacade(config.to_dict())
```

### Load from JSON
```python
config = ConfigLoader.from_json("config.json")
agent = UserAIFacade(config.to_dict())
```

### Programmatic Configuration
```python
from smart_agent_arch.config_loader import FullConfig, ModelProviderConfig

config = FullConfig(
    name="MyAgent",
    model_provider=ModelProviderConfig(
        provider="openai",
        model="gpt-4",
        api_key="sk-...",
    ),
    model_behavior=ModelBehaviorConfig(
        temperature=0.7,
        top_p=0.9,
    ),
)
agent = UserAIFacade(config.to_dict())
```

---

## Best Practices

1. **Start with defaults** - All settings have sensible defaults
2. **Test variations** - Different tasks benefit from different settings
3. **Monitor logs** - Use logging to understand agent behavior
4. **Cache aggressively** - For repeated queries, enable caching
5. **Rate limit appropriately** - Balance cost and throughput
6. **Version your configs** - Track config changes with your code
7. **Use system prompts for domain** - Custom suffixes for specialization
8. **Tune temperature** - Critical for consistency vs creativity tradeoff

---

## Troubleshooting Configuration

| Problem | Solution |
|---------|----------|
| Responses too generic | ↑ temperature, ↑ verbose_level |
| Responses too random | ↓ temperature, ↑ top_k |
| Slow responses | ↓ max_response_length, ↓ mentor_interval_sec |
| High API costs | Enable caching, ↓ requests_per_minute |
| Inconsistent answers | ↓ temperature, disable streaming |
| Memory bloat | ↓ memory_max_items, ↓ memory_retention_days |
| Lost context | ↑ memory_max_items, ↑ memory_retention_days |
