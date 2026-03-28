import os
import asyncio
from pathlib import Path
from smart_agent_arch.live_runtime import start_live_chat
from smart_agent_arch.config_loader import ConfigLoader

async def run_pack():
    current_dir = Path(__file__).parent
    
    # Load configuration
    config_file = current_dir / "agent_config.yaml"
    config = ConfigLoader.from_yaml(config_file)
    
    # Path to custom tools for this specific pack
    tools_dir = current_dir / "tools"
    
    print(f"[*] Starting CoderAgent Pack with isolated tools...")
    await start_live_chat(config, custom_tools_dir=str(tools_dir))

if __name__ == "__main__":
    try:
        asyncio.run(run_pack())
    except KeyboardInterrupt:
        print("\n[!] Pack execution terminated.")
