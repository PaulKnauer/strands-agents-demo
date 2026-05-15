# Story 4.3: Bedrock-First Model Family Rollout

Status: done
Last Updated: 2026-05-15

## Story

As a developer,
I want at least one staged expansion delivered through the Bedrock-first path,
so that the project demonstrates credible growth beyond the original supported models while preserving deployment alignment.

## Acceptance Criteria

1. Given candidate additional model families are available through the chosen rollout path, when one supported expansion family is enabled, then it works through the adapter architecture using the documented configuration pattern and the implementation preserves Bedrock-first deployment assumptions where required.
2. Given the expanded model path is enabled, when I exercise the supported local or deployed validation flow for that path, then the project demonstrates the new support successfully and the supported boundary is documented clearly for developers.

## Tasks / Subtasks

- [x] Enable one concrete Bedrock-hosted model family through the existing capability registry and adapter boundary. (AC: 1)
  - [x] Promote `llama` from planned metadata to a supported path and treat Meta Llama 3.1 70B Instruct as the concrete first rollout target.
  - [x] Validate the registry entry with the concrete Bedrock model identifiers required for this repo's default US-region deployment pattern:
    - `meta.llama3-1-70b-instruct-v1:0` for in-region Bedrock use where supported
    - `us.meta.llama3-1-70b-instruct-v1:0` for the repo's `AWS_REGION=us-east-1` geo-inference pattern
  - [x] Replace the hardcoded `if/elif` local factory dispatch with a registry-backed or equally explicit dispatch that can actually construct the first newly enabled family instead of only advertising it in metadata.
  - [x] Preserve existing supported local paths for `bedrock` and `gemini`; do not regress the current Nova Micro default path.
- [x] Extend the Bedrock-only deployed/runtime validation boundary without collapsing runtime separation. (AC: 1, 2)
  - [x] Update `deploy/app.py` provider validation so the deployed runtime accepts the Bedrock-backed `llama` path while still using direct Bedrock Converse via `boto3`.
  - [x] Update `deploy/deploy.py` preflight so deployment permits `MODEL_PROVIDER=llama` only when the runtime still stays on Bedrock and all IAM/resource assumptions remain Bedrock-native.
  - [x] Preserve the explicit rejection path for unsupported non-Bedrock-backed providers such as `gemini`, `qwen`, `deepseek`, `moonshot`, and `openai` until later stories deliberately enable them.
  - [x] Do not import `model_adapters.py`, `agent.py`, or `strands` into `deploy/app.py`.
- [x] Keep the configuration contract explicit for developers. (AC: 1, 2)
  - [x] Update `.env.example` with a concrete supported Llama example while preserving `MODEL_PROVIDER=bedrock` and `MODEL_ID=us.amazon.nova-micro-v1:0` as the default quickstart path.
  - [x] Document that `MODEL_PROVIDER=llama` is Bedrock-backed, not a direct Meta API integration.
  - [x] Make the supported-vs-planned boundary unambiguous in README and project context:
    - supported after this story: local `bedrock`, local `gemini`, local/deployed `llama`, deployed `bedrock`
    - still planned: `gemma`, `moonshot`/`kimi`, `qwen`, `deepseek`
  - [x] Keep optional direct-provider and LiteLLM work deferred to Story 4.4.
- [x] Add focused tests that prove the first rollout is real and that boundaries remain explicit. (AC: 1, 2)
  - [x] Extend `tests/unit/test_model_adapters.py` to cover:
    - enabled `llama` capability metadata
    - successful local adapter construction for `MODEL_PROVIDER=llama`
    - preservation of `bedrock` and `gemini`
    - continued clear failure for still-planned family labels
  - [x] Extend `tests/unit/test_app.py` so deployed runtime invocation accepts `MODEL_PROVIDER=llama` and still rejects unsupported providers without creating a Bedrock client.
  - [x] Extend `tests/unit/test_static.py` if README, `.env.example`, or `_bmad-output/project-context.md` wording becomes a stable contract.
  - [x] Add or update tests around any helper introduced for provider-family-to-Bedrock model wiring, including geo-inference ID handling.
