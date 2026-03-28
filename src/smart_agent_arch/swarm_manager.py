import asyncio
import json
import logging
import threading
from dataclasses import dataclass, field
from queue import Queue
from typing import Any, Callable, Dict, List, Optional

from smart_agent_arch import initialize_ai
from smart_agent_arch.user_api import UserAIFacade

logger = logging.getLogger(__name__)

@dataclass
class SwarmMessage:
    topic: str
    sender_id: str
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)

class MessageBroker:
    """Publish-Subscribe message broker for Swarm agents."""
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[SwarmMessage], None]]] = {}
        self._lock = threading.RLock()

    def subscribe(self, topic: str, callback: Callable[[SwarmMessage], None]):
        with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            if callback not in self._subscribers[topic]:
                self._subscribers[topic].append(callback)

    def unsubscribe(self, topic: str, callback: Callable[[SwarmMessage], None]):
        with self._lock:
            if topic in self._subscribers and callback in self._subscribers[topic]:
                self._subscribers[topic].remove(callback)

    def publish(self, message: SwarmMessage):
        with self._lock:
            subs = self._subscribers.get(message.topic, []) + self._subscribers.get("*", [])
        for sub in set(subs):
            try:
                sub(message)
            except Exception as e:
                logger.error(f"Error in subscriber callback for topic {message.topic}: {e}")

class SwarmManager:
    """Orchestrates multiple UserAIFacade instances to form a Swarm Intelligence network."""
    
    def __init__(self):
        self.broker = MessageBroker()
        self.agents: Dict[str, UserAIFacade] = {}
        self._agent_threads: Dict[str, threading.Thread] = {}
        self._running = False
        self._lock = threading.RLock()

    def add_agent(self, agent_id: str, config: dict | str):
        """Add a new agent to the swarm."""
        with self._lock:
            if agent_id in self.agents:
                raise ValueError(f"Agent {agent_id} already exists in swarm.")
            
            ai = initialize_ai(config)
            
            # Setup agent interception (if you want the agent to automatically listen to certain topics)
            # In a real swarm, tools would wrap broker.publish logic so the agent sends messages via function calls
            
            self.agents[agent_id] = ai

    def get_agent(self, agent_id: str) -> Optional[UserAIFacade]:
        return self.agents.get(agent_id)

    def start_all(self):
        """Start all agents in the swarm."""
        with self._lock:
            if self._running:
                return
            self._running = True
            for agent_id, agent in self.agents.items():
                agent.start()
                logger.info(f"Swarm agent started: {agent_id}")

    def stop_all(self):
        """Stop all agents in the swarm."""
        with self._lock:
            if not self._running:
                return
            self._running = False
            for agent_id, agent in self.agents.items():
                agent.stop()
                logger.info(f"Swarm agent stopped: {agent_id}")

    def broadcast(self, topic: str, sender: str, content: Any, metadata: dict = None):
        """Helper to quickly publish a message."""
        msg = SwarmMessage(topic=topic, sender_id=sender, content=content, metadata=metadata or {})
        self.broker.publish(msg)

    def run_until_complete(self):
        """Block until all agents signal completion (for test scripts)."""
        import time
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_all()

# Global singleton for plugins or UI access if needed
_global_swarm = SwarmManager()

def get_swarm() -> SwarmManager:
    return _global_swarm
