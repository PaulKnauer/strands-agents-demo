"""Unit tests for model_adapters.py — adapter selection, construction, and boundary."""

import dataclasses
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


# ── Capability registry ───────────────────────────────────────────────────────


class TestCapabilityRegistry:
    """Registry structure and content contracts."""

    def test_supported_local_providers_includes_bedrock_and_gemini(self):
        from model_adapters import supported_local_providers

        providers = supported_local_providers()
        assert "bedrock" in providers
        assert "gemini" in providers

    def test_supported_local_providers_excludes_planned_families(self):
        from model_adapters import supported_local_providers

        providers = supported_local_providers()
        for family in ("gemma", "moonshot", "kimi", "qwen", "deepseek"):
            assert family not in providers

    def test_planned_model_families_includes_all_candidate_provider_keys(self):
        from model_adapters import planned_model_families

        provider_keys = planned_model_families()
        for expected in ("gemma", "moonshot", "kimi", "qwen", "deepseek"):
            assert expected in provider_keys

    def test_get_model_capabilities_bedrock_is_enabled(self):
        from model_adapters import get_model_capabilities

        cap = get_model_capabilities("bedrock")
        assert cap is not None
        assert cap.enabled is True
        assert "local" in cap.runtimes
        assert "deployed" in cap.runtimes

    def test_get_model_capabilities_gemini_is_enabled(self):
        from model_adapters import get_model_capabilities

        cap = get_model_capabilities("gemini")
        assert cap is not None
        assert cap.enabled is True
        assert cap.runtimes == ("local",)

    def test_get_model_capabilities_bedrock_runtime_capabilities(self):
        from model_adapters import get_model_capabilities

        cap = get_model_capabilities("bedrock")
        assert cap.supports_converse is True
        assert cap.supports_tools is True
        assert cap.supports_guardrails is True
        assert cap.supports_streaming is True
        assert cap.bedrock_first is True
        assert "AWS_REGION" in cap.region_constraint

    def test_get_model_capabilities_gemini_runtime_capabilities(self):
        from model_adapters import get_model_capabilities

        cap = get_model_capabilities("gemini")
        assert cap.supports_converse is False
        assert cap.supports_tools is True
        assert cap.supports_guardrails is False
        assert cap.supports_streaming is False
        assert cap.bedrock_first is False
        assert "local-only" in cap.region_constraint

    def test_get_model_capabilities_bedrock_supports_guardrails(self):
        from model_adapters import get_model_capabilities

        cap = get_model_capabilities("bedrock")
        assert cap.supports_guardrails is True

    def test_get_model_capabilities_gemini_does_not_support_guardrails(self):
        from model_adapters import get_model_capabilities

        cap = get_model_capabilities("gemini")
        assert cap.supports_guardrails is False

    def test_get_model_capabilities_planned_families_not_enabled(self):
        from model_adapters import get_model_capabilities

        for provider in ("gemma", "moonshot", "kimi", "qwen", "deepseek"):
            cap = get_model_capabilities(provider)
            assert (
                cap is not None
            ), f"Missing registry entry for planned family: {provider}"
            assert (
                cap.enabled is False
            ), f"Planned family '{provider}' must not be enabled"

    def test_get_model_capabilities_planned_families_bedrock_first(self):
        from model_adapters import get_model_capabilities

        for provider in ("gemma", "moonshot", "kimi", "qwen", "deepseek"):
            cap = get_model_capabilities(provider)
            assert cap.runtimes == ("planned",)
            assert cap.supports_converse is False
            assert cap.region_constraint.startswith("Unknown")
            assert cap.bedrock_first is True

    def test_get_model_capabilities_unknown_returns_none(self):
        from model_adapters import get_model_capabilities

        assert get_model_capabilities("openai") is None
        assert get_model_capabilities("mistral") is None

    def test_registry_entries_are_immutable(self):
        from model_adapters import get_model_capabilities

        cap = get_model_capabilities("bedrock")
        with pytest.raises(dataclasses.FrozenInstanceError):
            cap.enabled = False  # frozen dataclass must reject mutation

    def test_moonshot_is_canonical_key_for_kimi_alias(self):
        from model_adapters import get_model_capabilities

        moonshot_cap = get_model_capabilities("moonshot")
        kimi_cap = get_model_capabilities("kimi")
        assert moonshot_cap is not None
        assert kimi_cap is not None
        assert moonshot_cap.family == kimi_cap.family
        assert "canonical" in moonshot_cap.notes.lower()
        assert "alias" in kimi_cap.notes.lower()