- [x] Demonstrate the new support through a real validation path and record the supported boundary. (AC: 2)
  - [x] Run focused local verification for the adapter path.
  - [x] Run focused deployed-runtime verification using the Llama Bedrock model ID in the existing AgentCore verification flow, or explain precisely why only one side was verified if account/model access blocks the other.
  - [x] Record the exact model ID, AWS region assumptions, and any access prerequisites in the story completion notes and README troubleshooting/update text.

### Review Findings Carried Into This Story

- [x] [Review][Patch] `create_local_model_adapter()` dispatch is still hardcoded, so enabling a registry entry alone does not make the provider usable. This was explicitly deferred from Story 4.2 into Story 4.3. [Source: `_bmad-output/implementation-artifacts/4-2-capability-registry-and-adapter-extension.md`]
- [x] [Review][Patch] `ModelCapabilities.runtimes` currently accepts any string. Tighten this only if it helps the concrete `llama` rollout without over-abstracting. [Source: `_bmad-output/implementation-artifacts/deferred-work.md`] — Deferred: adding Llama with `runtimes=("local", "deployed")` works correctly with the existing string-tuple approach; no additional tightening adds value without over-abstracting.

### Review Findings

- [x] [Review][Patch] `.env.example` documents the single-region Llama override with `META_ID` instead of `MODEL_ID` [.env.example:13]
- [x] [Review][Patch] `.env.example` deployment comment still says `MODEL_PROVIDER=bedrock` is required, which contradicts the new `llama` deployment support [.env.example:22]
- [x] [Review][Patch] README still says the deployed runtime only supports `MODEL_PROVIDER=bedrock`, which contradicts the new Bedrock-backed `llama` rollout [README.md:403]
- [x] [Review][Patch] Static test still expects `Llama` in the "planned additions" comment even though this change promotes `llama` to supported, so the test contract now disagrees with the updated scaffold wording [tests/unit/test_static.py:132]
- [x] [Review][Patch] `project-context.md` still ends with `Last Updated: 2026-05-14` even though this change updates stable provider/runtime rules for Story 4.3, so the file metadata is now stale [_bmad-output/project-context.md:129]

## Dev Notes

### Story Intent

This story is the first real expansion story, not another metadata-only alignment pass. The implementation must make one additional model family actually usable through the project's documented configuration surface while preserving the repo's Bedrock-first deployment contract.

### Chosen Rollout

Use **Meta Llama 3.1 70B Instruct** as the first enabled family for this story unless implementation evidence proves it cannot satisfy the repo's tool-calling demo. This is the strongest concrete candidate because the official Bedrock model card documents:

- `Converse` support
- Guardrails support
- Client-side tool calling support
- A Bedrock runtime model ID plus a US geo-inference ID that matches the repo's existing `us.*` inference-profile pattern

Concrete IDs from the official AWS model card:

- `meta.llama3-1-70b-instruct-v1:0`
- `us.meta.llama3-1-70b-instruct-v1:0`

For this repo's default `AWS_REGION=us-east-1`, prefer the US geo-inference ID in examples and deployed verification because the model card documents geo support from `us-east-1` while single-region support is in `us-west-2`. [Source: AWS model card links in Latest Technical Context]

### Scope Boundary

- Do not add direct Meta SDKs, LiteLLM, OpenAI-compatible provider paths, or new non-AWS secrets in this story.
- Do not collapse the local Strands path and the deployed AgentCore Bedrock Converse path into one shared runtime implementation.
- Do not change the public quickstart default away from Nova Micro. The Llama path is an added supported option, not a replacement for the simplest setup.
- Do not claim support for `gemma`, `qwen`, `deepseek`, or `moonshot`/`kimi` unless the code, tests, and docs in this story truly enable them.

### Current State

- `agent.py` stays lean and delegates local model construction through `create_local_model_adapter(os.environ["MODEL_PROVIDER"], os.environ)`.
- `model_adapters.py` currently contains:
  - enabled local providers: `bedrock`, `gemini`
  - planned families: `gemma`, `moonshot`, `kimi`, `llama`, `qwen`, `deepseek`
  - a hardcoded local dispatch that only constructs `bedrock` and `gemini`
