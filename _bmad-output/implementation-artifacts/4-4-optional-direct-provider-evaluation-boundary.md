# Story 4.4: Optional Direct-Provider Evaluation Boundary

Status: done
Last Updated: 2026-05-15

## Story

As a maintainer,
I want any non-Bedrock direct-provider or LiteLLM-style path treated as an explicit evaluated boundary,
so that optional expansion does not accidentally weaken the core architecture contract.

## Acceptance Criteria

1. Given a direct-provider or alternative gateway path is being considered, when I document or prototype that path, then it is clearly marked as optional and justified by capability gaps and it is not presented as default parity with the Bedrock-first path.
2. Given optional direct-provider support differs from the primary deployed path, when I review the resulting docs and configuration guidance, then the limitations and expected usage are explicit and developers can tell which paths are production-aligned versus exploratory.

## Tasks / Subtasks

- [x] Define an explicit evaluation boundary for non-Bedrock access without weakening the current Bedrock-first contract. (AC: 1, 2)
  - [x] Keep `bedrock` and `llama` as the production-aligned paths for both local and deployed runtimes.
  - [x] Introduce one clearly named optional local-only evaluation path, preferably `litellm`, rather than silently expanding provider parity across the repo.
  - [x] Preserve the existing deployed/runtime boundary: `deploy/app.py` and `deploy/deploy.py` must continue rejecting non-Bedrock-backed providers.
  - [x] State explicitly that Story 4.4 is an evaluation boundary, not a new default architecture.
- [x] Add a minimal local-only prototype path for direct-provider experimentation. (AC: 1)
  - [x] Implement a lazy-import local adapter for LiteLLM using Strands' `LiteLLMModel`, gated behind optional dependency installation.
  - [x] Keep the prototype limited to local Strands execution in `agent.py` via `model_adapters.py`; do not route the deployed AgentCore runtime through LiteLLM or vendor SDKs.
  - [x] Use one concrete OpenAI-compatible provider example for documentation and sanity checks. Recommended evaluation example: Moonshot/Kimi via LiteLLM with `base_url=https://api.moonshot.ai/v1`.
  - [x] Ensure missing optional dependency or missing direct-provider credentials fail with clear, actionable errors rather than falling back to Bedrock.
- [x] Make the exploratory boundary explicit in configuration and docs. (AC: 1, 2)
  - [x] Update `.env.example` with an optional, clearly commented LiteLLM/direct-provider section that is visibly separate from the default Bedrock path.
  - [x] Update README so developers can distinguish:
    - production-aligned: `bedrock`, `llama`
    - supported local-only: `gemini`
    - exploratory local-only evaluation: `litellm` / direct-provider path
  - [x] Update `_bmad-output/project-context.md` with short, rule-like guidance that direct-provider evaluation is local-only unless a later story deliberately changes deployment support.
  - [x] Do not imply that any direct-provider path is the recommended default for this repo.
- [x] Preserve and test the deployment boundary. (AC: 2)
  - [x] Keep `deploy/app.py` and `deploy/deploy.py` Bedrock-only in transport terms.
  - [x] If any wording changes are needed in deployed runtime error messages or README, keep them explicit that `litellm`/direct-provider support is not deployable through the current AgentCore path.
  - [x] Add or update unit tests proving `MODEL_PROVIDER=litellm` is rejected by deployed runtime and deployment preflight before any Bedrock client call or deployment attempt.
- [x] Add focused tests for the optional local prototype and its limits. (AC: 1, 2)
  - [x] Extend `tests/unit/test_model_adapters.py` to cover:
    - capability metadata for `litellm` or the chosen evaluation key
    - local adapter construction when optional dependency is available
    - clear import/credential failure when optional dependency is absent
    - continued clear rejection of still-unimplemented planned Bedrock-first families
  - [x] Extend `tests/unit/test_static.py` if `.env.example`, README, or project context wording becomes a stable contract.
  - [x] Run focused verification for the local-only prototype path and record what was and was not executed live.
