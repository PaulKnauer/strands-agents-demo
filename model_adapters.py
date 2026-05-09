"""Local model adapter — owns provider selection and model construction for local Strands runtime.

This module is intentionally local-only. deploy/app.py uses direct Bedrock Converse
via boto3 and must not import from here.
"""

from typing import Mapping

from strands.models import BedrockModel


class BedrockAdapter:
    def __init__(self, env: Mapping[str, str]):
        self._model_id = env["MODEL_ID"]
        self._region = env["AWS_REGION"]
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


class GeminiAdapter:
    def __init__(self, env: Mapping[str, str]):
        self._model_id = env["MODEL_ID"]

    def build(self):
        # Lazy import — strands-agents[gemini] is optional; absent dependency must surface
        from strands.models.gemini import GeminiModel

        return GeminiModel(model_id=self._model_id)


def create_local_model_adapter(provider: str, env: Mapping[str, str]):
    """Return the appropriate local model adapter for the given provider.

    Raises ValueError for unsupported providers — no silent fallback.
    """
    if provider == "bedrock":
        return BedrockAdapter(env)
    elif provider == "gemini":
        return GeminiAdapter(env)
    else:
        raise ValueError(
            f"Unknown MODEL_PROVIDER: '{provider}'. Expected 'bedrock' or 'gemini'."
        )
