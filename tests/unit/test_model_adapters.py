"""Unit tests for model_adapters.py — adapter selection, construction, and boundary."""

import os
import pytest
from unittest.mock import MagicMock, patch


class TestCreateLocalModelAdapter:
    def test_unknown_provider_raises_value_error(self):
        from model_adapters import create_local_model_adapter

        with pytest.raises(ValueError, match="Unknown MODEL_PROVIDER"):
            create_local_model_adapter(
                "openai", {"MODEL_ID": "gpt-4", "AWS_REGION": "us-east-1"}
            )

    def test_unsupported_provider_does_not_fall_back(self):
        """No silent fallback — ValueError must propagate, not return a Bedrock or Gemini adapter."""
        from model_adapters import (
            create_local_model_adapter,
            BedrockAdapter,
            GeminiAdapter,
        )

        with pytest.raises(ValueError):
            adapter = create_local_model_adapter("unknown", {})
        # If no exception was raised the test would fail at the line above

    def test_bedrock_provider_returns_bedrock_adapter(self):
        from model_adapters import create_local_model_adapter, BedrockAdapter

        adapter = create_local_model_adapter(
            "bedrock", {"MODEL_ID": "m", "AWS_REGION": "us-east-1"}
        )
        assert isinstance(adapter, BedrockAdapter)

    def test_gemini_provider_returns_gemini_adapter(self):
        from model_adapters import create_local_model_adapter, GeminiAdapter

        adapter = create_local_model_adapter("gemini", {"MODEL_ID": "gemini-pro"})
        assert isinstance(adapter, GeminiAdapter)


class TestBedrockAdapter:
    def test_build_constructs_bedrock_model_with_model_id_and_region(self):
        from model_adapters import BedrockAdapter

        with patch("model_adapters.BedrockModel") as mock_cls:
            adapter = BedrockAdapter(
                {"MODEL_ID": "some-model", "AWS_REGION": "us-east-1"}
            )
            adapter.build()
            kwargs = mock_cls.call_args.kwargs
            assert kwargs["model_id"] == "some-model"
            assert kwargs["region_name"] == "us-east-1"

    def test_build_omits_guardrail_kwargs_when_guardrail_id_absent(self):
        from model_adapters import BedrockAdapter

        env = {"MODEL_ID": "m", "AWS_REGION": "us-east-1"}
        with patch("model_adapters.BedrockModel") as mock_cls:
            BedrockAdapter(env).build()
            kwargs = mock_cls.call_args.kwargs
            assert "guardrail_id" not in kwargs
            assert "guardrail_version" not in kwargs

    def test_build_passes_guardrail_kwargs_when_guardrail_id_set(self):
        from model_adapters import BedrockAdapter

        env = {
            "MODEL_ID": "m",
            "AWS_REGION": "us-east-1",
            "GUARDRAIL_ID": "gid-123",
            "GUARDRAIL_VERSION": "2",
        }
        with patch("model_adapters.BedrockModel") as mock_cls:
            BedrockAdapter(env).build()
            kwargs = mock_cls.call_args.kwargs
            assert kwargs["guardrail_id"] == "gid-123"
            assert kwargs["guardrail_version"] == "2"

    def test_guardrail_version_defaults_to_draft_when_unset(self):
        from model_adapters import BedrockAdapter

        env = {
            "MODEL_ID": "m",
            "AWS_REGION": "us-east-1",
            "GUARDRAIL_ID": "gid-123",
        }
        with patch("model_adapters.BedrockModel") as mock_cls:
            BedrockAdapter(env).build()
            kwargs = mock_cls.call_args.kwargs
            assert kwargs["guardrail_version"] == "DRAFT"

    def test_missing_model_id_raises_key_error(self):
        from model_adapters import BedrockAdapter

        with pytest.raises(KeyError):
            BedrockAdapter({"AWS_REGION": "us-east-1"})

    def test_missing_aws_region_raises_key_error(self):
        from model_adapters import BedrockAdapter

        with pytest.raises(KeyError):
            BedrockAdapter({"MODEL_ID": "m"})


class TestGeminiAdapter:
    def test_build_constructs_gemini_model_with_model_id(self):
        from model_adapters import GeminiAdapter

        mock_gemini_cls = MagicMock()
        with patch.dict(
            "sys.modules",
            {"strands.models.gemini": MagicMock(GeminiModel=mock_gemini_cls)},
        ):
            GeminiAdapter({"MODEL_ID": "gemini-pro"}).build()
            mock_gemini_cls.assert_called_once_with(model_id="gemini-pro")

    def test_build_does_not_pass_guardrail_kwargs(self):
        """Gemini adapter must never receive Bedrock guardrail kwargs."""
        from model_adapters import GeminiAdapter

        mock_gemini_cls = MagicMock()
        with patch.dict(
            "sys.modules",
            {"strands.models.gemini": MagicMock(GeminiModel=mock_gemini_cls)},
        ):
            env = {
                "MODEL_ID": "gemini-pro",
                "GUARDRAIL_ID": "ignored",
                "GUARDRAIL_VERSION": "1",
            }
            GeminiAdapter(env).build()
            call_kwargs = mock_gemini_cls.call_args.kwargs
            assert "guardrail_id" not in call_kwargs
            assert "guardrail_version" not in call_kwargs

    def test_missing_model_id_raises_key_error(self):
        from model_adapters import GeminiAdapter

        with pytest.raises(KeyError):
            GeminiAdapter({})

    def test_import_failure_surfaces_clearly_without_fallback(self):
        """If the Google dependency is missing, ImportError must propagate — no Bedrock fallback."""
        from model_adapters import GeminiAdapter

        with patch.dict("sys.modules", {"strands.models.gemini": None}):
            with pytest.raises((ImportError, ModuleNotFoundError, TypeError)):
                GeminiAdapter({"MODEL_ID": "gemini-pro"}).build()
