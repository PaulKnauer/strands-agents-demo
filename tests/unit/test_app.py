"""Unit tests for deploy/app.py — agentic loop, tool dispatch, entrypoint."""

import os
import pytest
from unittest.mock import MagicMock, patch

from deploy.app import _get_today_date, _run_agent, handle_invocation

# ── Helpers ───────────────────────────────────────────────────────────────────


def _end_turn(text: str) -> dict:
    return {
        "output": {"message": {"role": "assistant", "content": [{"text": text}]}},
        "stopReason": "end_turn",
    }


def _tool_use(tool_use_id: str = "tu-001") -> dict:
    return {
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "toolUse": {
                            "name": "get_today_date",
                            "toolUseId": tool_use_id,
                            "input": {},
                        }
                    }
                ],
            }
        },
        "stopReason": "tool_use",
    }


# ── _get_today_date ───────────────────────────────────────────────────────────


class TestGetTodayDate:
    def test_returns_iso_format(self):
        import re

        result = _get_today_date()
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", result), f"Not ISO date: {result}"

    def test_returns_error_string_on_exception(self):
        with patch("deploy.app.datetime.date") as mock_date:
            mock_date.today.side_effect = Exception("system clock failure")
            result = _get_today_date()
        assert result.startswith("Error retrieving today's date:")
        assert "system clock failure" in result


# ── _run_agent ────────────────────────────────────────────────────────────────


class TestRunAgent:
    @patch("deploy.app.boto3.client")
    def test_end_turn_immediately_returns_text(self, mock_client):
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.converse.return_value = _end_turn("You are 13149 days old.")

        result = _run_agent("I was born on 14 March 1990")

        assert result == "You are 13149 days old."
        assert mock_bedrock.converse.call_count == 1

    @patch("deploy.app.boto3.client")
    def test_tool_use_then_end_turn(self, mock_client):
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.converse.side_effect = [
            _tool_use("tu-001"),
            _end_turn("You are 13149 days old."),
        ]

        result = _run_agent("I was born on 14 March 1990")

        assert result == "You are 13149 days old."
        assert mock_bedrock.converse.call_count == 2

    @patch("deploy.app.boto3.client")
    def test_tool_result_injected_correctly(self, mock_client):
        """Second converse call must carry the tool result in the messages list."""
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.converse.side_effect = [
            _tool_use("tu-abc"),
            _end_turn("Done."),
        ]

        _run_agent("some prompt")

        second_call_messages = mock_bedrock.converse.call_args_list[1][1]["messages"]
        # messages: [user, assistant(tool_use), user(tool_result)]
        tool_result_msg = second_call_messages[2]
        assert tool_result_msg["role"] == "user"
        assert tool_result_msg["content"][0]["toolResult"]["toolUseId"] == "tu-abc"

    @patch("deploy.app.boto3.client")
    def test_multiple_tool_use_turns(self, mock_client):
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.converse.side_effect = [
            _tool_use("tu-001"),
            _tool_use("tu-002"),
            _end_turn("Final answer."),
        ]

        result = _run_agent("prompt")

        assert result == "Final answer."
        assert mock_bedrock.converse.call_count == 3

    @patch("deploy.app.boto3.client")
    def test_no_text_block_returns_fallback(self, mock_client):
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.converse.return_value = {
            "output": {"message": {"role": "assistant", "content": [{"image": {}}]}},
            "stopReason": "end_turn",
        }

        result = _run_agent("prompt")

        assert result == "No response generated."

    @patch("deploy.app.boto3.client")
    def test_empty_prompt_passed_through(self, mock_client):
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.converse.return_value = _end_turn(
            "Please provide a date of birth."
        )

        _run_agent("")

        call_messages = mock_bedrock.converse.call_args[1]["messages"]
        assert call_messages[0]["content"][0]["text"] == ""


# ── guardrail wiring (deployed runtime path) ──────────────────────────────────


