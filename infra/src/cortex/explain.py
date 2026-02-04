# brain/explain.py
# @cognitive - IPPOC Self-Explanation Tool

import json
import os
import sys
import time

EXPLAIN_PATH = os.getenv("AUTONOMY_EXPLAIN_PATH", "data/explainability.json")

def get_latest_explanation():
    if not os.path.exists(EXPLAIN_PATH):
        return None
    try:
        with open(EXPLAIN_PATH, "r", encoding="utf-8") as f:
            content = json.load(f)
            if isinstance(content, list):
                return content[-1] if content else None
            return content
    except Exception:
        return None

def log_decision(action: str, reason: str, intent: dict = None, observation: dict = None, result: dict = None) -> None:
    """
    Logs a structured decision to the explainability file.
    """
    data = {
        "time": time.time(),
        "decision": {
            "action": action,
            "reason": reason,
            "intent": intent,
        },
        "observation": observation or {},
        "result": result or {}
    }
    try:
        os.makedirs(os.path.dirname(EXPLAIN_PATH), exist_ok=True)
        
        # Append logic
        existing = []
        if os.path.exists(EXPLAIN_PATH):
             try:
                 with open(EXPLAIN_PATH, "r", encoding="utf-8") as f:
                     content = json.load(f)
                     if isinstance(content, list):
                         existing = content
                     elif isinstance(content, dict):
                         existing = [content]
             except json.JSONDecodeError:
                 print("[Explain] Corrupt JSON, starting fresh.")
        
        existing.append(data)
        # Keep last 100 entries max to prevent bloat
        if len(existing) > 100: existing = existing[-100:]
            
        with open(EXPLAIN_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
            print(f"[Explain] Logged decision: {action} ({reason}) to {EXPLAIN_PATH}")
    except Exception as e:
        print(f"[Explain] Failed to log decision: {e}")

def format_explanation(data):
    if not data:
        return "No explanation available (I haven't acted yet)."
    
    ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get("time", 0)))
    decision = data.get("decision", {})
    obs = data.get("observation", {})
    result = data.get("result", {})
    
    action = decision.get("action", "unknown")
    reason = decision.get("reason", "unknown")
    intent = decision.get("intent")
    
    pain = obs.get("pain_score", 0.0)
    
    # Narrative Generation
    narrative = f"[{ts}] I decided to {action.upper()} because {reason}.\n"
    
    if action == "act" and intent:
        narrative += f"My Intent was to: {intent.get('description', 'Unknown')}\n"
        narrative += f"  (Type: {intent.get('intent_type')}, Priority: {intent.get('priority', 0):.2f})\n"
        narrative += f"  (Source: {intent.get('source', 'unknown')})\n"
    
    narrative += f"\nContext:\n"
    narrative += f"  - Pain Score: {pain:.2f}\n"
    narrative += f"  - Recent Actions: {obs.get('recent_actions', 0)}\n"
    
    if result:
        narrative += f"\nOutcome:\n  {result}\n"
        
    return narrative

if __name__ == "__main__":
    data = get_latest_explanation()
    print(format_explanation(data))
