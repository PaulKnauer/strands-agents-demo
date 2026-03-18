# Story 2.1: AgentCore Deployment Script

Status: review

## Story

As a developer,
I want to run `python deploy/deploy.py` to provision all required AWS infrastructure and deploy the agent to AgentCore in `us-east-1`,
so that my agent is running in production without any manual AWS console steps.

## Acceptance Criteria

1. **Given** I have valid AWS credentials and `AWS_REGION=us-east-1`, `AGENT_NAME`, `MODEL_ID`, and `MODEL_PROVIDER` set in `.env`, **When** I run `python deploy/deploy.py`, **Then** the script completes without errors, provisions the infrastructure, and prints the deployed AgentCore endpoint URL.

2. **Given** the deployment script runs, **When** it executes, **Then** it creates a least-privilege IAM service role scoped only to `bedrock:InvokeModel` on the specific model ARN and `bedrock-agentcore:*` on the specific agent resource — no over-provisioned permissions.

3. **Given** the agent has already been deployed once, **When** I run `python deploy/deploy.py` again, **Then** the script detects the existing agent, updates it rather than creating a duplicate, and exits cleanly — idempotent behaviour.

4. **Given** `deploy/deploy.py` executes, **When** it encounters a common error (missing IAM permission, wrong region, missing env var), **Then** it prints a descriptive troubleshooting hint specific to that error — not a raw AWS exception traceback.

5. **Given** `deploy/deploy.py` completes successfully, **When** I read the console output, **Then** the deployed agent endpoint URL is clearly displayed and I can copy it for verification.

6. **Given** I examine `deploy/deploy.py`, **When** I read it, **Then** all non-obvious blocks have inline comments explaining the *why*, it follows PEP 8, and `black deploy/deploy.py` produces no changes.

## Tasks / Subtasks

