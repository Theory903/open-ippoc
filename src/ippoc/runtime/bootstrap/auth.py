"""
IPPOC Authentication Bootstrap.
Central source of truth for API keys and trust roots.
"""
import os
import requests

DEFAULT_LOCAL_API_KEY = "ippoc-dev-token"
SOMA_BASE_URL = os.getenv("IPPOC_SOMA_URL", "http://localhost:8081")

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
    
    # If no API key in environment, request one from Soma
    try:
        response = requests.post(f"{SOMA_BASE_URL}/v1/auth/issue")
        if response.status_code == 200:
            data = response.json()
            return data["api_key"]
    except Exception as e:
        print(f"⚠️  Failed to get API key from Soma: {e}")
    
    if dev_mode:
        return DEFAULT_LOCAL_API_KEY
    
    raise RuntimeError("IPPOC_API_KEY is required in production mode. Set DEV_MODE=true to use default key.")

def validate_api_key(key: str) -> bool:
    """Validate API key using Soma's verification endpoint."""
    if os.getenv("DEV_MODE", "false").lower() == "true" and key == DEFAULT_LOCAL_API_KEY:
        return True
    
    try:
        response = requests.get(f"{SOMA_BASE_URL}/v1/auth/verify", headers={"Authorization": f"Bearer {key}"})
        return response.status_code == 200
    except Exception as e:
        print(f"⚠️  Failed to validate API key: {e}")
        return False
