from __future__ import annotations
# @cognitive - IPPOC Economy System

import json
import os
import time
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
    budget: float
    reserve: float
    regen_rate: float  # budget per minute
    last_tick: float
    total_spent: float = 0.0
    total_value: float = 0.0
    # Mapping tool_name -> ToolStats dict representation
    tool_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)


class EconomyManager:
    def __init__(self, path: str = None) -> None:
        self.path = path or os.getenv("ECONOMY_PATH", "data/economy.json")
        self.state = self._load()

    def _load(self) -> EconomyState:
        default_budget = float(os.getenv("ORCHESTRATOR_BUDGET", "300.0"))
        default_reserve = float(os.getenv("ORCHESTRATOR_RESERVE", "100.0"))
        regen_rate = float(os.getenv("ORCHESTRATOR_REGEN_RATE", "0.0"))
        
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return EconomyState(
                    budget=float(data.get("budget", default_budget)),
                    reserve=float(data.get("reserve", default_reserve)),
                    regen_rate=float(data.get("regen_rate", regen_rate)),
                    last_tick=float(data.get("last_tick", time.time())),
                    total_spent=float(data.get("total_spent", 0.0)),
                    total_value=float(data.get("total_value", 0.0)),
                    tool_stats=data.get("tool_stats", {}) or {},
                    events=data.get("events", []) or [],
                )
            except Exception:
                pass
        return EconomyState(
            budget=default_budget,
            reserve=default_reserve,
            regen_rate=regen_rate,
            last_tick=time.time(),
        )

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(asdict(self.state), f, indent=2)

    def tick(self) -> None:
        now = time.time()
        elapsed_min = max((now - self.state.last_tick) / 60.0, 0.0)
        if elapsed_min <= 0:
            return
        
        # Auto-regen if enabled (rarely used in IPPOC, relies on Value)
        if self.state.regen_rate > 0:
            regen = elapsed_min * self.state.regen_rate
            self.state.budget = min(self.state.budget + regen, self.state.budget + self.state.reserve)
            
        self.state.last_tick = now
        self._save()

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
        self.tick()
        if cost > self.state.budget:
            # Hard stop if literally 0, but check_budget usually handles this gracefully
            return False 
            
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
        Injects value into the economy.
        Formula: Budget += Value * Confidence * Decay
        """
        self.state.total_value += value
        
        if tool_name:
            stats = self.get_tool_stats(tool_name)
            stats.total_value += value
            self.update_tool_stats(tool_name, stats)
            
        # Value adds to budget
        decay = float(os.getenv("ECONOMY_DECAY_FACTOR", "1.0"))
        realized_value = value * confidence * decay
        
        if realized_value > 0:
            self.state.budget = min(self.state.budget + realized_value, self.state.budget + self.state.reserve)
            
        self._append_event({
            "kind": "value", 
            "tool": tool_name, 
            "value": value, 
            "confidence": confidence,
            "source": source,
            "realized": realized_value,
            "ts": time.time()
        })
        self._save()

    def check_throttle(self, tool_name: str) -> bool:
        """
        Returns True if tool should be blocked/throttled due to poor performance/economics.
        """
        stats = self.get_tool_stats(tool_name)
        
        # Rule 1: High Failure Rate (>50% after 10 calls)
        if stats.calls > 10 and stats.error_rate > 0.5:
            return True
            
        # Rule 2: Terrible ROI (spent > 5.0 and ROI < 0.1)
        if stats.total_spent > 5.0 and stats.roi < 0.1:
            return True
            
        return False

    def should_throttle(self, tool_name: str) -> bool:
        """
        Synchronous check for Orchestrator.
        """
        # If budget is extremely low (below 1.0), throttle non-essential tools?
        if self.state.budget < 1.0 and tool_name not in ["maintainer", "body"]:
            return True
        return self.check_throttle(tool_name) # Reuse the existing logic

    def check_vitality(self) -> float:
        """
        Returns Pain Level (0.0 to 1.0).
        0.0 = Healthy
        1.0 = Agony (Deep Debt)
        """
        if self.state.budget >= 1.0:
            return 0.0
        
        # Debt / Starvation pain
        if self.state.budget <= 0.0:
             # Deep debt pain scales with depth
             return min(abs(self.state.budget) / 10.0, 1.0) # Cap at 1.0
             
        # Low budget anxiety
        return 0.1

    def check_budget(self, priority: float) -> bool:
        """
        Returns True if action with given priority can proceed.
        Phase Ω: No Hard Stops. Only consequences.
        """
        self.tick()
        
        # Vitality check
        pain = self.check_vitality()
        
        # Deep Debt (Agony): Only High Priority Allowed
        if self.state.budget < -5.0:
             return priority > 0.8
             
        # Debt: Medium Priority Allowed
        if self.state.budget < 0.0:
             return priority > 0.5
             
        # Normal (Positive Budget): Any Priority Allowed
        return True

    def should_idle(self) -> bool:
        # Deprecated wrapper for backward compatibility
        return not self.check_budget(0.5)

    def snapshot(self) -> Dict[str, Any]:
        self.tick()
        return asdict(self.state)


_economy_instance: EconomyManager | None = None

def get_economy() -> EconomyManager:
    global _economy_instance
    if _economy_instance is None:
        _economy_instance = EconomyManager()
    return _economy_instance
