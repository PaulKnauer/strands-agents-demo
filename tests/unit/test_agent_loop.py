"""Unit tests for the _run_agent message protocol in deploy/app.py.

Validates the complete message sequence passed to the Bedrock Converse API,
ensuring the protocol (user → assistant → tool_result → assistant) is correct.

Note: These tests use mocked boto3 and do NOT exercise the Strands SDK or
make real AWS calls. Real SDK integration tests require live credentials and
are out of scope for the automated test suite.

AC #10 (Story 3.3): moved from tests/integration/ — honest naming for mock-only tests.
"""

import pytest
from unittest.mock import MagicMock, patch, call

from deploy.app import _run_agent


def _end_turn(text: str) -> dict:
    return {
        "output": {"message": {"role": "assistant", "content": [{"text": text}]}},
        "stopReason": "end_turn",
    }


def _tool_use_response(tool_use_id: str) -> dict:
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


class TestAgentLoopMessageSequence:
    @patch("deploy.app.boto3.client")
    def test_parseable_dob_tool_call_returns_deterministic_age(self, mock_client):
        """Parseable DOBs return deterministic age after the model requests today's date."""
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.converse.return_value = _tool_use_response("tu-001")

        with patch("deploy.app._get_today_date", return_value="2026-05-10"):
            result = _run_agent("I was born on 14 March 1990")

        assert "13,206 days old" in result
        assert mock_bedrock.converse.call_count == 1

        # Messages list is mutated in-place; the final state includes the user prompt and
        # assistant toolUse. The runtime returns deterministic age before a second model turn.
        final_messages = mock_bedrock.converse.call_args_list[-1][1]["messages"]
        assert len(final_messages) == 2

        assert final_messages[0]["role"] == "user"
        assert final_messages[0]["content"][0]["text"] == "I was born on 14 March 1990"

        assert final_messages[1]["role"] == "assistant"
        assert final_messages[1]["content"][0]["toolUse"]["toolUseId"] == "tu-001"

    @patch("deploy.app.boto3.client")
    def test_two_tool_calls_message_sequence(self, mock_client):
        """Two sequential tool calls accumulate messages correctly."""
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.converse.side_effect = [
            _tool_use_response("tu-001"),
            _tool_use_response("tu-002"),
            _end_turn("Final."),
        ]

        result = _run_agent("prompt")

        assert result == "Final."
        assert mock_bedrock.converse.call_count == 3

        # Messages list is mutated in-place; use call_args_list[-1] for final accumulated state.
        # user, asst(tu-001), user(result-001), asst(tu-002), user(result-002), asst(final)
        final_messages = mock_bedrock.converse.call_args_list[-1][1]["messages"]
        assert len(final_messages) == 6

    @patch("deploy.app.boto3.client")
    def test_system_prompt_sent_on_every_call(self, mock_client):
        """SYSTEM_PROMPT must be included in every converse invocation."""
        from deploy.app import SYSTEM_PROMPT

        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.converse.side_effect = [
            _tool_use_response("tu-001"),
            _end_turn("Done."),
        ]

        _run_agent("prompt")

        for call_args in mock_bedrock.converse.call_args_list:
            system = call_args[1]["system"]
            assert system == [{"text": SYSTEM_PROMPT}]

    @patch("deploy.app.boto3.client")
    def test_tool_config_sent_on_every_call(self, mock_client):
        """TOOLS config must be included in every converse invocation."""
        from deploy.app import TOOLS

        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.converse.side_effect = [
            _tool_use_response("tu-001"),
            _end_turn("Done."),
        ]

        _run_agent("prompt")

        for call_args in mock_bedrock.converse.call_args_list:
            assert call_args[1]["toolConfig"] == {"tools": TOOLS}
