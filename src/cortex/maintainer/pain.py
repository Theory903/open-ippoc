# brain/maintainer/pain.py

from brain.maintainer.types import SignalSummary, PainScore

def score_pain(signals: SignalSummary) -> PainScore:
    """
    Converts raw system signals into a 'Pain' (Upgrade Pressure) score.
    Logic is heuristic/pattern-based, simpler than a neural net but effective.
    """
    pressure = 0.0
    domains = []
    
    # Check 1: Error Rate
    if signals.errors_last_hour > 3:
        pressure += 0.3
        domains.append("stability")
        
    # Check 2: Economic Efficiency
    if signals.avg_cost > 2.0:
        pressure += 0.3
        domains.append("economy")
        
    # Check 3: Latency Trends (Stub)
    if signals.latency_trend == "up":
        pressure += 0.2
        domains.append("performance")
        
    # Check 4: Success Rate
    if signals.success_rate < 0.8:
        pressure += 0.3
        domains.append("cognition")

    # Clamping
    pressure = min(pressure, 1.0)
    
    # Confidence calculation (simple linear mapping for now)
    confidence = 0.8 if pressure > 0.5 else 0.4
    
    return PainScore(
        upgrade_pressure=pressure,
        domains_in_pain=domains,
        confidence=confidence
    )
