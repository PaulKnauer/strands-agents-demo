# Story 4.2: Capability Registry and Adapter Extension

Status: done
Last Review: 2026-05-14

## Story

As a developer,
I want the adapter layer extended with capability-aware model registration,
so that additional model families can be introduced in a controlled and explicit way.

## Acceptance Criteria

1. Given the adapter architecture currently supports the initial local model paths, when I extend the registry for new candidate model families, then each supported path is represented through explicit capability-aware registration and unsupported combinations fail clearly.
2. Given new model families are being introduced, when I review the local adapter implementation, then support is added without collapsing the separation between local and deployed runtime concerns and the code remains consistent with the documented abstraction boundary.
3. Given provider expansion affects more than one layer, when the implementation is updated, then code, tests, configuration docs, and deployment assumptions are advanced together and no hidden support gap is introduced.

## Tasks / Subtasks

- [x] Introduce explicit local model capability metadata in `model_adapters.py`. (AC: 1, 2)
  - [x] Add a small typed structure for model/provider capability registration, such as a frozen dataclass or equivalent, without adding runtime dependencies.
  - [x] Register the existing supported local paths: `bedrock` and `gemini`.
  - [x] Represent runtime scope explicitly, at minimum distinguishing local support from deployed AgentCore support.
  - [x] Represent capability flags explicitly enough for later rollout stories to reason about Bedrock Converse, tool use, guardrails, streaming, and region/model-family constraints.
  - [x] Keep `create_local_model_adapter(provider, env)` as the public construction entrypoint used by `agent.py`.
- [x] Add candidate model-family entries without falsely enabling runtime support. (AC: 1, 2, 3)
  - [x] Include Gemma, Moonshot/Kimi, Llama, Qwen, and DeepSeek as planned Bedrock-first candidate families in the registry metadata.
  - [x] Mark candidate entries as not yet selectable by `MODEL_PROVIDER` unless the story intentionally enables a real supported provider path.
  - [x] Preserve clear `ValueError` behavior for unknown or not-yet-enabled local provider values.
  - [x] Error messages should distinguish supported provider keys from planned-but-not-enabled family labels.
- [x] Preserve local/deployed runtime separation. (AC: 2)
  - [x] Do not import `model_adapters.py`, `strands`, or `agent.py` into `deploy/app.py`.
  - [x] Do not make deployed AgentCore accept `gemini`, `gemma`, `llama`, `qwen`, `deepseek`, `moonshot`, `kimi`, or `litellm` in this story.
  - [x] Keep deployment preflight in `deploy/deploy.py` Bedrock-only unless an explicit deployed Bedrock model-family rollout is implemented in Story 4.3.
  - [x] Do not add LiteLLM, direct-provider SDKs, API keys, or new secrets in Story 4.2.
- [x] Update tests for registry and failure contracts. (AC: 1, 2, 3)
  - [x] Extend `tests/unit/test_model_adapters.py` to assert registry entries for `bedrock`, `gemini`, and planned candidate families.
  - [x] Assert `bedrock` and `gemini` still build the same adapter classes.
  - [x] Assert planned candidate labels fail clearly when used as `MODEL_PROVIDER` today.
  - [x] Assert unknown providers still fail clearly and do not silently fall back.
  - [x] Preserve guardrail tests for `BedrockAdapter` and no-guardrail behavior for `GeminiAdapter`.
  - [x] Keep `tests/unit/test_static.py` coverage aligned if README, `.env.example`, or project-context wording changes.
  - [x] Keep `tests/unit/test_app.py` passing to preserve deployed runtime provider rejection.
- [x] Update documentation/configuration surfaces only as far as the new registry changes require. (AC: 3)
  - [x] If registry names are exported or documented, update README and `.env.example` so "supported", "planned", and "not yet enabled" remain distinct.
  - [x] Update `_bmad-output/project-context.md` if the registry becomes a stable project convention future agents must follow.
  - [x] Do not advertise a new runnable model family until Story 4.3 validates a concrete Bedrock model ID, region, and capability set.
