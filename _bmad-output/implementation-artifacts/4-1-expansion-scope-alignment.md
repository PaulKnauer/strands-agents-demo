# Story 4.1: Expansion Scope Alignment

Status: done

## Story

As a developer extending model support,
I want the planning and configuration artifacts aligned to the adapter-expansion strategy,
so that implementation starts from a coherent contract rather than mixed legacy assumptions.

## Acceptance Criteria

1. Given the project supports a Bedrock-first architecture with staged expansion, when I inspect the planning artifacts and configuration scaffolding, then they describe adapter-based provider selection consistently and distinguish initial support from future expansion targets.
2. Given `.env.example`, README, and project context reference supported model paths, when I review those artifacts, then they accurately reflect the supported local and deployed runtime boundaries and do not imply unsupported runtime symmetry.

## Tasks / Subtasks

- [x] Align the public README language with the current Epic 4 model-expansion plan. (AC: 1, 2)
  - [x] Replace the stale opening claim that "Epic 4" is the NIST AI RMF compliance layer with language that separates existing compliance artifacts from the current Epic 4 multi-provider expansion.
  - [x] Update the "What This Demonstrates" model-provider row so it does not imply broad runtime parity beyond the currently implemented local `bedrock` and `gemini` paths.
  - [x] Add a concise "Model expansion roadmap" or equivalent section explaining Bedrock-first staged expansion, future model-family targets, and direct-provider evaluation boundaries.
  - [x] Preserve existing setup, deployment, observability, NIST AI RMF, and troubleshooting guidance that remains accurate.
- [x] Align `.env.example` with supported versus planned model paths. (AC: 1, 2)
  - [x] Keep `MODEL_PROVIDER=bedrock` and `MODEL_ID=us.amazon.nova-micro-v1:0` as the default working path.
  - [x] Keep `gemini` documented as the existing optional local-only path.
  - [x] Add comments that candidate Gemma, Moonshot/Kimi, Llama, Qwen, and DeepSeek support is planned/staged, not currently enabled by setting arbitrary provider names.
  - [x] Keep the deployed runtime warning explicit: `deploy/app.py` currently requires `MODEL_PROVIDER=bedrock`.
- [x] Align `_bmad-output/project-context.md` with the current contract. (AC: 1, 2)
  - [x] Preserve the existing implementation rules for local/cloud runtime separation, fail-fast env vars, and AgentCore startup.
  - [x] Clarify that current implemented provider values are still `bedrock` and `gemini`.
  - [x] Clarify that candidate Bedrock-hosted model families and optional direct-provider/LiteLLM paths are future staged work, not supported configuration today.
  - [x] Update `Last Updated` and frontmatter date if the project convention in that file is maintained.
- [x] Check planning artifacts for visible mixed assumptions. (AC: 1)
  - [x] Review `_bmad-output/planning-artifacts/epics.md`, `prd.md`, and `architecture.md` for contradictions between initial support, future expansion, Bedrock-first deployment, and local-only Gemini.
  - [x] Only edit planning artifacts when they are materially misleading; avoid rewriting historical planning text that is already coherent.
  - [x] If planning artifacts are left unchanged, note why in the completion notes.
- [x] Update contract tests where documentation assertions become intentionally broader. (AC: 1, 2)
  - [x] Review `tests/unit/test_static.py` assertions around `.env.example` comments before changing those exact lines.
  - [x] Adjust or add tests so docs continue to assert no unsupported runtime symmetry and no silent provider fallback.
- [x] Run focused verification.
  - [x] Run `make lint` or `python -m black --check .` if available.
  - [x] Run `pytest tests/unit/test_static.py tests/unit/test_model_adapters.py`.
  - [x] Run broader tests only if implementation touches shared runtime code.

### Review Findings

- [x] [Review][Patch] Stale Epic 4 compliance claim remains [README.md:268]
- [x] [Review][Patch] New roadmap caveats are not statically guarded [tests/unit/test_static.py:114]
- [x] [Review][Patch] Verification notes omit the required `test_model_adapters.py` target [_bmad-output/implementation-artifacts/4-1-expansion-scope-alignment.md:259]
- [x] [Review][Patch] Provider `ValueError` wording overstates deployed-runtime behavior [_bmad-output/project-context.md:62]

