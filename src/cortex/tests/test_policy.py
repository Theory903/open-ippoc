# brain/tests/test_policy.py

import os
import pytest
from unittest.mock import patch, MagicMock
from cortex.core.policy import PolicyEngine, PolicyEffect, PolicyRule
from cortex.core.tools.base import ToolInvocationEnvelope
from cortex.core.exceptions import SecurityViolation

@pytest.fixture
def envelope():
    return ToolInvocationEnvelope(
        tool_name="test.tool",
        domain="memory",
        action="read",
        risk_level="low"
    )

def test_policy_rule_match_exact(envelope):
    rule = PolicyRule("test_rule", PolicyEffect.DENY, {"tool_name": "test.tool"})
    assert rule.matches(envelope) is True

    rule2 = PolicyRule("test_rule_2", PolicyEffect.DENY, {"tool_name": "other.tool"})
    assert rule2.matches(envelope) is False

def test_policy_rule_match_list(envelope):
    rule = PolicyRule("test_rule", PolicyEffect.DENY, {"risk_level": ["low", "medium"]})
    assert rule.matches(envelope) is True

    envelope.risk_level = "high"
    assert rule.matches(envelope) is False

def test_policy_rule_nested_field(envelope):
    envelope.context = {"environment": "prod"}
    rule = PolicyRule("test_rule", PolicyEffect.DENY, {"context.environment": "prod"})
    assert rule.matches(envelope) is True

    envelope.context = {"environment": "dev"}
    assert rule.matches(envelope) is False

def test_policy_engine_env_vars_kill_switch():
    with patch.dict(os.environ, {"ORCHESTRATOR_KILL_SWITCH": "true"}):
        engine = PolicyEngine()
        assert len(engine.rules) >= 1
        assert engine.rules[0].name == "env_kill_switch"

        env = ToolInvocationEnvelope(tool_name="any", domain="memory", action="read")
        with pytest.raises(SecurityViolation, match="Policy 'env_kill_switch' denied action"):
            engine.evaluate(env)

def test_policy_engine_env_vars_tool_deny():
    with patch.dict(os.environ, {"ORCHESTRATOR_TOOL_DENYLIST": "bad.tool,worse.tool"}):
        engine = PolicyEngine()
        # Find the rule
        rule = next((r for r in engine.rules if r.name == "env_tool_denylist"), None)
        assert rule is not None
        assert "bad.tool" in rule.conditions["tool_name"]

        env = ToolInvocationEnvelope(tool_name="bad.tool", domain="memory", action="read")
        with pytest.raises(SecurityViolation, match="Policy 'env_tool_denylist' denied action"):
            engine.evaluate(env)

def test_policy_engine_env_vars_risk():
    with patch.dict(os.environ, {"ORCHESTRATOR_MAX_RISK": "medium"}):
        engine = PolicyEngine()
        # Should deny "high"
        env = ToolInvocationEnvelope(tool_name="ok", domain="memory", action="read", risk_level="high")
        with pytest.raises(SecurityViolation, match="Policy 'env_risk_medium_cap' denied action"):
            engine.evaluate(env)

        # Should allow "medium"
        env.risk_level = "medium"
        engine.evaluate(env) # Should not raise

def test_policy_engine_file_load(tmp_path):
    policy_file = tmp_path / "policy.json"
    policy_content = [
        {
            "name": "file_rule",
            "effect": "deny",
            "conditions": {"tool_name": "forbidden.file.tool"}
        }
    ]
    import json
    with open(policy_file, "w") as f:
        json.dump(policy_content, f)

    engine = PolicyEngine(policy_path=str(policy_file))
    assert any(r.name == "file_rule" for r in engine.rules)

    env = ToolInvocationEnvelope(tool_name="forbidden.file.tool", domain="memory", action="read")
    with pytest.raises(SecurityViolation, match="Policy 'file_rule' denied action"):
        engine.evaluate(env)

def test_implicit_deny_allowlist():
    with patch.dict(os.environ, {"ORCHESTRATOR_TOOL_ALLOWLIST": "good.tool"}):
        engine = PolicyEngine()

        # Allowed tool
        env = ToolInvocationEnvelope(tool_name="good.tool", domain="memory", action="read")
        engine.evaluate(env)

        # Not allowed tool
        env_bad = ToolInvocationEnvelope(tool_name="bad.tool", domain="memory", action="read")
        with pytest.raises(SecurityViolation, match="Tool 'bad.tool' not in allowlist"):
            engine.evaluate(env_bad)
