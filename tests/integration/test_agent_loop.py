"""Integration tests for the full agentic loop in deploy/app.py.

Validates the complete message sequence passed to the Bedrock Converse API,
ensuring the protocol (user → assistant → tool_result → assistant) is correct.
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
    def test_single_tool_call_message_sequence(self, mock_client):
        """Verify the exact messages passed across both converse calls."""
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.converse.side_effect = [
            _tool_use_response("tu-001"),
            _end_turn("You are 13149 days old."),
        ]

        result = _run_agent("I was born on 14 March 1990")

        assert result == "You are 13149 days old."
        assert mock_bedrock.converse.call_count == 2

        # The messages list is mutated in-place; both call_args entries reference the
        # same list object showing its final accumulated state:
        # [user, assistant(tool_use), user(tool_result), assistant(final)]
        final_messages = mock_bedrock.converse.call_args_list[0][1]["messages"]
        assert len(final_messages) == 4

        assert final_messages[0]["role"] == "user"
        assert final_messages[0]["content"][0]["text"] == "I was born on 14 March 1990"

        assert final_messages[1]["role"] == "assistant"
        assert final_messages[1]["content"][0]["toolUse"]["toolUseId"] == "tu-001"

        tool_result = final_messages[2]["content"][0]["toolResult"]
        assert tool_result["toolUseId"] == "tu-001"
        # Tool result must be a valid ISO date returned by _get_today_date()
        import re
        tool_result_text = tool_result["content"][0]["text"]
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", tool_result_text)

        assert final_messages[3]["role"] == "assistant"
        assert final_messages[3]["content"][0]["text"] == "You are 13149 days old."

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

        # Final accumulated list (all call_args reference same in-place list):
        # user, asst(tu-001), user(result-001), asst(tu-002), user(result-002), asst(final)
        final_messages = mock_bedrock.converse.call_args_list[2][1]["messages"]
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
