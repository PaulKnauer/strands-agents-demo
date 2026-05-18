# Story 4.5: Expansion Documentation and Verification

Status: done
Last Updated: 2026-05-15

## Story

As a developer,
I want the expanded model-support surface documented and verified,
so that I can adopt supported new model paths with confidence.

## Acceptance Criteria

1. Given new model-support paths have been added or clarified, when I inspect the tests, verification notes, and documentation, then each supported path has an explicit verification strategy and local versus deployed runtime expectations are documented.
2. Given the expansion changes affect setup or troubleshooting, when I review README and related docs, then the new configuration and support boundaries are captured accurately and the guidance remains usable for a developer new to the repository.

## Tasks / Subtasks

- [x] Create a final model-support matrix in README and align adjacent setup/troubleshooting text. (AC: 1, 2)
  - [x] Document each current path with status, runtime support, required config, verification command, and deployment expectation:
    - `bedrock`: production-aligned local + deployed.
    - `llama`: production-aligned local + deployed, Bedrock-backed alias.
    - `gemini`: supported local-only.
    - `litellm`: exploratory local-only evaluation boundary.
    - `gemma`, `moonshot`/`kimi`, `qwen`, `deepseek`: planned Bedrock-first candidates, not runnable provider keys yet.
  - [x] Remove or replace wording that implies Gemma/Moonshot/Kimi/Qwen/DeepSeek are delivered by Story 4.5 unless the implementation actually enables and verifies them.
  - [x] Preserve the "AgentCore deployment remains Bedrock-backed only" message everywhere deployment is discussed.
- [x] Add a compact verification strategy section for provider/runtime paths. (AC: 1)
  - [x] List deterministic verification commands for the supported paths, including `venv/bin/python -m pytest tests/unit/test_model_adapters.py tests/unit/test_app.py tests/unit/test_deploy.py tests/unit/test_static.py`.
  - [x] State which paths are unit/static verified only versus live-smoke optional.
  - [x] State that `litellm` live smoke requires optional dependency installation, provider credentials, and outbound network access; do not require this in CI.
  - [x] State that deployed verification only applies to `bedrock` and `llama` in the current repo architecture.
- [x] Tighten `.env.example` as the setup contract. (AC: 2)
  - [x] Ensure the top-level provider comment includes `bedrock`, `llama`, `gemini`, and `litellm` with runtime labels.
  - [x] Keep the planned Bedrock candidates clearly marked as not yet enabled provider keys.
  - [x] Keep the Kimi/LiteLLM example local-only and exploratory, with `MOONSHOT_API_KEY` and `LITELLM_API_BASE=https://api.moonshot.ai/v1` shown as part of the example.
  - [x] Do not add real secrets or make LiteLLM a mandatory install path.
- [x] Update project context only if a stable rule changes. (AC: 1, 2)
  - [x] If README/.env wording establishes a final Epic 4 convention, update `_bmad-output/project-context.md` with concise rules.
  - [x] Preserve existing rules: local adapter supports `bedrock`, `gemini`, `llama`, `litellm`; deployed runtime supports only `bedrock` and `llama`; planned Bedrock candidates are future work unless explicitly enabled.
- [x] Strengthen static/unit tests so docs and verification strategy cannot drift. (AC: 1, 2)
  - [x] Extend `tests/unit/test_static.py` to assert README contains the final model-support matrix and per-path verification strategy.
  - [x] Extend `.env.example` static assertions if provider labels or planned-family wording changes.
  - [x] Reuse existing provider tests rather than duplicating runtime behavior tests unless a new contract is introduced.
  - [x] If any provider status changes from planned to enabled, update `tests/unit/test_model_adapters.py`, `tests/unit/test_app.py`, and `tests/unit/test_deploy.py` together.
- [x] Record final verification evidence in the story. (AC: 1)
  - [x] Run focused tests for provider/docs contracts.
  - [x] Run `make lint`.
  - [x] Run the full test suite if provider registry or runtime code changes.
  - [x] Record any live smoke tests that were not run and why.

### Review Findings

