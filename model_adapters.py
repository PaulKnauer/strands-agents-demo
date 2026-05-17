"""Local model adapter — owns provider selection and model construction for local Strands runtime.

This module is intentionally local-only. deploy/app.py uses direct Bedrock Converse
via boto3 and must not import from here.
"""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from urllib.parse import urlparse

from strands.models import BedrockModel


@dataclass(frozen=True)
class ModelCapabilities:
    provider: str
    family: str
    runtimes: tuple[str, ...]
    enabled: bool
    supports_converse: bool
    supports_tools: bool
    supports_guardrails: bool
    supports_streaming: bool
    bedrock_first: bool
    region_constraint: str
    notes: str = ""


# Registry of known provider/family entries.
# enabled=True  → valid MODEL_PROVIDER key for local runtime today.
# enabled=False → planned candidate; not selectable until a rollout story enables it.
_REGISTRY: tuple[ModelCapabilities, ...] = (
    ModelCapabilities(
        provider="bedrock",
        family="Amazon Bedrock",
        runtimes=("local", "deployed"),
        enabled=True,
        supports_converse=True,
        supports_tools=True,
        supports_guardrails=True,
        supports_streaming=True,
        bedrock_first=True,
        region_constraint="Configured AWS_REGION; default docs use us-east-1.",
        notes="Supports local Strands runtime and deployed AgentCore runtime.",
    ),
    ModelCapabilities(
        provider="gemini",
        family="Google Gemini",
        runtimes=("local",),
        enabled=True,
        supports_converse=False,
        supports_tools=True,
        supports_guardrails=False,
        supports_streaming=False,
        bedrock_first=False,
        region_constraint="Not region-scoped by AWS_REGION; local-only Google API path.",
        notes="Local only via strands-agents[gemini] optional dependency.",
    ),
    # Exploratory local-only evaluation boundary — Story 4.4.
    # Not deployable through AgentCore. Uses strands-agents[litellm] optional dependency.
    # One concrete example: Kimi via https://api.moonshot.ai/v1 with MOONSHOT_API_KEY bearer auth.
    ModelCapabilities(
        provider="litellm",
        family="LiteLLM (direct-provider evaluation)",
        runtimes=("local",),
        enabled=True,
        supports_converse=False,
        supports_tools=True,
        supports_guardrails=False,
        supports_streaming=True,
        bedrock_first=False,
        region_constraint="Not region-scoped by AWS_REGION; local-only direct-provider evaluation path.",
        notes="Exploratory local-only evaluation boundary (Story 4.4). Install via pip install 'strands-agents[litellm]'. Example: Kimi via https://api.moonshot.ai/v1. Not deployable through AgentCore.",
    ),
    # Enabled Bedrock-first family alias — Meta Llama 3.1 70B Instruct via Amazon Bedrock.
    # Concrete Bedrock model IDs (US region deployment default):
    #   us.meta.llama3-1-70b-instruct-v1:0  — geo-inference (us-east-1 default)
    #   meta.llama3-1-70b-instruct-v1:0     — single-region (us-west-2)
    # Requires Bedrock model access in the target account before use.
    ModelCapabilities(
        provider="llama",
        family="Llama",
        runtimes=("local", "deployed"),
        enabled=True,
        supports_converse=True,
        supports_tools=True,
        supports_guardrails=True,
        supports_streaming=True,
        bedrock_first=True,
        region_constraint="Configured AWS_REGION; us.meta.llama3-1-70b-instruct-v1:0 recommended for us-east-1 (geo-inference). Single-region ID meta.llama3-1-70b-instruct-v1:0 targets us-west-2.",
        notes="Bedrock-backed via Meta Llama 3.1 70B Instruct. Not a direct Meta API integration. Enabled in Story 4.3.",
    ),
    # Planned Bedrock-first candidate families — enabled=False until a future rollout story validates them.
    ModelCapabilities(
        provider="gemma",
        family="Gemma",
        runtimes=("planned",),
        enabled=False,
        supports_converse=False,
        supports_tools=False,
        supports_guardrails=False,
        supports_streaming=False,
        bedrock_first=True,
        region_constraint="Unknown until a future rollout story validates Bedrock model ID and region.",
        notes="Planned via Amazon Bedrock in a future Epic 4 story.",
    ),
    ModelCapabilities(
        provider="moonshot",
        family="Moonshot/Kimi",
        runtimes=("planned",),
        enabled=False,
        supports_converse=False,
        supports_tools=False,
        supports_guardrails=False,
        supports_streaming=False,
        bedrock_first=True,
        region_constraint="Unknown until a future rollout story validates Bedrock model ID and region.",
        notes="Planned via Amazon Bedrock in a future Epic 4 story. Canonical key: moonshot.",
    ),
    ModelCapabilities(
        provider="kimi",
        family="Moonshot/Kimi",
        runtimes=("planned",),
        enabled=False,
        supports_converse=False,
        supports_tools=False,
        supports_guardrails=False,
        supports_streaming=False,
        bedrock_first=True,
        region_constraint="Unknown until a future rollout story validates Bedrock model ID and region; alias for Moonshot/Kimi.",
        notes="Planned alias for Moonshot/Kimi via Amazon Bedrock in a future Epic 4 story.",
    ),
    ModelCapabilities(
        provider="qwen",
        family="Qwen",
        runtimes=("planned",),
        enabled=False,
        supports_converse=False,
        supports_tools=False,
        supports_guardrails=False,
        supports_streaming=False,
        bedrock_first=True,
        region_constraint="Unknown until a future rollout story validates Bedrock model ID and region.",
        notes="Planned via Amazon Bedrock in a future Epic 4 story.",
    ),
    ModelCapabilities(
        provider="deepseek",
        family="DeepSeek",
        runtimes=("planned",),
        enabled=False,
        supports_converse=False,
        supports_tools=False,
        supports_guardrails=False,
        supports_streaming=False,
        bedrock_first=True,
        region_constraint="Unknown until a future rollout story validates Bedrock model ID and region.",
        notes="Planned via Amazon Bedrock in a future Epic 4 story.",
    ),
)