### Review Findings (Second Pass)

- [x] [Review][Patch] Project-context provider boundary is not statically guarded [tests/unit/test_static.py:128]
- [x] [Review][Patch] README unsupported-provider wording blurs deployment preflight and runtime invocation behavior [README.md:415]
- [x] [Review][Patch] README stale-Epic regression test misses the opening claim [tests/unit/test_static.py:315]
- [x] [Review][Patch] Deployed unsupported-provider tests do not assert Bedrock is untouched [tests/unit/test_app.py:271]

## Dev Notes

### Scope Boundary

This is an alignment story, not the implementation of new model-family support.

Do not add provider runtime support, new SDK dependencies, a capability registry, LiteLLM integration, or direct-provider API clients in this story unless a test or doc update absolutely requires a small scaffold. Those belong to later Epic 4 stories:

- Story 4.2 owns capability-aware model registration and adapter extension.
- Story 4.3 owns at least one Bedrock-first model-family rollout.
- Story 4.4 owns optional direct-provider or LiteLLM evaluation boundaries.
- Story 4.5 owns expanded verification and documentation after support is added.

### Current State

The current sprint status defines this story as `4-1-expansion-scope-alignment` under "Epic 4: Multi-Provider Model Expansion". There is also an older file named `_bmad-output/implementation-artifacts/4-1-governance-foundation-documentation.md` from a March compliance-oriented story. Treat that older file as historical context only. Do not overwrite it or infer current story requirements from it.

Current implemented provider surface:

- Local path: `agent.py` calls `create_local_model_adapter(os.environ["MODEL_PROVIDER"], os.environ)`.
- Local adapter factory: `model_adapters.py` supports only `bedrock` and `gemini`; unsupported providers raise `ValueError`.
- Deployed AgentCore path: `deploy/app.py` requires `MODEL_PROVIDER=bedrock` and returns an explicit error for any other provider.
- Default model: `.env.example` and runtime fallback use `us.amazon.nova-micro-v1:0`.
- Optional Bedrock guardrails are only wired when `GUARDRAIL_ID` is set.

### Architecture Requirements

- Preserve runtime separation: `agent.py` is the local Strands REPL path; `deploy/app.py` is the AgentCore cloud path and uses direct Bedrock Converse via `boto3`.
- Do not import `strands`, `agent`, or `model_adapters` into `deploy/app.py`.
- Do not add silent defaults for required provider configuration. Unsupported providers must fail clearly.
- Any provider/model language must make the boundary explicit:
  - implemented today: local `bedrock`, local `gemini`, deployed `bedrock`;
  - planned staged expansion: Gemma, Moonshot/Kimi, Llama, Qwen, DeepSeek;
  - optional/evaluated later: direct-provider or LiteLLM-style paths where Bedrock cannot satisfy a capability need.
- Keep `.env.example` documentation-only and free of real credentials.
- Preserve existing NIST AI RMF docs and compliance features as existing project capabilities, but do not continue calling them "Epic 4" in current forward-looking docs.

### Files To Review And Likely Update

#### `README.md`

Current state:

- Lines 3-5 introduce the project and currently state that "Epic 4" is the NIST AI RMF compliance layer. That conflicts with the current sprint's Epic 4 model-expansion plan.
- Lines 13-19 describe model provider switching as Bedrock/Gemini and local/cloud fork points.
- Lines 72-74 document Gemini as optional.
- Lines 99-106 show the default env values.
- Lines 138-246 document AgentCore deployment and observability.
- The "How It Works" section includes a "Model provider switching (local only)" subsection that correctly says AgentCore uses Bedrock only.

Required change:

- Keep the accurate "local only" warning, but make the opening and summary language consistent with current Epic 4.
- Add a short, discoverable expansion roadmap so developers understand which provider paths are currently supported versus future staged targets.
- Avoid marketing broad "multi-provider" support that is not implemented yet.

Preserve:

- Setup commands, AgentCore deployment steps, observability guidance, NIST AI RMF section content, Make targets, and troubleshooting entries unless directly contradicted by this story.

#### `.env.example`

Current state:

