import base64
import json
import logging
from pathlib import Path

# Note: Requires `pip install docker`
try:
    import docker
except ImportError:
    docker = None

from smart_agent_arch.tools_loader import export_tool

logger = logging.getLogger(__name__)

@export_tool
def execute_secure_script(python_code: str, timeout_sec: int = 15) -> str:
    """
    Executes Python code securely in an isolated Docker sandbox.
    WARNING: Use this tool whenever writing experimental or potentially unsafe code.
    
    :param python_code: The Python source code to execute.
    :param timeout_sec: Maximum execution time in seconds (default 15).
    :return: The standard output and standard error from the execution.
    """
    if not docker:
        return "Error: Docker Python SDK is not installed. Please run `pip install docker`."
        
    try:
        client = docker.from_env()
    except Exception as e:
        return f"Error connecting to Docker daemon: {str(e)}. (Is Docker Desktop running?)"

    # Base64 encode the code to pass it safely via command line to the container
    # This prevents escaping issues with quotes and newlines
    encoded_code = base64.b64encode(python_code.encode("utf-8")).decode("utf-8")
    
    # We run the command: python -c "import base64; exec(base64.b64decode('...'))"
    cmd = ["python", "-c", f"import base64; exec(base64.b64decode('{encoded_code}'))"]
    
    try:
        # Run an ephemeral alpine python container
        # Network disabled, no volumes attached, read-only root limits malicious actions
        container = client.containers.run(
            image="python:3.10-alpine",
            command=cmd,
            detach=True,
            network_disabled=True,
            mem_limit="128m",
            cpu_period=100000,
            cpu_quota=50000, # 50% of CPU max
            read_only=True,
            tmpfs={'/tmp': 'size=64m'}
        )
        
        # Wait for the container to finish or timeout
        try:
            result = container.wait(timeout=timeout_sec)
        except Exception as e: # Catch Timeout
            container.kill()
            container.remove(force=True)
            return f"Error: Execution timed out after {timeout_sec} seconds."
            
        logs = container.logs().decode("utf-8", errors="replace")
        exit_code = result.get("StatusCode", 1)
        
        container.remove(force=True)
        
        if exit_code == 0:
            return f"Execution Successful:\n{logs}"
        else:
            return f"Execution Failed (Exit Code {exit_code}):\n{logs}"
            
    except Exception as e:
        return f"Sandbox Error: {str(e)}"