- [x] Task 1: Create `deploy/app.py` — AgentCore Runtime entrypoint (AC: #1, #5, #6)
  - [x] Import `BedrockAgentCoreApp` from `bedrock_agentcore`
  - [x] Add sys.path manipulation so `agent.py` at project root is importable from `deploy/`
  - [x] Import the `agent` object from `agent.py` (triggers model initialisation at import time — env vars must be set)
  - [x] Define `@app.entrypoint` handler that receives a `payload` dict, extracts `payload.get("prompt", "")`, calls `agent(prompt)`, returns `str(response)`
  - [x] Add `if __name__ == "__main__": app.run()` guard (starts HTTP server for AgentCore; not used locally)
  - [x] Add inline *why* comments on: sys.path manipulation, app.entrypoint decorator, `app.run()` vs REPL distinction
  - [x] Run `black deploy/app.py` — must pass `--check` clean

- [x] Task 2: Create `deploy/deploy.py` — deployment orchestration script (AC: #1, #2, #3, #4, #5, #6)
  - [x] Call `load_dotenv()` at module level before any `os.environ` access
  - [x] Validate required env vars with `os.environ[]` (fail-fast): `AWS_REGION`, `AGENT_NAME`, `MODEL_ID`, `MODEL_PROVIDER`
  - [x] Retrieve AWS account ID via `boto3.client("sts").get_caller_identity()["Account"]`
  - [x] Sanitize `AGENT_NAME`: replace hyphens with underscores (AgentCore naming constraint: `[a-zA-Z][a-zA-Z0-9_]{0,47}`)
  - [x] Ensure S3 bucket `bedrock-agentcore-code-{account_id}-{region}` exists (create if absent; `us-east-1` does NOT use `CreateBucketConfiguration` — see Dev Notes)
  - [x] Build in-memory ZIP containing `agent.py` (from project root) and `app.py` (from `deploy/app.py`, placed at ZIP root as the entrypoint)
  - [x] Upload ZIP bytes to `s3://{bucket}/{agent_name}/deployment.zip`
  - [x] Create least-privilege IAM execution role (see exact trust policy and permission policy in Dev Notes)
  - [x] Idempotency check: call `list_agent_runtimes()`, filter client-side for `agentRuntimeName == agent_name` (API has no server-side name filter)
    - [x] If NOT found: call `create_agent_runtime()` with S3 artifact, IAM role ARN, `networkMode=PUBLIC`, runtime env vars
    - [x] If found: call `update_agent_runtime()` with updated S3 artifact and existing `agentRuntimeId`
  - [x] Poll for `status == "READY"` (10-second intervals, up to 5 minutes; print dots while waiting)
  - [x] Print endpoint URL on success (format: `https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{arn}/invocations`)
  - [x] Wrap all major steps in `try/except ClientError` with troubleshooting hint print statements (see Dev Notes for exact hints)
  - [x] Run `black deploy/deploy.py` — must pass `--check` clean

- [ ] Task 3: Manual AC verification (AC: #1–#6)
  - [ ] AC #1: `python deploy/deploy.py` completes, endpoint URL printed (requires live AWS credentials)
  - [ ] AC #2: IAM role in AWS console has correct least-privilege policies — no wildcard Resources
  - [ ] AC #3: Run `deploy.py` a second time — no duplicate agent created, script exits cleanly
  - [x] AC #4: Simulate missing env var (unset `AWS_REGION`) — confirm descriptive troubleshooting hint prints ✅ verified statically
  - [ ] AC #5: Endpoint URL visible and copyable in console output
  - [x] AC #6: `black deploy/deploy.py` and `black deploy/app.py` both pass `--check` ✅ verified
  - ⚠️ AC #1–#3, #5 require live AWS credentials — Paul must verify these manually before closing this story

## Dev Notes

### Architecture Decision: Two Files for Two Concerns

The architecture requires `agent.py` to remain unchanged (local REPL tool, under 150 lines). AgentCore Runtime requires an HTTP-compatible entrypoint — different from a REPL. Solution:

- **`deploy/app.py`** — thin AgentCore entrypoint that imports the existing Strands `agent` object and wraps it with `BedrockAgentCoreApp`. This is packaged *into the deployment ZIP* alongside `agent.py`.
- **`deploy/deploy.py`** — AWS infrastructure orchestration only; no agent logic.

Do NOT modify `agent.py` — it is already in "review" status and works correctly for local development.

### AgentCore SDK: `BedrockAgentCoreApp` Pattern

`bedrock-agentcore` (already in `requirements.txt`) provides `BedrockAgentCoreApp`:

```python
# deploy/app.py — authoritative implementation pattern
import os
import sys

from dotenv import load_dotenv

# AgentCore runs this file from the ZIP root, but agent.py is also at ZIP root.
# This sys.path insert is not needed when both files are at ZIP root —
# include it defensively for local testing where paths may differ.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()  # Load env vars before agent.py is imported (agent.py accesses os.environ at module level)

from agent import agent  # triggers model instantiation using env vars
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()


@app.entrypoint
def handle_invocation(payload: dict) -> str:
    """Process an AgentCore runtime invocation and return the agent response."""
    prompt = payload.get("prompt", "")
    response = agent(prompt)
    # Strands Agent() returns an AgentResult — convert to str for AgentCore response
    return str(response)


if __name__ == "__main__":
    # app.run() starts the HTTP server that AgentCore Runtime wraps.
    # This is NOT used locally — local testing uses agent.py's REPL loop directly.
    app.run()
```

### AgentCore Boto3 Clients

Two separate clients — do NOT confuse them:

| Client | boto3 service name | Use |
|---|---|---|
| Control plane | `bedrock-agentcore-control` | create/update/list/get runtimes |
| Data plane | `bedrock-agentcore` | invoke (Story 2.2 only) |

```python
agentcore_ctrl = boto3.client("bedrock-agentcore-control", region_name=aws_region)
```

### AgentCore Naming Constraint — Critical

`create_agent_runtime()` `agentRuntimeName` must match `[a-zA-Z][a-zA-Z0-9_]{0,47}`.

The `.env.example` defines `AGENT_NAME=age-in-days-demo` — **hyphens are NOT allowed**. The deploy script MUST sanitize before using:

```python
# AgentCore runtime names allow only letters, digits, and underscores
agent_name = os.environ["AGENT_NAME"].replace("-", "_")
```

Print a note to the console when sanitization occurs so the developer knows what name was actually registered.

### S3 Bucket — `us-east-1` Has No Location Constraint

```python
def _ensure_s3_bucket(s3, bucket_name, region, account_id):
    try:
        s3.head_bucket(Bucket=bucket_name, ExpectedBucketOwner=account_id)
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            if region == "us-east-1":
                # us-east-1 must NOT pass CreateBucketConfiguration — AWS raises InvalidLocationConstraint
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": region},
                )
```

### Building the Deployment ZIP In-Memory

Package both files at the ZIP root (no subdirectory). AgentCore Runtime uses `app.py` as entrypoint:

```python
import io
import zipfile
import os

def _build_deployment_zip(project_root: str) -> bytes:
    """Create in-memory ZIP with agent.py and app.py at the archive root."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(os.path.join(project_root, "agent.py"), arcname="agent.py")
        zf.write(os.path.join(project_root, "deploy", "app.py"), arcname="app.py")
    return buf.getvalue()

# project_root detection:
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
```

### IAM Role — Exact Trust and Permission Policies

**Trust policy** (who can assume the role):
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
```

**Permission policy** (least-privilege per AC #2):
```python
# Construct resource ARNs from env vars — no hardcoded values
model_arn = f"arn:aws:bedrock:{aws_region}::foundation-model/{model_id}"
agent_resource = f"arn:aws:bedrock-agentcore:{aws_region}:{account_id}:runtime/{agent_name}*"

permission_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "bedrock:InvokeModel",
            "Resource": model_arn,
        },
        {
            "Effect": "Allow",
            "Action": "bedrock-agentcore:*",
            "Resource": agent_resource,
        },
    ],
}
```

**IAM idempotency**: check `iam.get_role(RoleName=role_name)` first; if `NoSuchEntityException` → create role. If exists → update inline policy only (role already has correct trust).

Role name pattern: `AmazonBedrockAgentCoreRuntime-{agent_name}` (stays under 64-char IAM limit for short agent names).

### `create_agent_runtime()` — Full Parameters

```python
response = agentcore_ctrl.create_agent_runtime(
    agentRuntimeName=agent_name,
    agentRuntimeArtifact={
        "codeConfiguration": {
            "code": {"s3": {"bucket": s3_bucket, "prefix": s3_key}},
            "runtime": "PYTHON_3_12",  # use 3.12 — 3.13 availability not guaranteed
            "entryPoint": ["python", "app.py"],
        }
    },
    networkConfiguration={"networkMode": "PUBLIC"},
    roleArn=role_arn,
    environmentVariables={
        "MODEL_PROVIDER": model_provider,
        "MODEL_ID": model_id,
        "AWS_REGION": aws_region,
    },
    description=f"Age-in-days demo agent deployed by deploy.py",
)
agent_runtime_id = response["agentRuntimeId"]
agent_arn = response["agentRuntimeArn"]
```

### Idempotency Check — `list_agent_runtimes()`

```python
def _find_existing_runtime(agentcore_ctrl, agent_name):
    """Return (agentRuntimeId, agentRuntimeArn) if agent_name exists, else (None, None)."""
    paginator = agentcore_ctrl.get_paginator("list_agent_runtimes") if hasattr(agentcore_ctrl, 'get_paginator') else None
    # Fallback to direct call if paginator not available
    response = agentcore_ctrl.list_agent_runtimes(maxResults=100)
    for runtime in response.get("agentRuntimes", []):
        if runtime["agentRuntimeName"] == agent_name:
            return runtime["agentRuntimeId"], runtime["agentRuntimeArn"]
    return None, None
