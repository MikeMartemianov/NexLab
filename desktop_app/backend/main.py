"""NexLab AI Code Editor - Full Backend API."""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path so smart_agent_arch is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

app = FastAPI(title="NexLab AI Editor Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════ GLOBAL STATE  ═══════════
WORKSPACE_ROOT = str(PROJECT_ROOT)
_ai_facade = None


def _get_ai():
    global _ai_facade
    if _ai_facade is None:
        try:
            from smart_agent_arch.user_api import UserAIFacade
            _ai_facade = UserAIFacade(config={
                "provider": "ollama",
                "model": "llama3",
                "temperature": 0.7,
            })
        except Exception:
            _ai_facade = None
    return _ai_facade


# ═══════════ MODELS ═══════════
class FileCreateRequest(BaseModel):
    path: str
    type: str = "file"


class FileSaveRequest(BaseModel):
    path: str
    content: str


class FileDeleteRequest(BaseModel):
    path: str


class FileRenameRequest(BaseModel):
    path: str
    newName: str


class TerminalExecRequest(BaseModel):
    command: str


class ProjectCreateRequest(BaseModel):
    path: str
    name: str


class ProjectStatsResponse(BaseModel):
    fileCount: int
    dirCount: int
    totalSize: int


class ChatRequest(BaseModel):
    message: str
    context: dict = {}


class AgentConfigRequest(BaseModel):
    provider: str = "ollama"
    model: str = "llama3"
    temperature: float = 0.7
    mentorEnabled: bool = True
    deepThinkerEnabled: bool = True
    mentorInterval: int = 5
    maxResponseLength: int = 4096
    tools: dict = {}


# ═══════════ PING ═══════════
@app.get("/api/ping")
def ping():
    return {"status": "ok", "message": "NexLab AI Editor Backend is running"}


# ═══════════ FILE SYSTEM ═══════════
def _scan_dir(dir_path: str, max_depth: int = 5, current_depth: int = 0) -> list[dict]:
    """Recursively scan a directory tree."""
    if current_depth >= max_depth:
        return []

    items = []
    try:
        entries = sorted(os.listdir(dir_path), key=lambda x: (not os.path.isdir(os.path.join(dir_path, x)), x.lower()))
    except PermissionError:
        return []

    skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.mypy_cache',
                 '.pytest_cache', 'dist', 'build', '.egg-info', '.tox', '.idea', '.vscode'}

    for entry in entries:
        if entry.startswith('.') and entry not in {'.gitignore', '.env'}:
            continue

        full_path = os.path.join(dir_path, entry)
        rel_path = os.path.relpath(full_path, WORKSPACE_ROOT).replace('\\', '/')

        if os.path.isdir(full_path):
            if entry in skip_dirs:
                continue
            children = _scan_dir(full_path, max_depth, current_depth + 1)
            items.append({
                "name": entry,
                "path": "/" + rel_path,
                "type": "directory",
                "children": children,
            })
        else:
            items.append({
                "name": entry,
                "path": "/" + rel_path,
                "type": "file",
            })
    return items


@app.get("/api/files")
def list_files():
    """Return the workspace file tree."""
    return {"files": _scan_dir(WORKSPACE_ROOT)}


@app.get("/api/file")
def read_file(path: str):
    """Read file content."""
    full_path = os.path.join(WORKSPACE_ROOT, path.lstrip("/"))
    if not os.path.isfile(full_path):
        return {"error": "File not found", "content": ""}

    try:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        return {"error": str(e), "content": ""}


