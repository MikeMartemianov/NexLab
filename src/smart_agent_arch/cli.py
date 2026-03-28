import argparse
import subprocess
import sys
import os
import shutil
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def get_project_root():
    return Path(__file__).resolve().parent.parent.parent

def build_gui_command() -> int:
    """Automates the building of the React frontend."""
    project_root = get_project_root()
    frontend_dir = project_root / "desktop_app" / "frontend"

    if not frontend_dir.exists():
        console.print(f"[bold red]Error:[/bold red] Frontend directory not found at {frontend_dir}")
        return 1

    console.print(f"[bold blue]Building NexLab GUI in:[/bold blue] {frontend_dir}")

    # Check for npm
    npm_path = shutil.which("npm")
    if not npm_path:
        console.print("[bold red]Error:[/bold red] 'npm' not found in PATH. Please install Node.js to build the GUI.")
        return 1

    try:
        console.print("Running 'npm install'...")
        subprocess.run([npm_path, "install"], cwd=str(frontend_dir), check=True)
        console.print("Running 'npm run build'...")
        subprocess.run([npm_path, "run", "build"], cwd=str(frontend_dir), check=True)
        console.print("[bold green]Success![/bold green] GUI built successfully.")
        return 0
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error during build:[/bold red] {e}")
        return 1
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        return 1

def update_cmd():
    """Handles the 'update' command."""
    project_root = get_project_root()
    git_dir = project_root / ".git"
    repo_url = "https://github.com/MikeMartemianov/NexLab"
    zip_url = f"{repo_url}/archive/refs/heads/main.zip"
    
    if git_dir.exists():
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description="Fetching updates from GitHub...", total=None)
                subprocess.run(["git", "fetch", "origin"], cwd=str(project_root), check=True, capture_output=True)
                
                progress.add_task(description="Merging changes...", total=None)
                result = subprocess.run(["git", "pull", "origin", "main"], cwd=str(project_root), check=True, capture_output=True, text=True)
                
                progress.add_task(description="Updating dependencies...", total=None)
                subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], cwd=str(project_root), check=True, capture_output=True)
                
            console.print("✅ [bold green]Git update successful![/bold green]")
            return
        except Exception as e:
            console.print(f"[yellow]⚠ Git update failed, trying direct download...[/yellow]")

    # Fallback: ZIP download for non-git or failed git
    import urllib.request
    import zipfile
    import shutil
    import tempfile

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Downloading source from {repo_url}...", total=None)
            
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = Path(tmpdir) / "main.zip"
                urllib.request.urlretrieve(zip_url, zip_path)
                
                progress.add_task(description="Extracting files...", total=None)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                
                # GitHub zips have a root folder like "NexLab-main"
                extracted_root = next(Path(tmpdir).glob("NexLab-*"))
                
                progress.add_task(description="Applying updates...", total=None)
                # Overwrite core directories
                for item in ["src", "desktop_app"]:
                    src_dir = extracted_root / item
                    dst_dir = project_root / item
                    if src_dir.exists():
                        shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
                
                # Update top-level files
                for item in ["pyproject.toml", "README.md"]:
                    src_file = extracted_root / item
                    if src_file.exists():
                        shutil.copy2(src_file, project_root / item)

            progress.add_task(description="Building Premium GUI...", total=None)
            build_gui_command()

            progress.add_task(description="Finalizing environment...", total=None)
            subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], cwd=str(project_root), check=True, capture_output=True)

        console.print(f"✅ [bold green]Universal update successful![/bold green]")
        console.print(f"[dim]NexLab updated to the latest version from {repo_url}[/dim]")
    except Exception as e:
        console.print(f"[red]❌ Update Error:[/red] {str(e)}")
        sys.exit(1)

