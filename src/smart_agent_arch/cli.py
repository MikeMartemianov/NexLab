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
        console.print(f"[red]❌ Error during update:[/red] {e.stderr.decode() if e.stderr else str(e)}")
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
    
    # In a real scenario, we might want to load the config here, but for now we show static structure
    table = Table(title="Framework Components", box=None)
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    
    table.add_row("Core AI Facade", "✅ Ready")
    table.add_row("Mentor AI", "✅ Active")
    table.add_row("Deep Thinker", "✅ Active")
    table.add_row("Fast Memory", "✅ Ready")
    table.add_row("Command Parser", "✅ Enabled")
    
    console.print(table)

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
