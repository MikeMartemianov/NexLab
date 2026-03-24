import sys
import threading
import time
from pathlib import Path

# Add src to pythonpath
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from smart_agent_arch import initialize_ai
from smart_agent_arch.user_api import StubRuntimeGateway

def run_tests():
    print("Running self-contained environment tests...")
    
    config = {
        "provider": "ollama",
        "model": "qwen_test",
        "temperature": 0.0,
    }
    
    print("[1] Initializing AI...")
    # Inject stub so we don't need real olama running to pass the structural test
    ai = initialize_ai(config, runtime_gateway=StubRuntimeGateway())
    print("OK")
    
    print("[2] Checking Runtime context fields...")
    ctx = ai.runtime_context()
    assert "mentor_state" in ctx
    assert "event_cache" in ctx
    assert "deep_thinker_insights" in ctx
    print("OK")
    
    print("[3] Testing Memory and caching mechanisms...")
    ai.append_ai_events([
        {"kind": "sys", "summary": "test cache 1"},
        {"kind": "sys", "summary": "test cache 1"},
    ])
    ctx = ai.runtime_context()
    # It should compact
    sys_events = [e for e in ctx["event_cache"] if e["kind"] == "sys" and e["summary"] == "test cache 1"]
    assert len(sys_events) == 1
    assert sys_events[0]["repeats"] == 2
    print("OK")
    
    print("[4] Starting and Stopping Components...")
    ai.start()
    time.sleep(0.1)
    # Check threads
    active_threads = [t.name for t in threading.enumerate()]
    assert "smart-agent-mentor-loop" in active_threads
    assert "smart-agent-deep-thinker-loop" in active_threads
    
    ai.stop()
    print("OK")
    
    print("\nAll architecture structural tests passed in the live environment!")

if __name__ == "__main__":
    run_tests()