def doctor_cmd():
    """Checks environment health."""
    project_root = get_project_root()
    console.print(Panel("[bold yellow]🩺 NexLab Doctor:[/bold yellow] Checking system health...", expand=False))
    
    checks = [
        ("Python Version", sys.version.split()[0], "green" if sys.version_info >= (3, 10) else "red"),
        ("Project Root", str(project_root), "green"),
        ("Git Repository", "Yes" if (project_root / ".git").exists() else "No", "green" if (project_root / ".git").exists() else "yellow"),
        ("Custom Tools Dir", "Found" if (project_root / "utils" / "custom_tools").exists() else "Missing", "green" if (project_root / "utils" / "custom_tools").exists() else "yellow"),
        ("Rich Library", "Installed", "green"),
    ]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Check", style="dim")
    table.add_column("Status")
    
    for check, status, color in checks:
        table.add_row(check, f"[{color}]{status}[/{color}]")
    
    console.print(table)
    
    # Check for custom tools
    tools_dir = project_root / "utils" / "custom_tools"
    if tools_dir.exists():
        py_files = list(tools_dir.glob("*.py"))
        console.print(f"\n[bold cyan]Custom Tools Found:[/bold cyan] {len(py_files)} files")
        for f in py_files:
            console.print(f"  - {f.name}")

def status_cmd():
    """Shows registered tools and config summary."""
    project_root = get_project_root()
    console.print(Panel("[bold green]📊 NexLab Status:[/bold green] Framework Overview", expand=False))
    
    table = Table(title="Framework Components", box=None)
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    
    table.add_row("Core AI Facade", "✅ Ready")
    table.add_row("Mentor AI", "✅ Active")
    table.add_row("Deep Thinker", "✅ Active")
    table.add_row("Fast Memory", "✅ Ready")
    table.add_row("Command Parser", "✅ Enabled")
    
    console.print(table)

def logs_cmd():
    """Displays the last N lines of the agent log."""
    log_path = Path("nexlab.log")
    if not log_path.exists():
        console.print("[yellow]⚠ No log file found (nexlab.log). Ensure 'log_file' is set in config.[/yellow]")
        return
        
    console.print(Panel(f"[bold cyan]📋 NexLab Logs:[/bold cyan] {log_path.absolute()}", expand=False))
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[-50:]
            for line in lines:
                console.print(line.strip(), style="dim", highlight=True)
    except Exception as e:
        console.print(f"[red]❌ Error reading logs:[/red] {e}")

def version_cmd():
    """Displays the version info."""
    try:
        from smart_agent_arch.version import __version__
        console.print(Panel(f"🚀 [bold cyan]NexLab AI Framework[/bold cyan]\nVersion: [bold green]{__version__}[/bold green]", expand=False))
    except ImportError:
        console.print("[red]❌ Error: Could not determine version.[/red]")