- [x] Run focused verification. (AC: 1, 2, 3)
  - [x] Run `venv/bin/python -m pytest tests/unit/test_model_adapters.py tests/unit/test_static.py tests/unit/test_app.py`.
  - [x] Run `make lint`.
  - [x] Run broader tests only if implementation touches shared runtime behavior beyond the adapter registry and docs.

### Review Findings

- [x] [Review][Patch] `kimi` planned-family alias falls through as unknown [model_adapters.py:64]
- [x] [Review][Patch] Bedrock runtime scope metadata omits deployed support [model_adapters.py:33]
- [x] [Review][Patch] Capability metadata lacks explicit Converse and region constraint fields [model_adapters.py:13]
- [x] [Review][Patch] `supported_local_providers()` filters only by enabled flag, not runtime scope [model_adapters.py:120]
- [x] [Review][Patch] Capability flags are not directly asserted for runnable providers [tests/unit/test_model_adapters.py:183]
- [x] [Review][Patch] Project-context registry convention is not statically guarded [tests/unit/test_static.py:341]
- [x] [Review][Patch] Story completion notes overstate added test count [_bmad-output/implementation-artifacts/4-2-capability-registry-and-adapter-extension.md:289]

#### Review Pass 2 — 2026-05-14

- [x] [Review][Patch] `moonshot`/`kimi` canonical alias undocumented in tests — `notes` says `moonshot` is canonical but no assertion enforces ordering or canonical relationship [model_adapters.py:72-97, tests/unit/test_model_adapters.py]
- [x] [Review][Patch] `_REGISTRY_BY_PROVIDER` is a mutable `dict` — should be `types.MappingProxyType(...)` to match frozen-dataclass immutability intent [model_adapters.py:140-142]
- [x] [Review][Patch] `test_registry_entries_are_immutable` catches bare `Exception` — should assert `dataclasses.FrozenInstanceError` specifically [tests/unit/test_model_adapters.py]
- [x] [Review][Patch] `project-context.md` `supported_local_providers()` description omits the `"local" in cap.runtimes` filter condition [_bmad-output/project-context.md]
- [x] [Review][Patch] `project-context.md` `planned_model_families()` says "registered but not yet enabled" — spec and code docstring say "planned but not yet enabled" [_bmad-output/project-context.md]
- [x] [Review][Patch] No duplicate-key assertion on `_REGISTRY_BY_PROVIDER` dict comprehension — silently drops any future collision [model_adapters.py:143-145]
- [x] [Review][Patch] `make lint` target omits `model_adapters.py` and test files — story claims "make lint clean" without linting the primary changed file [Makefile]
- [x] [Review][Defer] `create_local_model_adapter()` if/elif dispatch hardcoded; enabling a registry entry alone does not enable dispatch [model_adapters.py:195-215] — deferred, Story 4.3 scope
- [x] [Review][Defer] `runtimes` field accepts any string; no validation against allowed values (`"local"`, `"deployed"`, `"planned"`) [model_adapters.py:14] — deferred, Story 4.3 scope
- [x] [Review][Defer] Six planned-family rejection tests are copy-pasted instead of `@pytest.mark.parametrize` [tests/unit/test_model_adapters.py] — deferred, pre-existing maintenance cleanup
- [x] [Review][Defer] `TestPlannedFamilyProviderRejection._env` is a mutable shared class-level dict [tests/unit/test_model_adapters.py] — deferred, pre-existing test hygiene
- [x] [Review][Defer] Empty string provider falls through to misleading unknown-provider error [model_adapters.py:195] — deferred, low-priority input validation
- [x] [Review][Defer] `supported_local_providers()` called inside ValueError f-string — registry failure could mask original error [model_adapters.py:206] — deferred, defensive hygiene
- [x] [Review][Defer] `planned_model_families()` filters on `enabled=False` only; doesn't enforce `runtimes=("planned",)` [model_adapters.py:143] — deferred, no real case yet
- [x] [Review][Defer] Provider lookup is case-sensitive; `"Bedrock"` falls to unknown-provider error [model_adapters.py:197] — deferred, low-priority defensive change
- [x] [Review][Defer] No `__all__` defined; `_REGISTRY` and `_REGISTRY_BY_PROVIDER` importable as public symbols [model_adapters.py] — deferred, project-wide convention work

