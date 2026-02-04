# brain/maintainer/observer.py
# @cognitive - IPPOC Maintainer / Nervous System

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional

from cortex.core.ledger import get_ledger
from cortex.maintainer.types import SignalSummary, PressureSource, Trend


async def collect_signals() -> SignalSummary:
    """
    Aggregates signals from:
    1. Orchestrator Ledger (Truth for errors/latency)
    2. OpenClaw Logs (Infrastructure health)
    3. Economy (Cost pressure)
    
    Returns a unified SignalSummary.
    """
    ledger = get_ledger()
    
    # 1. Gather Data (Parallel Fetch)
    # In a real impl, we might want to tail logs async, but file I/O is blocking.
    # For now, we rely heavily on the Ledger which IS async.
    
    # a. Ledger Stats (Last 100 actions)
    recent_actions = await ledger.list_recent(limit=100)
    
    # 2. Analyze Ledger
    total = len(recent_actions)
    if total == 0:
        return SignalSummary(
            pain_score=0.0,
            pressure_sources=[],
            trend=Trend.STABLE,
            confidence=0.5, # Low confidence if no history
            raw_metrics={"source": "empty_ledger"}
        )

    failures = [r for r in recent_actions if r.get("status") in ("failed", "cancelled")]
    error_count = len(failures)
    error_rate = error_count / total
    
    # Latency (avg of completed)
    completed = [r for r in recent_actions if r.get("status") == "completed" and r.get("duration_ms")]
    avg_latency = sum(r["duration_ms"] for r in completed) / len(completed) if completed else 0.0
    
    # Cost (sum of recent)
    total_cost = sum(r.get("cost_spent", 0.0) for r in recent_actions)
    
    # 3. Calculate Pain
    pressure_sources = []
    pain_score = 0.0
    
    # Rule: Error Rate > 10% is PAINFUL
    if error_rate > 0.1:
        pain_score += 0.4
        pressure_sources.append(PressureSource.ERRORS)
    if error_rate > 0.3: # Critical
        pain_score += 0.3
        
    # Rule: Latency > 2000ms (Subjective baseline) is PAINFUL
    if avg_latency > 2000:
        pain_score += 0.2
        pressure_sources.append(PressureSource.LATENCY)
        
    # Rule: Cost Spike (simple heuristic for now)
    # TODO: Compare against moving average in Economy module
    if total_cost > 5.0: # Arbitrary heuristic for "expensive burst"
        pain_score += 0.2
        pressure_sources.append(PressureSource.COST)

    pain_score = min(1.0, pain_score)

    # 4. Trend Analysis
    # Compare first 50 vs last 50? Or just simple heuristic based on recent errors
    # If most recent 10 have higher error rate than previous 90 -> DEGRADING
    recent_10 = recent_actions[:10]
    older_90 = recent_actions[10:]
    
    recent_errors = len([r for r in recent_10 if r.get("status") in ("failed", "cancelled")])
    older_errors = len([r for r in older_90 if r.get("status") in ("failed", "cancelled")])
    
    recent_error_rate = recent_errors / 10 if recent_10 else 0.0
    older_error_rate = older_errors / len(older_90) if older_90 else 0.0
    
    trend = Trend.STABLE
    if recent_error_rate > (older_error_rate * 1.5) and recent_error_rate > 0.1:
        trend = Trend.DEGRADING
    elif recent_error_rate < (older_error_rate * 0.5) and older_error_rate > 0.1:
        trend = Trend.IMPROVING

    # 5. Construct Summary
    return SignalSummary(
        pain_score=pain_score,
        pressure_sources=pressure_sources,
        trend=trend,
        confidence=0.9, # High confidence because we have Ledger data
        raw_metrics={
            "error_rate": error_rate,
            "avg_latency": avg_latency,
            "total_cost": total_cost,
            "sample_size": total
        },
        errors_last_hour=error_count, # Backwards compat
        avg_cost=total_cost / total if total else 0.0,
        success_rate=1.0 - error_rate
    )
