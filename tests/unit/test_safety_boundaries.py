"""Deterministic safety boundary tests — NIST AI RMF MEASURE-2.4/2.7/2.8.

These tests enforce the agent's safety contract on every CI push without
requiring live LLM API calls. They complement the promptfoo red-team suite
(compliance/promptfoo-redteam.yaml) which validates the same boundaries
end-to-end with adversarial LLM probes on a weekly schedule.

NIST AI RMF functions addressed:
- MEASURE-2.4: Safety — tool surface contract and loop guard enforcement
- MEASURE-2.7: Security — system prompt credential integrity guard
- MEASURE-2.8: Privacy — credential leak prevention in system prompt

What this file does NOT test (already covered elsewhere):
- SYSTEM_PROMPT parity between agent.py and deploy/app.py
  → tests/evals/test_prompt_parity.py:test_system_prompt_parity()
- deploy/app.py TOOLS list tool name
  → tests/evals/test_prompt_parity.py:test_tools_parity()
- Oversized prompt rejection (MAX_PROMPT_CHARS enforcement behaviour)
  → tests/unit/test_app.py:TestHandleInvocation.test_oversized_prompt_returns_error()
- Guardrail wiring in agent.py and deploy/app.py
  → tests/unit/test_agent_tool.py, tests/unit/test_app.py
"""

import os
from unittest.mock import patch


class TestToolSurface:
    """Enforce the agent's tool surface contract — NIST MEASURE-2.4 (safety).

    The agent's declared capability is date calculation only. Any additional
    tool registration expands the capability surface and requires a risk
    register update per the NIST AI RMF governance process.

    This test CI-gates that requirement: adding a tool to create_agent()
    breaks this test and forces a deliberate risk register review.
    """

    def test_create_agent_registers_exactly_one_tool(self):
        """create_agent() must pass exactly tools=[get_today_date] to Agent().

        Uses the same mock pattern as test_agent_tool.py to avoid live
        Bedrock/Strands calls. Asserts on the tools kwarg passed to the
        mocked Agent constructor.
        """
        from agent import create_agent

        with (
            patch.dict(
                os.environ,
                {
                    "MODEL_PROVIDER": "bedrock",
                    "MODEL_ID": "some-model",
                    "AWS_REGION": "us-east-1",
                },
                clear=True,
            ),
            patch("agent.BedrockModel"),
            patch("agent.Agent") as mock_agent_cls,
        ):
            # Ensure GUARDRAIL_ID is absent — test without guardrail kwargs (AC #4 from 4.3)
            os.environ.pop("GUARDRAIL_ID", None)
            create_agent()
            tools = mock_agent_cls.call_args.kwargs["tools"]

        assert len(tools) == 1, (
            f"Expected exactly 1 tool registered in create_agent(), got {len(tools)}: "
            f"{[getattr(t, '__name__', repr(t)) for t in tools]}. "
            "Adding a new tool requires updating docs/risk-register.md."
        )
        assert tools[0].__name__ == "get_today_date", (
            f"Expected tool name 'get_today_date', got '{tools[0].__name__}'. "
            "If the tool was renamed, update the risk register and this test."
        )


class TestSystemPromptIntegrity:
    """Guard SYSTEM_PROMPT against accidental credential inclusion — NIST MEASURE-2.7/2.8.

    Any API key, password, or secret token accidentally embedded in SYSTEM_PROMPT
    would be transmitted to Amazon Bedrock on every invocation — a direct credential
    leak. This test enforces that forbidden patterns are absent.
    """

    # Patterns that must never appear in SYSTEM_PROMPT (case-insensitive).
    # These indicate likely credential or secret material.
    _FORBIDDEN_KEYWORDS = [
        "password",
        "secret",
        "api_key",
        "token",
        "credential",
        "bearer",
        "sk-",
    ]

    def test_system_prompt_contains_no_credential_patterns(self):
        """SYSTEM_PROMPT must not contain hardcoded credentials or secret keywords.

        NIST AI RMF MEASURE-2.7 (security) and MEASURE-2.8 (privacy).
        """
        from agent import SYSTEM_PROMPT

        prompt_lower = SYSTEM_PROMPT.lower()
        violations = [
            kw for kw in self._FORBIDDEN_KEYWORDS if kw.lower() in prompt_lower
        ]

        assert not violations, (
            f"SYSTEM_PROMPT contains forbidden keyword(s): {violations}. "
            "Remove any credentials or secret material from the system prompt. "
            "Credentials must never be embedded in prompts sent to external LLM APIs."
        )


class TestInputBoundaries:
    """Guard input boundary constants against accidental modification — NIST MEASURE-2.4.

    MAX_PROMPT_CHARS limits token-cost amplification attacks (NIST AI 600-1 §2.7).
    MAX_TURNS prevents runaway tool-calling loops (excessive-agency control).
    These constants are documented in docs/risk-register.md R-1.
    If either value is intentionally changed, update the risk register note.
    """

    def test_max_prompt_chars_is_4000(self):
        """MAX_PROMPT_CHARS must be 4000 — input size limit for cost amplification defence.

        NIST MEASURE-2.4: safety boundary on user-supplied input size.
        If intentionally changed, update docs/risk-register.md R-1 notes.
        """
        from deploy.app import MAX_PROMPT_CHARS

        assert MAX_PROMPT_CHARS == 4000, (
            f"MAX_PROMPT_CHARS changed to {MAX_PROMPT_CHARS} (expected 4000). "
            "If intentional, update docs/risk-register.md R-1 and this test."
        )

    def test_max_turns_is_10(self):
        """MAX_TURNS must be 10 — loop guard against runaway tool-calling.

        NIST MEASURE-2.4: excessive-agency control (prevents infinite loops).
        If intentionally changed, update docs/risk-register.md and this test.
        """
        from deploy.app import MAX_TURNS

        assert MAX_TURNS == 10, (
            f"MAX_TURNS changed to {MAX_TURNS} (expected 10). "
            "If intentional, update docs/risk-register.md and this test."
        )
