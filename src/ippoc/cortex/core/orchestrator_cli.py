import json
import sys
import logging

# CRITICAL: Configure logging FIRST, before any other imports that might log
# This ensures all logs go to stderr and stdout stays clean for JSON output
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
    handler.close()

# Remove any existing handlers on all loggers to prevent duplicate streams
for logger_name in logging.Logger.manager.loggerDict.keys():
    logger = logging.getLogger(logger_name)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format='%(message)s',
    force=True  # Force reconfiguration even if already configured
)

# Ensure stderr is flushed after each log message
class FlushStreamHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

# Add a flush handler to root logger
root_handler = FlushStreamHandler(sys.stderr)
root_handler.setFormatter(logging.Formatter('%(message)s'))
logging.root.addHandler(root_handler)

from typing import Any, Dict
from ippoc.cortex.core.bootstrap import bootstrap_tools
from ippoc.cortex.core.orchestrator import get_orchestrator
from ippoc.cortex.core.tools.base import ToolInvocationEnvelope


def _error(message: str, details: str | None = None, code: int = 1) -> None:
    payload: Dict[str, Any] = {"success": False, "error": message}
    if details:
        payload["details"] = details
    # Ensure output goes to stdout only - strip any trailing newlines and write cleanly
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()
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
        # Output only JSON to stdout - no logging output
        sys.stdout.write(json.dumps(output) + "\n")
        sys.stdout.flush()
    except Exception as exc:
        _error("Tool invocation failed.", str(exc))


if __name__ == "__main__":
    main()
