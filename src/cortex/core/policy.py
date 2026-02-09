# brain/core/policy.py

import os
import json
import logging
import re
from enum import Enum
from typing import List, Dict, Any, Optional, Set
from cortex.core.tools.base import ToolInvocationEnvelope
from cortex.core.exceptions import SecurityViolation

# Configure Logging
logger = logging.getLogger("IPPOC.Policy")

class PolicyEffect(Enum):
    ALLOW = "allow"
    DENY = "deny"

class PolicyRule:
    """
    Represents a single policy rule with conditions and an effect.
    """
    def __init__(self, name: str, effect: PolicyEffect, conditions: Dict[str, Any]):
        self.name = name
        self.effect = effect
        self.conditions = conditions

    def matches(self, envelope: ToolInvocationEnvelope) -> bool:
        """
        Check if the envelope matches all conditions in this rule.
        """
        for field, expected_value in self.conditions.items():
            actual_value = self._get_field_value(envelope, field)

            # Case 1: List matching (value must be in list)
            if isinstance(expected_value, list):
                if actual_value not in expected_value:
                    return False

            # Case 2: Boolean
            elif isinstance(expected_value, bool):
                if bool(actual_value) != expected_value:
                    return False

            # Case 3: Exact match
            else:
                 if actual_value != expected_value:
                     return False
        return True

    def _get_field_value(self, envelope: ToolInvocationEnvelope, field: str) -> Any:
        """
        Helper to extract nested values using dot notation (e.g. 'context.environment').
        """
        if "." in field:
            parts = field.split(".")
            obj = envelope
            for part in parts:
                if isinstance(obj, ToolInvocationEnvelope):
                    obj = getattr(obj, part, None)
                elif isinstance(obj, dict):
                    obj = obj.get(part)
                else:
                    return None
            return obj
        else:
            return getattr(envelope, field, None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "effect": self.effect.value,
            "conditions": self.conditions
        }

