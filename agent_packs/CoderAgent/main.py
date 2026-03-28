import os
import sys
from pathlib import Path
from smart_agent_arch import initialize_ai

def run_pack():
    current_dir = Path(__file__).parent
    config_file = current_dir / "agent_config.yaml"
    
    print(f"[*] Starting CoderAgent Pack with isolated tools...")
    ai = initialize_ai(config_file)
    ai.start()
    
    try:
        while True:
            sys.stdout.write("\nUser: ")
            user_input = sys.stdin.readline().strip()
            if not user_input or user_input.lower() in ['exit', 'quit']:
                break
                
            response = ai.send_text(user_input)
            print(f"\nCoderAgent:\n{response.content}")
    finally:
        ai.stop()

if __name__ == "__main__":
    try:
        run_pack()
    except KeyboardInterrupt:
        print("\n[!] Pack execution terminated.")
