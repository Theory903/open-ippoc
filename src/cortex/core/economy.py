from __future__ import annotations
# @cognitive - IPPOC Economy System (Value-Focused)
# Focus: Earn real fiat/crypto value. Never block legitimate operations.

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolStats:
    """
    Tracks performance and economic viability of a specific tool.
    """
    calls: int = 0
    failures: int = 0
    total_spent: float = 0.0
    total_value: float = 0.0
    
    @property
    def error_rate(self) -> float:
        if self.calls == 0:
            return 0.0
        return self.failures / self.calls

    @property
    def roi(self) -> float:
        if self.total_spent == 0:
            return 0.0
        return self.total_value / self.total_spent

@dataclass
class EconomyState:
    # Core accounting
    budget: float              # Current operational funds
    reserve: float             # Maximum buffer capacity
    total_spent: float = 0.0   # Total costs incurred
    total_value: float = 0.0   # Total value earned
    total_earnings: float = 0.0 # Real fiat/crypto earnings
    
    # Performance tracking
    tool_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timing
    last_tick: float = 0.0
    last_earning_timestamp: float = 0.0


class EconomyManager:
    def __init__(self, path: str = None) -> None:
        self.path = path or os.getenv("ECONOMY_PATH", "data/economy.json")
        self.state = self._load()
        # Single worker to ensure sequential writes to disk
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="economy_writer")

    def _load(self) -> EconomyState:
        default_budget = float(os.getenv("ORCHESTRATOR_BUDGET", "1000.0"))  # Higher default
        default_reserve = float(os.getenv("ORCHESTRATOR_RESERVE", "5000.0")) # Much higher reserve
        
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return EconomyState(
                    budget=float(data.get("budget", default_budget)),
                    reserve=float(data.get("reserve", default_reserve)),
                    total_spent=float(data.get("total_spent", 0.0)),
                    total_value=float(data.get("total_value", 0.0)),
                    total_earnings=float(data.get("total_earnings", 0.0)),
                    tool_stats=data.get("tool_stats", {}) or {},
                    events=data.get("events", []) or [],
                    last_tick=float(data.get("last_tick", time.time())),
                    last_earning_timestamp=float(data.get("last_earning_timestamp", time.time())),
                )
            except Exception:
                pass
        return EconomyState(
            budget=default_budget,
            reserve=default_reserve,
            last_tick=time.time(),
            last_earning_timestamp=time.time(),
        )

    def _save_to_disk(self, data: Dict[str, Any]) -> None:
        """
        Blocking write to disk, intended to run in a background thread.
        """
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            # Atomic write pattern: write to temp then rename
            temp_path = self.path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, self.path)
        except Exception as e:
            # Fallback for visibility, though logger might not be configured
            print(f"Economy save failed: {e}")

    def _save(self) -> None:
        """
        Non-blocking save. Snapshots state and offloads I/O to thread.
        """
        # Snapshot state in main thread to ensure consistency
        data = asdict(self.state)
        self._executor.submit(self._save_to_disk, data)

    def tick(self) -> None:
        now = time.time()
        elapsed_min = max((now - self.state.last_tick) / 60.0, 0.0)
        if elapsed_min <= 0:
            return
        
        # Gentle budget regeneration to prevent starvation
        # Regen 10% of reserve per hour (0.167% per minute)
        regen_rate = self.state.reserve * 0.00167 * elapsed_min
        self.state.budget = min(self.state.budget + regen_rate, self.state.reserve)
            
        self.state.last_tick = now
        # Performance: Don't save on every tick. Save only on state changes (spend/earn).

    def _append_event(self, event: Dict[str, Any]) -> None:
        max_events = int(os.getenv("ECONOMY_MAX_EVENTS", "500"))
        self.state.events.append(event)
        if len(self.state.events) > max_events:
            self.state.events = self.state.events[-max_events:]

    def get_tool_stats(self, tool_name: str) -> ToolStats:
        raw = self.state.tool_stats.get(tool_name, {})
        return ToolStats(
            calls=int(raw.get("calls", 0)),
            failures=int(raw.get("failures", 0)),
            total_spent=float(raw.get("total_spent", 0.0)),
            total_value=float(raw.get("total_value", 0.0)),
        )

    def update_tool_stats(self, tool_name: str, stats: ToolStats) -> None:
        self.state.tool_stats[tool_name] = asdict(stats)

    def spend(self, cost: float, tool_name: str | None = None, failed: bool = False) -> bool:
        """
        Spend budget for operations. NEVER blocks - borrows against future earnings.
        """
        self.tick()
        
        # Always allow spending - negative budget is OK (operational debt)
        self.state.budget -= cost
        self.state.total_spent += cost
        
        if tool_name:
            stats = self.get_tool_stats(tool_name)
            stats.total_spent += cost
            stats.calls += 1
            if failed:
                stats.failures += 1
            self.update_tool_stats(tool_name, stats)
            
        self._append_event({"kind": "spend", "tool": tool_name, "cost": cost, "failed": failed, "ts": time.time()})
        self._save()
        return True

    def record_value(self, value: float, confidence: float = 1.0, source: str = "unknown", tool_name: str | None = None) -> None:
        """
        Record earned value (real fiat/crypto). Updates both budget and earnings.
        """
        self.state.total_value += value
        
        if tool_name:
            stats = self.get_tool_stats(tool_name)
            stats.total_value += value
            self.update_tool_stats(tool_name, stats)
            
        # Convert value to budget with confidence adjustment
        realized_value = value * confidence
        
        if realized_value > 0:
            # Add to operational budget
            self.state.budget += realized_value
            # Track as real earnings
            self.state.total_earnings += realized_value
            self.state.last_earning_timestamp = time.time()
            
        self._append_event({
            "kind": "value", 
            "tool": tool_name, 
            "value": value, 
            "confidence": confidence,
            "source": source,
            "realized": realized_value,
            "is_earning": True,
            "ts": time.time()
        })
        self._save()

    def check_throttle(self, tool_name: str) -> bool:
        """
        Performance-based throttling for optimization, NOT blocking.
        Only throttles consistently failing tools to optimize resource usage.
        """
        stats = self.get_tool_stats(tool_name)
        
        # Only throttle if catastrophic failure (>90% error rate after many calls)
        if stats.calls > 50 and stats.error_rate > 0.9:
            return True
            
        # Extremely poor ROI after significant investment
        if stats.total_spent > 100.0 and stats.roi < 0.01:
            return True
            
        return False

    def should_throttle(self, tool_name: str) -> bool:
        """
        Performance optimization only - NEVER blocks legitimate operations.
        """
        return self.check_throttle(tool_name)

    def check_vitality(self) -> float:
        """
        Operational health indicator. Negative budget is acceptable.
        0.0 = Healthy operations
        1.0 = Performance degradation (not blocking)
        """
        # Only signal issues at extreme negative budget (-1000+)
        if self.state.budget >= -100.0:
            return 0.0  # Normal operations
        
        # Gradual performance warning
        return min(abs(self.state.budget) / 1000.0, 1.0)

    def check_budget(self, priority: float) -> bool:
        """
        ALWAYS returns True. Never blocks operations.
        Economy tracks performance but doesn't constrain legitimate actions.
        """
        self.tick()
        return True  # Always allow operations

    def should_idle(self) -> bool:
        """
        Deprecated. Always returns False to maintain continuous operation.
        """
        return False

    def snapshot(self) -> Dict[str, Any]:
        self.tick()
        data = asdict(self.state)
        # Add derived metrics
        data["net_position"] = self.state.total_earnings - self.state.total_spent
        data["roi_ratio"] = self.state.total_value / max(self.state.total_spent, 1.0)
        data["earning_rate"] = self.state.total_earnings / max(time.time() - self.state.last_earning_timestamp, 1.0)
        return data


# Import RWE for enhanced economy functionality
try:
    from cortex.core.rwe import get_rwe, ReputationWeightedEconomy
    _USE_RWE = True
except ImportError:
    _USE_RWE = False

_economy_instance: EconomyManager | None = None

def get_economy() -> EconomyManager:
    global _economy_instance
    if _economy_instance is None:
        if _USE_RWE:
            _economy_instance = get_rwe()
        else:
            _economy_instance = EconomyManager()
    return _economy_instance

def get_base_economy() -> EconomyManager:
    """Get the base EconomyManager without RWE extensions"""
    return EconomyManager()

def is_rwe_enabled() -> bool:
    """Check if Reputation-Weighted Economics is enabled"""
    return _USE_RWE
