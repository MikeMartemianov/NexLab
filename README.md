# 💎 NexLab AI Framework v1.8.0

A professional-grade, agentic AI development framework for building autonomous coding assistants and smart systems.

## 🚀 Version 1.8 Highlights (NEW)
- **PyProject Config Corrected**: Fixed invalid `__version__` field in `pyproject.toml` that caused build failures.
- **Static Asset Pipeline Refined**: Fully automated static file routing for production React builds.
- **Improved App Bootstrapper**: Added legacy-compatible `/api/ping` and missing `run_server` entrypoints.
- **Pro Node Flow Engine**: Real-time visual designing with live backend node execution.
- **Swarm Intelligence**: Multi-agent coordination (Coder, Architect, Tester) via `SwarmManager`.
- **Docker Sandbox**: Secure execution of AI code inside isolated containers.
- **AR Desktop HUD**: Sleek glassmorphic desktop overlay for real-time telemetry.
- **Agent Packs Integration**: Ready-to-use isolated intelligent agents (e.g., `agent_packs/CoderAgent`).
- **Local Model Loaders**: Built-in `@export_tool` classes for instant loading of `llama.cpp` (GGUF).

## 🛠️ Quick Start
1.  **Install**: `pip install -e .` (For perception models: `pip install -e .[advanced]`)
2.  **Launch Agent Pack**: `nexlab run agent_packs/CoderAgent`
3.  **Launch GUI**: `nexlab gui` OR `nexlab gui --hud` for the AR Widget.
4.  **Open Studio**: Inside the GUI, click "Node Studio" to visually design your Swarm architecture.

## 📁 Project Structure
- `src/smart_agent_arch/`: Core framework logic.
- `desktop_app/`: Windows desktop application (FastAPI + React).
- `examples/`: Reference implementations for custom tools.

---
© 2026 NexLab AI Team. Built for the future of agentic coding.

The intended external usage is fixed around `initialize_ai(config)`.

By default, the full AI response is returned directly to the user.

Optional command parsing can be enabled in config:
- AI emits specific command words.
- Parser extracts command arguments.
- Each argument can have its own description.
- Function output can have explicit description.
- A configured Python function from a separate file is executed.
- The function result is sent back to AI.
- AI returns final user-facing answer.
- Pattern plus argument/output descriptions are auto-injected into system prompt.

Mentor AI component:
- Runs in background every 5 seconds by default.
- Receives the same runtime context as main AI.
- Observes what main AI is doing and emits coaching feedback.
- Can assign complex tasks to deep-thinker AI.
- Feedback is visible to main AI via runtime context and stored in event cache.
- On stop, important cached mentor insights are promoted to long memory (knowledge).
- Mentor can pause itself.
- `start`, `pause`, and `stop` apply to all AI components simultaneously.

Deep-thinker AI component:
- Works on complex tasks in background until solution is both found and verified.
- Does not run by fixed interval; it keeps thinking continuously while task is pending.
- Can receive tasks from mentor AI (or manual submit API).
- On verified solution, executes internal "write_long_memory" action and stores result in long memory.
- If global stop happens while task is unfinished, deep-thinker is auto-restarted to finish it.

Fast-memory assist component:
- Extremely fast matcher for topic vs deep-memory similarity.
- Works for first AI, mentor AI, and deep-thinker AI topics.
- If similar memory is found, all AI components are briefly paused.
- Relevant deep-memory hints are injected into shared runtime context.
- Components continue from their previous states immediately after injection.

## Quick start

```bash
pip install -e .[dev]
pytest
```

## Configuration System (21+ Customizations)

SmartAgent supports extensive configuration through YAML, JSON, or Python modules.

### Loading Configuration

```python
from smart_agent_arch import initialize_ai

# From dictionary
ai = initialize_ai({"temperature": 0.7, "tone": "technical"})

# From YAML file
ai = initialize_ai("config.yaml")

# From JSON file  
ai = initialize_ai("config.json")

# From Python module with custom provider
ai = initialize_ai("config_custom.py")
```

### Configuration Customizations

SmartAgent provides **21+ customization dimensions**:

**1-2. Response Format** - Control output structure and length
```yaml
output_format: "json"          # json | markdown | html | latex | text
max_response_length: 6000      # Maximum characters
```

**3-5. Model Behavior** - Fine-tune generation parameters
```yaml
temperature: 0.7               # 0 (deterministic) - 2 (creative)
top_p: 0.9                     # Nucleus sampling threshold
top_k: 40                      # Top-K sampling limit
```

