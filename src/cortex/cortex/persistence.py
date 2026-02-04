# brain/cortex/persistence.py

import json
import os
from typing import Dict
from brain.cortex.schemas import ChatRoom
from pydantic import TypeAdapter

class ChatPersistence:
    def __init__(self, storage_path: str = "data/state/chat_rooms.json"):
        self.storage_path = storage_path
        self.adapter = TypeAdapter(Dict[str, ChatRoom])
        self._ensure_dir()

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

    def save(self, rooms: Dict[str, ChatRoom]):
        """
        Persist chat rooms to disk.
        """
        try:
            # Convert Pydantic models to dict
            data = self.adapter.dump_python(rooms, mode='json')
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"[Persistence] Saved {len(rooms)} rooms to {self.storage_path}")
        except Exception as e:
            print(f"[Persistence] Save Failed: {e}")

    def load(self) -> Dict[str, ChatRoom]:
        """
        Load chat rooms from disk.
        """
        if not os.path.exists(self.storage_path):
            return {}
        
        try:
            with open(self.storage_path, 'r') as f:
                raw_data = json.load(f)
            
            # Pydantic validation
            rooms = self.adapter.validate_python(raw_data)
            print(f"[Persistence] Loaded {len(rooms)} rooms from {self.storage_path}")
            return rooms
        except Exception as e:
            print(f"[Persistence] Load Failed (Resetting): {e}")
            return {}
