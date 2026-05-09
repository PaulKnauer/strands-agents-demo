# Story 2.2: Deployed Runtime Adapter Contract

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want the deployed runtime to follow the documented Bedrock-first adapter contract,
so that the cloud path remains reliable and distinct from the local Strands path.

## Acceptance Criteria

1. **Given** the deployed runtime entrypoint is implemented
   **When** I inspect `deploy/app.py`
   **Then** it uses the deployed runtime contract rather than importing the local Strands runtime directly
   **And** it preserves the required unconditional AgentCore startup behavior

2. **Given** provider support differs between local and deployed runtimes
   **When** the deployed runtime is configured
   **Then** supported and unsupported combinations are made explicit
   **And** the implementation does not hide those boundaries with silent fallbacks

3. **Given** deployment packaging is prepared
   **When** the artifact is assembled
   **Then** it bundles the deployed runtime path and required Linux wheels
   **And** it does not package `agent.py` as the production runtime entrypoint

## Tasks / Subtasks

- [x] Task 1: Reconcile `deploy/app.py` with the Story 2.2 runtime contract (AC: #1, #2)
  - [x] Inspect `deploy/app.py` before editing; treat it as the deployed runtime adapter, not as a duplicate of `agent.py`
  - [x] Preserve direct Bedrock Converse usage through `boto3.client("bedrock-runtime", region_name=region)`
  - [x] Verify `deploy/app.py` does not import `agent.py`, `model_adapters.py`, `strands`, or `strands-agents`
  - [x] Preserve the existing age-in-days behavior: identical system prompt intent, `get_today_date` tool contract, tool-use loop, and final text response handling
  - [x] Preserve `app.run(host="0.0.0.0")` as an unconditional module-level call; do not move it behind `if __name__ == "__main__"`

- [x] Task 2: Make supported and unsupported deployed provider combinations explicit (AC: #2)
  - [x] Keep `MODEL_ID` and `AWS_REGION` explicit runtime inputs for the deployed Bedrock path
  - [x] Decide whether `MODEL_PROVIDER` should be validated inside `deploy/app.py` or only before deployment in `deploy/deploy.py`; implement the smallest clear check that prevents silent non-Bedrock deployment behavior
  - [x] If `MODEL_PROVIDER != "bedrock"` reaches the deployed runtime, fail with a clear error string or clear startup/runtime diagnostic; do not silently fall back to Bedrock defaults
  - [x] Do not add Gemini or other provider support to `deploy/app.py` in this story; Epic 4 owns broader provider rollout
  - [x] Update README and/or `.env.example` only if current wording implies non-Bedrock AgentCore support

- [x] Task 3: Preserve prompt, tool, guardrail, and safety boundaries (AC: #1, #2)
  - [x] Keep `SYSTEM_PROMPT` behavior aligned with `agent.py`; if text changes, update prompt parity tests and promptfoo config as required
  - [x] Keep `TOOLS` as a single `get_today_date` Converse tool unless a deliberate risk-register update is made
  - [x] Preserve `MAX_TURNS = 10` and `MAX_PROMPT_CHARS = 4000` unless docs/risk-register and tests are updated
  - [x] Preserve optional Bedrock Guardrails wiring: include `guardrailConfig` only when `GUARDRAIL_ID` is set and default `GUARDRAIL_VERSION` to `DRAFT`
  - [x] Keep tool helpers returning useful strings instead of raising for recoverable tool failures

- [x] Task 4: Verify deployment artifact boundaries (AC: #3)
  - [x] Inspect `deploy/deploy.py` before editing; preserve the five-step deployment flow from Story 2.1
  - [x] Confirm `_build_deployment_zip()` packages `deploy/app.py` as `app.py` and does not package `agent.py`
  - [x] Confirm Linux wheel bundling still uses manylinux/cp312 and `--only-binary :all:` for `bedrock-agentcore`
  - [x] Confirm `_build_artifact()` keeps `runtime: "PYTHON_3_12"` and `entryPoint: ["app.py"]`
  - [x] Do not change IAM, S3, endpoint URL, or idempotency behavior unless a concrete defect blocks this story

- [x] Task 5: Add or tighten focused tests for the deployed runtime contract (AC: #1, #2, #3)
  - [x] Add static/unit coverage that `deploy/app.py` does not import local Strands runtime modules
  - [x] Add unit coverage for deployed provider boundary behavior, especially `MODEL_PROVIDER=gemini` or unknown provider
  - [x] Preserve existing tests for Converse message sequence, tool result injection, guardrail propagation, empty/oversized prompt rejection, and fallback response handling
  - [x] Preserve deployment artifact tests in `tests/unit/test_deploy.py` for `app.py` entrypoint, Python runtime, and no `agent.py` production entrypoint
  - [x] Keep mock-only tests named as unit tests; do not relabel them as integration tests

- [x] Task 6: Run deterministic validation and record live-validation status (AC: #1, #2, #3)
  - [x] Run `venv/bin/black --check deploy/app.py deploy/deploy.py tests/unit/test_app.py tests/unit/test_deploy.py tests/unit/test_static.py`
  - [x] Run `venv/bin/python -m pytest tests/unit/test_app.py`
  - [x] Run `venv/bin/python -m pytest tests/unit/test_deploy.py`
  - [x] Run `venv/bin/python -m pytest tests/unit/test_static.py tests/unit/test_safety_boundaries.py tests/unit/test_agent_loop.py`
  - [x] Run full regression suite with `venv/bin/python -m pytest`
  - [x] If live AWS credentials are available and deployment config is valid, run `python deploy/deploy.py` only if needed to confirm runtime startup; otherwise state plainly that live AgentCore validation was not performed

### Review Findings

- [x] [Review][Patch] Do not default missing deployed `MODEL_PROVIDER` to Bedrock [deploy/app.py:125]
- [x] [Review][Patch] Strengthen deployed import-isolation tests to parse imports structurally [tests/unit/test_static.py:255]

## Dev Notes

### Story Intent

This is a deployed-runtime contract story, not a new provider story and not endpoint verification. Story 2.1 established that the deployment path packages `deploy/app.py`, Linux wheels, and an AgentCore runtime artifact. Story 2.2 should now make the deployed runtime boundary explicit and testable: AgentCore uses a Bedrock-first direct Converse path in `deploy/app.py`, while local development uses Strands adapters through `agent.py` and `model_adapters.py`.

The likely implementation shape is brownfield reconciliation: inspect what already exists, preserve correct behavior, and add small validation/tests/docs where the current runtime contract is implicit or under-tested.

### Current State Of Files Likely To Be Modified

- `deploy/app.py`: current AgentCore cloud runtime entrypoint. It already uses direct Bedrock Converse via `boto3`, defines `SYSTEM_PROMPT`, declares a `get_today_date` Converse tool, handles client-side tool-use loops, validates empty and oversized prompts, wires optional guardrails, and calls `app.run(host="0.0.0.0")` unconditionally. This is the primary UPDATE file. [Source: deploy/app.py]
- `tests/unit/test_app.py`: already covers `_get_today_date`, `_run_agent`, tool-use loops, tool result injection, no-text fallback, guardrail propagation, and `handle_invocation` prompt guards. Extend this for provider boundary behavior if needed. [Source: tests/unit/test_app.py]
- `tests/unit/test_agent_loop.py`: verifies the exact Bedrock Converse message sequence and that `SYSTEM_PROMPT` and `TOOLS` are sent on each call. Preserve these tests and update only if the runtime contract intentionally changes. [Source: tests/unit/test_agent_loop.py]
- `tests/unit/test_safety_boundaries.py`: enforces the deployed tool surface, prompt safety boundaries, `MAX_PROMPT_CHARS`, `MAX_TURNS`, and promptfoo prompt parity. Update this only with matching risk-register/prompt changes. [Source: tests/unit/test_safety_boundaries.py]
- `tests/unit/test_deploy.py`: already includes Story 2.1 contract tests for runtime artifact shape and packaging assumptions. Use it for deployment artifact boundary checks if needed. [Source: tests/unit/test_deploy.py]
- `README.md` and `.env.example`: document local Bedrock/Gemini provider choices and AgentCore deployment. Update only if current wording hides that AgentCore deployed runtime is Bedrock-first. [Source: README.md#How It Works] [Source: .env.example]

### Files To Avoid Unless A Defect Requires Them

- `agent.py`: local Strands REPL path. Do not refactor it for Story 2.2 unless prompt/tool parity forces a tiny synchronized change. [Source: _bmad-output/project-context.md#Framework-Specific Rules]
- `model_adapters.py`: local-only adapter factory for Strands model construction. Do not import it into `deploy/app.py`. [Source: model_adapters.py]
- `deploy/deploy.py`: deployment orchestration. Inspect to verify artifact boundaries, but avoid changing IAM/S3/create-update behavior unless a concrete Story 2.2 defect is found. [Source: deploy/deploy.py]
- `requirements.txt`: do not add provider dependencies for Gemini or other model families in this story. [Source: _bmad-output/project-context.md#Provider And Model Rules]

### Current Worktree Caution

At story creation time, unrelated local changes exist in `Makefile`, `deploy/deploy.py`, `deploy/create_role.py`, `.claude/*`, and `_bmad-output/implementation-artifacts/epic-1-retro-2026-05-09.md`. The dev agent must inspect the worktree before editing and must not revert or accidentally absorb unrelated user changes.

### What Must Be Preserved

- `deploy/app.py` must not import `strands-agents`, `agent.py`, or `model_adapters.py`. The deployed runtime is intentionally direct Bedrock Converse because AgentCore startup/package constraints differ from local development. [Source: _bmad-output/project-context.md#Framework-Specific Rules]
- `app.run(host="0.0.0.0")` must remain unconditional. Guarding it behind `__main__` can make AgentCore startup health checks fail. [Source: deploy/app.py] [Source: _bmad-output/project-context.md#Framework-Specific Rules]
- `SYSTEM_PROMPT` must stay behaviorally aligned with `agent.py`; the local and deployed paths should calculate age in days the same way. [Source: tests/evals/test_prompt_parity.py] [Source: README.md#How It Works]
- The deployed tool surface is exactly one `get_today_date` tool unless the risk register and safety tests are intentionally updated. [Source: tests/unit/test_safety_boundaries.py]
- `MAX_TURNS = 10` and `MAX_PROMPT_CHARS = 4000` are safety boundaries and should not drift silently. [Source: tests/unit/test_safety_boundaries.py]
- Bedrock guardrails are optional and conditional: only send Converse `guardrailConfig` when `GUARDRAIL_ID` is set; default version is `DRAFT`. [Source: tests/unit/test_app.py]
- No custom logging should be added for observability. The demo value is that AgentCore provides managed traces without app logging code. [Source: _bmad-output/planning-artifacts/architecture.md#Observability & Monitoring]

### Architecture Compliance Guardrails

- Local path: `agent.py` uses Strands `Agent`, `@tool`, and `create_local_model_adapter()`. [Source: agent.py] [Source: model_adapters.py]
- Deployed path: `deploy/app.py` owns the runtime adapter contract and uses direct Bedrock Converse API calls via `boto3`. [Source: _bmad-output/planning-artifacts/architecture.md#Model Provider Abstraction]
- Provider support is asymmetric today: local adapters support `bedrock` and `gemini`, but the deployed AgentCore runtime path is Bedrock-first. Do not hide this difference with defaults or fallback behavior. [Source: _bmad-output/project-context.md#Provider And Model Rules]
- Deployment artifact must package `deploy/app.py` and Linux-compatible dependencies, not `agent.py` as the production entrypoint. [Source: _bmad-output/implementation-artifacts/2-1-agentcore-deployment-path.md#What Must Be Preserved]
- Story 2.3 owns endpoint verification and observability confirmation. Story 2.2 can keep tests deterministic and mock-based unless live validation is specifically needed for startup behavior. [Source: _bmad-output/planning-artifacts/epics.md#Story 2.3]

### Latest Technical Information

- AWS AgentCore direct code deployment for Python still requires a zip of code and dependencies plus an entrypoint `.py` file using `@app.entrypoint` or compatible `/invocations` and `/ping` endpoints. This supports preserving `deploy/app.py` as the runtime entrypoint. [Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-code-deploy-python.html]
- Current Boto3 Bedrock Runtime `converse()` supports `messages`, `system`, `toolConfig`, and `guardrailConfig`; using it requires `bedrock:InvokeModel`. This matches the deployed runtime's direct Converse loop. [Source: https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-runtime/client/converse.html]
- AWS Bedrock tool-use docs describe client-side tool calling for Converse: the application supplies tool definitions, receives `toolUse`, calls the tool itself, then sends a `toolResult` message back. This matches `_run_agent()` and should remain the deployed runtime pattern. [Source: https://docs.aws.amazon.com/bedrock/latest/userguide/tool-use.html]
- Bedrock Guardrails with Converse are configured through the `guardrailConfig` input parameter with guardrail ID and version. This supports keeping current conditional guardrail wiring and tests. [Source: https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-use-converse-api.html]

### Regression Risks To Avoid

- Importing local Strands runtime code into `deploy/app.py`, which can break AgentCore startup and violates the local/cloud boundary.
- Adding a default model/provider fallback in `deploy/app.py` that makes a misconfigured deployment appear to work against the wrong model.
- Letting local Gemini support imply deployed Gemini support. That belongs to Epic 4 or a separately validated AgentCore provider story.
- Changing prompt text in one runtime without updating parity checks and promptfoo config.
- Adding custom logging for tool calls, which undermines the AgentCore-managed observability message.
- Modifying deployment packaging in a way that reintroduces `agent.py` into the production runtime or removes Linux wheel bundling.

### Previous Story Intelligence

- Story 2.1 confirmed the correct deployment package shape: bundle `deploy/app.py`, not `agent.py`; install `bedrock-agentcore` and transitive dependencies as manylinux/cp312 wheels; use `PYTHON_3_12`; and set `entryPoint: ["app.py"]`. Preserve these assumptions. [Source: _bmad-output/implementation-artifacts/2-1-agentcore-deployment-path.md#Completion Notes List]
- Story 2.1 review tightened contract tests to exact resource assertions. Apply the same test-hardening mindset here: prefer exact import/package/runtime assertions over loose substring checks. [Source: _bmad-output/implementation-artifacts/2-1-agentcore-deployment-path.md#Review Findings]
- Story 1.3 established explicit local provider support and no silent fallback for unsupported providers. Reuse that principle for deployed runtime provider boundaries. [Source: tests/unit/test_model_adapters.py]
- Story 1.4 and Story 2.1 both used brownfield reconciliation successfully: preserve working implementation, patch only genuine gaps, and make evidence explicit. [Source: _bmad-output/implementation-artifacts/2-1-agentcore-deployment-path.md#Previous Story Intelligence]

### Git Intelligence

- `a182ab7` - Complete Story 2.1 review follow-up. Relevant because it added the active Story 2.1 artifact, marked Story 2.1 done, and tightened deployment contract tests.
- `56176d8` - Complete Story 1.4 VS Code debug experience. Relevant as another brownfield reconciliation/test-hardening pattern.
- `c29607d` - Add adapter-based local model selection. Relevant because it created the local adapter boundary that Story 2.2 must not import into AgentCore runtime.
- `5fc1cea` - Add Story 1.2 review artifacts. Background for prompt/tool behavior and review discipline.
- `634b5b9` - Update planning artifacts and add implementation readiness report. Background only.

### Project Structure Notes

- Expected UPDATE files:
  - `deploy/app.py`
  - `tests/unit/test_app.py`
  - `tests/unit/test_agent_loop.py`
  - `tests/unit/test_safety_boundaries.py`
  - `tests/unit/test_static.py`
  - `tests/unit/test_deploy.py`
  - `README.md` and/or `.env.example` only if docs need clearer deployed-provider boundaries
- Expected INSPECT-only files:
  - `agent.py`
  - `model_adapters.py`
  - `deploy/deploy.py`
  - `requirements.txt`
  - `Makefile`
- Do not create a new runtime adapter module unless it removes real duplication and keeps the cloud runtime simple. A simple explicit guard/check in `deploy/app.py` may be enough.

### Testing Requirements

- Deterministic unit/static checks:
  - `venv/bin/black --check deploy/app.py deploy/deploy.py tests/unit/test_app.py tests/unit/test_deploy.py tests/unit/test_static.py`
  - `venv/bin/python -m pytest tests/unit/test_app.py`
  - `venv/bin/python -m pytest tests/unit/test_agent_loop.py`
  - `venv/bin/python -m pytest tests/unit/test_safety_boundaries.py`
  - `venv/bin/python -m pytest tests/unit/test_deploy.py`
  - `venv/bin/python -m pytest tests/unit/test_static.py`
  - `venv/bin/python -m pytest`
- If `README.md`, `.env.example`, or prompt/config files change, run the relevant static/parity tests that assert documentation and prompt contracts.
- If live AgentCore validation is not run, state that explicitly in Dev Agent Record. Do not claim Story 2.2 was proven live unless `deploy/app.py` was actually packaged/deployed and reached READY.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.2]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.3]
- [Source: _bmad-output/planning-artifacts/prd.md#AgentCore Deployment]
- [Source: _bmad-output/planning-artifacts/prd.md#Non-Functional Requirements]
- [Source: _bmad-output/planning-artifacts/architecture.md#Model Provider Abstraction]
- [Source: _bmad-output/planning-artifacts/architecture.md#Architectural Boundaries]
- [Source: _bmad-output/planning-artifacts/architecture.md#Observability & Monitoring]
- [Source: _bmad-output/project-context.md#Framework-Specific Rules]
- [Source: _bmad-output/project-context.md#Provider And Model Rules]
- [Source: _bmad-output/project-context.md#Testing Rules]
- [Source: _bmad-output/implementation-artifacts/2-1-agentcore-deployment-path.md]
- [Source: agent.py]
- [Source: model_adapters.py]
- [Source: deploy/app.py]
- [Source: deploy/deploy.py]
- [Source: tests/unit/test_app.py]
- [Source: tests/unit/test_agent_loop.py]
- [Source: tests/unit/test_safety_boundaries.py]
- [Source: tests/unit/test_deploy.py]
- [Source: tests/unit/test_model_adapters.py]
- [Source: README.md#How It Works]
- [Source: .env.example]
- [Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-code-deploy-python.html]
- [Source: https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-runtime/client/converse.html]
- [Source: https://docs.aws.amazon.com/bedrock/latest/userguide/tool-use.html]
- [Source: https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-use-converse-api.html]

## Change Log

- 2026-05-09: Ultimate context engine analysis completed - comprehensive developer guide created.
- 2026-05-09: Story 2.2 implementation — brownfield reconciliation of deployed runtime adapter contract. Added MODEL_PROVIDER boundary validation to deploy/app.py (runtime) and deploy/deploy.py (deployment). Tightened test coverage with TestDeployAppImports (static import isolation), provider boundary tests in TestHandleInvocation, and non-bedrock provider test in TestMainEnvValidation. Updated README and .env.example to clarify AgentCore requires bedrock provider. All 184 tests pass.

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

No blockers encountered. Brownfield reconciliation as anticipated — deploy/app.py already satisfied Tasks 1, 3, and 4 contracts. Primary implementation work was Task 2 (provider boundary) and Task 5 (test hardening).

### Completion Notes List

- Task 1: deploy/app.py already satisfies the Story 2.2 contract. Uses boto3 directly via `boto3.client("bedrock-runtime")`, no strands imports, SYSTEM_PROMPT identical to agent.py, app.run(host="0.0.0.0") unconditional. No code changes required.
- Task 2: Added MODEL_PROVIDER validation in two complementary locations: (1) deploy/app.py handle_invocation — returns clear error string if MODEL_PROVIDER != "bedrock", following existing error-string pattern; (2) deploy/deploy.py main() — fails with sys.exit(1) and clear message before deploying a misconfigured runtime. Updated misleading Gemini comment in deploy/deploy.py. Updated README "Model provider switching" section to note it's local-only. Added note to .env.example AgentCore Deployment section that bedrock is required.
- Task 3: All boundaries verified preserved — SYSTEM_PROMPT parity confirmed (identical text), TOOLS has exactly one get_today_date entry, MAX_TURNS=10 and MAX_PROMPT_CHARS=4000 unchanged, guardrail wiring conditional on GUARDRAIL_ID, tool helper returns string not raise.
- Task 4: Artifact boundaries verified — _build_deployment_zip packages deploy/app.py as app.py (not agent.py), manylinux2014_x86_64 + cp312 + --only-binary :all: preserved, _build_artifact has PYTHON_3_12 and entryPoint: ["app.py"]. No changes to IAM/S3/endpoint/idempotency logic.
- Task 5: Added TestDeployAppImports class to test_static.py (4 tests: no strands import, no agent import, no model_adapters import, has bedrock_agentcore and boto3). Added 2 provider boundary tests to TestHandleInvocation in test_app.py (gemini and unknown provider). Added 1 provider validation test to TestMainEnvValidation in test_deploy.py.
- Task 6: black --check passes on all 5 target files. All individual test suites pass. Full regression suite: 184 passed, 0 failed. Live AgentCore validation not performed — no live AWS credentials/deployment required for this deterministic contract story. Story 2.3 owns endpoint verification and live validation.

### File List

- deploy/app.py (modified — added MODEL_PROVIDER boundary check in handle_invocation)
- deploy/deploy.py (modified — added MODEL_PROVIDER validation in main(), fixed misleading Gemini comment)
- tests/unit/test_app.py (modified — added test_non_bedrock_provider_returns_error, test_unknown_provider_returns_error)
- tests/unit/test_deploy.py (modified — added test_non_bedrock_model_provider_exits_1)
- tests/unit/test_static.py (modified — added TestDeployAppImports class with 4 tests)
- README.md (modified — clarified model provider switching is local-only, added AgentCore bedrock-only note)
- .env.example (modified — added bedrock-required note in AgentCore Deployment section)