```

### `update_agent_runtime()` Call

```python
agentcore_ctrl.update_agent_runtime(
    agentRuntimeId=existing_runtime_id,
    agentRuntimeArtifact={
        "codeConfiguration": {
            "code": {"s3": {"bucket": s3_bucket, "prefix": s3_key}},
            "runtime": "PYTHON_3_12",
            "entryPoint": ["python", "app.py"],
        }
    },
    networkConfiguration={"networkMode": "PUBLIC"},
    roleArn=role_arn,
    environmentVariables={
        "MODEL_PROVIDER": model_provider,
        "MODEL_ID": model_id,
        "AWS_REGION": aws_region,
    },
)
```

### Polling for READY Status

```python
def _wait_for_ready(agentcore_ctrl, agent_runtime_id, timeout_seconds=300):
    """Poll until runtime status is READY or timeout."""
    elapsed = 0
    print("Waiting for agent to be ready", end="", flush=True)
    while elapsed < timeout_seconds:
        response = agentcore_ctrl.get_agent_runtime(agentRuntimeId=agent_runtime_id)
        status = response["status"]
        if status == "READY":
            print(" ✅")
            return
        if status in ("FAILED", "DELETING"):
            print(f" ❌\nDeployment failed with status: {status}")
            raise RuntimeError(f"Agent runtime entered {status} state")
        print(".", end="", flush=True)
        time.sleep(10)
        elapsed += 10
    raise TimeoutError("Agent did not become READY within 5 minutes")