- [x] [Review][Patch] Update `deploy/verify.py` provider hint to include `llama` deployed support [deploy/verify.py:417]
- [x] [Review][Patch] Update README `make test` count to the actual Story 4.5 test total [README.md:458]
- [x] [Review][Patch] Replace ambiguous "Bedrock-only" wording/static assertion with "Bedrock-backed" deployed boundary [README.md:418]
- [x] [Review][Patch] Tighten `litellm` project-context static assertion to bind exploratory/local-only wording to the `litellm` rule [tests/unit/test_static.py:357]
- [x] [Review][Patch] Replace `Story 4.5+` planned-family wording with unambiguous post-Story-4.5 future-work wording [_bmad-output/project-context.md:66]
- [x] [Review][Patch] Add static coverage for every provider row in the README verification strategy [tests/unit/test_static.py:417]

<!-- Code review 2 — 2026-05-15 -->
- [x] [Review][Decision] Should LITELLM_API_BASE validation restrict http:// URLs to localhost-only or allow all http:// endpoints? — Resolved: restrict http:// to localhost/127.x only; added http-external rejection test, localhost acceptance test, and 127.x acceptance test [model_adapters.py:234, tests/unit/test_model_adapters.py]
- [x] [Review][Patch] Replace full-table row snapshot in TestReadmeVerificationStrategy with individual property assertions — Replaced exact pipe-delimited row assertions with semantic checks: all provider tokens, pinned model IDs, credential names, planned-family rejection label [tests/unit/test_static.py:463]
- [x] [Review][Defer] MOONSHOT_API_KEY validation is moonshot-prefix-only; other LiteLLM provider prefixes pass __init__ without credential check and fail later at runtime with no guidance [model_adapters.py:222] — deferred, acceptable for exploratory path
- [x] [Review][Defer] self._client_args or None silently converts {} to None; works today but fragile if future code stores any falsy-truthy value in _client_args [model_adapters.py:230] — deferred, currently correct
- [x] [Review][Defer] "local" not in cap.runtimes guard is dead code given current registry invariants; all enabled entries have "local" [model_adapters.py:278] — deferred, defensive programming for future entries
- [x] [Review][Defer] test_litellm_rejection_occurs_before_bedrock_call in test_app.py duplicates the assert_not_called assertion already in test_litellm_provider_rejected_by_deployed_runtime [tests/unit/test_app.py:398] — deferred, harmless
- [x] [Review][Defer] deploy/verify.py Llama hint not actionable — doesn't name the Bedrock model ID the operator must request access for [deploy/verify.py:416] — deferred, quality nit
- [x] [Review][Defer] LITELLM_API_BASE path component not validated; URLs like https://api.example.com (no /v1 path) pass silently and may misbehave with some LiteLLM provider wrappers [model_adapters.py:227] — deferred, acceptable for exploratory path
- [x] [Review][Defer] create_local_model_adapter gemini branch reached only after registry checks; a future enabled=False on gemini would produce misleading "planned candidate" error [model_adapters.py:282] — deferred, future registry risk
- [x] [Review][Defer] Enabled provider with bedrock_first=False and no specific adapter branch silently falls through to confusing "no local adapter implementation" error [model_adapters.py:288] — deferred, future extensibility risk
- [x] [Review][Defer] Model-support matrix (roadmap table + verification table) missing explicit required-config and deployment-expectation columns; info is split across four prose locations [README.md:406] — deferred, info present in surrounding prose
- [x] [Review][Defer] TestReadmeProviderRoadmap asserts backtick-coupled Markdown syntax for ValueError string; breaks on prose reformat without actual regression [tests/unit/test_static.py:337] — deferred, working correctly today

## Dev Notes

### Story Intent

Story 4.5 is the closure story for Epic 4. It should make the expanded provider surface understandable and auditable. It is not permission to broaden runtime support casually.

The expected implementation shape is primarily documentation plus static/unit contract tests. Only modify provider/runtime code if the current docs cannot truthfully describe the implemented behavior.

### Current Provider Surface To Preserve

- `bedrock`: supported locally via `BedrockAdapter`; supported in deployed AgentCore via direct Bedrock Converse. This remains the default production-aligned path.
- `llama`: supported locally and deployed as a Bedrock-backed family alias. It routes through Amazon Bedrock Converse, not a direct Meta API.
- `gemini`: supported locally only through a dedicated Strands Gemini adapter. It is not deployable through AgentCore in this repo.
- `litellm`: exploratory local-only evaluation boundary through `LiteLLMAdapter`. It is not deployable through AgentCore and requires optional dependency installation plus provider-specific credentials.
- `gemma`, `moonshot`, `kimi`, `qwen`, `deepseek`: present as planned registry candidates with `enabled=False`. They must continue to fail clearly unless this story deliberately enables one with complete docs/tests/deployment assumptions.