_REGISTRY_BY_PROVIDER: Mapping[str, ModelCapabilities] = MappingProxyType(
    {cap.provider: cap for cap in _REGISTRY}
)
if len(_REGISTRY_BY_PROVIDER) != len(_REGISTRY):
    raise RuntimeError("Duplicate provider keys in _REGISTRY")


def get_model_capabilities(provider: str) -> ModelCapabilities | None:
    """Return capability metadata for a provider key, or None if unknown."""
    return _REGISTRY_BY_PROVIDER.get(provider)


def supported_local_providers() -> list[str]:
    """Return provider keys that are currently enabled for local runtime use."""
    return [
        cap.provider for cap in _REGISTRY if cap.enabled and "local" in cap.runtimes
    ]


def planned_model_families() -> list[str]:
    """Return provider keys that are planned but not yet enabled."""
    return [cap.provider for cap in _REGISTRY if not cap.enabled]


class LocalModelAdapter(ABC):
    """Abstract base class for all local model adapters.

    Every concrete adapter must implement ``build()`` and return a
    framework-compatible model instance.  This contract is enforced at
    class-definition time, preventing silent duck-typing failures when a
    new adapter forgets to implement the method.
    """

    @abstractmethod
    def build(self):
        """Return a framework-compatible model instance."""


class BedrockAdapter(LocalModelAdapter):
    def __init__(self, env: Mapping[str, str]):
        self._model_id = env["MODEL_ID"]
        self._region = env["AWS_REGION"]
        # Guardrails are optional — only wired when GUARDRAIL_ID is configured
        guardrail_id = env.get("GUARDRAIL_ID")
        if guardrail_id:
            self._guardrail_kwargs = {
                "guardrail_id": guardrail_id,
                "guardrail_version": env.get("GUARDRAIL_VERSION", "DRAFT"),
            }
        else:
            self._guardrail_kwargs = {}

    def build(self):
        return BedrockModel(
            model_id=self._model_id,
            region_name=self._region,
            **self._guardrail_kwargs,
        )