#### Review Pass 3 — 2026-05-14

- [x] [Review][Patch] Module-level `assert` for duplicate keys is stripped by `python -O` — must be an explicit `if` check raising `RuntimeError` [model_adapters.py:143-144]
- [x] [Review][Patch] `make format` target still missing `model_adapters.py` — only `lint` was updated, creating an asymmetry [Makefile]
- [x] [Review][Patch] Planned-family rejection tests match `"planned"` not `"planned candidate"` — spec requires the full phrase [tests/unit/test_model_adapters.py]
- [x] [Review][Patch] `test_moonshot_is_canonical_key_for_kimi_alias` does not assert `moonshot_cap.family == kimi_cap.family` [tests/unit/test_model_adapters.py]
- [x] [Review][Defer] No test verifies the duplicate-key guard fires on a malformed registry [model_adapters.py:143-145] — deferred, low-priority guard coverage

## Dev Notes

### Scope Boundary

Story 4.2 creates the capability-aware registry and adapter extension surface. It should not be the rollout of a new runnable model family unless the implementation can fully satisfy docs, tests, deployment assumptions, and model capability validation in this same story.

Treat this story as the bridge between Story 4.1 alignment and Story 4.3 rollout:

- Story 4.1 clarified current support: local `bedrock`, local `gemini`, deployed `bedrock`.
- Story 4.2 should make the adapter layer capability-aware and ready for controlled expansion.
- Story 4.3 should enable at least one concrete Bedrock-first model family.
- Story 4.4 owns optional direct-provider or LiteLLM evaluation.

Do not add new provider SDK dependencies, LiteLLM integration, direct-provider API clients, or new secret variables here. Those are scope escalation unless explicitly justified by a failing acceptance criterion.

### Current State

Current implementation surface:

- The current sprint status defines this story as `4-2-capability-registry-and-adapter-extension` under "Epic 4: Multi-Provider Model Expansion".
- There is an older historical file named `_bmad-output/implementation-artifacts/4-2-audit-hooks.md` from the previous compliance-oriented Epic 4 numbering. Treat it as historical context only; do not infer current requirements from it.
- `agent.py` calls `load_dotenv()` before env access, then calls `create_local_model_adapter(os.environ["MODEL_PROVIDER"], os.environ)` and passes `adapter.build()` into `Agent`.
- `model_adapters.py` is intentionally local-only and currently contains `BedrockAdapter`, `GeminiAdapter`, and `create_local_model_adapter()`.
- `BedrockAdapter` uses `MODEL_ID`, `AWS_REGION`, and optional `GUARDRAIL_ID` / `GUARDRAIL_VERSION`.
- `GeminiAdapter` uses `MODEL_ID` and lazily imports `strands.models.gemini.GeminiModel`.
- `deploy/app.py` uses direct Bedrock Converse via `boto3` and rejects non-`bedrock` `MODEL_PROVIDER` values before creating a Bedrock client.
- `deploy/deploy.py` rejects non-`bedrock` values at deployment preflight.

Current tests:

- `tests/unit/test_model_adapters.py` covers current adapter selection, missing env keys, Bedrock guardrail kwargs, Gemini lazy import, and unsupported provider failure.
- `tests/unit/test_static.py` guards `.env.example`, README provider-roadmap wording, project-context local/deployed provider boundaries, `agent.py` line count, and deploy import isolation.
- `tests/unit/test_app.py` verifies deployed runtime rejects missing or unsupported providers without creating a Bedrock client.

### Architecture Requirements