### Non-Negotiable Boundaries

- Do not import `model_adapters.py`, `agent.py`, or Strands into `deploy/app.py`.
- Do not route AgentCore deployment through LiteLLM, direct Kimi/Moonshot, direct Gemini, direct Qwen, direct DeepSeek, or any external provider SDK in this story.
- Do not add silent fallbacks from unsupported providers to Bedrock.
- Do not claim production parity for `gemini` or `litellm`.
- Do not mark planned Bedrock families as supported unless the dev agent updates registry metadata, env docs, README, deployed runtime assumptions, IAM/model ARN handling, and tests together.

### Files To Review And Likely Update

#### `README.md`

Current state:

- Contains a "Model expansion roadmap" table with `bedrock`, `llama`, `gemini`, `litellm`, and planned Bedrock-first families.
- Contains troubleshooting guidance for `MODEL_PROVIDER` and deployed runtime support.
- Contains make-target comments whose test count may be stale after Story 4.4.

Expected Story 4.5 changes:

- Convert the roadmap into a final model-support and verification matrix or add a verification subsection immediately below it.
- Make "planned Bedrock-first" wording precise: current planned candidates are not implemented provider paths.
- Include the exact commands developers should use for deterministic verification.
- Keep guidance readable for a developer new to the repository.

#### `.env.example`

Current state:

- Documents `bedrock`, `llama`, `gemini`, and `litellm`.
- Documents `litellm` as local-only exploratory and shows Kimi/Moonshot credentials plus API base.
- Marks Gemma/Moonshot/Kimi/Qwen/DeepSeek as planned additions that fail explicitly today.

Expected Story 4.5 changes:

- Keep this file as the setup contract, not a marketing roadmap.
- Ensure each provider label matches README and project context.
- If README introduces a new status term, mirror it here only when useful for setup.

#### `_bmad-output/project-context.md`

Current state:

- Captures stable provider rules and local/deployed runtime boundaries.
- Already states `litellm` is exploratory local-only and planned families are future work.

Expected Story 4.5 changes:

- Update only concise, stable rules. Do not turn project context into a long roadmap.
- If Epic 4 closes with a final support matrix, add one short rule that future provider changes must update README, `.env.example`, registry metadata, deployment assumptions, and verification strategy together.

#### `tests/unit/test_static.py`

Current state:

- Guards README provider roadmap wording.
- Guards project-context provider rules.
- Guards `.env.example` LiteLLM/Kimi documentation.

Expected Story 4.5 changes:

- Add static tests for README verification strategy per provider path.
- Add tests for final support status wording if it changes.
- Prefer direct string/section assertions over brittle full-table snapshots.

#### `tests/unit/test_model_adapters.py`

Current state:

- Verifies local adapter routing, planned-family rejection, registry metadata, LiteLLM import/credential/API-base behavior.

Expected Story 4.5 changes:

- No changes required if this story only documents current behavior.
- If any planned provider becomes enabled, this file must receive corresponding registry, adapter, and negative tests.

#### `tests/unit/test_app.py` and `tests/unit/test_deploy.py`

Current state:

- Verify deployed runtime and deployment preflight reject non-Bedrock-backed providers, including `litellm`.

Expected Story 4.5 changes:

- No changes required unless deployed support changes.
- If docs mention a rejection contract, static tests may be enough; behavior is already covered.

### Previous Story Intelligence

From Story 4.4:

- Documentation drift is the primary risk. Code review found stale and ambiguous `.env.example` and README wording after the first implementation pass.
- The final Story 4.4 state added:
  - actionable LiteLLM optional dependency errors
  - Moonshot/Kimi credential validation
  - `LITELLM_API_BASE` validation and tests
  - deployment preflight coverage for `MODEL_PROVIDER=litellm`
  - registry-gated LiteLLM adapter routing
  - corrected README deployment guidance
  - static tests locking Kimi API-base and provider comments
