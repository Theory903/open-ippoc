import asyncio
from typing import Dict, Any
import time

_thought_queue = asyncio.Queue()

async def emit_thought(level: str, content: str, metadata: Dict[str, Any] = None):
    """
    Push a thought event into the global cognitive queue.
    """
    event = {
        "timestamp": time.time(),
        "level": level, # info, warning, intent, result
        "content": content,
        "metadata": metadata or {}
    }
    await _thought_queue.put(event)

def get_thought_queue() -> asyncio.Queue:
    return _thought_queue