class TestRunAgentGuardrails:
    """Verify that _run_agent wires GUARDRAIL_ID/VERSION into converse() — AC #11."""

    @patch("deploy.app.boto3.client")
    def test_guardrail_config_passed_when_guardrail_id_set(self, mock_client):
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.converse.return_value = _end_turn("You are 1000 days old.")

        with patch.dict(
            os.environ, {"GUARDRAIL_ID": "gr-123", "GUARDRAIL_VERSION": "2"}
        ):
            _run_agent("born 1 Jan 2020")

        kwargs = mock_bedrock.converse.call_args.kwargs
        assert "guardrailConfig" in kwargs
        assert kwargs["guardrailConfig"]["guardrailIdentifier"] == "gr-123"
        assert kwargs["guardrailConfig"]["guardrailVersion"] == "2"

    @patch("deploy.app.boto3.client")
    def test_guardrail_config_absent_when_guardrail_id_not_set(self, mock_client):
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.converse.return_value = _end_turn("You are 1000 days old.")

        with patch.dict(
            os.environ, {"MODEL_ID": "haiku", "AWS_REGION": "us-east-1"}, clear=True
        ):
            _run_agent("born 1 Jan 2020")

        kwargs = mock_bedrock.converse.call_args.kwargs
        assert "guardrailConfig" not in kwargs

    @patch("deploy.app.boto3.client")
    def test_guardrail_version_defaults_to_draft_when_unset(self, mock_client):
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.converse.return_value = _end_turn("You are 1000 days old.")

        with patch.dict(os.environ, {"GUARDRAIL_ID": "gr-456"}):
            os.environ.pop("GUARDRAIL_VERSION", None)
            _run_agent("born 1 Jan 2020")

        kwargs = mock_bedrock.converse.call_args.kwargs
        assert kwargs["guardrailConfig"]["guardrailVersion"] == "DRAFT"

    @patch("deploy.app.boto3.client")
    def test_guardrail_config_applied_on_every_converse_turn(self, mock_client):
        """Guardrail config must be present on all turns including tool-use loops."""
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.converse.side_effect = [
            _tool_use("tu-001"),
            _end_turn("Done."),
        ]

        with patch.dict(
            os.environ, {"GUARDRAIL_ID": "gr-789", "GUARDRAIL_VERSION": "1"}
        ):
            _run_agent("born 1 Jan 2020")

        for call in mock_bedrock.converse.call_args_list:
            assert "guardrailConfig" in call.kwargs


# ── handle_invocation ─────────────────────────────────────────────────────────


class TestHandleInvocation:
    @patch("deploy.app.boto3.client")
    def test_prompt_key_routed_to_agent(self, mock_client):
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.converse.return_value = _end_turn("You are 1000 days old.")

        result = handle_invocation({"prompt": "born 1 Jan 2020"})

        assert result == "You are 1000 days old."

    def test_missing_prompt_key_returns_error(self):
        """AC #7 (Story 2.1): missing prompt key → error string, no Bedrock call."""
        result = handle_invocation({})
        assert result == "Error: empty prompt."

    def test_empty_prompt_returns_error(self):
        """AC #7 (Story 2.1): empty/whitespace prompt → error string, no Bedrock call."""
        result = handle_invocation({"prompt": "   "})
        assert result == "Error: empty prompt."

    def test_oversized_prompt_returns_error(self):
        """AC #7 (Story 2.1): prompt > 4000 chars → error string, no Bedrock call."""
        result = handle_invocation({"prompt": "x" * 4001})
        assert "4000" in result

    def test_missing_model_provider_returns_error(self):
        """AC #2 (Story 2.2): Missing MODEL_PROVIDER must return a clear error, no Bedrock fallback."""
        with patch.dict(os.environ, {}, clear=True):
            result = handle_invocation({"prompt": "born 1 Jan 2020"})
        assert result.startswith("Error:")
        assert "MODEL_PROVIDER" in result

    def test_non_bedrock_provider_returns_error(self):
        """AC #2 (Story 2.2): MODEL_PROVIDER='gemini' must return a clear error, not silently use Bedrock."""
        with patch.dict(os.environ, {"MODEL_PROVIDER": "gemini"}):
            result = handle_invocation({"prompt": "born 1 Jan 2020"})
        assert result.startswith("Error:")
        assert "gemini" in result

    def test_unknown_provider_returns_error(self):
        """AC #2 (Story 2.2): Unknown MODEL_PROVIDER must return a clear error, no Bedrock call."""
        with patch.dict(os.environ, {"MODEL_PROVIDER": "openai"}):
            result = handle_invocation({"prompt": "born 1 Jan 2020"})
        assert result.startswith("Error:")
        assert "openai" in result