```

### Troubleshooting Hint Messages (AC #4)

Wrap every `ClientError` catch with specific hints:

```python
except ClientError as e:
    code = e.response["Error"]["Code"]
    msg = e.response["Error"]["Message"]
    if code == "AccessDeniedException" or code == "UnauthorizedException":
        print(f"❌ IAM permission error: {msg}")
        print("   Hint: Your AWS user/role needs bedrock-agentcore-control:* permissions.")
        print("   See: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html")
    elif code == "ResourceNotFoundException":
        print(f"❌ Resource not found: {msg}")
        print("   Hint: Check that AWS_REGION is correct and AgentCore is available in that region.")
        print("   AgentCore is currently only available in select regions (e.g., us-east-1, us-west-2).")
    elif "credentials" in msg.lower() or code == "InvalidClientTokenId":
        print(f"❌ AWS credentials error: {msg}")
        print("   Hint: Ensure AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY are set, or ~/.aws/credentials is configured.")
    else:
        print(f"❌ AWS error ({code}): {msg}")
        print("   Hint: Check AWS_REGION, AGENT_NAME, and MODEL_ID in your .env file.")
    sys.exit(1)
```

Also handle `KeyError` (missing env var) at the top of `main()`:

```python
except KeyError as e:
    print(f"❌ Missing required environment variable: {e}")
    print("   Hint: Copy .env.example to .env and fill in all required values.")
    sys.exit(1)
