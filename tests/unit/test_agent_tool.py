"""Unit tests for agent.py — get_today_date tool and create_agent factory."""

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
    def test_unknown_provider_raises_value_error(self):
        from agent import create_agent
        with patch.dict(os.environ, {"MODEL_PROVIDER": "openai", "MODEL_ID": "gpt-4", "AWS_REGION": "us-east-1"}):
            with pytest.raises(ValueError, match="Unknown MODEL_PROVIDER"):
                create_agent()

    def test_bedrock_provider_constructs_bedrock_model(self):
        from agent import create_agent
        with (
            patch.dict(os.environ, {"MODEL_PROVIDER": "bedrock", "MODEL_ID": "some-model", "AWS_REGION": "us-east-1"}),
            patch("agent.BedrockModel") as mock_bedrock_cls,
            patch("agent.Agent") as mock_agent_cls,
        ):
            create_agent()
            mock_bedrock_cls.assert_called_once_with(model_id="some-model", region_name="us-east-1")
            mock_agent_cls.assert_called_once()

    def test_gemini_provider_constructs_gemini_model(self):
        from agent import create_agent
        mock_gemini_cls = MagicMock()
        with (
            patch.dict(os.environ, {"MODEL_PROVIDER": "gemini", "MODEL_ID": "gemini-pro", "AWS_REGION": "us-east-1"}),
            patch.dict("sys.modules", {"strands.models.gemini": MagicMock(GeminiModel=mock_gemini_cls)}),
            patch("agent.Agent") as mock_agent_cls,
        ):
            create_agent()
            mock_gemini_cls.assert_called_once_with(model_id="gemini-pro")
            mock_agent_cls.assert_called_once()
