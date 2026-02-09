"""
IPPOC Runtime Port Registry.
Single source of truth for all service bindings.
"""

PORTS = {
    "cortex": 8000,
    "soma": 8081,
    "telemetry": 8002, 
    "redis": 6379,
}

def get_port(service: str, default: int = 8000) -> int:
    return PORTS.get(service, default)