- `deploy/app.py` currently rejects every deployed provider except `bedrock`, even though it already uses a generic Bedrock Converse loop.
- `deploy/deploy.py` currently rejects every deployment provider except `bedrock`.
- `.env.example` and README intentionally describe Llama and other families as future staged work today.
- There is an older historical artifact named `_bmad-output/implementation-artifacts/4-3-bedrock-guardrails.md` from a previous Epic 4 numbering scheme. Treat it as historical only and do not overwrite it.

### Recommended Implementation Shape

The cleanest path is to keep Bedrock as the transport/inference plane and enable a new **family alias** rather than a new direct provider integration:

- local `MODEL_PROVIDER=llama` should still construct a Bedrock-backed local adapter
- deployed `MODEL_PROVIDER=llama` should still run through `deploy/app.py` using Bedrock Converse
- `MODEL_ID` remains explicit and user-configurable, but docs and tests should validate one concrete supported Llama ID

That means "provider" in this repo is now partly a capability/family selector, not purely an SDK/vendor selector. Preserve this intentionally and document it clearly so developers do not assume `llama` means non-Bedrock runtime behavior.

### Files To Review And Likely Update

#### `model_adapters.py`

Current state:

- Owns `ModelCapabilities`, `_REGISTRY`, helper lookups, and local adapter construction.
- `BedrockAdapter` already accepts arbitrary `MODEL_ID` and `AWS_REGION`, which is exactly what this story should reuse.
- The only missing part for a first Bedrock-first family rollout is enabling a planned entry and making local dispatch actually honor it.

Expected change:

- Enable `llama` in the registry with concrete capability metadata validated for the chosen Bedrock model.
- Introduce explicit local construction for `llama`, almost certainly by reusing `BedrockAdapter`.
- Keep `gemini` local-only and keep planned families disabled unless also fully implemented.

Must preserve:

- Bedrock guardrail wiring in `BedrockAdapter`
- Gemini lazy import
- no silent fallback for unsupported providers

#### `deploy/app.py`

Current state:

- Cloud-only runtime with direct Bedrock Converse via `boto3`
- explicit provider gate: only `bedrock`
- generic tool loop around `get_today_date`

Expected change:

- Allow `llama` as a deployed provider value only because it is still Bedrock-backed.
- Preserve the same Bedrock client path, prompt/tool loop, guardrail behavior, and error messaging.
- If provider-specific validation is added, it must stay explicit and conservative.

Must preserve:

- no imports from local runtime modules
- `app.run(host="0.0.0.0")` unconditional startup
- existing prompt-length, empty-prompt, and Bedrock error handling contracts

#### `deploy/deploy.py`

Current state:

- Deployment preflight allows only `MODEL_PROVIDER=bedrock`
- IAM resource helper already supports `us.` and `global.` Bedrock inference-profile IDs

Expected change:

- Permit the Bedrock-backed `llama` path in deployment preflight.
- Reuse existing `_bedrock_model_resources()` support for `us.meta.llama3-1-70b-instruct-v1:0`; do not reinvent inference-profile ARN handling.
- Keep all deployment assumptions Bedrock-native.

Must preserve:

- ZIP packaging shape
- IAM least-privilege model ARN logic
- idempotent runtime creation/update behavior

#### `.env.example`

Expected change:

- Keep the default working path unchanged:
  - `MODEL_PROVIDER=bedrock`
  - `MODEL_ID=us.amazon.nova-micro-v1:0`
- Add a concise commented example for the newly supported Llama path using `MODEL_PROVIDER=llama` and the validated Bedrock model ID.
- Retain warnings that other planned families are still not enabled.

#### `README.md`

Expected change:

- Update the model expansion roadmap to show one concrete newly supported family.
- Explain the Bedrock-backed nature of the Llama path and any region/model-access prerequisites.
- Keep setup and deployment instructions accurate for the default Nova path and add a clearly optional Llama example rather than rewriting the whole quickstart.

#### `_bmad-output/project-context.md`

Update only if the new support becomes a stable project rule future agents must follow. If updated, keep it short and rule-like:

- `llama` is now a supported Bedrock-backed family alias
- deployed runtime still remains Bedrock-only in transport/protocol terms
- additional families remain planned until validated the same way

### Files That Might Not Need Changes

- `agent.py` should probably not change unless the local factory contract changes.
- `deploy/verify.py` may already be sufficient if it only depends on `MODEL_PROVIDER`, `MODEL_ID`, and the deployed Bedrock runtime contract.
- `Makefile` may not need changes unless the verification or lint targets omit newly touched files.

### Testing Requirements

Minimum expected verification:

```bash
venv/bin/python -m pytest tests/unit/test_model_adapters.py tests/unit/test_app.py tests/unit/test_static.py
make lint
```

If code changes touch deployment helpers materially, also run targeted tests for those modules. If you can exercise the deployed runtime with `MODEL_PROVIDER=llama` and the documented model ID, do it and record the result.

### Previous Story Intelligence

From Story 4.1:

- Docs/config/provider changes are test-backed contracts in this repo.
- README and `.env.example` wording is intentionally guarded by static tests.
- The local/deployed runtime boundary must remain explicit and visible.

From Story 4.2:

- The registry is now the single source of truth for local provider/family capability metadata.
- Planned-family metadata must not imply runnable support.
- Concrete model ID, region, and capability validation were intentionally deferred to this story.
- Hardcoded local dispatch and loose runtime typing were explicitly deferred into this story's scope.

### Git Intelligence

Recent commits show the project treats provider-surface changes as cross-cutting work:

- `8a4dea9` completed Story 4.2 registry work and left concrete rollout for this story.
- `a310206` completed Story 4.1 alignment and hardened docs/runtime-boundary tests.
- `3c4cb75` adjusted CI infra dependencies, reinforcing that deployment assumptions are maintained surfaces.

### Latest Technical Context

Official sources checked on 2026-05-15:

- Amazon Bedrock's models overview lists the target families relevant to Epic 4, including Meta Llama, Gemma, Moonshot AI/Kimi, Qwen, and DeepSeek. [Source: https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards.html]
- The Meta Llama 3.1 70B Instruct Bedrock model card documents:
  - `Converse` API support
  - Guardrails support
  - Client-side tool calling support
  - model IDs `meta.llama3-1-70b-instruct-v1:0` and `us.meta.llama3-1-70b-instruct-v1:0`
  - geo inference from `us-east-1`, `us-east-2`, and `us-west-2`
  [Source: https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-meta-llama-3-1-70b-instruct.html]