- Preserve the local/cloud runtime split. `model_adapters.py` belongs to local Strands execution; `deploy/app.py` belongs to AgentCore deployed Bedrock Converse execution.
- Keep `agent.py` lean. Static tests enforce it stays under 150 lines, and this story should not move registry logic into `agent.py`.
- Keep the public local factory call stable unless there is a compelling reason to change it: `create_local_model_adapter(provider, env)`.
- Avoid hidden defaults. Required env vars should continue to fail loudly through `os.environ[...]` or explicit validation; unsupported providers must not fall back to Bedrock.
- Model capabilities should be explicit data, not scattered prose or hard-coded branching. Future stories need a single place to ask what a provider/family supports.
- The registry should make unsupported combinations obvious before an LLM call is made.

### Recommended Registry Shape

Use a minimal structure that supports current behavior and future family rollout. A practical shape is:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ModelCapabilities:
    provider: str
    family: str
    runtime: str  # "local", "deployed", or "planned"
    enabled: bool
    supports_tools: bool
    supports_guardrails: bool
    supports_streaming: bool
    bedrock_first: bool
    notes: str = ""
```

The exact names can differ, but the implementation should preserve these ideas:

- `bedrock` and `gemini` are enabled local providers.
- `bedrock` is the only deployed provider today.
- Gemma, Moonshot/Kimi, Llama, Qwen, and DeepSeek are planned Bedrock-first candidate families, not provider strings that work locally today.
- Guardrails are Bedrock-specific in this repo.
- Capability flags are conservative. Use `False` or "unknown/planned" when capability is not validated in code and tests.

Prefer small helper functions such as `get_model_capabilities()`, `supported_local_providers()`, and `planned_model_families()` if they reduce test brittleness. Do not add abstraction layers beyond what tests and docs need.

### Files To Review And Likely Update

#### `model_adapters.py`

Current state:

- Local-only module.
- Imports `BedrockModel` at module load.
- `BedrockAdapter` stores model ID, region, and optional guardrail kwargs.
- `GeminiAdapter` lazily imports `GeminiModel`.
- `create_local_model_adapter()` uses direct `if/elif` branching for `bedrock` and `gemini`, and raises `ValueError` for everything else.

Expected change:

- Add explicit capability registry metadata.
- Keep adapter construction behavior stable for `bedrock` and `gemini`.
- Make unsupported/planned provider failures clearer without silently enabling candidate families.

Must preserve:

- No import from deploy runtime.
- No direct-provider SDK imports.
- Gemini lazy import.
- Bedrock guardrail kwargs behavior.

#### `tests/unit/test_model_adapters.py`

Expected change:

- Add registry tests.
- Keep current adapter construction and guardrail tests.
- Add tests that planned family labels do not become valid `MODEL_PROVIDER` values by accident.

Use tests to lock the terminology:

- supported/enabled local provider: currently `bedrock`, `gemini`
- deployed provider: currently `bedrock`
- planned Bedrock-first family: `gemma`, `moonshot`/`kimi`, `llama`, `qwen`, `deepseek`

#### `tests/unit/test_static.py`

Expected change only if docs or project-context are changed:

- Preserve existing Story 4.1 tests around planned providers and runtime boundaries.
- Add coverage only for new stable wording or exported registry references.

#### `README.md` and `.env.example`

Expected change only if registry terms are surfaced:

- Keep `MODEL_PROVIDER=bedrock` and `MODEL_ID=us.amazon.nova-micro-v1:0` as the default path.
- Keep `gemini` documented as local-only.
- Keep planned family language clearly marked as not yet enabled.
- Do not list a concrete Bedrock model ID for a new family until Story 4.3 validates it.

#### `_bmad-output/project-context.md`

Update if the registry becomes a stable convention. Keep it short and rule-like:

- local adapter registry owns provider/family capability metadata
- planned family metadata must not imply runnable provider support
- deployed runtime remains Bedrock-only until a deployed rollout story changes it

### Files Not Expected To Change

- `agent.py` should not change unless the public factory contract changes. Prefer not to change it.
- `deploy/app.py` should not import or use the local registry in this story.
- `deploy/deploy.py` should remain Bedrock-only for deployment preflight.
- `requirements.txt` should not change unless a new dependency is explicitly justified. A pure metadata registry needs no new dependency.

Changing these files requires a completion note explaining why the scope expanded.

### Previous Story Intelligence

Story 4.1 established the critical language and test guardrails for Epic 4:

- Current support is local `bedrock`, local `gemini`, deployed `bedrock`.
- Planned families must remain explicitly future work until enabled by code, tests, and docs.
- Local `ValueError` behavior and deployed unsupported-provider behavior are intentionally different.
- `tests/unit/test_static.py` now guards README and project-context provider boundaries.
- `tests/unit/test_app.py` asserts unsupported deployed providers return before a Bedrock client is created.

Review feedback from Story 4.1 is directly relevant:

- Do not make broad runtime claims without tests.
- If docs mention a behavior, add or update a test that guards it.
- Avoid wording that collapses local adapter behavior and deployed runtime behavior.
- Audit notes must distinguish changed files from reviewed-but-unchanged planning artifacts.

### Git Intelligence

Recent commits show this project treats docs/config/provider changes as test-backed contract work:

- `a310206` completed Story 4.1 with README, `.env.example`, project-context, adapter/deployed runtime tests, and sprint artifacts.
- `3c4cb75` installed infra dependencies in CI test jobs, reinforcing that changes touching deployment assumptions need CI awareness.
- `c940217` finalized Epic 3 documentation, reinforcing README and setup accuracy as maintained surfaces.

### Latest Technical Context

Use current official docs when selecting any concrete model capability in later stories:

- Amazon Bedrock currently lists the target families relevant to Epic 4, including Gemma, Moonshot/Kimi, Llama, Qwen, and DeepSeek, with model IDs and regional support in the supported models table. Source: https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html
- Bedrock model feature support varies by model. Before enabling a family, check Converse support, streaming, tool use, guardrails, input/output modality, and region. Source: https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-supported-models-features.html
- Bedrock guardrails can be included with Converse calls, but supported model/feature combinations still need validation. Source: https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-use-converse-api.html
- Strands supports multiple Python model providers, including Bedrock, Google/Gemini, and LiteLLM, but most non-Bedrock providers are optional dependencies. Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/
- Strands LiteLLM exists as a Python provider, but this story should not adopt it implicitly; optional direct-provider/LiteLLM evaluation belongs to Story 4.4. Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/litellm/

### Testing Requirements

Minimum focused verification:

```bash
venv/bin/python -m pytest tests/unit/test_model_adapters.py tests/unit/test_static.py tests/unit/test_app.py
make lint
```

Add or adjust tests before changing behavior. For this story, test the registry directly rather than relying only on README text. Suggested test cases:

- Registry exposes `bedrock` and `gemini` as enabled local providers.
- Registry exposes planned candidate families without enabling them as local providers.
- `create_local_model_adapter("bedrock", env)` still returns `BedrockAdapter`.
- `create_local_model_adapter("gemini", env)` still returns `GeminiAdapter`.
- `create_local_model_adapter("gemma", env)`, `("llama", env)`, `("qwen", env)`, `("deepseek", env)`, and `("moonshot", env)` raise `ValueError` with planned/not-enabled language.
- Unknown providers raise `ValueError` with supported provider guidance.
- Deployed runtime tests still reject non-`bedrock` before Bedrock client creation.

### Implementation Guidance

- Prefer a simple registry dictionary over a hierarchy of classes.
- Keep registry data close to `create_local_model_adapter()` so provider behavior and metadata cannot drift.
- Avoid model-ID validation in Story 4.2 unless it is purely metadata. Concrete Bedrock model ID validation belongs to Story 4.3.
- If a planned family has multiple labels (`moonshot`, `kimi`), choose one canonical key and document aliases clearly in tests or metadata.
- Keep comments short and focused on non-obvious runtime boundaries.
- Use ASCII in Python source unless the file already requires Unicode.

### Project Structure Notes

This story should align with the existing source tree:

- top-level `model_adapters.py` for local adapter registry and construction
- top-level `agent.py` only as a consumer of `create_local_model_adapter()`
- `deploy/` remains isolated for AgentCore runtime and deployment scripts
- `tests/unit/` remains the place for registry/static/runtime contract tests
- `_bmad-output/project-context.md` remains the concise rule file for future agents

No frontend or UX assets are involved.

### References

- Source: `_bmad-output/planning-artifacts/epics.md` - Epic 4 and Story 4.2 acceptance criteria
- Source: `_bmad-output/planning-artifacts/prd.md` - model selection, integration, and staged expansion requirements
- Source: `_bmad-output/planning-artifacts/architecture.md` - model provider abstraction and runtime boundary decisions
- Source: `_bmad-output/project-context.md` - current provider/model implementation rules
- Source: `_bmad-output/implementation-artifacts/4-1-expansion-scope-alignment.md` - previous story intelligence and review findings
- Source: `model_adapters.py` - current local adapter implementation
- Source: `agent.py` - current local factory consumer
- Source: `deploy/app.py` - deployed runtime provider rejection and Bedrock Converse path
- Source: `deploy/deploy.py` - deployment preflight provider rejection
- Source: `tests/unit/test_model_adapters.py` - adapter behavior contract tests
- Source: `tests/unit/test_static.py` - static provider-boundary contract tests
- Source: `tests/unit/test_app.py` - deployed runtime provider rejection tests

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation proceeded cleanly without halts or retries.

### Completion Notes List

- Story context created on 2026-05-14.
- Ultimate context engine analysis completed - comprehensive developer guide created.
- Implemented `ModelCapabilities` frozen dataclass registry in `model_adapters.py` with no new runtime dependencies.
- Registered `bedrock` (enabled, local+deployed) and `gemini` (enabled, local-only) as active local providers with explicit runtime, Converse, tool, guardrail, streaming, Bedrock-first, and region-constraint metadata.
- Registered planned Bedrock-first candidate provider keys (`gemma`, `moonshot`, `kimi`, `llama`, `qwen`, `deepseek`) with `enabled=False`; these cannot be used as `MODEL_PROVIDER` values and raise `ValueError` with "planned candidate" language.
- Added helper functions `get_model_capabilities()`, `supported_local_providers()`, `planned_model_families()` as stable registry API for future rollout stories.
- `create_local_model_adapter()` public contract unchanged; `agent.py` required no edits.
- `deploy/app.py` and `deploy/deploy.py` required no changes; runtime isolation confirmed by static import tests.
- Added registry and failure-contract tests to `tests/unit/test_model_adapters.py` covering registry structure, runtime/capability metadata, planned family rejection, and unknown provider rejection.
- Added static coverage for the Story 4.2 project-context registry convention.
- Focused verification passes: `venv/bin/python -m pytest tests/unit/test_model_adapters.py tests/unit/test_static.py tests/unit/test_app.py` reports 102 passed; `make lint` clean; `black` formatting applied.
- `_bmad-output/project-context.md` updated with Local Adapter Registry Convention section.
- README and `.env.example` required no changes (existing wording already satisfies AC #3 test guards).

### File List

- `model_adapters.py` — added `ModelCapabilities` dataclass with runtime, Converse, tool, guardrail, streaming, Bedrock-first, and region-constraint metadata; added `_REGISTRY`, `_REGISTRY_BY_PROVIDER`, `get_model_capabilities()`, `supported_local_providers()`, `planned_model_families()`; updated `create_local_model_adapter()` error messages
- `tests/unit/test_model_adapters.py` — added `TestCapabilityRegistry` and `TestPlannedFamilyProviderRejection` test classes
- `tests/unit/test_static.py` — added project-context registry convention coverage
- `_bmad-output/project-context.md` — added Local Adapter Registry Convention section
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — updated story status to in-progress → review

## Change Log

- 2026-05-14: Implemented capability-aware model registry in `model_adapters.py`; added 32 registry/failure-contract tests; updated project-context with registry convention. No runtime behavior changes for existing `bedrock` and `gemini` providers.
