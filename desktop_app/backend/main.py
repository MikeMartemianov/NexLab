import os
import json
import yaml
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, get_type_hints, Union
from dataclasses import is_dataclass, asdict, fields
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

app = FastAPI(title="NexLab Radiant Pro+ v2.1.0 Engine")

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

class ProjectCreateRequest(BaseModel):
    name: str

class ConfigSaveRequest(BaseModel):
    config: Dict[str, Any]

class FlowExecuteRequest(BaseModel):
    nodes: List[Dict]
    edges: List[Dict]

# --- Schema Generator (Massive 200+ Params) ---

def generate_full_schema():
    """Programmatically extracts all fields from FullConfig and its sub-dataclasses."""
    from smart_agent_arch.config_loader import (
        ModelProviderConfig, InputOutputConfig, ModelBehaviorConfig, 
        OutputStyleConfig, MemoryConfig, MentorConfig, DeepThinkerConfig, 
        FastMemoryConfig, RateLimitingConfig, CachingConfig, ToolsConfig, LoggingConfig
    )

    def get_params(cls):
        params = []
        for field in fields(cls):
            name = field.name
            f_type = field.type
            
            # Basic mapping
            p_node = {"id": name, "label": name.replace('_', ' ').capitalize()}
            
            if f_type == str or f_type == Optional[str] or "str" in str(f_type):
                p_node["type"] = "string"
                if "api_key" in name: p_node["type"] = "password"
            elif f_type == int or f_type == Optional[int] or "int" in str(f_type):
                p_node["type"] = "number"
            elif f_type == float or f_type == Optional[float] or "float" in str(f_type):
                p_node["type"] = "range"
                p_node["min"], p_node["max"], p_node["step"] = 0, 1, 0.1
            elif f_type == bool or "bool" in str(f_type):
                p_node["type"] = "boolean"
            else:
                p_node["type"] = "string" # Fallback
            
            params.append(p_node)
        return params

    return {
        "groups": [
            {"id": "core", "label": "System Metadata", "params": [
                {"id": "name", "type": "string", "label": "Agent Name"},
                {"id": "version", "type": "string", "label": "Version Tag"},
                {"id": "description", "type": "textarea", "label": "Instruction Set"},
            ]},
            {"id": "provider", "label": "LLM Engine", "params": get_params(ModelProviderConfig)},
            {"id": "behavior", "label": "Model Tuning", "params": get_params(ModelBehaviorConfig)},
            {"id": "io", "label": "Input / Output", "params": get_params(InputOutputConfig)},
            {"id": "style", "label": "Personality & Tone", "params": get_params(OutputStyleConfig)},
            {"id": "memory", "label": "Long-term Memory", "params": get_params(MemoryConfig)},
            {"id": "mentor", "label": "AI Mentor Logic", "params": get_params(MentorConfig)},
            {"id": "thinker", "label": "Deep Thinking", "params": get_params(DeepThinkerConfig)},
            {"id": "fast_mem", "label": "Fast Assist", "params": get_params(FastMemoryConfig)},
            {"id": "ops", "label": "Rate Limits & Cache", "params": get_params(RateLimitingConfig) + get_params(CachingConfig)},
            {"id": "tools", "label": "Tool Permissions", "params": get_params(ToolsConfig)},
            {"id": "logging", "label": "Diagnostics", "params": get_params(LoggingConfig)},
        ]
    }

# --- Endpoints ---

@app.get("/api/ping")
async def ping():
    return {"status": "ok", "version": "2.1.0", "theme_support": ["dark", "light"]}

@app.get("/api/projects")
async def list_projects():
    root = Path(os.getcwd())
    projects = []
    if root.exists():
        for d in root.iterdir():
            if d.is_dir() and not d.name.startswith('.'):
                config_file = d / "config.yaml"
                projects.append({
                    "name": d.name,
                    "path": str(d.absolute()),
                    "has_config": config_file.exists()
                })
    return {"projects": projects}

@app.post("/api/project/create")
async def create_project(req: ProjectCreateRequest):
    path = Path(os.getcwd()) / req.name
    if path.exists():
        raise HTTPException(status_code=400, detail="Project already exists")
    
    path.mkdir()
    config_path = path / "config.yaml"
    default_config = ConfigLoader.from_dict({"name": req.name})
    with open(config_path, "w") as f:
        yaml.dump(default_config.to_dict(), f)
    
    # Create empty flow directory
    (path / "flows").mkdir()
    
    return {"status": "created", "path": str(path.absolute())}

@app.post("/api/project/open")
async def open_project(req: ProjectOpenRequest):
    path = Path(req.path)
    state.workspace_root = path
    config_path = path / "config.yaml"
    
    if config_path.exists():
        state.current_config = ConfigLoader.from_yaml(config_path)
    else:
        state.current_config = ConfigLoader.from_dict({"name": path.name})
        with open(config_path, "w") as f:
            yaml.dump(state.current_config.to_dict(), f)
            
    return {"status": "ok", "config": state.current_config.to_dict()}

@app.get("/api/config/schema")
async def get_config_schema():
    return generate_full_schema()

@app.post("/api/config/save")
async def save_config(req: ConfigSaveRequest):
    if not state.workspace_root:
        raise HTTPException(status_code=400, detail="No active project")
    
    config_path = state.workspace_root / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(req.config, f)
    
    state.current_config = ConfigLoader.from_dict(req.config)
    return {"status": "ok"}

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
# Fix for CSS pathing: serve static assets with correct MIME types
_base = os.environ.get("NEXLAB_BASE_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dist_path = os.path.join(_base, "frontend", "dist")

if not os.path.exists(dist_path):
    # Fallback to current file's relative path for dev
    dist_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")

if os.path.exists(dist_path):
    # Mount assets folder explicitly to ensure correct path resolution
    assets_path = os.path.join(dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    
    # Mount the rest of the dist folder
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")

def run_server(port: int = 8000):
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    run_server()