class TestLlamaAdapter:
    """Llama is an enabled Bedrock-first family alias after Story 4.3 rollout."""

    _env = {
        "MODEL_ID": "us.meta.llama3-1-70b-instruct-v1:0",
        "AWS_REGION": "us-east-1",
    }

    def test_llama_is_enabled_in_registry(self):
        from model_adapters import get_model_capabilities

        cap = get_model_capabilities("llama")
        assert cap is not None
        assert cap.enabled is True

    def test_llama_runtimes_include_local_and_deployed(self):
        from model_adapters import get_model_capabilities

        cap = get_model_capabilities("llama")
        assert "local" in cap.runtimes
        assert "deployed" in cap.runtimes

    def test_llama_capability_metadata(self):
        from model_adapters import get_model_capabilities

        cap = get_model_capabilities("llama")
        assert cap.supports_converse is True
        assert cap.supports_tools is True
        assert cap.supports_guardrails is True
        assert cap.bedrock_first is True

    def test_llama_in_supported_local_providers(self):
        from model_adapters import supported_local_providers

        assert "llama" in supported_local_providers()

    def test_llama_not_in_planned_model_families(self):
        from model_adapters import planned_model_families

        assert "llama" not in planned_model_families()

    def test_llama_local_adapter_returns_bedrock_adapter(self):
        from model_adapters import create_local_model_adapter, BedrockAdapter

        adapter = create_local_model_adapter("llama", self._env)
        assert isinstance(adapter, BedrockAdapter)

    def test_llama_adapter_uses_model_id_from_env(self):
        from model_adapters import create_local_model_adapter

        with patch("model_adapters.BedrockModel") as mock_cls:
            adapter = create_local_model_adapter("llama", self._env)
            adapter.build()
            kwargs = mock_cls.call_args.kwargs
            assert kwargs["model_id"] == "us.meta.llama3-1-70b-instruct-v1:0"
            assert kwargs["region_name"] == "us-east-1"

    def test_llama_adapter_wires_guardrails_when_set(self):
        from model_adapters import create_local_model_adapter

        env = {**self._env, "GUARDRAIL_ID": "gr-llama", "GUARDRAIL_VERSION": "1"}
        with patch("model_adapters.BedrockModel") as mock_cls:
            adapter = create_local_model_adapter("llama", env)
            adapter.build()
            kwargs = mock_cls.call_args.kwargs
            assert kwargs["guardrail_id"] == "gr-llama"
            assert kwargs["guardrail_version"] == "1"

    def test_llama_notes_document_bedrock_model_ids(self):
        from model_adapters import get_model_capabilities

        cap = get_model_capabilities("llama")
        # Notes must make clear this is Bedrock-backed, not a direct Meta API
        assert "Bedrock" in cap.notes or "bedrock" in cap.notes.lower()
        assert "Meta" in cap.notes

    def test_llama_region_constraint_documents_geo_inference_id(self):
        from model_adapters import get_model_capabilities

        cap = get_model_capabilities("llama")
        assert "us.meta.llama3-1-70b-instruct-v1:0" in cap.region_constraint


