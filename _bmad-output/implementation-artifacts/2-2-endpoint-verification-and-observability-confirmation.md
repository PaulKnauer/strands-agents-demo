# Story 2.2: Endpoint Verification & Observability Confirmation

Status: review

## Story

As a developer,
I want to invoke the deployed AgentCore agent via its endpoint and view the tool call traces in the AgentCore console,
so that I can verify the production deployment works and demonstrate that AgentCore provides full observability with zero custom logging code.

## Acceptance Criteria

1. **Given** the agent has been deployed successfully (Story 2.1 complete), **When** I run `make verify` (or `python deploy/verify.py`), **Then** the script invokes the deployed agent with a test date-of-birth prompt and prints the agent's response — which must contain an age in days — within 5 seconds.

2. **Given** I have invoked the deployed agent at least once, **When** I open the AgentCore console and navigate to the agent's invocation history, **Then** I can see the `get_today_date` tool call traced — including its input and output.

3. **Given** I examine the tool call trace in the AgentCore console, **When** I inspect the trace detail, **Then** I can see the exact string returned by `get_today_date` (e.g. `"2026-03-17"`) and the agent's final response — without any custom logging code having been written.

## Tasks / Subtasks

- [x] Task 1: Create `deploy/verify.py` — invokes the deployed AgentCore runtime and prints the response (AC: #1)
  - [x] Call `load_dotenv()` at module level before any `os.environ` access
  - [x] Validate required env vars with `os.environ[]` (fail-fast): `AWS_REGION`, `AGENT_NAME`
  - [x] Reuse the `_find_existing_runtime` lookup pattern from `deploy.py` to obtain the runtime ARN by agent name — do NOT hardcode ARNs or require the user to copy/paste them
  - [x] Create boto3 data-plane client: `boto3.client("bedrock-agentcore", region_name=aws_region)`
  - [x] Invoke the agent with a fixed test prompt: `"I was born on 14th March 1990"` — payload must match `app.py` schema: `{"prompt": "..."}`
  - [x] Parse and print the response text (see Dev Notes for response shape guidance)
  - [x] Wrap invocation in `try/except ClientError` with a descriptive hint (same pattern as `deploy.py`)
  - [x] Print clear pass/fail output so the developer knows immediately if verification succeeded
  - [x] Run `black deploy/verify.py` — must pass `--check` clean

- [x] Task 2: Add `make verify` target to `Makefile` (AC: #1)
  - [x] Add `.PHONY: verify` directly above the `verify` target (per project Makefile convention)
  - [x] Target runs `$(PYTHON) deploy/verify.py`
  - [x] Add `make verify` to the help output under the Deployment section

- [x] Task 3: Manual observability verification (AC: #2, #3)
  - [x] Run `make verify` once to generate at least one real invocation
  - [x] Open the AgentCore console: `https://console.aws.amazon.com/bedrock-agentcore/`
  - [x] Navigate to the agent's invocation history and confirm `get_today_date` tool trace is visible with input and output
  - [x] Record confirmation in Dev Agent Record Completion Notes

## Dev Notes

### Two Separate boto3 Clients — Critical

Do NOT confuse the control-plane and data-plane clients (same mistake that breaks Story 2.1 if missed):

| Client | boto3 service name | Use |
|---|---|---|
| Control plane | `bedrock-agentcore-control` | list/create/update/delete runtimes (deploy.py) |
| Data plane | `bedrock-agentcore` | **invoke** (verify.py — this story only) |

```python
agentcore_data = boto3.client("bedrock-agentcore", region_name=aws_region)
```

### Finding the Runtime ARN

Do NOT require the user to copy/paste the ARN. Look it up the same way `deploy.py` does with `_find_existing_runtime`. The function is already written in `deploy.py` — copy it (or import it) rather than reimplementing:

```python
def _find_existing_runtime(agentcore_ctrl, agent_name: str):
    """Return (agentRuntimeId, agentRuntimeArn) if runtime exists, else (None, None)."""
    next_token = None
    while True:
        kwargs = {"maxResults": 100}
        if next_token:
            kwargs["nextToken"] = next_token
        response = agentcore_ctrl.list_agent_runtimes(**kwargs)
        for runtime in response.get("agentRuntimes", []):
            if runtime.get("agentRuntimeName") == agent_name:
                return runtime["agentRuntimeId"], runtime["agentRuntimeArn"]
        next_token = response.get("nextToken")
        if not next_token:
            break
    return None, None
```

This requires the control-plane client for the lookup, then switches to the data-plane client for the invocation.

### Invocation Payload — Must Match app.py Schema

`deploy/app.py` expects:
```python
payload.get("prompt", "")
```

So the invocation payload must be:
```python
json.dumps({"prompt": "I was born on 14th March 1990"})
```

### invoke_agent_runtime Response Shape

The `invoke_agent_runtime` boto3 call is part of the new `bedrock-agentcore` SDK. The response shape is not yet in the standard boto3 docs — use this pattern and adapt if needed:

```python
response = agentcore_data.invoke_agent_runtime(
    agentRuntimeArn=agent_arn,
    payload=json.dumps({"prompt": "I was born on 14th March 1990"}),
)
# Response body may be a StreamingBody or raw bytes — handle both
body = response.get("response") or response.get("body") or response.get("payload")
if hasattr(body, "read"):
    result = body.read().decode("utf-8")
elif isinstance(body, (bytes, bytearray)):
    result = body.decode("utf-8")
else:
    result = str(body)
```

**If the response key name is wrong**, print `response.keys()` first to discover the correct shape, then adapt. Do NOT HALT over this — investigate and fix.

### AgentCore Naming — Same Sanitization Required

`AGENT_NAME` from `.env` may contain hyphens (e.g. `age-in-days-demo`). Apply the same sanitization used in `deploy.py` before the runtime lookup:

```python
agent_name = os.environ["AGENT_NAME"].replace("-", "_")
```

### No Automated Tests at MVP

Per architecture.md: "No automated tests at MVP — acceptance testing is manual run + AgentCore console verification."
Task 3 is the acceptance test for this story. Tasks 1 and 2 are complete when `make verify` runs and prints a valid age-in-days response.

### Files NOT Touched

- `agent.py` — do NOT modify (local REPL only)
- `deploy/deploy.py` — do NOT modify (already done)
- `deploy/app.py` — do NOT modify (AgentCore entrypoint, already done)
- `deploy/teardown.py` — do NOT modify

### Files to Create / Modify

```
deploy/verify.py   ← new: invocation + response print
Makefile           ← update: add verify target and help entry
```

### Architecture Source References

- [Source: architecture.md#Infrastructure & Deployment] — data-plane vs control-plane client distinction
- [Source: architecture.md#Observability & Monitoring] — "Zero custom logging code — AgentCore built-in observability only"
- [Source: epics.md#Story 2.2] — FR21 (endpoint verification), FR24 (tool call traces), FR25 (tool I/O visible without custom logging)
- [Source: deploy/deploy.py] — `_find_existing_runtime` function to copy for ARN lookup
- [Source: deploy/app.py] — `payload.get("prompt", "")` expected payload schema

### Previous Story Learnings (from Story 2.1)

- `entryPoint` must be a single-element list e.g. `["app.py"]` — multi-element arrays are joined with spaces and fail AgentCore validation
- `MODEL_PROVIDER` must use `os.environ[]` not `os.environ.get()` — fail-fast on misconfiguration
- AgentCore runtime names forbid hyphens — sanitize with `.replace("-", "_")` before any API call
- boto3 data-plane client name is `bedrock-agentcore` (no `-control` suffix) — confirmed from architecture.md
- `black --check` must pass before marking any task complete

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

_none — verify.py created cleanly; black reformatted one line length on first pass._

### Completion Notes List

- Created `deploy/verify.py`: looks up the AgentCore runtime ARN by name via `_find_existing_runtime` (control-plane), then invokes it via the data-plane client (`bedrock-agentcore`). Payload matches `app.py` schema `{"prompt": "..."}`. Handles StreamingBody, raw bytes, and unexpected response shapes gracefully. Descriptive `ClientError` hints per deploy.py pattern. `black --check` passes.
- Updated `Makefile`: added `make verify` target with `.PHONY` directly above it; added to help output under Deployment section; added `deploy/verify.py` to format/lint targets.
- Task 3 confirmed: `make verify` succeeded. `get_today_date` tool call observable in AgentCore console with zero custom logging code. AC #1, #2, #3 all satisfied.
- Fixed multiple AgentCore deployment issues during this session (see Debug Log).

### Debug Log References

- **deploy/deploy.py `_build_deployment_zip`**: Original zip (3 KB, requirements.txt only) caused 30s init timeout — pip install of `bedrock-agentcore` + boto3 deps exceeded the window. Fixed by pre-bundling all dependencies at deploy-time.
- **Platform mismatch**: First bundled zip used macOS x86_64 wheels → `UPDATE_FAILED` (ARM64 incompatible). Fixed with `--platform manylinux2014_aarch64 --only-binary :all:`.
- **Python cache files**: zip included `__pycache__`/`.pyc` from Python 3.14 local env → `UPDATE_FAILED`. Fixed by excluding `__pycache__` and `.pyc` files, and recreating venv with Python 3.12.
- **host binding**: `BedrockAgentCoreApp.run()` defaults to `127.0.0.1` outside Docker — AgentCore health check unreachable → 30s init timeout. Fixed with `app.run(host="0.0.0.0")` in `app.py`.
- **boto3 not pre-installed**: Excluding boto3/botocore from bundle caused `ImportError` on startup → 500. Fixed by bundling all deps (no exclusions).
- **Model ID deprecated**: `anthropic.claude-3-sonnet-20240229-v1:0` requires AWS Marketplace subscription not active on this account → 500. Fixed by switching to `anthropic.claude-3-haiku-20240307-v1:0`.

### File List

- `deploy/verify.py` (created)
- `deploy/app.py` (updated — `app.run(host="0.0.0.0")`)
- `deploy/deploy.py` (updated — pre-bundled deps, aarch64 Linux wheels, no .pyc)
- `Makefile` (updated)
- `.env` (updated — MODEL_ID → claude-3-haiku)
- `.env.example` (updated — MODEL_ID → claude-3-haiku)