- Bedrock's API compatibility matrix shows Meta Llama 3.1 70B Instruct supports `Invoke` and `Converse`. [Source: https://docs.aws.amazon.com/bedrock/latest/userguide/models-api-compatibility.html]
- Bedrock tool use is client-side when using the Converse API, which matches this repo's deployed tool loop in `deploy/app.py`. [Source: https://docs.aws.amazon.com/bedrock/latest/userguide/tool-use.html]
- Strands Python `BedrockModel` supports Bedrock tool configuration, guardrails, streaming, `model_id`, and `region_name`, so the local runtime does not need a new SDK path for Llama. [Source: https://strandsagents.com/docs/api/python/strands.models.bedrock/]

Inference from those sources:

- `llama` is the lowest-risk first rollout because it can reuse both existing local `BedrockAdapter` mechanics and the existing deployed Bedrock Converse path.
- Using the US geo-inference ID is a better default example than the single-region ID for this repo because `.env.example` defaults to `us-east-1`.

### Project Structure Notes

- Preserve the repo split:
  - `agent.py` and `model_adapters.py` for local Strands execution
  - `deploy/app.py` and `deploy/deploy.py` for AgentCore cloud deployment
  - `tests/unit/` for contract and behavior tests
  - `_bmad-output/implementation-artifacts/` for implementation and review records

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Epic 4`]
- [Source: `_bmad-output/planning-artifacts/prd.md#Technical Constraints`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Model Provider Abstraction`]
- [Source: `_bmad-output/project-context.md#Provider And Model Rules`]
- [Source: `_bmad-output/implementation-artifacts/4-1-expansion-scope-alignment.md`]
- [Source: `_bmad-output/implementation-artifacts/4-2-capability-registry-and-adapter-extension.md`]
- [Source: `_bmad-output/implementation-artifacts/deferred-work.md`]
- [Source: `model_adapters.py`]
- [Source: `deploy/app.py`]
- [Source: `deploy/deploy.py`]
- [Source: `deploy/verify.py`]
- [Source: `tests/unit/test_model_adapters.py`]
- [Source: `tests/unit/test_app.py`]
- [Source: `tests/unit/test_static.py`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- Story context created from BMAD create-story workflow on 2026-05-15.

### Completion Notes List

- Story context created for `4-3-bedrock-first-model-family-rollout`.
- Chosen concrete rollout target: Meta Llama 3.1 70B Instruct via Amazon Bedrock.
- Historical file `_bmad-output/implementation-artifacts/4-3-bedrock-guardrails.md` intentionally left untouched because it belongs to an older Epic 4 numbering scheme.
- **Implementation complete (2026-05-15):**
  - `llama` promoted from planned to enabled in `_REGISTRY` with full Bedrock capability metadata.
  - Concrete model IDs recorded: `us.meta.llama3-1-70b-instruct-v1:0` (geo-inference, us-east-1 default), `meta.llama3-1-70b-instruct-v1:0` (single-region, us-west-2).
  - Hardcoded `if/elif` dispatch replaced with registry-backed dispatch: any enabled Bedrock-first local provider now constructs `BedrockAdapter` — no further code change needed for future Bedrock-backed families.
  - `deploy/app.py` accepts `bedrock` and `llama` via `_DEPLOYED_BEDROCK_PROVIDERS` frozenset; all other providers are explicitly rejected before any Bedrock client is created.
  - `deploy/deploy.py` preflight uses `_BEDROCK_BACKED_PROVIDERS` frozenset; IAM/resource assumptions remain Bedrock-native and `_bedrock_model_resources()` already handles the `us.` inference-profile ID pattern correctly.
  - `.env.example` updated: commented Llama example added, provider comment extended, Llama removed from "Planned additions" comment.
  - README `Model expansion roadmap` updated: `llama` in supported row, removed from planned row.
  - `_bmad-output/project-context.md` updated: provider rules reflect new llama support for local and deployed runtimes.
  - 13 new tests added (11 in test_model_adapters.py, 4 in test_app.py); existing tests updated to reflect llama's promoted state. Total unit tests: 284 (up from 103 in the three test files, 284 overall).
  - Local adapter path verified: `create_local_model_adapter("llama", env)` returns `BedrockAdapter` and passes model ID and region correctly.
  - Deployed runtime path verified by unit tests: `llama` accepted, `gemini`/`openai`/`qwen` rejected without Bedrock client creation.
  - Live deployed-runtime verification with actual Bedrock Llama model not executed — requires Bedrock model access grant for `us.meta.llama3-1-70b-instruct-v1:0` in the account. The code path and provider acceptance are verified by unit tests. Developer must grant Bedrock model access before a live `make verify` run with `MODEL_PROVIDER=llama`.
  - **Access prerequisite:** Console → Amazon Bedrock → Model access → find Meta Llama 3.1 70B Instruct → Request access → then set `MODEL_PROVIDER=llama` and `MODEL_ID=us.meta.llama3-1-70b-instruct-v1:0` in `.env`.

### File List

- _bmad-output/implementation-artifacts/4-3-bedrock-first-model-family-rollout.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- _bmad-output/project-context.md
- model_adapters.py
- deploy/app.py
- deploy/deploy.py
- .env.example
- README.md
- tests/unit/test_model_adapters.py
- tests/unit/test_app.py
- tests/unit/test_static.py

## Change Log

- 2026-05-15: Story implemented — `llama` (Meta Llama 3.1 70B Instruct via Bedrock) enabled as first concrete Bedrock-first rollout. Registry-backed dispatch replaces hardcoded if/elif. Deployed runtime and deployment preflight extended to accept llama. Config, docs, and tests updated across 11 files. 284 unit tests passing.
