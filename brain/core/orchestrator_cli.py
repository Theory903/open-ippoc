import json
import sys
from typing import Any, Dict

from brain.core.bootstrap import bootstrap_tools
from brain.core.orchestrator import get_orchestrator
from brain.core.tools.base import ToolInvocationEnvelope


def _error(message: str, details: str | None = None, code: int = 1) -> None:
    payload: Dict[str, Any] = {"success": False, "error": message}
    if details:
        payload["details"] = details
    print(json.dumps(payload))
    sys.exit(code)


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        _error("No input received for orchestration.")

    try:
        payload = json.loads(raw)
    except Exception as exc:
        _error("Invalid JSON payload.", str(exc))

    try:
        bootstrap_tools()
    except Exception as exc:
        _error("Failed to bootstrap tools.", str(exc))

    try:
        envelope = ToolInvocationEnvelope(**payload)
    except Exception as exc:
        _error("Invalid tool invocation envelope.", str(exc))

    try:
        result = get_orchestrator().invoke(envelope)
        output = result.model_dump() if hasattr(result, "model_dump") else result.dict()
        print(json.dumps(output))
    except Exception as exc:
        _error("Tool invocation failed.", str(exc))


if __name__ == "__main__":
    main()