- Lines 1-7 document `MODEL_PROVIDER=bedrock`, Bedrock Nova Micro, and Gemini.
- Lines 13-16 correctly warn that deployed runtime uses Bedrock Converse directly and requires `MODEL_PROVIDER=bedrock`.
- Lines 31-33 document optional Gemini local credentials.

Required change:

- Add comments that planned target families are not enabled by setting `MODEL_PROVIDER=gemma`, `moonshot`, `llama`, `qwen`, or `deepseek` today.
- Keep exact default values unless a later story changes runtime support.

Testing risk:

- `tests/unit/test_static.py` currently asserts exact `.env.example` comment strings for provider/model lines. Update tests alongside any intentional wording changes.

#### `_bmad-output/project-context.md`

Current state:

- Lines 59-65 already state the important provider/model rules.
- Lines 91-97 list critical rules for runtime separation, no silent defaults, prompt/tool/guardrail propagation, and test coupling.
- It was last updated on 2026-05-07.

Required change:

- Clarify the staged expansion plan without implying support exists now.
- Keep this file optimized for future AI agents: short, rule-like, and focused on non-obvious constraints.

#### `_bmad-output/planning-artifacts/epics.md`

Current state:

- Lines 155-159 define current Epic 4 as Multi-Provider Model Expansion.
- Lines 390-410 define Story 4.1 and both acceptance criteria.
- Lines 412-487 define the later Epic 4 stories and scope boundaries.

Required change:

- Likely no edit needed unless implementation finds a direct contradiction. The current epics file is the source of truth for this story and is already coherent.

#### `_bmad-output/planning-artifacts/prd.md` and `architecture.md`

Current state:

- PRD and architecture already describe Bedrock as primary, Gemini as initial local support, staged expansion toward Gemma/Moonshot/Llama/Qwen/DeepSeek, and optional direct-provider/LiteLLM paths.
- Architecture still contains older examples using an Anthropic Claude model ID in some snippets. Do not change historical examples unless they are actively misleading in current setup docs.

Required change:

- Review for contradictions. Edit only if required to satisfy AC1; otherwise record that no planning artifact edits were needed.

### Relevant Tests

- `tests/unit/test_static.py`
  - Checks `.env.example` section headers, required variables, exact comments, absence of real AWS keys, `agent.py` line count, and deployed runtime import isolation.
- `tests/unit/test_model_adapters.py`
  - Checks `bedrock` and `gemini` adapter construction and clear failure for unsupported providers.
- `tests/unit/test_app.py`
  - Relevant if any change touches deployed runtime messaging, provider validation, or Bedrock invocation behavior.

For this story, expected verification is:

```bash
pytest tests/unit/test_static.py tests/unit/test_model_adapters.py
```

If only docs and `.env.example` comments changed, broad live evals are not required. Do not run live LLM tests unless explicitly requested or needed.

### Latest Technical Context

As of 2026-05-14, official docs support the Bedrock-first direction:

- Amazon Bedrock's supported model list includes model families relevant to this expansion, including DeepSeek, Google Gemma, Meta Llama, Moonshot/Kimi, and Qwen. Use current Bedrock model IDs and region support from the official model table when later stories enable a concrete family. Source: https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html
- Bedrock model compatibility is feature-specific; not every model supports the same API operations. Later stories must check Converse, streaming, tool-use, guardrail, and region support per model instead of assuming provider-wide parity. Source: https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-supported-models-features.html
- AgentCore Runtime is model-flexible and can host agents using models in or outside Bedrock, but this repo's current deployed runtime is intentionally Bedrock-only. Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html
- AWS provides "use any foundation model" AgentCore examples for Bedrock and external providers, but adopting those examples in this repo requires deliberate runtime, secret, network, and test changes. Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/using-any-model.html
- Strands model-provider docs support multiple providers, including Bedrock and LiteLLM paths, but this repo should not add LiteLLM as an implicit default in this alignment story. Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/

### Previous Work Intelligence

Story 4.1 is the first story in the current Epic 4, so there is no previous story in this epic to inherit from.

Recent project work still matters:

- Commit `c940217` finalized Epic 3 documentation; README clarity and setup accuracy are actively maintained surfaces.
- Commit `3c4cb75` adjusted CI infra dependencies, reinforcing that docs/config changes often require test or workflow awareness.
- Epic 3 retro notes indicate documentation quality and implementation drift are recurring risks; keep this story's changes precise and test-backed.

