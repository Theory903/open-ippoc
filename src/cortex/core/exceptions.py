# brain/core/exceptions.py

class IPPOCError(Exception):
    """Base exception for all IPPOC errors."""
    pass

class ToolExecutionError(IPPOCError):
    """Raised when a tool fails to execute correctly."""
    def __init__(self, tool_name: str, reason: str):
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"Tool '{tool_name}' failed: {reason}")

class SecurityViolation(IPPOCError):
    """Raised when a permission check or safety guard is violated."""
    def __init__(self, rule: str, context: dict = None):
        self.rule = rule
        self.context = context or {}
        super().__init__(f"Security Violation: {rule} (Context: {self.context})")

class BudgetExceeded(IPPOCError):
    """Raised when an action costs more than the available budget."""
    def __init__(self, required: float, available: float):
        self.required = required
        self.available = available
        super().__init__(f"Budget Exceeded: Required {required}, Available {available}")
