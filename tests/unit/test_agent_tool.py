"""Unit tests for agent.py — get_today_date tool, create_agent factory, run_repl loop."""

import os
import re
import pytest
from unittest.mock import MagicMock, patch, call


class TestGetTodayDate:
    def test_returns_iso_date_format(self):
        from agent import get_today_date

        result = get_today_date()
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", result), f"Not ISO date: {result}"

    def test_returns_error_string_on_exception(self):
        from agent import get_today_date

        with patch("agent.datetime.date") as mock_date:
            mock_date.today.side_effect = Exception("clock failure")
            result = get_today_date()
        assert "Error retrieving today's date:" in result
        assert "clock failure" in result


class TestCreateAgent:
    def test_unknown_provider_raises_value_error(self):
        from agent import create_agent

        with patch.dict(
            os.environ,
            {
                "MODEL_PROVIDER": "openai",
                "MODEL_ID": "gpt-4",
                "AWS_REGION": "us-east-1",
            },
        ):
            with pytest.raises(ValueError, match="Unknown MODEL_PROVIDER"):
                create_agent()

    def test_bedrock_provider_constructs_bedrock_model(self):
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
            patch("agent.BedrockModel") as mock_bedrock_cls,
            patch("agent.Agent") as mock_agent_cls,
        ):
            # Ensure GUARDRAIL_ID is absent so no guardrail kwargs are passed (AC #4)
            os.environ.pop("GUARDRAIL_ID", None)
            create_agent()
            kwargs = mock_bedrock_cls.call_args.kwargs
            assert kwargs["model_id"] == "some-model"
            assert kwargs["region_name"] == "us-east-1"
            assert "guardrail_id" not in kwargs
            assert "guardrail_version" not in kwargs
            mock_agent_cls.assert_called_once()

    def test_bedrock_with_guardrail_id_passes_guardrail_kwargs(self):
        from agent import create_agent

        with (
            patch.dict(
                os.environ,
                {
                    "MODEL_PROVIDER": "bedrock",
                    "MODEL_ID": "some-model",
                    "AWS_REGION": "us-east-1",
                    "GUARDRAIL_ID": "test-guardrail-id",
                    "GUARDRAIL_VERSION": "1",
                },
            ),
            patch("agent.BedrockModel") as mock_bedrock_cls,
            patch("agent.Agent"),
        ):
            create_agent()
            kwargs = mock_bedrock_cls.call_args.kwargs
            assert kwargs["guardrail_id"] == "test-guardrail-id"
            assert kwargs["guardrail_version"] == "1"

    def test_bedrock_without_guardrail_id_omits_guardrail_kwargs(self):
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
            patch("agent.BedrockModel") as mock_bedrock_cls,
            patch("agent.Agent"),
        ):
            os.environ.pop("GUARDRAIL_ID", None)
            create_agent()
            kwargs = mock_bedrock_cls.call_args.kwargs
            assert "guardrail_id" not in kwargs
            assert "guardrail_version" not in kwargs

    def test_bedrock_guardrail_version_defaults_to_draft_when_unset(self):
        from agent import create_agent

        with (
            patch.dict(
                os.environ,
                {
                    "MODEL_PROVIDER": "bedrock",
                    "MODEL_ID": "some-model",
                    "AWS_REGION": "us-east-1",
                    "GUARDRAIL_ID": "gid-123",
                },
            ),
            patch("agent.BedrockModel") as mock_bedrock_cls,
            patch("agent.Agent"),
        ):
            os.environ.pop("GUARDRAIL_VERSION", None)
            create_agent()
            kwargs = mock_bedrock_cls.call_args.kwargs
            assert kwargs["guardrail_version"] == "DRAFT"

    def test_gemini_provider_constructs_gemini_model(self):
        from agent import create_agent

        mock_gemini_cls = MagicMock()
        with (
            patch.dict(
                os.environ,
                {
                    "MODEL_PROVIDER": "gemini",
                    "MODEL_ID": "gemini-pro",
                    "AWS_REGION": "us-east-1",
                },
            ),
            patch.dict(
                "sys.modules",
                {"strands.models.gemini": MagicMock(GeminiModel=mock_gemini_cls)},
            ),
            patch("agent.Agent") as mock_agent_cls,
        ):
            create_agent()
            mock_gemini_cls.assert_called_once_with(model_id="gemini-pro")
            mock_agent_cls.assert_called_once()

    def test_gemini_provider_ignores_guardrail_env_var(self):
        from agent import create_agent

        mock_gemini_cls = MagicMock()
        with (
            patch.dict(
                os.environ,
                {
                    "MODEL_PROVIDER": "gemini",
                    "MODEL_ID": "gemini-pro",
                    "AWS_REGION": "us-east-1",
                    "GUARDRAIL_ID": "should-be-ignored",
                    "GUARDRAIL_VERSION": "1",
                },
            ),
            patch.dict(
                "sys.modules",
                {"strands.models.gemini": MagicMock(GeminiModel=mock_gemini_cls)},
            ),
            patch("agent.Agent"),
        ):
            create_agent()
            # GeminiModel must be called with model_id only — no guardrail kwargs
            mock_gemini_cls.assert_called_once_with(model_id="gemini-pro")


class TestRunRepl:
    """Tests for the run_repl() REPL loop in agent.py.

    AC #9 (Story 1.2): exit/quit/q exits cleanly.
    AC #14 / Finding 14 (Story 3.3): empty input is not forwarded to the agent.
    """

    def _run_with_inputs(self, inputs: list) -> MagicMock:
        """Helper: run run_repl with scripted input() responses, return mock agent."""
        from agent import run_repl

        mock_agent = MagicMock(return_value="some response")
        with patch("builtins.input", side_effect=inputs):
            run_repl(mock_agent)
        return mock_agent

    def test_exit_keyword_exits_repl(self):
        """AC #9 (Story 1.2): 'exit' terminates the REPL without calling the agent."""
        mock_agent = self._run_with_inputs(["exit"])
        mock_agent.assert_not_called()

    def test_quit_keyword_exits_repl(self):
        """AC #9 (Story 1.2): 'quit' terminates the REPL without calling the agent."""
        mock_agent = self._run_with_inputs(["quit"])
        mock_agent.assert_not_called()

    def test_q_keyword_exits_repl(self):
        """AC #9 (Story 1.2): 'q' terminates the REPL without calling the agent."""
        mock_agent = self._run_with_inputs(["q"])
        mock_agent.assert_not_called()

    def test_exit_keyword_case_insensitive(self):
        """AC #9 (Story 1.2): exit keywords are case-insensitive (EXIT, Quit, Q)."""
        for keyword in ("EXIT", "Quit", "Q", "EXIT"):
            mock_agent = self._run_with_inputs([keyword])
            mock_agent.assert_not_called()

    def test_empty_input_not_forwarded_to_agent(self):
        """Finding 14 / AC #5 (Story 3.3): empty input is silently skipped, not sent to LLM."""
        mock_agent = self._run_with_inputs(["", "   ", "exit"])
        mock_agent.assert_not_called()

    def test_valid_input_forwarded_to_agent(self):
        """REPL forwards non-empty, non-exit input to the agent exactly once."""
        mock_agent = self._run_with_inputs(["I was born 1 Jan 1990", "exit"])
        mock_agent.assert_called_once_with("I was born 1 Jan 1990")