- [x] Record the rationale for why this path remains exploratory. (AC: 1, 2)
  - [x] Capture the exact gaps that justify evaluation, such as provider-specific capabilities, API surface flexibility, or portability needs that Bedrock does not yet satisfy.
  - [x] Document the additional operational costs of this path: extra secrets, outbound networking assumptions, more mocking surfaces, and a wider test matrix.
  - [x] Make clear that Story 4.5 will own the final expanded documentation and verification surface after this boundary is defined.

### Review Findings

- [x] [Review][Patch] Make missing LiteLLM optional dependency errors actionable [model_adapters.py:224]
- [x] [Review][Patch] Validate documented Moonshot/Kimi credentials for the LiteLLM example path [model_adapters.py:218]
- [x] [Review][Patch] Guard and test `LITELLM_API_BASE` propagation and invalid values [model_adapters.py:221]
- [x] [Review][Patch] Add deployment preflight coverage for `MODEL_PROVIDER=litellm` [tests/unit/test_deploy.py:308]
- [x] [Review][Patch] Route `litellm` adapter creation through registry enabled/runtime metadata [model_adapters.py:241]
- [x] [Review][Patch] Fix contradictory README deployment guidance and tighten static contract coverage [README.md:495]
- [x] [Review][Patch] Update `.env.example` top-level provider guidance to include exploratory `litellm` [.env.example:2]
- [x] [Review][Patch] Make Kimi `LITELLM_API_BASE` documentation part of the concrete example, not only a generic override [.env.example:54]

## Dev Notes

### Story Intent

Story 4.4 should define and, at most, lightly prototype an optional direct-provider path. It must not erode the repository's primary architectural claim: Bedrock is still the production-aligned control plane, and AgentCore deployment remains Bedrock-native in this repo.

### Recommended Scope

The safest implementation is:

- add a **local-only** `litellm` evaluation provider in `model_adapters.py`
- keep `deploy/app.py` and `deploy/deploy.py` rejecting that path
- document one concrete direct-provider example through LiteLLM
- mark the entire path exploratory in code comments, `.env.example`, README, and project context

This is preferable to adding one-off bespoke SDK integrations for DeepSeek, Kimi, Qwen, or Gemma because it keeps the evaluation surface narrow and preserves the provider abstraction.

### Chosen Evaluation Example

Use **LiteLLM + Kimi API** as the primary example path unless implementation discovers a concrete blocker.

Why Kimi is the best first example for Story 4.4:

- official Kimi docs describe an OpenAI-compatible chat completions API
- the service address and auth model are explicit
- this fits naturally with LiteLLM and avoids introducing a provider-specific SDK into the repo

Concrete official Kimi details to use in docs:

- base URL: `https://api.moonshot.ai/v1`
- auth: `Authorization: Bearer $MOONSHOT_API_KEY`

Keep this as an example, not a hardcoded default. The actual local prototype should remain generic enough to support other LiteLLM-backed providers later.

### Scope Boundary

- Do not make `litellm` or any direct provider deployable through `deploy/app.py`.
- Do not route AgentCore deployment through OpenAI, Gemini, Fireworks, Kimi, DeepSeek, or any other external API in this story.
- Do not add silent fallback from `litellm` or direct-provider failures back to Bedrock.
- Do not claim production parity, observability parity, or guardrail parity with the Bedrock-first path.
- Do not add multiple direct-provider implementations in this story. One generic LiteLLM boundary is enough.

### Current State After Story 4.3

- Production-aligned local/deployed paths are `bedrock` and `llama` (Bedrock-backed).
- `gemini` remains local-only through a dedicated adapter.
- `model_adapters.py` already contains a capability registry and explicit local adapter construction boundary.
- `deploy/app.py` and `deploy/deploy.py` accept only Bedrock-backed providers and are intentionally isolated from the local adapter module.
- `.env.example`, README, and project context now describe Bedrock-first support and planned future Bedrock-hosted families explicitly.

There is an older historical artifact named `_bmad-output/implementation-artifacts/4-4-red-team-ci.md` from a previous Epic 4 numbering scheme. Treat it as historical only and do not overwrite it.