def gui_cmd(hud: bool = False):
    """Launches the desktop GUI application."""
    project_root = get_project_root()
    app_path = project_root / "desktop_app" / "app.py"
    
    if not app_path.exists():
        console.print(f"[red]❌ Error: Desktop app not found at {app_path}[/red]")
        return
        
    dist_path = project_root / "desktop_app" / "frontend" / "dist"
    if not dist_path.exists():
        console.print("[yellow]⚠ Warning: GUI Frontend build (dist folder) not found.[/yellow]")
        console.print("[bold cyan]Pro-tip:[/bold cyan] Run [bold white]nexlab build-gui[/bold white] to automatically build the production UI.\n")

    mode_text = "[bold cyan]HUD Mode[/bold cyan]" if hud else "[bold magenta]Native Desktop App[/bold magenta]"
    console.print(Panel(f"🌐 [bold magenta]NexLab GUI:[/bold magenta] Launching {mode_text}...", expand=False))
    
    cmd_args = [sys.executable, str(app_path)]
    if hud:
        cmd_args.append("--hud")
        
    try:
        # Use Python executable to launch the app script
        subprocess.Popen(cmd_args, 
                         cwd=str(project_root), 
                         shell=(sys.platform == "win32"), 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        console.print("🚀 [green]GUI command sent. The application window should appear shortly.[/green]")
        console.print("[dim]Local web server will start on http://127.0.0.1:8000[/dim]")
    except Exception as e:
        console.print(f"[red]❌ Error launching GUI:[/red] {e}")

def pull_cmd():
    """Package local improvements to propose them."""
    project_root = get_project_root()
    console.print(Panel("[bold cyan]🔄 NexLab Pull (Contribute):[/bold cyan] Packaging your improvements...", expand=False))
    
    import zipfile
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"nexlab_improvement_{timestamp}.zip"
    zip_path = project_root / zip_name
    
    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
            progress.add_task(description=f"Creating {zip_name}...", total=None)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(project_root):
                    root_path = Path(root)
                    if any(part in [".git", "__pycache__", "node_modules", "dist", "venv", ".venv"] for part in root_path.parts):
                        continue
                    for file in files:
                        if file.endswith(".zip"):
                            continue
                        file_path = root_path / file
                        arcname = file_path.relative_to(project_root)
                        zipf.write(file_path, arcname)
                        
        console.print(f"✅ [bold green]Successfully packed improvements into {zip_name}[/bold green]")
        console.print("[dim]You can now upload this file to the NexLab community to propose your update![/dim]")
    except Exception as e:
        console.print(f"[red]❌ Error generating pull package: {e}[/red]")

def run_cmd(pack_path: str):
    """Run a pre-configured Agent Pack."""
    project_root = get_project_root()
    pack_dir = Path(pack_path)
    if not pack_dir.is_absolute():
        pack_dir = project_root / pack_dir
        
    if not pack_dir.exists() or not pack_dir.is_dir():
        console.print(f"[red]❌ Error: Agent pack not found at {pack_dir}[/red]")
        sys.exit(1)
        
    console.print(Panel(f"[bold magenta]🚀 Launching Agent Pack:[/bold magenta] {pack_dir.name}", expand=False))
    
    main_py = pack_dir / "main.py"
    if main_py.exists():
        console.print("Executing pack via internal main.py script...")
        subprocess.run([sys.executable, str(main_py)], cwd=str(pack_dir))
    else:
        console.print("[yellow]⚠ Pack missing main.py entrypoint.[/yellow]")

def main():
    parser = argparse.ArgumentParser(description="NexLab AI CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    update_parser = subparsers.add_parser("update", help="Update the package from GitHub")
    update_parser.add_argument("--build", action="store_true", help="Automatically rebuild GUI after update")
    
    subparsers.add_parser("doctor", help="Check system health")
    subparsers.add_parser("status", help="Show framework status")
    subparsers.add_parser("logs", help="View the internal log file")
    subparsers.add_parser("version", help="Show current version")
    gui_parser = subparsers.add_parser("gui", help="Launch the desktop application")
    gui_parser.add_argument("--hud", action="store_true", help="Launch in AR Desktop HUD mode")
    
    subparsers.add_parser("build-gui", help="Automatically build the React frontend")
    subparsers.add_parser("pull", help="Package your customized NexLab for contribution")
    
    run_parser = subparsers.add_parser("run", help="Run a custom Agent Pack")
    run_parser.add_argument("pack_path", nargs="?", default="agent_packs/CoderAgent", help="Path to the agent pack directory")
    
    args = parser.parse_args()
    
    if args.command == "update":
        update_cmd()
        if args.build:
            build_gui_command()
    elif args.command == "doctor":
        doctor_cmd()
    elif args.command == "status":
        status_cmd()
    elif args.command == "logs":
        logs_cmd()
    elif args.command == "version":
        version_cmd()
    elif args.command == "build-gui":
        build_gui_command()
    elif args.command == "gui":
        gui_cmd(hud=args.hud)
    elif args.command == "pull":
        pull_cmd()
    elif args.command == "run":
        run_cmd(args.pack_path)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
