import sys
import time
import threading
from pathlib import Path

# Add src to pythonpath
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
except ImportError:
    print("Please install rich to use the dashboard: pip install rich")
    sys.exit(1)

from smart_agent_arch import initialize_ai

console = Console()

def run_dashboard():
    config = {
        "provider": "ollama",     # Assuming local ollama for testing based on models.txt Qwen
        "model": "qwen2-vl-2b-instruct", 
        "temperature": 0.7,
        "mentor_interval_sec": 3.0,
        "deep_thinker_max_iterations": 10,
        "max_command_hops": 0
    }
    
    console.print(Panel("[bold green]Initializing Smart Agent Arch (Live Gateways!)[/]", title="System"))
    
    try:
        ai = initialize_ai(config)
        ai.start()
    except Exception as e:
        console.print(f"[bold red]Failed to initialize: {e}[/bold red]")
        sys.exit(1)
    
    console.print("[cyan]Agent is running. Type 'quit' to exit, 'task: <text>' to assign a deep thinker task.[/cyan]")
    
    # We access the private state purely for the dashboard visualization loop
    def background_monitor():
        last_mentor_count = 0
        last_thinker_task = False
        last_hints_count = 0
        
        while ai._state != "stopped":
            ctx = ai.runtime_context()
            
            # Mentor feedback
            m_feed = ctx.get("mentor_feedback", [])
            if len(m_feed) > last_mentor_count:
                for f in m_feed[last_mentor_count:]:
                    console.print(f"\n[bold yellow]🦉 Mentor:[/bold yellow] [yellow]{f}[/yellow]")
                last_mentor_count = len(m_feed)
            
            # Fast memory hints
            hints = ctx.get("fast_memory_hints", [])
            if len(hints) > last_hints_count:
                console.print(f"\n[bold blue]⚡ Fast Memory Inject:[/bold blue] [blue]Found {len(hints[-1].get('memories', []))} related memories[/blue]")
                last_hints_count = len(hints)
                
            # Deep Thinker state
            task = ctx.get("deep_thinker_task", {})
            has_task = task.get("has_task", False)
            if has_task and not last_thinker_task:
                console.print(f"\n[bold purple]🧠 Thinker:[/bold purple] [purple]Started working on: {task.get('text')}[/purple]")
            elif not has_task and last_thinker_task:
                insights = ctx.get("deep_thinker_insights", [])
                if insights:
                    console.print(f"\n[bold purple]🧠 Thinker Done:[/bold purple] [purple]{insights[-1]}[/purple]")
            last_thinker_task = has_task
                
            time.sleep(0.5)

    t = threading.Thread(target=background_monitor, daemon=True)
    t.start()

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
            if not user_input.strip():
                continue
                
            if user_input.lower() in {'quit', 'exit'}:
                break
            
            if user_input.lower().startswith("task:"):
                ai.submit_deep_task(user_input[5:].strip(), source="dashboard")
                console.print("[dim]Task submitted to background thinker.[/dim]")
                continue
                
            response = ai.send_text(user_input)
            
            if response.status == "error":
                console.print(Panel(response.content, title="[bold red]Error[/bold red]", border_style="red"))
            else:
                console.print(Panel(response.content, title=f"[bold green]AI Output ({response.metadata.get('provider', 'unknown')})[/bold green]", border_style="green"))
            
        except KeyboardInterrupt:
            break
            
    console.print("\n[bold red]Stopping agent and flushing memories...[/bold red]")
    ai.stop()
    console.print("[bold green]Graceful shutdown complete.[/bold green]")

if __name__ == "__main__":
    run_dashboard()
