import argparse
import subprocess
import sys
from pathlib import Path

def update_cmd():
    """Handles the 'update' command."""
    print("🚀 NexLab: Updating smart-agent-arch from GitHub...")
    
    # Try to find project root (assuming we are installed in editable mode or running from source)
    # If installed via pip, we might need a different approach, but for this dev environment:
    project_root = Path(__file__).resolve().parent.parent.parent
    
    if not (project_root / ".git").exists():
        print("❌ Error: Project root not found or not a git repository.")
        sys.exit(1)
        
    try:
        # Fetch
        subprocess.run(["git", "fetch", "origin"], cwd=str(project_root), check=True)
        # Pull
        result = subprocess.run(["git", "pull", "origin", "main"], cwd=str(project_root), check=True, capture_output=True, text=True)
        
        # Re-install in editable mode to refresh entrypoints/CLI
        print("📦 Re-installing package...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], cwd=str(project_root), check=True, capture_output=True)
        
        print("✅ Update successful!")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during update: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="NexLab AI CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Update command
    subparsers.add_parser("update", help="Update the package from GitHub")
    
    args = parser.parse_args()
    
    if args.command == "update":
        update_cmd()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
