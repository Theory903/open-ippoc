# brain/maintainer/scheduler.py

from brain.maintainer.observer import collect_signals
from brain.maintainer.pain import score_pain
from brain.maintainer.evolution_loop import maybe_evolve

def maintainer_tick():
    """
    The Heartbeat.
    Call this function periodically (e.g. every 5-60 mins).
    """
    print("[MAINTAINER] Tick Started...")
    
    # 1. Observe
    signals = collect_signals()
    print(f"[MAINTAINER] Observed Signals: Errors={signals.errors_last_hour}, Cost={signals.avg_cost}")
    
    # 2. Feel Pain
    pain = score_pain(signals)
    print(f"[MAINTAINER] Pain Score: Pressure={pain.upgrade_pressure}, Conf={pain.confidence}")
    
    # 3. Decide/Act
    maybe_evolve(pain, signals)
    
    print("[MAINTAINER] Tick Completed.")