### Architecture Requirements

- Preserve runtime separation:
  - local REPL path: `agent.py` + `model_adapters.py`
  - deployed path: `deploy/app.py` via Bedrock Converse only
- Keep direct-provider experimentation out of the deployed runtime unless a later story deliberately expands the deployment architecture.
- Use lazy imports for optional local-only dependencies, just as `GeminiAdapter` already does.
- Keep required env vars fail-fast and explicit.
- Prefer a single evaluation abstraction (`LiteLLMModel`) over bespoke vendor SDK clients.

### Files To Review And Likely Update

#### `model_adapters.py`

Current state:

- Owns the registry and local provider factory.
- Already handles one optional local-only path (`gemini`) through lazy import.
- Already distinguishes enabled providers from planned families.

Expected change:

- Add a local-only `litellm` capability entry or equally explicit evaluation key.
- Add a lazy-import adapter using `strands.models.litellm.LiteLLMModel`.
- Keep the registry wording clear that this is exploratory/local-only.

Must preserve:

- Bedrock adapter behavior
- Gemini adapter behavior
- planned-family rejection behavior
- no imports from local adapter code into deployed runtime

#### `requirements.txt`

Current state:

- Does not include LiteLLM today.

Decision guidance:

- Prefer **not** to make LiteLLM a hard mandatory dependency for the whole project unless the repo already expects it in CI and developer setup.
- A better default is to keep it optional and surface a clear ImportError/message telling the developer to install `strands-agents[litellm]`.
- If tests require the dependency in CI, document that tradeoff explicitly in the story completion notes.

#### `.env.example`

Expected change:

- Keep the default Bedrock path unchanged at the top.
- Add a distinct exploratory section for LiteLLM/direct-provider evaluation, for example:
  - `MODEL_PROVIDER=litellm`
  - `MODEL_ID=<provider/model>`
  - provider-specific secret env vars such as `MOONSHOT_API_KEY`
  - optional `LITELLM_API_BASE` or equivalent only if the implementation truly needs it
- Make it unmistakable that this path is local-only and exploratory.

#### `README.md`

Expected change:

- Update the roadmap and local setup guidance so exploratory direct-provider evaluation is described as optional and non-default.
- Explain that AgentCore deployment in this repo remains Bedrock-only even if local LiteLLM evaluation is added.
- Capture the specific extra setup burden for exploratory paths: optional install, extra API keys, and likely reduced contract coverage compared to Bedrock-first flows.

#### `_bmad-output/project-context.md`

Expected change:

- Add concise, stable rules only if the evaluation path becomes a real project convention, for example:
  - `litellm` is exploratory and local-only
  - deployed runtime remains Bedrock-only
  - direct-provider evaluation must not be presented as default parity

#### `tests/unit/test_model_adapters.py`

Expected change:

- Add local adapter tests for the LiteLLM boundary.
- Assert clear failure when the optional dependency is missing.
- Assert it is local-only in capability metadata.

#### `tests/unit/test_app.py`

Expected change:

- Preserve or expand rejection tests for `litellm` in the deployed runtime.

#### `tests/unit/test_static.py`

Expected change:

- Guard new README and `.env.example` wording if it becomes part of the stable contract.

### Files That Should Probably Not Change

- `agent.py` should likely stay unchanged if `create_local_model_adapter()` remains the stable entrypoint.
- `deploy/verify.py` should remain Bedrock-runtime verification only in this story.
- IAM or packaging logic in `deploy/deploy.py` should not expand to support external-provider credentials or networking.

### Previous Story Intelligence

From Story 4.3:

- Provider-surface changes in this repo are cross-cutting and test-backed.
- Documentation, `.env.example`, and static tests drift easily if wording is not updated together.
- The Bedrock-backed `llama` rollout succeeded because it reused the existing transport plane rather than introducing a new one.
- Review findings in Story 4.3 were almost entirely contract-alignment issues, so Story 4.4 must keep docs/tests/config perfectly synchronized if it introduces exploratory wording.