**6-8. Output Style** - Set communication style
```yaml
tone: "technical"              # formal | casual | technical | friendly | academic
language: "en"                 # ISO 639-1 language code (en, ru, fr, etc.)
verbose_level: 1               # 0 (terse) - 3 (exhaustive)
```

**9-10. Memory** - Configure storage and retention
```yaml
memory_retention_days: 30      # Auto-expire old memories
storage_backend: "sqlite"      # memory | sqlite | redis
storage_path: "./agent.db"
```

**11. Component Intervals** - Control background processing speeds
```yaml
mentor_interval_sec: 5.0       # How often mentor reviews main AI
deep_thinker_max_iterations: 50
fast_memory_threshold: 0.34    # Memory matching sensitivity
```

**12-13. Tools & Commands** - Enable/control execution
```yaml
enable_commands: true
max_command_hops: 2
```

**14. Rate Limiting** - Prevent API overload
```yaml
requests_per_minute: 60
enable_throttling: false
```

**15. Caching** - Improve latency
```yaml
enable_caching: true
cache_ttl_sec: 3600
cache_backend: "redis"         # memory | redis | disk
```

**16. Dynamic Tool Creation** - Add tools by dropping Python files
```yaml
# Place tools in utils/custom_tools/ decorated with @export_tool
command_parser:
  enabled: true

**17. Self-Update System** - Update from GitHub via command
```python
# Use the tool from the AI interface:
update_from_github()
```

**18. NexLab CLI** - Command-line interface for maintenance and execution
```bash
# Update from terminal:
nexlab update

# Launch an Agent Pack:
nexlab run agent_packs/CoderAgent

# Zip and propose local changes:
nexlab pull
```

**19. Event Hook System** - Subscribe to agent lifecycle events
```python
agent.register_hook(EventKind.ON_INPUT, my_callback)
```

**20-21. Diagnostics** - Advanced health checks and detailed logging
```yaml
detailed_diagnostics: true
# Then run: nexlab doctor
```
```

### System Prompts per Component

Each AI component has an immutable base prompt that can be extended with custom instructions:

```yaml
system_prompts:
  main_ai_suffix: |
    You are analyzing technical problems.
    Be precise and thorough.
  
  mentor_ai_suffix: |
    Focus on code quality and efficiency.
  
  deep_thinker_ai_suffix: |
    Solve complex problems with rigorous analysis.
```

### Model Providers

Configure LLM connection via provider + model + API key:

```yaml
# OpenAI
provider: "openai"
model: "gpt-4-turbo"
api_key: "${OPENAI_API_KEY}"

# Anthropic
provider: "anthropic"
model: "claude-3-opus"
api_key: "${ANTHROPIC_API_KEY}"

# Ollama (local)
provider: "ollama"  
model: "llama2"
base_url: "http://localhost:11434"
```

### Custom Model Provider

For specialized backends, define a custom provider function:

```python
# config_custom.py
def create_model_provider(prompt, system_prompt="", config=None, **kwargs):
    # Connect to your custom LLM backend
    response = requests.post("http://localhost:8000/generate", json={
        "prompt": prompt, 
        "system_prompt": system_prompt,
        "temperature": kwargs.get("temperature", 0.7),
    })
    return response.json()["text"]

CONFIG = {"provider": "custom_function", "model": "custom"}
```

Load it:
```python
ai = initialize_ai("config_custom.py")
```

### Complete Example Configs

See [CUSTOMIZATION_GUIDE.md](CUSTOMIZATION_GUIDE.md) for detailed documentation of all 21+ customizations, best practices, and troubleshooting guide.

Ready-to-use example configs in `examples/`:
- `config_basic.yaml` - Essential customizations with OpenAI
- `config_advanced.yaml` - Full feature set with all customizations  
- `config_custom_provider.py` - Custom provider integration example

## Optional command parser in config

```python
from smart_agent_arch import initialize_ai

config = {
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "api_key": "${OPENAI_API_KEY}",  # Set via environment variable
    "temperature": 0.7,
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
                    "file": "./user_commands.py",
                    "name": "sum_numbers",
                },
                "description": "Adds two numbers",
            }
        ],
    },
    "max_command_hops": 1,
}

ai = initialize_ai(config)

# Model can emit command text like: RUN_SUM a=2 b=3
result = ai.send_text("Please calculate 2 + 3")
print(result.content)

# Access internal context including mentor feedback
context = ai.runtime_context()
print(context["mentor_feedback"])
```

Example function file referenced by config:

```python
def sum_numbers(a, b):
    return a + b
```