class GeminiAdapter(LocalModelAdapter):
    def __init__(self, env: Mapping[str, str]):
        self._model_id = env["MODEL_ID"]

    def build(self):
        # Lazy import — strands-agents[gemini] is optional; absent dependency must surface
        from strands.models.gemini import GeminiModel

        return GeminiModel(model_id=self._model_id)


class LiteLLMAdapter(LocalModelAdapter):
    def __init__(self, env: Mapping[str, str]):
        self._model_id = env["MODEL_ID"]
        if (
            self._model_id.startswith("moonshot/")
            and not env.get("MOONSHOT_API_KEY", "").strip()
        ):
            raise ValueError(
                "MODEL_PROVIDER=litellm with a moonshot/* MODEL_ID requires "
                "MOONSHOT_API_KEY. Set MOONSHOT_API_KEY for the documented "
                "Kimi evaluation path."
            )
        api_base = env.get("LITELLM_API_BASE", "").strip()
        if api_base:
            parsed = urlparse(api_base)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                raise ValueError(
                    "LITELLM_API_BASE must be an absolute http(s) URL, "
                    "for example https://api.moonshot.ai/v1."
                )
            hostname = parsed.hostname or ""
            if (
                parsed.scheme == "http"
                and hostname != "localhost"
                and not hostname.startswith("127.")
            ):
                raise ValueError(
                    "LITELLM_API_BASE with http:// is only allowed for localhost endpoints; "
                    "use https:// for external providers (e.g. https://api.moonshot.ai/v1)."
                )
        self._client_args = {"api_base": api_base} if api_base else {}

    def build(self):
        # Lazy import — strands-agents[litellm] is optional; absent dependency must surface
        try:
            from strands.models.litellm import LiteLLMModel
        except ImportError as exc:
            raise ImportError(
                "LiteLLM support requires the optional dependency: "
                "pip install 'strands-agents[litellm]'."
            ) from exc

        return LiteLLMModel(
            client_args=self._client_args or None,
            model_id=self._model_id,
        )


# Dispatch map for non-Bedrock local adapters (OCP: add new provider here + a new class,
# no edits needed inside create_local_model_adapter).
_ADAPTER_MAP: dict[str, type[LocalModelAdapter]] = {
    "gemini": GeminiAdapter,
    "litellm": LiteLLMAdapter,
}


def create_local_model_adapter(
    provider: str, env: Mapping[str, str]
) -> LocalModelAdapter:
    """Return the appropriate local model adapter for the given provider.

    Raises ValueError for unsupported providers — no silent fallback.
    Distinguishes planned-but-not-enabled families from completely unknown keys.
    Registry-backed: any enabled Bedrock-first local provider uses BedrockAdapter.
    Non-Bedrock providers are dispatched via _ADAPTER_MAP — extend that dict to add
    a new provider without touching this function.
    """
    cap = _REGISTRY_BY_PROVIDER.get(provider)
    if cap is None:
        raise ValueError(
            f"Unknown MODEL_PROVIDER: '{provider}'. "
            f"Supported local providers: {supported_local_providers()}."
        )
    if not cap.enabled:
        raise ValueError(
            f"MODEL_PROVIDER '{provider}' ({cap.family}) is a planned candidate "
            f"and is not yet enabled for local runtime use. "
            f"Supported local providers: {supported_local_providers()}."
        )
    if "local" not in cap.runtimes:
        raise ValueError(
            f"MODEL_PROVIDER '{provider}' is not enabled for local runtime use. "
            f"Supported local providers: {supported_local_providers()}."
        )
    if provider in _ADAPTER_MAP:
        return _ADAPTER_MAP[provider](env)
    if cap.bedrock_first:
        return BedrockAdapter(env)
    raise ValueError(
        f"MODEL_PROVIDER '{provider}' has no local adapter implementation. "
        f"Supported local providers: {supported_local_providers()}."
    )
