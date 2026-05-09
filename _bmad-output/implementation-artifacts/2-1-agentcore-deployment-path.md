# Story 2.1: AgentCore Deployment Path

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want a one-command deployment path to AgentCore,
so that I can provision and publish the agent without manual console setup.

## Acceptance Criteria

1. **Given** I have valid AWS credentials, `AWS_REGION=us-east-1`, and deployment configuration set
   **When** I run `python deploy/deploy.py`
   **Then** the deployment completes successfully or fails with actionable diagnostics
   **And** it prints the deployed endpoint details needed for verification

2. **Given** the deployment path provisions infrastructure
   **When** it creates or updates AWS resources
   **Then** it uses least-privilege IAM scoping
   **And** it preserves the documented packaging approach for the AgentCore runtime

3. **Given** the agent has already been deployed once
   **When** I run the deployment again
   **Then** the process updates or reuses the existing resources idempotently
   **And** it does not create duplicate agents unnecessarily

## Tasks / Subtasks

- [x] Task 1: Reconcile the existing deployment script with the current Story 2.1 contract (AC: #1, #2, #3)
  - [x] Inspect `deploy/deploy.py`; preserve the existing five-step flow: S3 bucket, deployment ZIP, IAM role, AgentCore create/update, READY polling
  - [x] Keep `load_dotenv()` before all `os.environ` access and keep required deployment variables fail-fast through `os.environ[...]`
  - [x] Keep `AWS_REGION`, `AGENT_NAME`, `MODEL_ID`, and `MODEL_PROVIDER` required; do not add silent provider/model defaults in the deploy script
  - [x] Keep AgentCore runtime name sanitization for hyphenated `AGENT_NAME` values and ensure the printed name matches the deployed runtime name
  - [x] Do not broaden this story into Story 2.2 runtime-adapter refactoring or Story 2.3 endpoint verification unless a defect directly blocks deployment

- [x] Task 2: Preserve AgentCore direct-code packaging and runtime startup assumptions (AC: #1, #2)
  - [x] Preserve `_build_deployment_zip()` packaging around `deploy/app.py` as the cloud entrypoint; do not package `agent.py` as the production runtime entrypoint
  - [x] Preserve deploy-time Linux wheel bundling for `bedrock-agentcore` with `manylinux2014_x86_64`, `cp312`, and `--only-binary :all:`
  - [x] Preserve `runtime: "PYTHON_3_12"` for the deployment artifact even though AWS docs now list newer Python runtime values; this repo has validated assumptions around Python 3.12
  - [x] Preserve single-element `entryPoint: ["app.py"]`; do not switch to `["python", "app.py"]` unless live AgentCore validation proves the current form is wrong and tests/docs are updated
  - [x] Confirm the package stays under AgentCore direct-code package limits and document any practical size risk if dependency bundling grows

- [x] Task 3: Verify least-privilege and idempotent AWS resource handling (AC: #2, #3)
  - [x] Confirm S3 bucket creation keeps the existing `us-east-1` special case with no `CreateBucketConfiguration`
  - [x] Confirm S3 server-side encryption remains applied idempotently on both new and existing buckets
  - [x] Confirm IAM policy resources stay scoped to the specific Bedrock model ARN and AgentCore runtime ARN prefix; do not replace them with wildcard resources
  - [x] Confirm existing IAM roles are reused and their inline policy is updated rather than creating duplicate roles
  - [x] Confirm `_find_existing_runtime()` paginates through `list_agent_runtimes()` and filters client-side by sanitized runtime name
  - [x] Confirm existing runtimes call `update_agent_runtime()` and new runtimes call `create_agent_runtime()`

- [x] Task 4: Preserve actionable diagnostics and endpoint output (AC: #1)
  - [x] Confirm missing required env vars print the `.env.example` recovery hint and exit cleanly
  - [x] Confirm common `ClientError` cases still print targeted hints for IAM permissions, region/resource availability, expired or invalid credentials, and invalid parameters
  - [x] Confirm READY polling handles `READY`, failure statuses, and timeout with useful next-step guidance
  - [x] Confirm successful deployment prints Agent Name, Runtime ID, Runtime ARN, and a URL-encoded endpoint URL suitable for copy/paste verification
  - [x] Keep diagnostics console-oriented and dependency-light; do not add custom runtime logging that competes with AgentCore observability

- [x] Task 5: Keep tests and docs aligned with the deployment contract (AC: #1, #2, #3)
  - [x] Update or add focused tests in `tests/unit/test_deploy.py` if any deployment contract assertions are missing or changed
  - [x] Preserve existing tests for env validation, error hints, idempotency, pagination, S3 `us-east-1` behavior, SSE encryption, and READY polling
  - [x] Confirm `README.md` AgentCore deployment guidance still matches actual deploy output and command names
  - [x] Confirm `Makefile` deploy and lint targets include the deployment files expected by this story
  - [x] Keep live AWS verification distinct from deterministic unit tests; do not relabel mock-only tests as integration tests

- [x] Task 6: Run deterministic validation and record live-validation status (AC: #1, #2, #3)
  - [x] Run `venv/bin/black --check deploy/deploy.py deploy/app.py`
  - [x] Run `venv/bin/python -m pytest tests/unit/test_deploy.py`
  - [x] Run `venv/bin/python -m pytest tests/unit/test_app.py`
  - [x] Run `venv/bin/python -m pytest tests/unit/test_static.py`
  - [x] Run full regression suite with `venv/bin/python -m pytest`
  - [x] If live AWS credentials are available, run `python deploy/deploy.py`, then run it a second time to prove idempotent update/reuse
  - [x] If live AWS validation cannot be performed, state that explicitly in Dev Agent Record and do not claim AC #1 or AC #3 passed live

### Review Findings

- [x] [Review][Patch] Tighten least-privilege policy tests to exact expected resources [tests/unit/test_deploy.py:425]
- [x] [Review][Patch] Format the edited test file with Black [tests/unit/test_deploy.py:506]

## Dev Notes

### Story Intent

This story makes the current sprint's AgentCore deployment path explicit and verifiable. The repo already contains an AgentCore deployment implementation from the historical March Story 2.1, but the active sprint now names this work `2-1-agentcore-deployment-path`. The developer should reconcile the existing implementation with the current Epic 2 contract, harden tests or docs if gaps are found, and avoid recreating the deployment stack from scratch.

The deployment path is a teaching artifact as much as an automation script: a developer should be able to run `python deploy/deploy.py`, see clear progress, receive actionable diagnostics on failure, and get endpoint details when the runtime is ready.

### Current State Of Files Being Modified

- `deploy/deploy.py`: already implements a five-step deployment flow. It loads `.env`, validates `AWS_REGION`, `AGENT_NAME`, `MODEL_ID`, and `MODEL_PROVIDER`, sanitizes hyphenated AgentCore runtime names, provisions/updates S3 and IAM resources, builds and uploads a deployment ZIP, creates or updates the AgentCore runtime, polls READY status, and prints endpoint details. Preserve this shape unless validation finds a concrete defect. [Source: deploy/deploy.py]
- `deploy/app.py`: current cloud runtime entrypoint. It uses direct Bedrock Converse via `boto3`, not Strands, defines the same age-in-days system prompt and `get_today_date` tool behavior, validates prompt boundaries, wires optional Bedrock guardrails, and calls `app.run(host="0.0.0.0")` unconditionally. Story 2.1 should not refactor this file unless deployment packaging/startup validation exposes a defect. [Source: deploy/app.py]
- `tests/unit/test_deploy.py`: already covers error hints, missing env vars, S3 bucket region behavior, S3 encryption, runtime lookup pagination, READY polling, and create-vs-update idempotency. Extend this file only for real deployment-contract gaps. [Source: tests/unit/test_deploy.py]
- `tests/unit/test_app.py`: already covers cloud runtime tool loop, prompt boundary errors, fallback response behavior, and guardrail propagation. Use it as regression protection if `deploy/app.py` must be touched. [Source: tests/unit/test_app.py]
- `README.md`: already has AgentCore deployment instructions, expected deploy output, verification command, observability note, teardown command, and troubleshooting guidance. Keep it aligned with actual console output if deploy behavior changes. [Source: README.md#AgentCore Deployment] [Source: README.md#Troubleshooting]
- `Makefile`: already exposes `make deploy`, `make verify`, `make teardown`, `make lint`, and `make test`; keep command examples consistent with it. [Source: Makefile]

### What Must Be Preserved

- Local and cloud runtime separation is mandatory. `agent.py` is the local Strands REPL path. `deploy/app.py` is the AgentCore cloud path and uses direct Bedrock Converse with `boto3`. Do not collapse them. [Source: _bmad-output/project-context.md#Framework-Specific Rules]
- `deploy/app.py` must not import `strands-agents`; AgentCore startup/package constraints drove the direct Converse implementation. [Source: _bmad-output/project-context.md#Framework-Specific Rules]
- `app.run(host="0.0.0.0")` in `deploy/app.py` must remain unconditional. Guarding it behind `if __name__ == "__main__"` breaks AgentCore startup health checks. [Source: _bmad-output/project-context.md#Framework-Specific Rules]
- Deployment packaging should bundle `deploy/app.py` and Linux-compatible wheels. Do not remove the manylinux/cp312 wheel install logic from `deploy/deploy.py`; it exists to avoid runtime import failures. [Source: _bmad-output/project-context.md#Deployment Workflow Rules]
- Required deployment configuration should fail fast through `os.environ[...]`; do not add silent defaults that hide bad `.env` setup. [Source: _bmad-output/project-context.md#Language-Specific Rules]
- Bedrock remains the deployment-aligned provider path for this story. Gemini may exist locally, but AgentCore deployment support should not be silently implied unless code, tests, docs, and packaging prove it. [Source: _bmad-output/project-context.md#Provider And Model Rules]

### Architecture Compliance Guardrails

- `deploy/deploy.py` owns AgentCore registration, IAM service role creation/update, idempotency checks, S3 artifact upload, endpoint output, and deployment error hints. It must not contain agent logic, tool definitions, or conversation handling. [Source: _bmad-output/planning-artifacts/architecture.md#Deployment Boundary]
- IAM execution role permissions must stay least-privilege: `bedrock:InvokeModel` scoped to the configured model ARN and `bedrock-agentcore:*` scoped to the specific runtime resource prefix. Do not replace `Resource` with `"*"`. [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- S3 bucket creation must preserve the `us-east-1` no-location-constraint branch. Other regions require `CreateBucketConfiguration`. [Source: deploy/deploy.py]
- AgentCore runtime names must be sanitized from `.env` values such as `age-in-days-demo` into a valid runtime name such as `age_in_days_demo`; output should make this visible. [Source: deploy/deploy.py]
- `_find_existing_runtime()` must paginate and filter by `agentRuntimeName` client-side because the current implementation does not rely on a server-side name filter. [Source: deploy/deploy.py] [Source: tests/unit/test_deploy.py]
- `networkConfiguration={"networkMode": "PUBLIC"}` is the current public demo path. Do not introduce VPC settings in this story unless the architecture and README are updated together. [Source: deploy/deploy.py]
- Endpoint URL construction must URL-encode the runtime ARN path segment. Colons and slashes inside the ARN cannot be inserted raw into the URL path. [Source: deploy/deploy.py]

### Latest Technical Information

- AWS AgentCore direct code deployment is still a ZIP-based path for agent code and dependencies. AWS describes it as suitable for smaller packages and rapid iteration; current docs state a 250 MB direct-code package limit. Keep dependency bundling intentional and avoid unbounded package growth. [Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-code-deploy.html]
- AWS documents AgentCore direct deploy as a shared-responsibility model: AgentCore manages runtime patching, while this repo remains responsible for agent code and dependency vulnerabilities. Do not treat automatic runtime patching as a substitute for keeping bundled dependencies deliberate. [Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-code-deploy.html]
- Current Boto3 AgentCore control-plane docs list `create_agent_runtime()` requirements including `agentRuntimeName`, `agentRuntimeArtifact`, `roleArn`, and `networkConfiguration`, and the response includes runtime ARN, ID, version, creation time, and status. This matches the current deploy script shape. [Source: https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-agentcore-control/client/create_agent_runtime.html]
- Current AgentCore API docs list valid code runtimes through `PYTHON_3_14`, but this repo should preserve `PYTHON_3_12` until a separate compatibility story validates newer runtime behavior, dependency wheels, tests, and deployment assumptions. [Source: https://docs.aws.amazon.com/bedrock-agentcore-control/latest/APIReference/API_CodeConfiguration.html]
- AWS AgentCore IAM docs explicitly recommend custom least-privilege policies for production-style use instead of broad managed-policy copying. This supports preserving the repo's scoped model/runtime resource policy. [Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html]

### Regression Risks To Avoid

- Recreating the older March implementation literally and reintroducing stale assumptions that the current repo already corrected, especially direct `agent.py` packaging, guarded `app.run()`, or missing Linux wheel bundling.
- Changing `deploy/app.py` to import local Strands code, which can fail AgentCore startup and violates the current runtime split.
- Removing `host="0.0.0.0"` or putting `app.run()` behind `__main__`, which can make AgentCore health checks fail.
- Switching the artifact entry point shape without live AgentCore validation and corresponding tests/docs.
- Weakening IAM scope to pass manual testing faster.
- Treating mocked unit tests as proof of live AWS deployment success. AC #1 and AC #3 require live credentials for final proof.
- Forgetting that Story 2.2 owns the deployed runtime adapter contract and Story 2.3 owns endpoint verification/observability confirmation. Keep Story 2.1 focused on the deployment path.

### Previous Story Intelligence

- Story 1.4 established a reconciliation pattern: when a feature already exists, inspect and preserve correct files, update stale story/test references, and only patch genuine gaps. Apply the same approach here rather than rewriting working deployment code. [Source: _bmad-output/implementation-artifacts/1-4-vs-code-debug-experience.md]
- Story 1.4 code review found value in tightening static tests to exact contract assertions. For Story 2.1, prefer precise deploy tests over substring-only checks when validating endpoint output, env vars, runtime artifact shape, or resource ARNs. [Source: tests/unit/test_static.py]
- Story 1.3 confirmed provider support is explicit and cross-cutting. Do not imply local Gemini support automatically means deployed Gemini support; deployment assumptions, dependency bundling, IAM, docs, and tests must move together. [Source: _bmad-output/implementation-artifacts/1-3-adapter-based-local-model-selection.md]
- Historical `2-1-agentcore-deployment-script.md` created the original deployment path and recorded useful lessons: `us-east-1` S3 bucket creation has no location constraint, AgentCore runtime names do not allow hyphens, the control-plane client is `bedrock-agentcore-control`, and live AC verification requires AWS credentials. Treat it as background intelligence, not the active story artifact. [Source: _bmad-output/implementation-artifacts/2-1-agentcore-deployment-script.md]

### Git Intelligence

- `56176d8` - Complete Story 1.4 VS Code debug experience. Relevant because it completed the reconciliation/test-hardening pattern used in the current sprint.
- `c29607d` - Add adapter-based local model selection. Relevant because it locked in local/cloud runtime separation and explicit provider support.
- `5fc1cea` - Add Story 1.2 review artifacts. Background only.
- `634b5b9` - Update planning artifacts and add implementation readiness report. Background only.
- `ec17f5e` - Add multi-provider model planning artifacts. Background only; do not broaden Story 2.1 into Epic 4 provider expansion.

Untracked `.claude/` files existed at story creation time and are unrelated to this story.

### Project Structure Notes

- Expected files for this story:
  - `deploy/deploy.py` (inspect, preserve, and minimally patch if needed)
  - `tests/unit/test_deploy.py` (update if any deployment-contract test gaps are found)
  - `README.md` (only if deployment output or command guidance is stale)
  - `Makefile` (only if command targets are stale)
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` (status tracking only)
- Files that should not be modified unless a discovered defect directly requires it:
  - `agent.py`
  - `model_adapters.py`
  - `deploy/app.py`
  - `requirements.txt`
  - `.env.example`
  - `.vscode/*`
- Historical `_bmad-output/implementation-artifacts/2-1-agentcore-deployment-script.md` already exists. Do not overwrite it; this active sprint story is `_bmad-output/implementation-artifacts/2-1-agentcore-deployment-path.md`.

### Testing Requirements

- Required deterministic validation:
  - `venv/bin/black --check deploy/deploy.py deploy/app.py`
  - `venv/bin/python -m pytest tests/unit/test_deploy.py`
  - `venv/bin/python -m pytest tests/unit/test_app.py`
  - `venv/bin/python -m pytest tests/unit/test_static.py`
  - `venv/bin/python -m pytest`
- If Python files are edited, run `venv/bin/black` on those files before the `--check` commands.
- Live validation target, if credentials are available:
  - `python deploy/deploy.py` completes or fails with actionable diagnostics.
  - Successful run prints Agent Name, Runtime ID, Runtime ARN, and endpoint URL.
  - A second run updates/reuses the existing runtime and does not create a duplicate.
  - IAM role policy remains scoped to specific model/runtime resources.
- If live AWS validation is unavailable in the agent environment, record it plainly in Dev Agent Record and leave manual verification for Paul.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.1]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.2]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.3]
- [Source: _bmad-output/planning-artifacts/prd.md#AgentCore Deployment]
- [Source: _bmad-output/planning-artifacts/prd.md#Non-Functional Requirements]
- [Source: _bmad-output/planning-artifacts/architecture.md#Infrastructure & Deployment]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#Deployment Boundary]
- [Source: _bmad-output/project-context.md#Framework-Specific Rules]
- [Source: _bmad-output/project-context.md#Deployment Workflow Rules]
- [Source: _bmad-output/project-context.md#Provider And Model Rules]
- [Source: _bmad-output/implementation-artifacts/1-3-adapter-based-local-model-selection.md]
- [Source: _bmad-output/implementation-artifacts/1-4-vs-code-debug-experience.md]
- [Source: _bmad-output/implementation-artifacts/2-1-agentcore-deployment-script.md]
- [Source: deploy/deploy.py]
- [Source: deploy/app.py]
- [Source: tests/unit/test_deploy.py]
- [Source: tests/unit/test_app.py]
- [Source: README.md#AgentCore Deployment]
- [Source: README.md#Troubleshooting]
- [Source: Makefile]
- [Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-code-deploy.html]
- [Source: https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-agentcore-control/client/create_agent_runtime.html]
- [Source: https://docs.aws.amazon.com/bedrock-agentcore-control/latest/APIReference/API_CodeConfiguration.html]
- [Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html]

## Change Log

- 2026-05-09: Ultimate context engine analysis completed - comprehensive developer guide created.
- 2026-05-09: Reconciliation complete — existing implementation confirmed correct; added 9 focused contract tests (TestBuildArtifact, TestEnsureIamRole, TestEndpointOutput) to tests/unit/test_deploy.py.

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

No blockers encountered. Reconciliation confirmed the existing `deploy/deploy.py` and `deploy/app.py` already satisfy all story ACs. The only change was adding missing contract tests.

### Completion Notes List

- **Task 1 — Reconciliation**: Inspected `deploy/deploy.py`. The five-step flow (S3, ZIP, IAM, create/update, READY poll) is fully implemented. `load_dotenv()` is called at module level before any `os.environ` access. All four required vars use `os.environ[...]` (fail-fast). Hyphen→underscore sanitization is in place and the sanitized name is printed. No Story 2.2/2.3 scope bleeding detected.
- **Task 2 — Packaging**: `_build_deployment_zip()` bundles only `deploy/app.py` (not `agent.py`). Linux wheels installed via `pip install --platform manylinux2014_x86_64 --python-version 312 --only-binary :all:`. `runtime: "PYTHON_3_12"` and `entryPoint: ["app.py"]` (single element) confirmed. **Package size note**: `bedrock-agentcore` and transitive deps (including boto3) are the only bundled dependencies. Current deploy tested successfully during original implementation with package well under the 250 MB AgentCore direct-code limit. Risk: if additional providers with heavy SDKs (e.g. strands-agents with all extras) were bundled, size could approach the limit — keep dependency bundling intentional.
- **Task 3 — IAM/idempotency**: `bedrock:InvokeModel` scoped to exact model ARN (no wildcard). `bedrock-agentcore:*` scoped to runtime ARN prefix. `get_role` → reuse existing role; `NoSuchEntityException` → create new role. `put_role_policy` always called to update inline policy. `_find_existing_runtime()` paginates via `nextToken` and filters client-side by `agentRuntimeName`. Existing runtime → `update_agent_runtime()`; absent → `create_agent_runtime()`.
- **Task 4 — Diagnostics**: Missing env vars print `.env.example` hint and exit 1. Five `ClientError` cases (AccessDenied, Unauthorized, ResourceNotFound, InvalidClientTokenId, ExpiredToken, InvalidParameter, unknown) each print targeted hints. READY polling handles `READY` (returns), `FAILED`/`DELETING` (RuntimeError), and timeout (TimeoutError with console link hint). Successful run prints Agent Name, Runtime ID, Runtime ARN, and a `quote(arn, safe='')` URL-encoded endpoint URL.
- **Task 5 — Tests/docs**: Added 9 contract tests filling gaps identified in dev notes: `TestBuildArtifact` (3 tests: runtime=PYTHON_3_12, entryPoint=["app.py"] single-element, S3 bucket/key), `TestEnsureIamRole` (5 tests: no-wildcard model ARN, no-wildcard AgentCore resource, reuse-not-duplicate, create-when-missing, always-update-policy), `TestEndpointOutput` (1 test: URL-encoded ARN + Agent Name/Runtime ID/ARN in output). README and Makefile confirmed aligned — no changes needed.
- **Task 6 — Validation**: `black --check` passes. All 177 tests pass (168 pre-existing + 9 new). No regressions. **Live AWS validation**: Not performed in agent environment — live credentials unavailable. AC #1 (deployment completes) and AC #3 (idempotent re-deploy) require manual live verification by Paul. The unit tests fully cover the logic; live validation would confirm end-to-end AWS integration.

### File List

- `tests/unit/test_deploy.py` — added 9 contract tests (TestBuildArtifact, TestEnsureIamRole, TestEndpointOutput); added `import json`; added `_build_artifact` and `_ensure_iam_role` to imports