- Full verification after Story 4.4 review follow-up: 320 tests passed and `make lint` was clean.
- Live LiteLLM smoke was not run because `strands-agents[litellm]` and `MOONSHOT_API_KEY` were not provisioned.

From Story 4.3:

- Bedrock-backed rollout succeeded because it reused the existing Bedrock transport rather than adding a new deployed transport.
- Keep `llama` clearly described as Bedrock-backed, not a direct Meta API.

### Git Intelligence

Recent committed sequence:

- `ee5d9f5` completed Story 4.3 and reinforced Bedrock-first Llama rollout.
- `8a4dea9` introduced the capability registry and adapter extension pattern.
- `a310206` aligned Epic 4 scope and provider-boundary docs/tests.

Current working tree note:

- Story 4.4 changes are still uncommitted in the working tree at story creation time. Do not revert or overwrite them.
- `_bmad-output/implementation-artifacts/4-4-optional-direct-provider-evaluation-boundary.md` is untracked but is the current previous-story context.
- Older files such as `_bmad-output/implementation-artifacts/4-5-compliance-dashboard.md` belong to a historical compliance-oriented Epic 4 numbering scheme. Treat them as historical only.

### Latest Technical Context

Official source checks on 2026-05-15:

- AWS Bedrock API compatibility docs show the Converse family is the unified synchronous conversation API and list Converse support across model providers, including current Gemma, Moonshot/Kimi, Qwen, and DeepSeek entries. This supports keeping the future expansion path Bedrock-first, but model-level capability must still be verified before enabling any provider key. [Source: https://docs.aws.amazon.com/bedrock/latest/userguide/models-api-compatibility.html]
- AWS supported foundation model docs list current Bedrock model IDs for newer providers, including `google.gemma-3-*`, `moonshot.kimi-k2-thinking`, Qwen model IDs, and DeepSeek entries. Use those docs as current reference material if this story updates candidate model examples. [Source: https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html]
- Strands model-provider docs identify Amazon Bedrock as the default provider with wide model selection and enterprise features, and Strands' model architecture supports multiple provider implementations behind a model abstraction. This aligns with the repo's Bedrock-first plus adapter-boundary direction. [Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/]
- Strands custom model provider docs describe the `Model` abstraction that Bedrock, LiteLLM, and custom providers implement. This reinforces that future provider variability should stay behind adapter/model boundaries, not leak into app logic. [Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/custom_model_provider/]

Implementation inference:

- Story 4.5 should not hardcode newly surfaced model IDs into runnable config unless tests and deployment assumptions are updated at the same time.
- A documentation table can reference examples as "current candidate examples" only if it makes clear they are not enabled provider keys yet.
- Verification strategy should distinguish deterministic repo tests from optional live provider smoke tests.

### Architecture Compliance

- Preserve runtime separation:
  - local path: `agent.py` + `model_adapters.py` + Strands model classes
  - deployed path: `deploy/app.py` + direct Bedrock Converse via `boto3`
- Preserve fail-fast env behavior: required env vars use `os.environ[...]` where missing config should hard-fail.
- Preserve `.env.example` as documentation-only scaffolding with no real secrets.
- Preserve static contract test style for README and `.env.example`.
- Keep docs and project context in English.

### Testing Requirements

Minimum expected verification:

```bash
venv/bin/python -m pytest tests/unit/test_static.py
venv/bin/python -m pytest tests/unit/test_model_adapters.py tests/unit/test_app.py tests/unit/test_deploy.py tests/unit/test_static.py
make lint
```

Run the full suite if any provider registry, deployed runtime, deployment script, or adapter behavior changes:

```bash
venv/bin/python -m pytest
```

Optional live verification:

- `MODEL_PROVIDER=bedrock` local smoke if AWS credentials/model access are available.
- `MODEL_PROVIDER=llama` local and deployed smoke only if Bedrock model access is available.
- `MODEL_PROVIDER=gemini` local smoke only if `GOOGLE_API_KEY` and optional dependency are available.
- `MODEL_PROVIDER=litellm` local smoke only if `strands-agents[litellm]`, provider credentials, and outbound network access are available.

Do not block this story on optional live smoke tests. Record skipped live tests explicitly.

### Project Structure Notes

- Primary likely files:
  - `README.md`
  - `.env.example`
  - `_bmad-output/project-context.md`
  - `tests/unit/test_static.py`
- Conditional files only if support status changes:
  - `model_adapters.py`
  - `deploy/app.py`
  - `deploy/deploy.py`
  - `tests/unit/test_model_adapters.py`
  - `tests/unit/test_app.py`
  - `tests/unit/test_deploy.py`
- Do not edit historical compliance story files for this current Epic 4 sequence.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 4.5: Expansion Documentation and Verification`]
- [Source: `_bmad-output/planning-artifacts/prd.md#Technical Constraints`]
- [Source: `_bmad-output/planning-artifacts/prd.md#Configuration Management`]
- [Source: `_bmad-output/planning-artifacts/prd.md#Documentation Standards`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Model Provider Abstraction`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural Boundaries`]
- [Source: `_bmad-output/planning-artifacts/research/technical-multi-provider-model-support-research-2026-05-07.md#Phased Recommendation`]
- [Source: `_bmad-output/project-context.md#Provider And Model Rules`]
- [Source: `_bmad-output/implementation-artifacts/4-4-optional-direct-provider-evaluation-boundary.md`]
- [Source: `README.md#Model expansion roadmap`]
- [Source: `.env.example`]
- [Source: `model_adapters.py`]
- [Source: `tests/unit/test_static.py`]
- [Source: `tests/unit/test_model_adapters.py`]
- [Source: `tests/unit/test_app.py`]
- [Source: `tests/unit/test_deploy.py`]
- [Source: https://docs.aws.amazon.com/bedrock/latest/userguide/models-api-compatibility.html]
- [Source: https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html]
- [Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/]
- [Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/custom_model_provider/]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- Story context created from BMAD create-story workflow on 2026-05-15.
- Discovery loaded whole planning artifacts: PRD, architecture, epics, and multi-provider research.
- No UX artifact found.
- `.env.example` required no changes — already satisfied all Task 3 subtasks from Story 4.4 work.
- `test_static.py` `_verification_section()` helper initially split on raw `---` which matched table header separators; fixed to split on `## Make Targets` heading instead.
- Live smoke tests not run: no `MOONSHOT_API_KEY`, `GOOGLE_API_KEY`, or `strands-agents[litellm]` provisioned. Skipped per story Dev Notes guidance.

### Completion Notes List

- README: changed `🔜 Epic 4.5` to `🔜 Planned — not yet enabled` in the support matrix table; updated Epic 4 intro to past tense; added `#### Verification strategy` subsection with per-provider verification level table and deterministic pytest command; updated stale make test count from 134 to 320.
- `.env.example`: no changes required — all provider labels and planned-family wording already in final state.
- `_bmad-output/project-context.md`: extended the cross-cutting provider change rule to include verification strategy and enumerate specific files.
- `tests/unit/test_static.py`: added `TestReadmeVerificationStrategy` class (5 tests) asserting verification strategy heading, pytest command, litellm CI exclusion, deployed scope, and no Epic 4.5 delivery claim.
- 325 tests pass (320 baseline + 5 new). `make lint` clean.
- Code review follow-up: addressed 6 patch findings; full test suite now 326 tests pass, 0 failures. `make lint` clean.
- Code review 2 follow-up: restricted LITELLM_API_BASE http:// to localhost/127.x only (added 3 new tests); replaced brittle full-table snapshot with semantic assertions; updated README make test count to 329. Full suite 329 passed, 0 failures.

### File List

- README.md
- _bmad-output/project-context.md
- deploy/verify.py
- tests/unit/test_static.py
- tests/unit/test_model_adapters.py
- model_adapters.py
- _bmad-output/implementation-artifacts/sprint-status.yaml
- _bmad-output/implementation-artifacts/4-5-expansion-documentation-and-verification.md

### Change Log

- 2026-05-15: Implemented Story 4.5 documentation and verification strategy.
- 2026-05-15: Addressed code review findings — clarified Bedrock-backed deployed boundary, updated verifier hint and test count, tightened static contract coverage, and removed ambiguous Story 4.5+ future-work wording.
- 2026-05-15: Addressed code review 2 findings — restricted LITELLM_API_BASE http:// to localhost/127.x only; replaced brittle full-table snapshot test with semantic assertions; updated README test count to 329.
