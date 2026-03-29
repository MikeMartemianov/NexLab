import os
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import logging
import uvicorn

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from smart_agent_arch.config_loader import ConfigLoader, FullConfig
from smart_agent_arch.flow_executor import FlowExecutor

app = FastAPI(title="NexLab AI v1.7.0 Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- State ---
class GlobalState:
    workspace_root: Optional[Path] = None
    current_config: Optional[FullConfig] = None
    active_executor: Optional[FlowExecutor] = None

state = GlobalState()

# --- Models ---
class ProjectOpenRequest(BaseModel):
    path: str

class ConfigSaveRequest(BaseModel):
    config: Dict[str, Any]

class FlowExecuteRequest(BaseModel):
    nodes: List[Dict]
    edges: List[Dict]

# --- Endpoints ---

@app.get("/api/ping")
async def ping():
    return {"status": "ok", "message": "NexLab AI Engine is running"}

@app.get("/api/projects")
async def list_projects():
    """List potential project directories in the current folder."""
    root = Path(os.getcwd())
    projects = []
    for d in root.iterdir():
        if d.is_dir() and not d.name.startswith('.'):
            config_file = d / "config.yaml"
            projects.append({
                "name": d.name,
                "path": str(d.absolute()),
                "has_config": config_file.exists()
            })
    return {"projects": projects}

@app.post("/api/project/open")
async def open_project(req: ProjectOpenRequest):
    path = Path(req.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Project path not found")
    
    state.workspace_root = path
    config_path = path / "config.yaml"
    
    if config_path.exists():
        state.current_config = ConfigLoader.from_yaml(config_path)
    else:
        # Create default config if missing
        state.current_config = ConfigLoader.from_dict({"name": path.name})
        with open(config_path, "w") as f:
            yaml.dump(state.current_config.to_dict(), f)
            
    return {"status": "ok", "config": state.current_config.to_dict()}

@app.get("/api/config/schema")
async def get_config_schema():
    """
    Returns a flattened schema of all 200+ parameters available in FullConfig.
    In a real implementation, this would be auto-generated from the dataclasses.
    """
    return {
        "groups": [
            {
                "id": "core",
                "label": "Core Settings",
                "params": [
                    {"id": "name", "type": "string", "label": "Agent Name", "default": "SmartAgent"},
                    {"id": "version", "type": "string", "label": "Version", "default": "1.0"},
                    {"id": "description", "type": "textarea", "label": "Description"},
                ]
            },
            {
                "id": "model",
                "label": "Model & Provider",
                "params": [
                    {"id": "provider", "type": "select", "label": "Provider", "options": ["openai", "openrouter", "ollama", "anthropic"]},
                    {"id": "model", "type": "string", "label": "Model ID"},
                    {"id": "temperature", "type": "range", "label": "Temperature", "min": 0, "max": 2, "step": 0.1},
                    {"id": "top_p", "type": "range", "label": "Top P", "min": 0, "max": 1, "step": 0.05},
                    {"id": "api_key", "type": "password", "label": "API Key"},
                    {"id": "base_url", "type": "string", "label": "Base URL Override"},
                ]
            },
            {
                "id": "components",
                "label": "Intelligence Modules",
                "params": [
                    {"id": "mentor_enabled", "type": "boolean", "label": "Enable AI Mentor"},
                    {"id": "mentor_interval_sec", "type": "number", "label": "Mentor Check Interval (s)"},
                    {"id": "deep_thinker_enabled", "type": "boolean", "label": "Enable Deep Thinker"},
                    {"id": "deep_thinker_max_iterations", "type": "number", "label": "Max Thinking Iterations"},
                    {"id": "fast_memory_enabled", "type": "boolean", "label": "Enable Fast Memory Assist"},
                ]
            },
            {
                "id": "memory",
                "label": "Memory & Storage",
                "params": [
                    {"id": "storage_backend", "type": "select", "label": "Backend", "options": ["memory", "sqlite", "redis"]},
                    {"id": "memory_max_items", "type": "number", "label": "Max History Items"},
                    {"id": "memory_retention_days", "type": "number", "label": "Retention Days"},
                ]
            }
        ]
    }

@app.post("/api/config/save")
async def save_config(req: ConfigSaveRequest):
    if not state.workspace_root:
        raise HTTPException(status_code=400, detail="No active project")
    
    config_path = state.workspace_root / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(req.config, f)
    
    state.current_config = ConfigLoader.from_dict(req.config)
    return {"status": "ok"}

# --- WebSockets for Logs ---

@app.websocket("/api/flow/ws")
async def flow_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            if state.active_executor:
                log = await state.active_executor.log_queue.get()
                await websocket.send_json(log)
            else:
                await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass

@app.post("/api/flow/execute")
async def execute_flow(req: FlowExecuteRequest, background_tasks: BackgroundTasks):
    if not state.workspace_root:
        raise HTTPException(status_code=400, detail="No active project")
    
    executor = FlowExecutor(req.nodes, req.edges, state.current_config.to_dict())
    state.active_executor = executor
    background_tasks.add_task(executor.execute)
    return {"status": "Execution started"}

# ═══════════ STATIC FILES (Production) ═══════════
_base = os.environ.get("NEXLAB_BASE_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dist_path = os.path.join(_base, "frontend", "dist")

if not os.path.exists(dist_path):
    # Fallback to current file's relative path for dev
    dist_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")

if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")

def run_server(port: int = 8000):
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    run_server()