### Git Intelligence

Recent commits show the intended sequence:

- `ee5d9f5` completed Story 4.3 and reinforced Bedrock-first production alignment.
- `8a4dea9` established the capability registry that Story 4.4 can extend without changing deployed runtime assumptions.
- `a310206` aligned docs and tests around supported versus planned provider boundaries.

### Latest Technical Context

Official sources checked on 2026-05-15:

- Strands model-provider docs show LiteLLM support is available for Python and is a separate provider path, while the provider matrix indicates LiteLLM is local-capable and not a deployed default path in the repo's current architecture. [Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/]
- Strands LiteLLM docs show:
  - install via `pip install 'strands-agents[litellm]' strands-agents-tools`
  - use `from strands.models.litellm import LiteLLMModel`
  - configure the underlying model via `model_id` and `client_args`
  [Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/litellm/]
- AgentCore "use any model" docs show Runtime can technically host Bedrock, OpenAI, Gemini, and other providers, but that is an AWS platform capability, not this repo's current deployed contract. [Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/using-any-model.html]
- AgentCore overview docs explicitly state Runtime can work with models inside or outside Bedrock. Again, treat this as platform capability, not repo-default behavior. [Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html]
- Kimi API docs state the API is OpenAI Chat Completions compatible, with base URL `https://api.moonshot.ai/v1`, official OpenAI SDK compatibility, and `MOONSHOT_API_KEY`-style bearer auth. [Source: https://platform.kimi.ai/docs/api/overview]
- DeepSeek API docs state the API is compatible with OpenAI and Anthropic formats, with base URLs `https://api.deepseek.com` and `https://api.deepseek.com/anthropic`. The docs also note deprecations for `deepseek-chat` and `deepseek-reasoner` on 2026-07-24, which makes DeepSeek a less stable example default than Kimi for this story. [Source: https://api-docs.deepseek.com/]
- Google Gemma can be accessed through the Gemini API with a Gemini API key, but that path is less aligned with the repo's likely LiteLLM/OpenAI-compatible evaluation shape for Story 4.4. [Source: https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api]

Inference from those sources:

- The cleanest Story 4.4 prototype is a local-only LiteLLM boundary, not a deployed direct-provider runtime.
- Kimi is a better example than DeepSeek for documentation because the OpenAI-compatible path is explicit and there is no near-term model-name deprecation warning in the surfaced docs.
- Any direct-provider path expands secrets, outbound networking assumptions, and failure modes, so the story should bias toward explicit documentation of tradeoffs rather than broad enablement.

### Testing Requirements

Minimum expected verification:

```bash
venv/bin/python -m pytest tests/unit/test_model_adapters.py tests/unit/test_app.py tests/unit/test_static.py
make lint
```

Optional additional verification if secrets are available:

- local smoke test with `MODEL_PROVIDER=litellm` and the chosen provider credentials
- no deployed runtime verification for the direct-provider path in this story unless the architecture is deliberately changed, which it should not be

### Project Structure Notes

- Keep Story 4.4 work centered in:
  - `model_adapters.py`
  - `.env.example`
  - `README.md`
  - `_bmad-output/project-context.md`
  - unit tests
- Avoid changing deployment/runtime packaging unless the change is purely to preserve or clarify the rejection boundary.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Epic 4`]
- [Source: `_bmad-output/planning-artifacts/prd.md#Integration Requirements`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Model Provider Abstraction`]
- [Source: `_bmad-output/planning-artifacts/research/technical-multi-provider-model-support-research-2026-05-07.md`]
- [Source: `_bmad-output/project-context.md#Provider And Model Rules`]
- [Source: `_bmad-output/implementation-artifacts/4-3-bedrock-first-model-family-rollout.md`]
- [Source: `model_adapters.py`]
- [Source: `deploy/app.py`]
- [Source: `deploy/deploy.py`]
- [Source: `requirements.txt`]
- [Source: `.env.example`]
- [Source: `README.md`]
- [Source: `tests/unit/test_model_adapters.py`]
- [Source: `tests/unit/test_app.py`]
- [Source: `tests/unit/test_static.py`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- Story context created from BMAD create-story workflow on 2026-05-15.
- Implementation completed 2026-05-15.

### Completion Notes List

- Added `litellm` as an exploratory local-only evaluation provider in `model_adapters.py`:
  - New `ModelCapabilities` registry entry: `enabled=True`, `runtimes=("local",)`, `bedrock_first=False`, `supports_guardrails=False`.
  - New `LiteLLMAdapter` class with lazy import of `strands.models.litellm.LiteLLMModel`. Reads `MODEL_ID` (required) and optional `LITELLM_API_BASE`. Fails with `ImportError` if `strands-agents[litellm]` is not installed — no Bedrock fallback.
  - Updated `create_local_model_adapter()` to route `litellm` to `LiteLLMAdapter` before the registry lookup, mirroring the `gemini` pattern.
- `deploy/app.py` required no changes — `_DEPLOYED_BEDROCK_PROVIDERS` frozenset already rejects `litellm` with a clear error before any Bedrock call.
- Updated `.env.example` with a distinct exploratory section: `MODEL_PROVIDER=litellm`, `MODEL_ID=moonshot/moonshot-v1-8k`, `MOONSHOT_API_KEY`, and `LITELLM_API_BASE`.
- Updated README model expansion roadmap table to three-tier structure: production-aligned, supported local-only, exploratory local-only evaluation, and planned Bedrock-first. Added explanatory paragraph on `litellm` operational costs.
- Updated `_bmad-output/project-context.md`: provider rules now include `litellm` as exploratory local-only; Epic 4.5+ owns the Bedrock-first Gemma/Kimi/Qwen/DeepSeek rollout.
- Added 12 new tests in `tests/unit/test_model_adapters.py` (`TestLiteLLMAdapter`).
- Added 2 new tests in `tests/unit/test_app.py` (`TestHandleInvocationLiteLLM`); also added `litellm` to existing provider rejection list.
- Added 8 new static contract tests in `tests/unit/test_static.py` covering `.env.example` and README litellm wording; updated one assertion in `TestProjectContextProviderRules` and one in `TestReadmeProviderRoadmap` to match new provider-boundary language.
- Full test suite: 313 tests pass, 0 failures. `make lint` clean.
- Code review follow-up: addressed 6 patch findings; full test suite now 319 tests pass, 0 failures. `make lint` clean.
- Code review rerun follow-up: addressed 2 `.env.example` documentation-contract findings; full test suite now 320 tests pass, 0 failures. `make lint` clean.
- Live smoke test NOT executed — `strands-agents[litellm]` and `MOONSHOT_API_KEY` not provisioned in this environment. All adapter behavior verified through mocked unit tests.
- Rationale for keeping `litellm` exploratory: no Bedrock Converse transport, no Bedrock guardrail integration, extra outbound networking, additional credential surface, and a wider provider-specific test matrix. Story 4.5 owns the final documentation and verification surface.

### File List

- _bmad-output/implementation-artifacts/4-4-optional-direct-provider-evaluation-boundary.md
- model_adapters.py
- .env.example
- README.md
- _bmad-output/project-context.md
- tests/unit/test_model_adapters.py
- tests/unit/test_app.py
- tests/unit/test_static.py
- tests/unit/test_deploy.py
- _bmad-output/implementation-artifacts/sprint-status.yaml

### Change Log

- 2026-05-15: Implemented Story 4.4 — added `litellm` exploratory local-only evaluation boundary; updated registry, adapter factory, docs, config, and tests; 22 new tests; deployment boundary preserved.
- 2026-05-15: Addressed code review findings — added actionable LiteLLM dependency and credential validation, API-base validation, registry-gated adapter routing, deployment preflight coverage, and README/static contract fixes.
- 2026-05-15: Addressed rerun review findings — aligned `.env.example` top-level provider guidance with `litellm` and made the Kimi API-base line part of the concrete example.