class TestPlannedFamilyProviderRejection:
    """Planned family labels must fail clearly when used as MODEL_PROVIDER."""

    _env = {"MODEL_ID": "any", "AWS_REGION": "us-east-1"}

    def test_gemma_raises_value_error(self):
        from model_adapters import create_local_model_adapter

        with pytest.raises(ValueError, match="planned candidate"):
            create_local_model_adapter("gemma", self._env)

    def test_moonshot_raises_value_error(self):
        from model_adapters import create_local_model_adapter

        with pytest.raises(ValueError, match="planned candidate"):
            create_local_model_adapter("moonshot", self._env)

    def test_kimi_raises_value_error(self):
        from model_adapters import create_local_model_adapter

        with pytest.raises(ValueError, match="planned candidate"):
            create_local_model_adapter("kimi", self._env)

    def test_qwen_raises_value_error(self):
        from model_adapters import create_local_model_adapter

        with pytest.raises(ValueError, match="planned candidate"):
            create_local_model_adapter("qwen", self._env)

    def test_deepseek_raises_value_error(self):
        from model_adapters import create_local_model_adapter

        with pytest.raises(ValueError, match="planned candidate"):
            create_local_model_adapter("deepseek", self._env)

    def test_unknown_provider_error_mentions_supported_providers(self):
        """Unknown providers must distinguish themselves from planned-but-not-enabled families."""
        from model_adapters import create_local_model_adapter

        with pytest.raises(ValueError, match="bedrock") as exc_info:
            create_local_model_adapter("openai", self._env)
        assert "gemini" in str(exc_info.value)

    def test_planned_provider_error_distinguishes_from_unknown(self):
        """Planned-but-not-enabled error must mention 'planned' to distinguish from unknown."""
        from model_adapters import create_local_model_adapter

        with pytest.raises(ValueError) as exc_info:
            create_local_model_adapter("gemma", self._env)
        error_msg = str(exc_info.value)
        assert "planned" in error_msg.lower() or "not yet enabled" in error_msg.lower()


