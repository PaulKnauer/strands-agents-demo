"""Behavioral contract evals for the agentic loop.

Uses a scripted fake converse to assert behavioral properties:
- what to assert: tool was called, response contains a number, questions asked
- what NOT to assert: exact wording, specific day counts

These run without AWS credentials. For live LLM evals, mark tests with @pytest.mark.eval.
"""

import re
import pytest
from unittest.mock import MagicMock, patch

from deploy.app import _run_agent


def _fake_converse_factory(responses):
    """Return a mock bedrock client whose converse() replays `responses` in order."""
    mock_bedrock = MagicMock()
    mock_bedrock.converse.side_effect = responses
    return mock_bedrock


def _end_turn(text):
    return {
        "output": {"message": {"role": "assistant", "content": [{"text": text}]}},
        "stopReason": "end_turn",
    }


def _tool_use(tool_use_id="tu-001"):
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


class TestToolUseContract:
    @patch("deploy.app.boto3.client")
    def test_agent_calls_get_today_date_before_answering(self, mock_client):
        """Agent MUST use get_today_date — never rely on training knowledge for today's date."""
        mock_client.return_value = _fake_converse_factory(
            [
                _tool_use("tu-001"),
                _end_turn("You are 13149 days old."),
            ]
        )

        result = _run_agent("I was born on 14 March 1990")

        # Two converse calls = tool was invoked
        assert mock_client.return_value.converse.call_count == 2
        assert re.search(r"\d+", result), "Response must contain a numeric age-in-days"


class TestResponseQualityContract:
    @patch("deploy.app.boto3.client")
    def test_valid_dob_response_contains_number(self, mock_client):
        """A valid DOB prompt must yield a response containing at least one number."""
        mock_client.return_value = _fake_converse_factory(
            [
                _tool_use(),
                _end_turn("You were born 13149 days ago."),
            ]
        )
        result = _run_agent("I was born on 14th March 1990")
        assert re.search(r"\d+", result), f"No number in response: {result!r}"

    @patch("deploy.app.boto3.client")
    def test_unparseable_date_response_has_no_number(self, mock_client):
        """AC #5 (Story 1.2): unparseable input must not yield any numeric calculation.

        Uses 'born on the moon' — clearly uninterpretable as a date. The scripted
        response must contain no numbers at all (not just no 4+ digit numbers).
        """
        mock_client.return_value = _fake_converse_factory(
            [
                _end_turn(
                    "I couldn't parse that as a date. Please provide a valid date of birth."
                ),
            ]
        )
        result = _run_agent("I was born on the moon")
        # Error responses should not contain any numeric value
        assert not re.search(
            r"\d+", result
        ), f"Unparseable input should not yield any number in response: {result!r}"


class TestAmbiguousDateContract:
    @patch("deploy.app.boto3.client")
    def test_ambiguous_date_prompts_clarification(self, mock_client):
        """Ambiguous date (e.g. 3/4/1990) must trigger a clarifying question."""
        mock_client.return_value = _fake_converse_factory(
            [
                _end_turn("Did you mean April 3rd or March 4th? Please clarify."),
            ]
        )
        result = _run_agent("I was born on 3/4/1990")
        assert "?" in result, f"Expected a clarifying question, got: {result!r}"


class TestDDMMYYYYContract:
    @patch("deploy.app.boto3.client")
    def test_dd_mm_yyyy_format_yields_tool_call(self, mock_client):
        """DD/MM/YYYY unambiguous date (day > 12) must proceed to tool call, not ask for clarification."""
        mock_client.return_value = _fake_converse_factory(
            [
                _tool_use(),
                _end_turn("You are 13149 days old."),
            ]
        )
        result = _run_agent("I was born on 14/03/1990")
        # Tool was called — agent did not ask for clarification
        assert mock_client.return_value.converse.call_count == 2
        assert re.search(r"\d+", result)