class PolicyEngine:
    """
    Evaluates ToolInvocationEnvelopes against a set of policies.
    """
    def __init__(self, policy_path: Optional[str] = None):
        self.rules: List[PolicyRule] = []
        # Default behavior if no rules match.
        # To be safe and mimic previous behavior (which was mostly permissive unless restrictions were set),
        # we might need a "Default Allow" unless a Deny rule is hit, OR "Default Deny" if Allowlist exists.
        # However, the previous logic was mixed.
        # We will implement "First Match Wins".

        self.load_defaults_from_env()
        if policy_path:
            self.load_from_file(policy_path)

        # If external policies are loaded, they are appended.
        # But maybe we want them to take precedence?
        # Let's insert file-based policies at the beginning if we want them to override env vars,
        # or append if we want env vars to be "hard overrides".
        # Typically env vars are operational overrides.

        logger.info(f"PolicyEngine initialized with {len(self.rules)} rules.")

    def load_defaults_from_env(self) -> None:
        """
        Synthesize rules from legacy environment variables to ensure backward compatibility.
        """
        # 1. Kill Switch (High Priority Deny)
        if os.getenv("ORCHESTRATOR_KILL_SWITCH", "false").lower() == "true":
            self.rules.append(PolicyRule(
                name="env_kill_switch",
                effect=PolicyEffect.DENY,
                conditions={}  # Matches everything
            ))

        # 2. Tool Allowlist (If set, everything else is implicitly denied later? No, we implement explicit rules)
        # The logic was: if tool_allow set, and tool not in allow, raise.
        # So we create an ALLOW rule for the tools, and then a DENY ALL rule?
        # Wait, if we mix this with other rules, it gets complex.
        # Let's map the specific checks 1-to-1.

        tool_allow_str = os.getenv("ORCHESTRATOR_TOOL_ALLOWLIST", "")
        tool_allow = set(filter(None, tool_allow_str.split(",")))

        tool_deny_str = os.getenv("ORCHESTRATOR_TOOL_DENYLIST", "")
        tool_deny = set(filter(None, tool_deny_str.split(",")))

        # Deny List (Explicit Deny)
        if tool_deny:
            self.rules.append(PolicyRule(
                name="env_tool_denylist",
                effect=PolicyEffect.DENY,
                conditions={"tool_name": list(tool_deny)}
            ))

        # Allow List (If exists, we need to enforce it)
        # Current logic: if allowlist exists, and tool NOT in it -> Deny.
        # This implies a "Deny All" baseline effectively for tools, BUT only if the list is non-empty.
        # To represent this in rules:
        # We can't easily represent "if list is non-empty check membership" without a custom logic.
        # Alternatively: If allowlist is present, we add a rule that ALLOWs these tools.
        # AND we must add a fallback DENY for tools if this list was active.
        # But wait, there are other checks (risk, domain).

        # Let's look at the original code structure:
        # if tool_allow and name not in tool_allow: fail
        # if name in tool_deny: fail

        # This means Deny List takes precedence over Allow List? No, check logic:
        # 1. Check Allow List (if active). If fail -> Raise.
        # 2. Check Deny List. If match -> Raise.

        # So effectively:
        # Rule 1: If tool_allow is active, and NOT in list -> Deny.
        # This is hard to express as a simple "match" rule unless we support "NOT IN".
        # Or we can express it as:
        # If tool_allow active:
        #   Rule A: Match tools in allowlist -> Continue (or Allow? No, subsequent checks might fail)
        #   Rule B: Match ALL tools -> Deny.

        # Actually, the simplest way is to implement `matches` logic to support the complexity,
        # or just generate specific rules.

        if tool_allow:
            # We add a rule that DENIES if NOT in allowlist?
            # My simple engine supports "exact" or "list membership".
            # It doesn't support "NOT in list".
            # I will improve `matches` to support more complex logic or just custom logic.
            # But let's stick to simple "Allow" rules for now.

            # If we want to strictly follow "First Match Wins", we can say:
            # 1. Allow [tools in allowlist]
            # 2. Deny All Tools (if allowlist existed)
            # But we have other checks (Risk) that must also pass!
            # So "Allow" here is dangerous if it skips Risk checks.
            pass

        # To handle the complexity of "Allow List implies Deny Others" + "Risk Checks must still pass",
        # We might need a "Soft Allow" or "Pass" effect, or structured phases.

        # However, for this task, I am replacing the hardcoded checks.
        # I can make the PolicyEngine powerful enough.

        # Let's map the Risk Check:
        # max_risk = os.getenv("ORCHESTRATOR_MAX_RISK", "high")
        # if risk > max_risk: Deny.

        max_risk = os.getenv("ORCHESTRATOR_MAX_RISK", "high").lower()
        risk_levels = ["low", "medium", "high"]
        allowed_risks = []
        if max_risk == "high":
            allowed_risks = ["low", "medium", "high"]
        elif max_risk == "medium":
            allowed_risks = ["low", "medium"]
        else:
            allowed_risks = ["low"]

        # We can add a rule: Deny if risk NOT in allowed_risks.
        # Or: Deny if risk == "high" and max_risk < high...

        # Let's create specific Deny rules for risks.
        if max_risk == "medium":
            self.rules.append(PolicyRule(
                name="env_risk_medium_cap",
                effect=PolicyEffect.DENY,
                conditions={"risk_level": "high"}
            ))
        elif max_risk == "low":
             self.rules.append(PolicyRule(
                name="env_risk_low_cap",
                effect=PolicyEffect.DENY,
                conditions={"risk_level": ["medium", "high"]} # My matches supports list
            ))

        # Domain checks
        domain_allow_str = os.getenv("ORCHESTRATOR_DOMAIN_ALLOWLIST", "")
        domain_allow = set(filter(None, domain_allow_str.split(",")))
        domain_deny_str = os.getenv("ORCHESTRATOR_DOMAIN_DENYLIST", "")
        domain_deny = set(filter(None, domain_deny_str.split(",")))

        if domain_deny:
            self.rules.append(PolicyRule(
                name="env_domain_denylist",
                effect=PolicyEffect.DENY,
                conditions={"domain": list(domain_deny)}
            ))

        # Sandbox / Evolution check
        # if envelope.domain == "evolution" and envelope.context.get("environment") == "stable":
        #      if not envelope.requires_validation:
        #          raise SecurityViolation("Stable channel evolution requires manual validation.")
        self.rules.append(PolicyRule(
            name="env_evolution_stable_validation",
            effect=PolicyEffect.DENY,
            conditions={
                "domain": "evolution",
                "context.environment": "stable",
                "requires_validation": False
            }
        ))

        # High Risk Validation Check
        # if envelope.risk_level == "high" and not envelope.requires_validation: logger.warning...
        # (This was just a warning in code, maybe we enforce it or keep it as warning?)
        # The code said: logger.warning. It didn't raise.
        # I will leave it out of DENY rules.

        # Store allowlists to handle "Implicit Deny" logic in evaluate()
        # because it's hard to express as a single rule without "NOT" logic.
        self._env_tool_allow = tool_allow
        self._env_domain_allow = domain_allow

    def load_from_file(self, path: str) -> None:
        """
        Load policies from a JSON file.
        Format:
        [
            {
                "name": "rule1",
                "effect": "deny",
                "conditions": { "tool_name": "dangerous_tool" }
            }
        ]
        """
        if not os.path.exists(path):
            logger.warning(f"Policy file not found: {path}")
            return

        try:
            with open(path, "r") as f:
                data = json.load(f)

            for rule_data in data:
                try:
                    effect = PolicyEffect(rule_data["effect"].lower())
                    rule = PolicyRule(
                        name=rule_data.get("name", "unnamed"),
                        effect=effect,
                        conditions=rule_data.get("conditions", {})
                    )
                    self.rules.append(rule)
                except ValueError:
                    logger.warning(f"Invalid policy effect in rule: {rule_data}")
        except Exception as e:
            logger.error(f"Failed to load policies from {path}: {e}")

    def evaluate(self, envelope: ToolInvocationEnvelope) -> None:
        """
        Evaluate the envelope against all rules.
        Raises SecurityViolation if denied.
        """

        # 0. Handle "Implicit Deny" from Allowlists (Environment variable legacy logic)
        # This logic is: If allowlist exists, and item not in it, DENY.
        # This acts as a precondition.
        if self._env_tool_allow and envelope.tool_name not in self._env_tool_allow:
             raise SecurityViolation(f"Tool '{envelope.tool_name}' not in allowlist")

        if self._env_domain_allow and envelope.domain not in self._env_domain_allow:
             raise SecurityViolation(f"Domain '{envelope.domain}' not in allowlist")

        # 1. Iterate through Rules
        for rule in self.rules:
            if rule.matches(envelope):
                logger.debug(f"Rule matched: {rule.name} -> {rule.effect}")
                if rule.effect == PolicyEffect.DENY:
                    raise SecurityViolation(f"Policy '{rule.name}' denied action", context={"rule": rule.name})
                elif rule.effect == PolicyEffect.ALLOW:
                    # If Explicit Allow, do we stop?
                    # If we follow "First Match Wins", we stop and return (Approving).
                    # But we must be careful. If we have a generic "Allow All" rule at the top, it bypasses checks.
                    # Assuming policies are ordered by priority.
                    return

        # 2. Default Behavior
        # If no rule matched, we proceed (Default Allow).
        # Unless we want to be strict.
        # Given the legacy system was permissive (unless listed in Deny list), Default Allow is appropriate here.
        return