class TestLiteLLMAdapter:
    """LiteLLM is an exploratory local-only evaluation boundary (Story 4.4)."""

    def test_litellm_is_enabled_in_registry(self):
        from model_adapters import get_model_capabilities

        cap = get_model_capabilities("litellm")
        assert cap is not None
        assert cap.enabled is True

    def test_litellm_is_local_only(self):
        from model_adapters import get_model_capabilities

        cap = get_model_capabilities("litellm")
        assert cap.runtimes == ("local",)
        assert "deployed" not in cap.runtimes

    def test_litellm_is_not_bedrock_first(self):
        from model_adapters import get_model_capabilities

        cap = get_model_capabilities("litellm")
        assert cap.bedrock_first is False

    def test_litellm_does_not_support_converse(self):
        from model_adapters import get_model_capabilities

        cap = get_model_capabilities("litellm")
        assert cap.supports_converse is False

    def test_litellm_does_not_support_guardrails(self):
        from model_adapters import get_model_capabilities

        cap = get_model_capabilities("litellm")
        assert cap.supports_guardrails is False

    def test_litellm_in_supported_local_providers(self):
        from model_adapters import supported_local_providers

        assert "litellm" in supported_local_providers()

    def test_litellm_not_in_planned_model_families(self):
        from model_adapters import planned_model_families

        assert "litellm" not in planned_model_families()

    def test_litellm_notes_mark_as_exploratory(self):
        from model_adapters import get_model_capabilities

        cap = get_model_capabilities("litellm")
        notes_lower = cap.notes.lower()
        assert "exploratory" in notes_lower or "evaluation" in notes_lower

    def test_litellm_local_adapter_returns_litellm_adapter(self):
        from model_adapters import create_local_model_adapter, LiteLLMAdapter

        adapter = create_local_model_adapter(
            "litellm",
            {
                "MODEL_ID": "moonshot/moonshot-v1-8k",
                "MOONSHOT_API_KEY": "test-key",
            },
        )
        assert isinstance(adapter, LiteLLMAdapter)

    def test_litellm_local_adapter_requires_moonshot_api_key_for_moonshot_models(self):
        from model_adapters import create_local_model_adapter

        with pytest.raises(ValueError, match="MOONSHOT_API_KEY"):
            create_local_model_adapter(
                "litellm", {"MODEL_ID": "moonshot/moonshot-v1-8k"}
            )

    def test_litellm_adapter_build_constructs_model_with_model_id(self):
        from model_adapters import LiteLLMAdapter

        mock_litellm_cls = MagicMock()
        with patch.dict(
            "sys.modules",
            {"strands.models.litellm": MagicMock(LiteLLMModel=mock_litellm_cls)},
        ):
            LiteLLMAdapter(
                {
                    "MODEL_ID": "moonshot/moonshot-v1-8k",
                    "MOONSHOT_API_KEY": "test-key",
                }
            ).build()
            mock_litellm_cls.assert_called_once()
            assert (
                mock_litellm_cls.call_args.kwargs.get("model_id")
                == "moonshot/moonshot-v1-8k"
            )

    def test_litellm_adapter_passes_api_base_client_arg(self):
        from model_adapters import LiteLLMAdapter

        mock_litellm_cls = MagicMock()
        with patch.dict(
            "sys.modules",
            {"strands.models.litellm": MagicMock(LiteLLMModel=mock_litellm_cls)},
        ):
            LiteLLMAdapter(
                {
                    "MODEL_ID": "moonshot/moonshot-v1-8k",
                    "MOONSHOT_API_KEY": "test-key",
                    "LITELLM_API_BASE": " https://api.moonshot.ai/v1 ",
                }
            ).build()
        assert mock_litellm_cls.call_args.kwargs["client_args"] == {
            "api_base": "https://api.moonshot.ai/v1"
        }

    def test_litellm_adapter_omits_client_args_without_api_base(self):
        from model_adapters import LiteLLMAdapter

        mock_litellm_cls = MagicMock()
        with patch.dict(
            "sys.modules",
            {"strands.models.litellm": MagicMock(LiteLLMModel=mock_litellm_cls)},
        ):
            LiteLLMAdapter(
                {
                    "MODEL_ID": "moonshot/moonshot-v1-8k",
                    "MOONSHOT_API_KEY": "test-key",
                    "LITELLM_API_BASE": " ",
                }
            ).build()
        assert mock_litellm_cls.call_args.kwargs["client_args"] is None

    def test_litellm_adapter_rejects_malformed_api_base(self):
        from model_adapters import LiteLLMAdapter

        with pytest.raises(ValueError, match="LITELLM_API_BASE"):
            LiteLLMAdapter(
                {
                    "MODEL_ID": "moonshot/moonshot-v1-8k",
                    "MOONSHOT_API_KEY": "test-key",
                    "LITELLM_API_BASE": "api.moonshot.ai/v1",
                }
            )

    def test_litellm_adapter_rejects_http_for_external_host(self):
        from model_adapters import LiteLLMAdapter

        with pytest.raises(ValueError, match="localhost"):
            LiteLLMAdapter(
                {
                    "MODEL_ID": "moonshot/moonshot-v1-8k",
                    "MOONSHOT_API_KEY": "test-key",
                    "LITELLM_API_BASE": "http://api.moonshot.ai/v1",
                }
            )

    def test_litellm_adapter_accepts_http_for_localhost(self):
        from model_adapters import LiteLLMAdapter

        adapter = LiteLLMAdapter(
            {
                "MODEL_ID": "some/local-model",
                "LITELLM_API_BASE": "http://localhost:8080/v1",
            }
        )
        assert adapter._client_args == {"api_base": "http://localhost:8080/v1"}

    def test_litellm_adapter_accepts_http_for_127_loopback(self):
        from model_adapters import LiteLLMAdapter

        adapter = LiteLLMAdapter(
            {
                "MODEL_ID": "some/local-model",
                "LITELLM_API_BASE": "http://127.0.0.1:11434/v1",
            }
        )
        assert adapter._client_args == {"api_base": "http://127.0.0.1:11434/v1"}

    def test_litellm_adapter_import_failure_surfaces_clearly(self):
        """If strands-agents[litellm] is missing, error guidance must be actionable."""
        from model_adapters import LiteLLMAdapter

        with patch.dict("sys.modules", {"strands.models.litellm": None}):
            with pytest.raises(ImportError, match=r"strands-agents\[litellm\]"):
                LiteLLMAdapter(
                    {
                        "MODEL_ID": "moonshot/moonshot-v1-8k",
                        "MOONSHOT_API_KEY": "test-key",
                    }
                ).build()

    def test_litellm_adapter_missing_model_id_raises_key_error(self):
        from model_adapters import LiteLLMAdapter

        with pytest.raises(KeyError):
            LiteLLMAdapter({})

    def test_litellm_factory_respects_registry_disabled_state(self):
        import model_adapters
        from model_adapters import create_local_model_adapter

        disabled = dataclasses.replace(
            model_adapters.get_model_capabilities("litellm"), enabled=False
        )
        registry = {cap.provider: cap for cap in model_adapters._REGISTRY}
        registry["litellm"] = disabled
        with patch.object(model_adapters, "_REGISTRY_BY_PROVIDER", registry):
            with pytest.raises(ValueError, match="planned candidate|not yet enabled"):
                create_local_model_adapter(
                    "litellm",
                    {
                        "MODEL_ID": "moonshot/moonshot-v1-8k",
                        "MOONSHOT_API_KEY": "test-key",
                    },
                )