### Implementation Guidance

- Prefer minimal, exact copy changes over broad rewrites.
- Keep support terminology consistent:
  - "supported" means code and tests work today;
  - "planned", "candidate", or "future" means Epic 4 target;
  - "optional/evaluated" means direct-provider or LiteLLM paths not yet adopted.
- When mentioning model families available through Bedrock, avoid hardcoding a long list of model IDs in README unless the later rollout story validates them. Link to official AWS docs or describe the family-level direction.
- Do not remove existing compliance docs. The project has compliance features; the conflict is the README's use of "Epic 4" for old compliance work while current sprint Epic 4 means model expansion.
- If updating tests, assert intent rather than brittle prose where possible. Exact strings are acceptable only when the copy is part of the public configuration contract.

### Project Structure Notes

This story aligns documentation and configuration scaffolding. It should not create a new runtime module. Expected touched files are limited to:

- `README.md`
- `.env.example`
- `_bmad-output/project-context.md`
- `tests/unit/test_static.py` if `.env.example` assertions need updates
- planning artifacts only if contradictions are found

No changes are expected in:

- `agent.py`
- `model_adapters.py`
- `deploy/app.py`
- `deploy/deploy.py`
- `requirements.txt`

Changing those files would be a scope escalation and should be justified in completion notes.

### References

- Source: `_bmad-output/planning-artifacts/epics.md:390`
- Source: `_bmad-output/planning-artifacts/epics.md:394`
- Source: `_bmad-output/planning-artifacts/epics.md:412`
- Source: `_bmad-output/planning-artifacts/prd.md`
- Source: `_bmad-output/planning-artifacts/architecture.md`
- Source: `_bmad-output/project-context.md:59`
- Source: `.env.example:1`
- Source: `README.md:3`
- Source: `model_adapters.py`
- Source: `deploy/app.py`
- Source: `tests/unit/test_static.py`
- Source: `tests/unit/test_model_adapters.py`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — no implementation failures or unexpected states encountered.

### Completion Notes List

- Story context created on 2026-05-14.
- Ultimate context engine analysis completed — comprehensive developer guide created.
- README.md: Removed stale Epic 4 attribution from NIST AI RMF compliance intro and section body; added Epic 4 model-expansion callout sentence; updated "What This Demonstrates" model-provider row to "(local only)"; added "Model expansion roadmap" section and ToC entry with a 3-row support/planned/optional table and explicit local/deployed unsupported-provider behavior.
- .env.example: Added two-line planned-providers comment after MODEL_ID explaining Gemma/Moonshot/Llama/Qwen/DeepSeek are staged Epic 4 work and will fail explicitly today.
- project-context.md: Clarified Provider And Model Rules — added staged expansion bullet (Stories 4.2–4.4), separated local adapter `ValueError` behavior from deployed unsupported-provider errors, updated frontmatter date and Last Updated to 2026-05-14.
- Planning artifacts review: epics.md reviewed — Epic 4 already correctly defined as Multi-Provider Model Expansion with coherent story definitions. No edits needed. prd.md and architecture.md not edited (story notes confirm they are already coherent with Bedrock-first, Gemini local-only framing).
- test_static.py: Added static contract coverage for planned-provider caveats, README roadmap runtime boundaries, and removal of the stale NIST-as-current-Epic-4 claim.
- test_static.py: Added second-pass static coverage for project-context provider boundaries and stale Epic 4 wording in the README introduction.
- test_app.py: Added assertions that missing or unsupported deployed `MODEL_PROVIDER` values return before creating a Bedrock client.
- make lint: Passes on all 9 project source files.
- pytest: `tests/unit/test_static.py`, `tests/unit/test_model_adapters.py`, and `tests/unit/test_app.py` pass.

### File List

- README.md
- .env.example
- _bmad-output/project-context.md
- tests/unit/test_app.py
- tests/unit/test_static.py
- _bmad-output/implementation-artifacts/4-1-expansion-scope-alignment.md
- _bmad-output/implementation-artifacts/sprint-status.yaml

## Change Log

- 2026-05-14: Implemented Story 4.1 — aligned README, .env.example, and project-context.md to Bedrock-first staged expansion contract; focused static/model-adapter tests pass; no planning artifact edits required.
