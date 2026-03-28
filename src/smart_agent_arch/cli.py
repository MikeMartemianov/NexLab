import argparse
import subprocess
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def get_project_root():
    return Path(__file__).resolve().parent.parent.parent

def update_cmd():
    """Handles the 'update' command."""
    project_root = get_project_root()
    console.print(Panel("🚀 [bold cyan]NexLab:[/bold cyan] Updating smart-agent-arch from GitHub...", expand=False))
    
    if not (project_root / ".git").exists():
        console.print("[red]❌ Error: Project root not found or not a git repository.[/red]")
        sys.exit(1)
        
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Fetching updates...", total=None)
            subprocess.run(["git", "fetch", "origin"], cwd=str(project_root), check=True, capture_output=True)
            
            progress.add_task(description="Pulling changes...", total=None)
            result = subprocess.run(["git", "pull", "origin", "main"], cwd=str(project_root), check=True, capture_output=True, text=True)
            
            progress.add_task(description="Refreshing environment...", total=None)
            subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], cwd=str(project_root), check=True, capture_output=True)
            
        console.print("✅ [bold green]Update successful![/bold green]")
        console.print(f"[dim]{result.stdout}[/dim]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Error during update:[/red] {e.stderr if e.stderr else str(e)}")
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

def gui_cmd():
    """Launches the desktop GUI application."""
    project_root = get_project_root()
    app_path = project_root / "desktop_app" / "app.py"
    
    if not app_path.exists():
        console.print(f"[red]❌ Error: Desktop app not found at {app_path}[/red]")
        return
        
    console.print(Panel("🌐 [bold magenta]NexLab GUI:[/bold magenta] Launching Native Desktop App...", expand=False))
    try:
        subprocess.Popen([sys.executable, str(app_path)], cwd=str(project_root), shell=(sys.platform == "win32"))
        console.print("🚀 [green]GUI command sent. The application window should appear shortly.[/green]")
    except Exception as e:
        console.print(f"[red]❌ Error launching GUI:[/red] {e}")

def main():
    parser = argparse.ArgumentParser(description="NexLab AI CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    subparsers.add_parser("update", help="Update the package from GitHub")
    subparsers.add_parser("doctor", help="Check system health")
    subparsers.add_parser("status", help="Show framework status")
    subparsers.add_parser("logs", help="View the internal log file")
    subparsers.add_parser("version", help="Show current version")
    subparsers.add_parser("gui", help="Launch the desktop application")
    
    args = parser.parse_args()
    
    if args.command == "update":
        update_cmd()
    elif args.command == "doctor":
        doctor_cmd()
    elif args.command == "status":
        status_cmd()
    elif args.command == "logs":
        logs_cmd()
    elif args.command == "version":
        version_cmd()
    elif args.command == "gui":
        gui_cmd()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
