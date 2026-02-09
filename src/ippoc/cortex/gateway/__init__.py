# brain/gateway/__init__.py
# @bridge - Gateway Layer

from .openclaw_adapter import handle_openclaw_action

__all__ = ["handle_openclaw_action"]
