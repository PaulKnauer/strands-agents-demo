You are the Blind Hunter reviewer for Story `4-4-optional-direct-provider-evaluation-boundary`.

Review the diff below with no project context. Focus on bugs, regressions, misleading behavior, risky assumptions, and internal inconsistencies visible from the patch alone.

Output findings as a Markdown list. Each finding should include:
- a short title
- severity (`high`, `medium`, or `low`)
- concise evidence from the diff
- the concrete risk

If there are no findings, say `No findings.`

```diff
diff --git a/.env.example b/.env.example
index 5987b98..1ae97e5 100644
--- a/.env.example
+++ b/.env.example
@@ -39,3 +39,17 @@ AGENT_NAME=age-in-days-demo
 # --- Optional: Google Gemini (only if MODEL_PROVIDER=gemini) ---
 # Your Google AI Studio API key (required when MODEL_PROVIDER=gemini)
 # GOOGLE_API_KEY=your-gemini-api-key-here
+
+# --- Optional: LiteLLM direct-provider evaluation (local-only, exploratory) ---
+# This path is NOT deployable through AgentCore. It is an evaluation boundary (Story 4.4),
+# not a production-aligned alternative to the Bedrock-first path.
+# Requires: pip install 'strands-agents[litellm]'
+# Extra burden: provider-specific secrets, outbound networking, wider test matrix.
+#
+# Example: Kimi (Moonshot) via LiteLLM — OpenAI-compatible API
+# MODEL_PROVIDER=litellm
+# MODEL_ID=moonshot/moonshot-v1-8k
+# MOONSHOT_API_KEY=your-moonshot-api-key-here
+#
+# Optional: override the API base URL for other OpenAI-compatible providers
+# LITELLM_API_BASE=https://api.moonshot.ai/v1
diff --git a/README.md b/README.md
index c5da0c6..a420319 100644
--- a/README.md
+++ b/README.md
@@ -408,12 +408,15 @@ Epic 4 adds Bedrock-first staged support for additional model families. The tabl
 
 | Stage | Providers / families | Status |
 |-------|---------------------|--------|
-| Supported today | `bedrock` (local + deployed), `gemini` (local only), `llama` (local + deployed, Bedrock-backed) | ✅ |
-| Planned — Bedrock-first | Gemma, Moonshot/Kimi, Qwen, DeepSeek via Amazon Bedrock | 🔜 Epic 4.4 |
-| Optional / evaluated later | Direct-provider or LiteLLM paths outside Bedrock | 🔭 Epic 4.4 |
+| Production-aligned | `bedrock` (local + deployed), `llama` (local + deployed, Bedrock-backed) | ✅ |
+| Supported local-only | `gemini` (local only, Google API) | ✅ |
+| Exploratory local-only evaluation | `litellm` (direct-provider via LiteLLM, e.g. Kimi; **not deployable through AgentCore**) | 🔭 |
+| Planned — Bedrock-first | Gemma, Moonshot/Kimi, Qwen, DeepSeek via Amazon Bedrock | 🔜 Epic 4.5 |
 
 Setting `MODEL_PROVIDER` to a planned family name today (e.g. `gemma`, `qwen`) will fail explicitly because those paths are not yet implemented. Local adapter selection raises `ValueError`; AgentCore deployment preflight rejects non-Bedrock-backed providers; and an already-running deployed runtime returns an unsupported-provider error before invoking Bedrock.
 
+The `litellm` path is an evaluation boundary, not a default alternative to Bedrock. It requires an optional dependency (`pip install 'strands-agents[litellm]'`), provider-specific credentials (e.g. `MOONSHOT_API_KEY`), and outbound network access to the chosen provider. AgentCore deployment in this repo remains Bedrock-only even when the local `litellm` path is used.
+
 `MODEL_PROVIDER=llama` is Bedrock-backed — it routes through Amazon Bedrock Converse, not a direct Meta API. The concrete supported model is `us.meta.llama3-1-70b-instruct-v1:0` (Meta Llama 3.1 70B Instruct) for `us-east-1` deployments. Llama model access must be granted in your Bedrock account (Console → Amazon Bedrock → Model access) before using this path.
 
 ---
diff --git a/_bmad-output/implementation-artifacts/sprint-status.yaml b/_bmad-output/implementation-artifacts/sprint-status.yaml
index 62267e6..692d165 100644
--- a/_bmad-output/implementation-artifacts/sprint-status.yaml
+++ b/_bmad-output/implementation-artifacts/sprint-status.yaml
@@ -35,7 +35,7 @@
 # - Dev moves story to 'review', then runs code-review (fresh context, different LLM recommended)
 
 generated: 2026-05-08 20:42:26 SAST
-last_updated: 2026-05-15 10:54:37 SAST
+last_updated: 2026-05-15 10:59:40 SAST
 project: strands-agents-demo
 project_key: NOKEY
 tracking_system: file-system
@@ -69,6 +69,6 @@ development_status:
   4-1-expansion-scope-alignment: done
   4-2-capability-registry-and-adapter-extension: done
   4-3-bedrock-first-model-family-rollout: done
-  4-4-optional-direct-provider-evaluation-boundary: backlog
+  4-4-optional-direct-provider-evaluation-boundary: review
   4-5-expansion-documentation-and-verification: backlog
   epic-4-retrospective: optional
diff --git a/_bmad-output/project-context.md b/_bmad-output/project-context.md
index 17c7b68..fb38db8 100644
--- a/_bmad-output/project-context.md
+++ b/_bmad-output/project-context.md
@@ -59,10 +59,11 @@ _This file contains critical rules and patterns that AI agents must follow when
 ### Provider And Model Rules
 
 - Current provider abstraction is explicit: `MODEL_PROVIDER` plus `MODEL_ID`.
- Local adapter code supports `bedrock`, `gemini`, and `llama` (Bedrock-backed); all other local provider values raise `ValueError`.
+ Local adapter code supports `bedrock`, `gemini`, `llama`, and `litellm` (exploratory local-only evaluation boundary); all other local provider values raise `ValueError`.
 - Deployed AgentCore code supports `bedrock` and `llama` (both Bedrock-backed via Converse); other deployed provider values return an explicit unsupported-provider error before Bedrock invocation.
 - `llama` is a Bedrock-backed family alias (Meta Llama 3.1 70B Instruct via Amazon Bedrock); it is not a direct Meta API integration. Enabled as of Story 4.3.
- Epic 4 staged expansion targets Gemma, Moonshot/Kimi, Qwen, and DeepSeek through Amazon Bedrock (Story 4.4+); these are future work, not currently configured providers. Optional direct-provider or LiteLLM paths outside Bedrock are evaluated later (Story 4.4).
+ - `litellm` is an exploratory local-only evaluation boundary (Story 4.4). It is not deployable through AgentCore. It requires `pip install 'strands-agents[litellm]'` and provider-specific credentials. Do not treat it as a production-aligned default or as parity with the Bedrock-first path.
+ - Epic 4 staged expansion targets Gemma, Moonshot/Kimi, Qwen, and DeepSeek through Amazon Bedrock (Story 4.5+); these are future work, not currently configured providers.
 - Adding any new provider requires extending the abstraction, tests, docs, and deployment assumptions together — never a one-file edit.
 - Do not assume a model change is local-only. Bedrock/AgentCore deployment, IAM scopes, `.env.example`, README, and tests are coupled to provider choices.
 - Bedrock guardrails are optional and must only be wired when `GUARDRAIL_ID` is set.
diff --git a/model_adapters.py b/model_adapters.py
index d535156..b8fb0bd 100644
--- a/model_adapters.py
+++ b/model_adapters.py
@@ -56,6 +56,22 @@ _REGISTRY: tuple[ModelCapabilities, ...] = (
         region_constraint="Not region-scoped by AWS_REGION; local-only Google API path.",
         notes="Local only via strands-agents[gemini] optional dependency.",
     ),
+    # Exploratory local-only evaluation boundary — Story 4.4.
+    # Not deployable through AgentCore. Uses strands-agents[litellm] optional dependency.
+    # One concrete example: Kimi via https://api.moonshot.ai/v1 with MOONSHOT_API_KEY bearer auth.
+    ModelCapabilities(
+        provider="litellm",
+        family="LiteLLM (direct-provider evaluation)",
+        runtimes=("local",),
+        enabled=True,
+        supports_converse=False,
+        supports_tools=True,
+        supports_guardrails=False,
+        supports_streaming=True,
+        bedrock_first=False,
+        region_constraint="Not region-scoped by AWS_REGION; local-only direct-provider evaluation path.",
+        notes="Exploratory local-only evaluation boundary (Story 4.4). Install via pip install 'strands-agents[litellm]'. Example: Kimi via https://api.moonshot.ai/v1. Not deployable through AgentCore.",
+    ),
     # Enabled Bedrock-first family alias — Meta Llama 3.1 70B Instruct via Amazon Bedrock.
     # Concrete Bedrock model IDs (US region deployment default):
     #   us.meta.llama3-1-70b-instruct-v1:0  — geo-inference (us-east-1 default)
@@ -199,6 +215,22 @@ class GeminiAdapter:
         return GeminiModel(model_id=self._model_id)
 
 
+class LiteLLMAdapter:
+    def __init__(self, env: Mapping[str, str]):
+        self._model_id = env["MODEL_ID"]
+        api_base = env.get("LITELLM_API_BASE")
+        self._client_args = {"api_base": api_base} if api_base else {}
+
+    def build(self):
+        # Lazy import — strands-agents[litellm] is optional; absent dependency must surface
+        from strands.models.litellm import LiteLLMModel
+
+        return LiteLLMModel(
+            client_args=self._client_args or None,
+            model_id=self._model_id,
+        )
+
+
 def create_local_model_adapter(provider: str, env: Mapping[str, str]):
     """Return the appropriate local model adapter for the given provider.
 
@@ -206,9 +238,12 @@ def create_local_model_adapter(provider: str, env: Mapping[str, str]):
     Distinguishes planned-but-not-enabled families from completely unknown keys.
     Registry-backed: any enabled Bedrock-first local provider uses BedrockAdapter.
     """
-    # Gemini requires its own adapter (not Bedrock-backed)
+    # Non-Bedrock local adapters — each requires its own class
     if provider == "gemini":
         return GeminiAdapter(env)
+    # LiteLLM is an exploratory local-only evaluation boundary (Story 4.4)
+    if provider == "litellm":
+        return LiteLLMAdapter(env)
     cap = _REGISTRY_BY_PROVIDER.get(provider)
     if cap is not None:
         if not cap.enabled:
diff --git a/tests/unit/test_app.py b/tests/unit/test_app.py
index e67a1a8..a3c5c0e 100644
--- a/tests/unit/test_app.py
+++ b/tests/unit/test_app.py
@@ -382,7 +382,7 @@ class TestHandleInvocationLlama:
     @patch("deploy.app.boto3.client")
     def test_non_bedrock_backed_provider_returns_error(self, mock_client):
         """Providers not in _DEPLOYED_BEDROCK_PROVIDERS must be rejected without a Bedrock call."""
-        for bad_provider in ("qwen", "deepseek", "openai"):
+        for bad_provider in ("qwen", "deepseek", "openai", "litellm"):
             mock_client.reset_mock()
             with patch.dict(os.environ, {"MODEL_PROVIDER": bad_provider}):
                 result = handle_invocation({"prompt": "born 1 Jan 2020"})
@@ -390,3 +390,22 @@ class TestHandleInvocationLlama:
                 "Error:"
             ), f"Expected error for provider={bad_provider}"
             mock_client.assert_not_called()
+
+
+class TestHandleInvocationLiteLLM:
+    """litellm is local-only — the deployed runtime must reject it (Story 4.4)."""
+
+    @patch("deploy.app.boto3.client")
+    def test_litellm_provider_rejected_by_deployed_runtime(self, mock_client):
+        with patch.dict(os.environ, {"MODEL_PROVIDER": "litellm"}):
+            result = handle_invocation({"prompt": "born 1 Jan 2020"})
+        assert result.startswith("Error:")
+        assert "litellm" in result
+        mock_client.assert_not_called()
+
+    @patch("deploy.app.boto3.client")
+    def test_litellm_rejection_occurs_before_bedrock_call(self, mock_client):
+        """litellm rejection must fire before any boto3 client is created."""
+        with patch.dict(os.environ, {"MODEL_PROVIDER": "litellm"}):
+            handle_invocation({"prompt": "born 1 Jan 2020"})
+        mock_client.assert_not_called()
diff --git a/tests/unit/test_model_adapters.py b/tests/unit/test_model_adapters.py
index 428b295..3e22735 100644
--- a/tests/unit/test_model_adapters.py
+++ b/tests/unit/test_model_adapters.py
@@ -411,3 +411,93 @@ class TestPlannedFamilyProviderRejection:
             create_local_model_adapter("gemma", self._env)
         error_msg = str(exc_info.value)
         assert "planned" in error_msg.lower() or "not yet enabled" in error_msg.lower()
+
+
+class TestLiteLLMAdapter:
+    """LiteLLM is an exploratory local-only evaluation boundary (Story 4.4)."""
+
+    def test_litellm_is_enabled_in_registry(self):
+        from model_adapters import get_model_capabilities
+
+        cap = get_model_capabilities("litellm")
+        assert cap is not None
+        assert cap.enabled is True
+
+    def test_litellm_is_local_only(self):
+        from model_adapters import get_model_capabilities
+
+        cap = get_model_capabilities("litellm")
+        assert cap.runtimes == ("local",)
+        assert "deployed" not in cap.runtimes
+
+    def test_litellm_is_not_bedrock_first(self):
+        from model_adapters import get_model_capabilities
+
+        cap = get_model_capabilities("litellm")
+        assert cap.bedrock_first is False
+
+    def test_litellm_does_not_support_converse(self):
+        from model_adapters import get_model_capabilities
+
+        cap = get_model_capabilities("litellm")
+        assert cap.supports_converse is False
+
+    def test_litellm_does_not_support_guardrails(self):
+        from model_adapters import get_model_capabilities
+
+        cap = get_model_capabilities("litellm")
+        assert cap.supports_guardrails is False
+
+    def test_litellm_in_supported_local_providers(self):
+        from model_adapters import supported_local_providers
+
+        assert "litellm" in supported_local_providers()
+
+    def test_litellm_not_in_planned_model_families(self):
+        from model_adapters import planned_model_families
+
+        assert "litellm" not in planned_model_families()
+
+    def test_litellm_notes_mark_as_exploratory(self):
+        from model_adapters import get_model_capabilities
+
+        cap = get_model_capabilities("litellm")
+        notes_lower = cap.notes.lower()
+        assert "exploratory" in notes_lower or "evaluation" in notes_lower
+
+    def test_litellm_local_adapter_returns_litellm_adapter(self):
+        from model_adapters import create_local_model_adapter, LiteLLMAdapter
+
+        adapter = create_local_model_adapter(
+            "litellm", {"MODEL_ID": "moonshot/moonshot-v1-8k"}
+        )
+        assert isinstance(adapter, LiteLLMAdapter)
+
+    def test_litellm_adapter_build_constructs_model_with_model_id(self):
+        from model_adapters import LiteLLMAdapter
+
+        mock_litellm_cls = MagicMock()
+        with patch.dict(
+            "sys.modules",
+            {"strands.models.litellm": MagicMock(LiteLLMModel=mock_litellm_cls)},
+        ):
+            LiteLLMAdapter({"MODEL_ID": "moonshot/moonshot-v1-8k"}).build()
+            mock_litellm_cls.assert_called_once()
+            assert (
+                mock_litellm_cls.call_args.kwargs.get("model_id")
+                == "moonshot/moonshot-v1-8k"
+            )
+
+    def test_litellm_adapter_import_failure_surfaces_clearly(self):
+        """If strands-agents[litellm] is missing, ImportError must propagate — no Bedrock fallback."""
+        from model_adapters import LiteLLMAdapter
+
+        with patch.dict("sys.modules", {"strands.models.litellm": None}):
+            with pytest.raises((ImportError, ModuleNotFoundError, TypeError)):
+                LiteLLMAdapter({"MODEL_ID": "moonshot/moonshot-v1-8k"}).build()
+
+    def test_litellm_adapter_missing_model_id_raises_key_error(self):
+        from model_adapters import LiteLLMAdapter
+
+        with pytest.raises(KeyError):
+            LiteLLMAdapter({})
diff --git a/tests/unit/test_static.py b/tests/unit/test_static.py
index e226337..cdcbc05 100644
--- a/tests/unit/test_static.py
+++ b/tests/unit/test_static.py
@@ -325,10 +325,11 @@ class TestReadmeProviderRoadmap:
         assert "earlier work" in nist_section
 
     def test_model_expansion_roadmap_preserves_runtime_boundary(self):
-        """AC #2 (Story 4.1/4.3): README must distinguish supported and planned provider paths."""
+        """AC #2 (Story 4.1/4.3/4.4): README must distinguish supported and planned provider paths."""
         content = self._content()
         assert "### Model expansion roadmap" in content
-        assert "`bedrock` (local + deployed), `gemini` (local only)" in content
+        assert "`bedrock` (local + deployed)" in content
+        assert "`gemini` (local only" in content
         assert "`llama` (local + deployed, Bedrock-backed)" in content
         assert "Planned" in content and "Gemma" in content and "DeepSeek" in content
         assert "Local adapter selection raises `ValueError`" in content
@@ -344,13 +345,19 @@ class TestProjectContextProviderRules:
         return (PROJECT_ROOT / "_bmad-output" / "project-context.md").read_text()
 
     def test_provider_rules_distinguish_local_and_deployed_support(self):
-        """AC #2 (Story 4.1/4.3): project context must preserve local/cloud provider boundaries."""
+        """AC #2 (Story 4.1/4.3/4.4): project context must preserve local/cloud provider boundaries."""
         content = self._content()
-        assert "Local adapter code supports `bedrock`, `gemini`, and `llama`" in content
+        assert "Local adapter code supports `bedrock`, `gemini`, `llama`, and `litellm`" in content
         assert "all other local provider values raise `ValueError`" in content
         assert "Deployed AgentCore code supports `bedrock` and `llama`" in content
         assert "unsupported-provider error before Bedrock invocation" in content
 
+    def test_litellm_documented_as_exploratory_local_only(self):
+        """AC #1 (Story 4.4): project context must mark litellm as exploratory and local-only."""
+        content = self._content()
+        assert "litellm" in content
+        assert "exploratory" in content.lower() or "local-only" in content.lower()
+
     def test_provider_rules_mark_expansion_targets_as_future_work(self):
         """AC #1 (Story 4.1/4.3): project context must not imply still-planned families are enabled."""
         content = self._content()
@@ -368,3 +375,60 @@ class TestProjectContextProviderRules:
         assert "planned_model_families()" in content
         assert "get_model_capabilities(provider)" in content
         assert "must not import or use the local registry" in content
+
+
+# ── .env.example LiteLLM exploratory section (Story 4.4) ─────────────────────
+
+
+class TestEnvExampleLiteLLM:
+    def _content(self) -> str:
+        return (PROJECT_ROOT / ".env.example").read_text()
+
+    def test_has_litellm_exploratory_section_header(self):
+        """AC #1 (Story 4.4): .env.example must have a distinct LiteLLM exploratory section."""
+        assert "# --- Optional: LiteLLM" in self._content()
+
+    def test_litellm_section_includes_model_provider_example(self):
+        """AC #1 (Story 4.4): .env.example must show MODEL_PROVIDER=litellm as an example."""
+        assert "MODEL_PROVIDER=litellm" in self._content()
+
+    def test_litellm_section_includes_moonshot_api_key_example(self):
+        """AC #1 (Story 4.4): .env.example must document a direct-provider credential example."""
+        assert "MOONSHOT_API_KEY" in self._content()
+
+    def test_litellm_section_marked_local_only(self):
+        """AC #2 (Story 4.4): LiteLLM section must be explicitly marked as local-only."""
+        content = self._content()
+        assert "local-only" in content or "local only" in content
+
+
+# ── README LiteLLM exploratory path (Story 4.4) ───────────────────────────────
+
+
+class TestReadmeLiteLLMBoundary:
+    def _content(self) -> str:
+        return (PROJECT_ROOT / "README.md").read_text()
+
+    def _roadmap_section(self) -> str:
+        return self._content().split("### Model expansion roadmap", 1)[1].split(
+            "##", 1
+        )[0]
+
+    def test_readme_mentions_litellm_in_roadmap(self):
+        """AC #1/2 (Story 4.4): README roadmap must document the litellm evaluation path."""
+        section = self._roadmap_section()
+        assert "litellm" in section.lower() or "LiteLLM" in section
+
+    def test_readme_marks_litellm_as_exploratory_not_production(self):
+        """AC #2 (Story 4.4): litellm must not be presented as a production-aligned path."""
+        section = self._roadmap_section()
+        assert (
+            "exploratory" in section.lower()
+            or "local only" in section.lower()
+            or "local-only" in section.lower()
+        )
+
+    def test_readme_agentcore_deployment_remains_bedrock_only(self):
+        """AC #2 (Story 4.4): README must state AgentCore deployment is Bedrock-only."""
+        content = self._content()
+        assert "Bedrock-backed providers" in content or "Bedrock Converse" in content
```
