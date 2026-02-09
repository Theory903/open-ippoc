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
        # Check for legacy JSON list format first by peeking
        is_legacy = False
        if os.path.getsize(EXPLAIN_PATH) > 0:
            with open(EXPLAIN_PATH, "r", encoding="utf-8") as f:
                first_char = f.read(1)
                if first_char == '[':
                    is_legacy = True

        if is_legacy:
            with open(EXPLAIN_PATH, "r", encoding="utf-8") as f:
                content = json.load(f)
                if isinstance(content, list):
                    return content[-1] if content else None
                return content
        else:
            # JSONL: Read last line efficiently
            with open(EXPLAIN_PATH, "rb") as f:
                try:
                    # Seek to the end of the file
                    f.seek(0, os.SEEK_END)
                    file_size = f.tell()
                    if file_size == 0:
                        return None

                    # Go to the character before the last character
                    # (assuming last char is newline, we want to skip it)
                    f.seek(-2, os.SEEK_END)
                    while f.read(1) != b'\n':
                        f.seek(-2, os.SEEK_CUR)
                except OSError:
                    # File is small or contains one line
                    f.seek(0)

                last_line = f.readline().decode('utf-8')
                if not last_line.strip():
                     return None
                return json.loads(last_line)

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
        
        # Migration logic: Check if file exists and is in legacy format
        if os.path.exists(EXPLAIN_PATH) and os.path.getsize(EXPLAIN_PATH) > 0:
             is_legacy = False
             with open(EXPLAIN_PATH, "r", encoding="utf-8") as f:
                 if f.read(1) == '[':
                     is_legacy = True

             if is_legacy:
                 print(f"[Explain] Migrating legacy log file {EXPLAIN_PATH} to JSONL...")
                 try:
                     with open(EXPLAIN_PATH, "r", encoding="utf-8") as f:
                         content = json.load(f)

                     # Rewrite as JSONL
                     if isinstance(content, list):
                         with open(EXPLAIN_PATH, "w", encoding="utf-8") as f:
                             for entry in content:
                                 f.write(json.dumps(entry) + "\n")
                     elif isinstance(content, dict):
                          with open(EXPLAIN_PATH, "w", encoding="utf-8") as f:
                             f.write(json.dumps(content) + "\n")
                 except Exception as e:
                     print(f"[Explain] Migration failed: {e}. Proceeding with append.")

        # Append in JSONL format
        with open(EXPLAIN_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")
            
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
