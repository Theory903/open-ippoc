"""
IPPOC Authentication Bootstrap.
Central source of truth for API keys and trust roots.
"""
import os

DEFAULT_LOCAL_API_KEY = "ippoc-local-dev-key"

def get_api_key() -> str:
    """
    Retrieve the active API key for this runtime.
    
    Behavior:
    - If DEV_MODE=true: Fallback to default key if missing
    - If DEV_MODE=false: Fail fast if key is missing
    """
    dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"
    api_key = os.getenv("IPPOC_API_KEY")
    
    if api_key:
        return api_key
    
    if dev_mode:
        return DEFAULT_LOCAL_API_KEY
    
    raise RuntimeError("IPPOC_API_KEY is required in production mode. Set DEV_MODE=true to use default key.")
