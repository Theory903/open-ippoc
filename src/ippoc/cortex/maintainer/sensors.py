import time
import json
import asyncio
import subprocess
from pathlib import Path
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class InternalSignal(BaseModel):
    type: str
    source: str
    content: Any
    timestamp: float = time.time()
    confidence: float = 1.0

class FileSensor:
    """Monitors the instance directory for critical changes."""
    def __init__(self, watch_path: str):
        self.watch_path = Path(watch_path)
        self.last_state = self._snapshot()

    def _snapshot(self) -> Dict[str, float]:
        state = {}
        for root, _, files in os.walk(self.watch_path):
            for f in files:
                p = Path(root) / f
                try:
                    state[str(p)] = os.path.getmtime(p)
                except OSError:
                    pass
        return state

    async def detect_anomalies(self) -> List[InternalSignal]:
        current_state = self._snapshot()
        signals = []
        
        # New or modified files
        for p, mtime in current_state.items():
            if p not in self.last_state:
                signals.append(InternalSignal(
                    type="SIGHT",
                    source="sensor.fs",
                    content=f"New file detected: {os.path.basename(p)}"
                ))
            elif mtime > self.last_state[p]:
                # Only report if it's not a log file (too noisy)
                if not p.endswith(".log"):
                    signals.append(InternalSignal(
                        type="SIGHT",
                        source="sensor.fs",
                        content=f"File modified: {os.path.basename(p)}"
                    ))

        # Deleted files
        for p in self.last_state:
            if p not in current_state:
                signals.append(InternalSignal(
                    type="SIGHT",
                    source="sensor.fs",
                    content=f"File deleted: {os.path.basename(p)}"
                ))

        self.last_state = current_state
        return signals

class MemorySensor:
    """Monitors internal state and database health."""
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)

    async def check_health(self) -> List[InternalSignal]:
        signals = []
        if not self.db_path.exists():
             signals.append(InternalSignal(
                type="HEARING",
                source="sensor.memory",
                content="Database file missing!",
                confidence=1.0
            ))
        else:
            size = os.path.getsize(self.db_path)
            if size > 100 * 1024 * 1024: # 100MB
                signals.append(InternalSignal(
                    type="HEARING",
                    source="sensor.memory",
                    content=f"Database size large: {size // (1024*1024)}MB",
                    confidence=0.8
                ))
        return signals

class ProcessSensor:
    """Monitors system resources (CPU/Memory)."""
    async def check_metabolism(self) -> List[InternalSignal]:
        signals = []
        try:
            # Using 'ps' on Mac/Linux for basic stats to avoid dependencies
            cmd = ["ps", "-A", "-o", "%cpu,%mem"]
            out = subprocess.check_output(cmd).decode().splitlines()
            # Skip header
            rows = [line.split() for line in out[1:] if line.split()]
            total_cpu = sum(float(row[0]) for row in rows if row)
            total_mem = sum(float(row[1]) for row in rows if row)
            
            if total_cpu > 80.0:
                signals.append(InternalSignal(
                    type="HEARING",
                    source="sensor.process",
                    content=f"High CPU load detected: {total_cpu:.1f}%",
                    confidence=0.9
                ))
            if total_mem > 50.0: # 50% of available mem? actually %mem in ps is per process relative to total
                 pass # Too complex to aggregate correctly without psutil, but let's just use it as a probe
        except Exception:
            pass
        return signals

async def run_sensor_loop(interval: int = 60, cortex_url: str = "http://localhost:8001"):
    instance_dir = os.getenv("IPPOC_INSTANCE_DIR", "data")
    db_path = os.getenv("CHAT_DB_PATH", "data/state/chat_rooms.json")
    
    fs_sensor = FileSensor(instance_dir)
    mem_sensor = MemorySensor(db_path)
    proc_sensor = ProcessSensor()
    
    # Needs requests for ingest
    import requests
    api_key = os.getenv("IPPOC_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    while True:
        try:
            signals = []
            signals.extend(await fs_sensor.detect_anomalies())
            signals.extend(await mem_sensor.check_health())
            signals.extend(await proc_sensor.check_metabolism())
            
            for s in signals:
                # Ingest into Cortex
                try:
                    requests.post(f"{cortex_url}/v1/signals/ingest", json=s.dict(), headers=headers, timeout=5)
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"[SensorLoop] Error: {e}")
            
        await asyncio.sleep(interval)
