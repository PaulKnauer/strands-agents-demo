# Story 1.3: Adapter-Based Local Model Selection

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want local model selection routed through the adapter abstraction,
so that I can switch between supported local model paths without editing application logic.

## Acceptance Criteria

1. **Given** the local runtime supports the initial `bedrock` and `gemini` adapter paths
   **When** I configure `MODEL_PROVIDER` and `MODEL_ID` for one of those supported paths
   **Then** the local agent builds the model through the adapter boundary
   **And** no application-logic code changes are required

2. **Given** an unsupported provider or unsupported local/runtime combination is configured
   **When** the local agent starts
   **Then** it fails clearly with an explicit configuration error
   **And** it does not silently fall back to another provider

3. **Given** I inspect the local model selection implementation
   **When** I review the code
   **Then** adapter selection logic is separated from the conversational REPL logic
   **And** the implementation preserves the architecture rule that local and deployed runtimes remain distinct

## Tasks / Subtasks

- [x] Task 1: Extract local model construction into a dedicated adapter module (AC: #1, #2, #3)
  - [x] Create `model_adapters.py` at the repository root; this module owns local provider selection and model construction
  - [x] Move the existing `bedrock` and `gemini` selection branches out of `agent.py` without changing their runtime behavior
  - [x] Expose a small local API, preferably `create_local_model_adapter(provider: str, env: Mapping[str, str])` plus an adapter `.build()` method, matching the architecture example
  - [x] Keep the adapter boundary local-only; do not import or reuse `deploy/app.py`

- [x] Task 2: Preserve Bedrock behavior exactly while moving it behind the adapter boundary (AC: #1, #2)
  - [x] Continue to read `MODEL_ID` and `AWS_REGION` as required values via `env[...]`; no silent defaults for the local path
  - [x] Continue to construct `BedrockModel(model_id=..., region_name=...)`
  - [x] Preserve optional guardrail wiring only when `GUARDRAIL_ID` is set
  - [x] Preserve default `GUARDRAIL_VERSION="DRAFT"` when `GUARDRAIL_ID` is set and `GUARDRAIL_VERSION` is absent

- [x] Task 3: Preserve Gemini behavior exactly while moving it behind the adapter boundary (AC: #1, #2)
  - [x] Continue lazy-importing `GeminiModel` only inside the Gemini adapter path because the optional Google dependency may be absent
  - [x] Continue constructing `GeminiModel(model_id=env["MODEL_ID"])`
  - [x] Do not pass Bedrock guardrail kwargs to Gemini
  - [x] If the optional Google dependency is missing, allow the import failure to surface clearly; do not fall back to Bedrock

- [x] Task 4: Simplify `agent.py` to consume the adapter boundary (AC: #1, #3)
  - [x] Keep `load_dotenv()` before any `os.environ` access
  - [x] Keep `agent.py` responsible for `SYSTEM_PROMPT`, `get_today_date`, `create_agent()`, `run_repl()`, `Agent(...)`, and `AuditLoggingHook()`
  - [x] Replace inline provider branching in `create_agent()` with adapter construction and `.build()`
  - [x] Keep `agent.py` under 150 lines after the extraction

- [x] Task 5: Update tests around the new ownership boundary (AC: #1, #2, #3)
  - [x] Add focused `tests/unit/test_model_adapters.py` coverage for Bedrock, Bedrock guardrails, Gemini, unsupported provider, and no-fallback behavior
  - [x] Update `tests/unit/test_agent_tool.py` so `create_agent()` verifies it calls the adapter boundary and still passes the returned model into `Agent(...)`
  - [x] Update patch paths from `agent.BedrockModel` to the new adapter module where relevant
  - [x] Preserve existing REPL, tool, prompt parity, and safety tests

- [x] Task 6: Run deterministic validation and formatting (AC: #1, #2, #3)
  - [x] `venv/bin/black agent.py model_adapters.py tests/unit/test_agent_tool.py tests/unit/test_model_adapters.py`
  - [x] `venv/bin/python -m pytest tests/unit/test_agent_tool.py`
  - [x] `venv/bin/python -m pytest tests/unit/test_model_adapters.py`
  - [x] `venv/bin/python -m pytest tests/evals/test_prompt_parity.py`
  - [x] `venv/bin/python -m pytest tests/unit/test_safety_boundaries.py`
  - [x] `venv/bin/python -m pytest tests/unit/test_static.py`

## Dev Notes

### Story Intent

This is the planned adapter extraction story. The current repo already has working local provider selection, but it lives inside `agent.py`. The implementation should move that model construction logic into a root-level `model_adapters.py` module while preserving behavior, tests, and the local/cloud runtime separation.

Do not broaden this story into Epic 4's staged multi-provider expansion. The only supported local provider paths for this story are still `bedrock` and `gemini`.

### Current State Of Files Being Modified

- `agent.py`: currently imports `BedrockModel` directly and performs `MODEL_PROVIDER` branching inside `create_agent()` lines 35-67. It constructs Gemini lazily, constructs Bedrock with optional guardrail kwargs, raises `ValueError` for unknown providers, then passes the model into `Agent(...)` with `get_today_date`, `SYSTEM_PROMPT`, and `AuditLoggingHook()` lines 68-73. Preserve the prompt, tool, hook, and REPL behavior. [Source: agent.py]
- `tests/unit/test_agent_tool.py`: currently owns provider-selection tests by patching `agent.BedrockModel`, injecting a fake `strands.models.gemini`, and asserting guardrail kwargs and unsupported-provider behavior. After extraction, those assertions belong mostly in `tests/unit/test_model_adapters.py`; `test_agent_tool.py` should only verify `create_agent()` delegates to the adapter and wires the returned model to `Agent(...)`. [Source: tests/unit/test_agent_tool.py]
- `tests/unit/test_static.py`: currently enforces `agent.py` under 150 lines and still has historical docstring references to Story 1.3 as VS Code debug. Update only if tests need clearer current-story comments; do not weaken existing scaffold checks. [Source: tests/unit/test_static.py]
- `deploy/app.py`: direct Bedrock Converse runtime for AgentCore. It must remain separate and should not import `model_adapters.py`; the adapter extraction is for local Strands runtime only. [Source: deploy/app.py]

### Required Adapter Shape

Use the architecture's intended ownership boundary:

```python
adapter = create_local_model_adapter(os.environ["MODEL_PROVIDER"], os.environ)
model = adapter.build()
agent = Agent(model=model, tools=[get_today_date], ...)
```

Implementation can use small classes, dataclasses, or simple objects if the public boundary stays explicit. Keep it boring and testable. Do not introduce a registry framework unless it removes real complexity for the two existing providers.

### Architecture Compliance Guardrails

- `load_dotenv()` must still run before any `os.environ` access in the local entrypoint.
- Required local configuration must stay fail-fast through `os.environ[...]` or equivalent `env[...]` access.
- Unsupported providers must raise an explicit configuration error. Do not silently fall back to Bedrock, Gemini, or any default.
- Bedrock guardrails remain optional and only apply when `GUARDRAIL_ID` is set.
- `agent.py` and `deploy/app.py` remain different runtime paths: local uses Strands; AgentCore uses direct Bedrock Converse via `boto3`.
- Do not import `strands-agents` into `deploy/app.py`.
- Preserve system prompt parity; this story should not need prompt edits. If the prompt changes anyway, update `deploy/app.py` and `compliance/promptfoo-redteam.yaml` in the same change set.
- Keep tool surface unchanged: exactly one tool, `get_today_date`.

### Regression Risks To Avoid

- Moving provider selection but losing guardrail kwargs or the default `GUARDRAIL_VERSION="DRAFT"`.
- Importing Gemini at module import time and breaking installs without the optional Google dependency.
- Masking unsupported providers with a default branch or a catch-all fallback.
- Accidentally requiring `AWS_REGION` for Gemini beyond the existing test setup; Gemini should only need `MODEL_ID` and the optional provider dependency/API key path handled by Strands.
- Collapsing deployed runtime behavior into local adapter code or making AgentCore depend on Strands.
- Letting tests keep patching `agent.BedrockModel` after `agent.py` no longer owns Bedrock construction.

### Previous Story Intelligence

- Story 1.2 confirmed the current implementation already satisfies the local age-in-days behavior through deterministic tests and live startup evidence.
- Story 1.2 explicitly deferred adapter extraction to Story 1.3; do not repeat Story 1.2's validation-only approach here.
- Story 1.2 established evidence discipline: record actual commands run and distinguish deterministic tests from live credential-backed validation.
- Story 1.2 live Bedrock conversation checks were blocked by revoked access to `us.amazon.nova-micro-v1:0`; do not treat that infrastructure/account issue as an adapter bug unless this story changes model IDs or Bedrock request construction.

### Git Intelligence

Recent commits are story artifact and planning updates, not adapter implementation:

- `5fc1cea` - Add Story 1.2 review artifacts
- `1b0a675` - Add Story 1.1 review follow-up
- `634b5b9` - Update planning artifacts and add implementation readiness report
- `ec17f5e` - Add multi-provider model planning artifacts
- `8ffe0d0` - Updated BMAD

There are no current uncommitted changes at story creation time.

### Latest Technical Information

- PyPI currently lists `strands-agents` latest as `1.39.0`, uploaded on 2026-05-08. This repo intentionally pins `strands-agents==1.26.0`; do not upgrade in this story without a separate compatibility decision. [Source: https://pypi.org/pypi/strands-agents/json]
- Official Strands docs show `BedrockModel` accepts `region_name` and model configuration such as `model_id`; this matches the repo's existing local Bedrock construction. [Source: https://strandsagents.com/1.x/documentation/docs/api-reference/python/models/bedrock/]
- Official Strands model-provider docs continue to present provider switching through model instances passed into `Agent(model=...)`; this supports a local adapter boundary that returns a model object rather than changing `Agent(...)` usage. [Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/]
- PyPI currently lists `bedrock-agentcore` latest as `1.9.0`, `python-dotenv` latest as `1.2.2`, and `boto3` latest as `1.43.6`. This story should not move dependency versions; it is a local code ownership refactor. [Source: https://pypi.org/pypi/bedrock-agentcore/json] [Source: https://pypi.org/pypi/python-dotenv/json] [Source: https://pypi.org/pypi/boto3/json]
- The installed venv currently has `strands-agents==1.26.0`, `bedrock-agentcore==1.4.6`, `python-dotenv==1.2.2`, `boto3==1.42.70`, and `strands-agents-tools==0.2.22`. Treat that as local environment evidence, not a requirements change.

### Project Structure Notes

- Add exactly one root implementation module: `model_adapters.py`.
- Add exactly one focused unit test module if needed: `tests/unit/test_model_adapters.py`.
- Keep `agent.py` as the local REPL entrypoint and teaching artifact.
- Keep `deploy/app.py` as the cloud runtime entrypoint.
- Historical `_bmad-output/implementation-artifacts/1-3-vs-code-debug-configuration.md` exists from the older March story plan. It is not the current sprint story and should not be overwritten.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3]
- [Source: _bmad-output/planning-artifacts/prd.md#Configuration Management]
- [Source: _bmad-output/planning-artifacts/prd.md#Integration]
- [Source: _bmad-output/planning-artifacts/architecture.md#Model Provider Abstraction]
- [Source: _bmad-output/planning-artifacts/architecture.md#Architectural Boundaries]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules]
- [Source: _bmad-output/project-context.md#Provider And Model Rules]
- [Source: _bmad-output/implementation-artifacts/1-2-local-age-in-days-agent.md]
- [Source: agent.py]
- [Source: deploy/app.py]
- [Source: tests/unit/test_agent_tool.py]
- [Source: tests/unit/test_static.py]
- [Source: tests/evals/test_prompt_parity.py]
- [Source: tests/unit/test_safety_boundaries.py]
- [Source: compliance/promptfoo-redteam.yaml]
- [Source: requirements.txt]
- [Source: .env.example]
- [Source: https://pypi.org/pypi/strands-agents/json]
- [Source: https://strandsagents.com/1.x/documentation/docs/api-reference/python/models/bedrock/]
- [Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/]
- [Source: https://pypi.org/pypi/bedrock-agentcore/json]
- [Source: https://pypi.org/pypi/python-dotenv/json]
- [Source: https://pypi.org/pypi/boto3/json]

## Change Log

- 2026-05-09: Ultimate context engine analysis completed - comprehensive developer guide created.
- 2026-05-09: Implementation complete. Extracted provider selection into model_adapters.py; simplified agent.py to 63 lines; added 14 new adapter tests; updated patch paths in test_agent_tool.py and test_safety_boundaries.py. 65 tests pass, 0 failures.

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

All 65 tests passed. No regressions. black reformatted test_agent_tool.py and test_model_adapters.py (style only).

### Completion Notes List

- Created `model_adapters.py` with `BedrockAdapter`, `GeminiAdapter`, and `create_local_model_adapter()` factory. All Bedrock/Gemini construction logic moved here. Bedrock imported at module level; Gemini lazy-imported inside `build()` to protect installs without the optional Google dependency.
- Simplified `agent.py` from 93 lines to 63 lines. Provider branching replaced with a single `create_local_model_adapter(os.environ["MODEL_PROVIDER"], os.environ).build()` call. `load_dotenv()` retained before all env access. All other responsibilities (`SYSTEM_PROMPT`, `get_today_date`, `run_repl`, `Agent`, `AuditLoggingHook`) unchanged.
- Added `tests/unit/test_model_adapters.py` with 14 tests covering: Bedrock construction, guardrail presence/absence/default-version, missing required vars, Gemini construction, no-guardrail-kwargs for Gemini, unsupported provider ValueError, no-silent-fallback, and import-failure surfacing.
- Updated `tests/unit/test_agent_tool.py`: replaced 7 provider-construction tests with 3 adapter-delegation tests verifying `create_local_model_adapter` is called, `.build()` is called, and the model is wired into `Agent(...)`. REPL tests untouched.
- Updated `tests/unit/test_safety_boundaries.py`: patch path changed from `agent.BedrockModel` to `model_adapters.BedrockModel`.
- `deploy/app.py` untouched — cloud runtime remains separate from the local adapter.

### File List

- model_adapters.py (new)
- agent.py (modified)
- tests/unit/test_model_adapters.py (new)
- tests/unit/test_agent_tool.py (modified)
- tests/unit/test_safety_boundaries.py (modified)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified)
- _bmad-output/implementation-artifacts/1-3-adapter-based-local-model-selection.md (modified)
