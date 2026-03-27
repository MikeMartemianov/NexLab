import subprocess
import os
from pathlib import Path
from smart_agent_arch.tools_loader import export_tool

@export_tool
def update_from_github() -> str:
    """
    Updates the smart-agent-arch package from GitHub repository while preserving local changes.
    This tool performs a 'git pull' and reinstalls dependencies if needed.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    try:
        # Check if it's a git repo
        if not (project_root / ".git").exists():
            return "Error: This project is not a git repository. Cannot update via GitHub."

        # Fetch latest changes
        subprocess.run(["git", "fetch", "origin"], cwd=str(project_root), check=True, capture_output=True, text=True)
        
        # Pull changes
        # Use --rebase to keep local changes clean or just standard pull
        result = subprocess.run(["git", "pull", "origin", "main"], cwd=str(project_root), check=True, capture_output=True, text=True)
        
        # Also run pip install -e . to ensure entrypoints/deps are refreshed
        # subprocess.run(["pip", "install", "-e", "."], cwd=str(project_root), check=True, capture_output=True, text=True)
        
        return f"Update successful!\n{result.stdout}\n\nLocal configuration and custom tools in 'utils/custom_tools/' were preserved."
        
    except subprocess.CalledProcessError as e:
        return f"Error during update: {e.stderr or e.stdout}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