```

### Endpoint URL Format

```
https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{url_encoded_arn}/invocations
```

The ARN contains colons and slashes which must be URL-encoded when constructing the URL manually. However, for the console output, print the ARN separately so the developer can use the boto3 `invoke_agent_runtime()` call directly (Story 2.2) — avoid constructing the encoded URL in deploy.py:

```python
print(f"\n🎉 Agent deployed successfully!")
print(f"   Agent Name : {agent_name}")
print(f"   Runtime ARN: {agent_arn}")
print(f"   Runtime ID : {agent_runtime_id}")
print(f"\n   Use the ARN above to invoke via Story 2.2 verification script.")
print(f"   Or find the endpoint in the AgentCore console: https://console.aws.amazon.com/bedrock-agentcore/")
```

### Previous Story Learnings

From Story 1.2 (critical SDK correction): `BedrockModel` uses `region_name` (not `region`) — already applied in `agent.py`. No change needed.

From Story 1.3: No `black` check needed for JSON files. Deploy.py and app.py are Python — `black` IS required.

From architecture.md "Process Patterns": Comment the *why*, not the *what* on every non-obvious block.

### No Automated Tests

MVP has no automated tests. All AC verification is manual — live AWS credentials required. Per architecture.md: "No automated tests at MVP — acceptance testing is manual run + AgentCore console verification."

### Files NOT Touched

- `agent.py` — do NOT modify (local REPL agent, already in review)
- `requirements.txt` — `bedrock-agentcore` already listed
- `.env.example` — AGENT_NAME=age-in-days-demo already documented (deploy.py sanitizes the name)
- `.vscode/` — no changes
- `_bmad/`, `_bmad-output/`, `venv/` — do NOT touch

### Files to Create

```
deploy/
├── app.py     ← AgentCore Runtime entrypoint (wraps agent.py for cloud deployment)
└── deploy.py  ← AWS infrastructure orchestration + deployment script
```

No `deploy/__init__.py` needed — these are standalone scripts, not a package.

### Architecture Source References

- [Source: architecture.md#Infrastructure & Deployment] — deploy.py responsibilities (idempotency, IAM, endpoint output, error hints)
- [Source: architecture.md#Authentication & Security] — least-privilege IAM role scoped to `bedrock:InvokeModel` + `bedrock-agentcore:*`
- [Source: architecture.md#Deployment Boundary] — "does NOT contain agent logic, tool definitions, conversation handling"
- [Source: epics.md#Story 2.1] — FR20 (no manual console steps), FR22 (us-east-1), FR23 (troubleshooting hints)
- [Source: architecture.md#Complete Project Directory Structure] — `deploy/deploy.py` file placement
- [Source: architecture.md#Process Patterns] — inline comment standard (why not what), `black` formatter

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

_none — both files created cleanly on first attempt; black reformatted deploy.py line lengths on first pass._

### Completion Notes List

- Created `deploy/app.py`: thin AgentCore Runtime entrypoint using `BedrockAgentCoreApp`. Wraps existing `agent` object via `@app.entrypoint`; sys.path manipulation ensures `agent.py` is importable both locally (from `deploy/`) and in the ZIP (same directory). `black --check` passes.
- Created `deploy/deploy.py`: full 5-step deployment orchestration — S3 bucket provisioning, in-memory ZIP packaging (`agent.py` + `app.py` at ZIP root), IAM least-privilege role creation, AgentCore `create_agent_runtime()`/`update_agent_runtime()` with client-side idempotency check via `list_agent_runtimes()`, READY status polling, and per-step `ClientError` troubleshooting hints. `black --check` passes.
- Key corrections applied from research: `us-east-1` S3 bucket creation must NOT include `CreateBucketConfiguration`; AgentCore `agentRuntimeName` forbids hyphens — sanitized with `replace("-", "_")`; boto3 client is `bedrock-agentcore-control` (not `bedrock-agentcore`) for control-plane operations.
- AC #4 verified statically (missing env var → descriptive hint, no raw exception). AC #6 verified (`black --check` passes both files).
- AC #1–#3, #5 require live AWS credentials — Paul must run `python deploy/deploy.py` manually.
- ✅ Resolved review finding [patch]: Constructed and printed explicit AgentCore endpoint URL (`https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{url_encoded_arn}/invocations`) on successful deployment — satisfies AC #1 and AC #5.
- ✅ Resolved review finding [patch]: Changed `MODEL_PROVIDER` loading from `os.environ.get(...)` to `os.environ[...]` — misconfigured deployments now fail-fast instead of silently defaulting to Bedrock.

### File List

- `deploy/app.py` (created)
- `deploy/deploy.py` (created)

### Change Log

- 2026-03-16: Created `deploy/app.py` and `deploy/deploy.py` for Story 2.1 (AgentCore deployment script)
- 2026-03-17: Addressed code review findings — 2 items resolved: (1) print endpoint URL on success, (2) MODEL_PROVIDER fail-fast validation