@app.post("/api/file/save")
def save_file(req: FileSaveRequest):
    """Save content to a file."""
    full_path = os.path.join(WORKSPACE_ROOT, req.path.lstrip("/"))
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(req.content)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/api/file/create")
def create_file(req: FileCreateRequest):
    """Create a new file or directory."""
    full_path = os.path.join(WORKSPACE_ROOT, req.path.lstrip("/"))
    try:
        if req.type == "directory":
            os.makedirs(full_path, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write("")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/api/file/delete")
def delete_file(req: FileDeleteRequest):
    """Delete a file or directory."""
    full_path = os.path.join(WORKSPACE_ROOT, req.path.lstrip("/"))
    try:
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        elif os.path.isfile(full_path):
            os.remove(full_path)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/api/file/rename")
def rename_file(req: FileRenameRequest):
    """Rename a file or directory."""
    full_path = os.path.join(WORKSPACE_ROOT, req.path.lstrip("/"))
    parent = os.path.dirname(full_path)
    new_path = os.path.join(parent, req.newName)
    try:
        os.rename(full_path, new_path)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/api/project/create")
def create_new_project(req: ProjectCreateRequest):
    """Scaffold a new agent project directory."""
    try:
        target_path = Path(req.path).resolve()
        target_path.mkdir(parents=True, exist_ok=True)

        config_path = target_path / "config.yaml"
        if not config_path.exists():
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(f"""# NexLab Agent Configuration: {req.name}
provider: openai
model: gpt-4o
temperature: 0.7
mentor_enabled: true
deep_thinker_enabled: true
""")

        main_path = target_path / "main.py"
        if not main_path.exists():
            with open(main_path, "w", encoding="utf-8") as f:
                f.write(f"""from smart_agent_arch import initialize_ai

def main():
    print("Starting NexLab Agent: {req.name}")
    ai = initialize_ai()
    response = ai.send_text("Hello, who are you?")
    print(f"Agent: {{response.content}}")

if __name__ == "__main__":
    main()
""")

        return {"status": "ok", "message": f"Project '{req.name}' created at {target_path}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/api/project/stats")
def get_project_stats():
    """Return interesting statistics about the current project."""
    try:
        file_count = 0
        total_size = 0
        for root, dirs, files in os.walk(WORKSPACE_ROOT):
            # Skip hidden and large dirs
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__')]
            for f in files:
                file_count += 1
                total_size += os.path.getsize(os.path.join(root, f))
        
        return {
            "fileCount": file_count,
            "totalSizeKb": round(total_size / 1024, 1),
            "projectName": os.path.basename(WORKSPACE_ROOT),
        }
    except Exception as e:
        return {"error": str(e)}


# ═══════════ TERMINAL ═══════════
@app.post("/api/terminal/exec")
def terminal_exec(req: TerminalExecRequest):
    """Execute a terminal command and return output."""
    try:
        result = subprocess.run(
            req.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=WORKSPACE_ROOT,
        )
        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr
        return {"output": output.strip()}
    except subprocess.TimeoutExpired:
        return {"output": "[Command timed out after 30s]"}
    except Exception as e:
        return {"output": f"[Error: {e}]"}


# ═══════════ AI CHAT ═══════════
@app.post("/api/chat")
def chat(req: ChatRequest):
    """Process a chat message through the AI facade."""
    ai = _get_ai()

    if ai is None:
        # Fallback: simple echo when AI is not configured
        return {
            "reply": (
                f"I received your message: \"{req.message[:100]}\".\n\n"
                "⚠️ The AI backend (smart-agent-arch) is initializing. "
                "Please configure a valid model provider in Agent Studio."
            ),
            "thinking": "Checking AI backend availability...",
        }

    try:
        response = ai.send_text(req.message)
        context = ai.runtime_context()

        thinking = None
        thinker_insights = context.get("thinker_insights", [])
        if thinker_insights:
            thinking = thinker_insights[-1]

        return {
            "reply": response.content if response else "No response generated.",
            "thinking": thinking,
        }
    except Exception as e:
        return {
            "reply": f"⚠️ AI Error: {str(e)}",
            "thinking": "An error occurred during processing.",
        }


# ═══════════ AGENT CONFIGURATION ═══════════
@app.post("/api/agent/configure")
def configure_agent(req: AgentConfigRequest):
    """Reconfigure the AI facade with new settings."""
    global _ai_facade
    try:
        from smart_agent_arch.user_api import UserAIFacade

        config_dict: dict[str, Any] = {
            "provider": req.provider,
            "model": req.model,
            "temperature": req.temperature,
            "mentor_enabled": req.mentorEnabled,
            "deep_thinker_enabled": req.deepThinkerEnabled,
            "mentor_interval_sec": req.mentorInterval,
            "max_response_length": req.maxResponseLength,
        }

        # Stop existing facade
        if _ai_facade:
            try:
                _ai_facade.stop()
            except Exception:
                pass

        _ai_facade = UserAIFacade(config=config_dict)
        return {"status": "ok", "message": "Agent reconfigured successfully"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/api/agent/diagnostics")
def get_diagnostics(n: int = 30):
    """Return recent diagnostic events."""
    ai = _get_ai()
    if not ai:
        return {"events": []}
    return {"events": ai.diagnostics(last_n=n)}


@app.get("/api/agent/tools")
def get_tools():
    """Return currently registered tools."""
    ai = _get_ai()
    if not ai:
        return {"tools": []}
    # UserAIFacade has _command_parser.describe()
    context = ai.runtime_context()
    return {"tools": context.get("command_parser", {}).get("commands", [])}


@app.get("/api/agent/status")
def get_status():
    """Return high-level agent status."""
    ai = _get_ai()
    if not ai:
        return {"state": "uninitialized"}
    context = ai.runtime_context()
    return {
        "state": context.get("runtime_state"),
        "mentor_state": context.get("mentor_state"),
        "deep_thinker_state": context.get("deep_thinker_state"),
        "version": "1.0.0"
    }


# ═══════════ STATIC FILES (Production) ═══════════
# In PyInstaller frozen mode, the dist folder is bundled relative to _MEIPASS
_base = os.environ.get("NEXLAB_BASE_DIR", os.path.join(os.path.dirname(__file__), ".."))
dist_path = os.path.join(_base, "desktop_app", "frontend", "dist")
if not os.path.exists(dist_path):
    # Fallback: dev mode relative path
    dist_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")


def run_server(port: int = 8000):
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    run_server()
