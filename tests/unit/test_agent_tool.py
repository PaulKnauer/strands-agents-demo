"""Unit tests for agent.py — get_today_date tool, create_agent adapter delegation, run_repl loop."""

import os
import re
import pytest
from unittest.mock import MagicMock, patch


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
    """create_agent() must delegate model construction to the adapter boundary."""

    def test_delegates_to_adapter_and_passes_model_to_agent(self):
        """create_agent() calls create_local_model_adapter and wires its model into Agent."""
        from agent import create_agent

        mock_model = MagicMock()
        mock_adapter = MagicMock()
        mock_adapter.build.return_value = mock_model

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
            patch(
                "agent.create_local_model_adapter", return_value=mock_adapter
            ) as mock_factory,
            patch("agent.Agent") as mock_agent_cls,
        ):
            os.environ.pop("GUARDRAIL_ID", None)
            create_agent()

            mock_factory.assert_called_once_with("bedrock", os.environ)
            mock_adapter.build.assert_called_once()
            agent_kwargs = mock_agent_cls.call_args.kwargs
            assert agent_kwargs["model"] is mock_model

    def test_unknown_provider_propagates_value_error(self):
        """Unsupported provider ValueError from adapter surfaces through create_agent()."""
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

    def test_agent_receives_get_today_date_tool(self):
        """create_agent() must pass exactly [get_today_date] to Agent."""
        from agent import create_agent

        mock_adapter = MagicMock()
        mock_adapter.build.return_value = MagicMock()

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
            patch("agent.create_local_model_adapter", return_value=mock_adapter),
            patch("agent.Agent") as mock_agent_cls,
        ):
            os.environ.pop("GUARDRAIL_ID", None)
            create_agent()
            tools = mock_agent_cls.call_args.kwargs["tools"]
            assert len(tools) == 1
            assert tools[0].__name__ == "get_today_date"


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
