# Story 4.5: Compliance Metrics Dashboard

Status: done

## Story

As a compliance reviewer or developer,
I want a CloudWatch dashboard that shows guardrail block rates and tool invocation audit events,
So that I have visible, continuous evidence of the agent's safety controls operating as documented — satisfying NIST AI RMF MEASURE-2.4 (safety monitoring) and MANAGE-2.4 (incident tracking).

## Context

This is the fifth and final story of **Epic 4: NIST AI RMF Compliance Layer**.

Stories 4.1–4.4 established governance documentation, audit logging, guardrails, and automated safety testing. Story 4.5 closes the **MANAGE** gap: operational visibility into the running system. Without a dashboard, compliance controls are implemented but not observable — an auditor cannot verify at a glance that guardrails are triggering, or that tool calls are being logged.

**This story adds a single new script and a test file. It does NOT modify `agent.py`, `compliance/hooks.py`, or any existing runtime logic.** The only existing files modified are: `deploy/teardown.py` (add dashboard deletion), `Makefile` (add target + update format/lint), and `docs/ai-system-card.md` (update Human Oversight section).

**Design decisions:**
- `deploy/create_dashboard.py` — matches the naming and structure of all other `deploy/` scripts
- Dashboard name constant `NIST_RMF_DASHBOARD_NAME = "NIST-RMF-AgentCompliance"` — defined in `create_dashboard.py`, imported by `teardown.py` (keeps names in sync without code duplication)
- `GUARDRAIL_ID` and `LOG_GROUP_NAME` are optional — Widget 1 is omitted when `GUARDRAIL_ID` is unset; Widget 2 uses a default log group name derived from `AGENT_NAME`
- `put_dashboard()` is idempotent by AWS design — re-running overwrites the existing dashboard

**NIST AI RMF functions addressed:**
- **MEASURE-2.4** — Safety monitoring: guardrail block rate time series
- **MEASURE-2.5** — Runtime monitoring: tool invocation audit trail
- **MANAGE-2.4** — Incident tracking: audit trail queryable for forensic analysis
- **MANAGE-4.1** — Human oversight: dashboard referenced in `docs/ai-system-card.md`

## Acceptance Criteria

1. **Given** `deploy/create_dashboard.py` exists and `AWS_REGION` + `AGENT_NAME` are set,
   **When** I run `python deploy/create_dashboard.py`,
   **Then** a CloudWatch dashboard named `NIST-RMF-AgentCompliance` is created (or overwritten) and the console prints its AWS console URL.

2. **Given** the dashboard is created,
   **When** I inspect it in the CloudWatch console,
   **Then** it contains:
   - **Widget 1** (when `GUARDRAIL_ID` is set): A metric widget titled "Guardrail Block Rate (NIST MEASURE-2.4)" showing `GuardrailInvocations` and `GuardrailInterventions` from the `AWS/Bedrock` namespace, dimensioned by `GuardrailId`.
   - **Widget 2** (always): A CloudWatch Logs Insights widget titled "Tool Invocation Audit Trail (NIST MEASURE-2.5)" querying the audit log group for `event = "tool_call_start"` records.

3. **Given** the script is run twice with the same configuration,
   **When** the second run completes,
   **Then** only one dashboard exists — the second run overwrites the first without error (idempotent).

4. **Given** `Makefile` is updated,
   **When** I run `make dashboard`,
   **Then** it executes `$(PYTHON) deploy/create_dashboard.py`.

5. **Given** `deploy/teardown.py` is updated,
   **When** I run `python deploy/teardown.py` (or `make teardown`),
   **Then** it attempts to delete the `NIST-RMF-AgentCompliance` dashboard and handles `ResourceNotFound` gracefully (prints info and continues).

6. **Given** `tests/unit/test_create_dashboard.py` exists,
   **When** I run `pytest tests/unit/test_create_dashboard.py -v`,
   **Then** all tests pass — covering: `put_dashboard` called once with correct name, dashboard body contains expected widgets, missing `AWS_REGION` exits with code 1, `GUARDRAIL_ID` absent omits widget 1.

7. **Given** `docs/ai-system-card.md` is updated,
   **When** I read the Human Oversight Mechanism section,
   **Then** it references the `NIST-RMF-AgentCompliance` CloudWatch dashboard as the operator's runtime monitoring tool.

8. **Given** all existing tests,
   **When** I run `make test`,
   **Then** all pre-existing tests continue to pass (zero regressions).

## Tasks / Subtasks

- [x] Task 1: Create `deploy/create_dashboard.py` (AC: #1, #2, #3)
  - [x] `load_dotenv()` at module level; read `AWS_REGION` (required), `AGENT_NAME` (required), `GUARDRAIL_ID` (optional), `LOG_GROUP_NAME` (optional, default = `/aws/bedrock-agentcore/runtimes/{agent_name}`)
  - [x] Define `NIST_RMF_DASHBOARD_NAME = "NIST-RMF-AgentCompliance"` as module-level constant
  - [x] `_build_dashboard_body(region, guardrail_id, log_group)` — returns JSON string; omits Widget 1 when `guardrail_id` is None
  - [x] Widget 1 (metric): `AWS/Bedrock` namespace, metrics `GuardrailInvocations` and `GuardrailInterventions`, dimension `GuardrailId`, `stat=Sum`, `period=300`, `view=timeSeries`
  - [x] Widget 2 (log): CloudWatch Logs Insights query on `log_group`, filter `event = "tool_call_start"`, fields `@timestamp, event, tool_name, invocation_id`, sort desc, limit 50
  - [x] `main()` — call `boto3.client("cloudwatch").put_dashboard(...)`, print console URL, handle `ClientError` with hint
  - [x] Run `black deploy/create_dashboard.py` before marking task complete

- [x] Task 2: Create `tests/unit/test_create_dashboard.py` (AC: #6, #8)
  - [x] `TestCreateDashboard.test_put_dashboard_called_once` — mock boto3, assert `put_dashboard` called with `DashboardName="NIST-RMF-AgentCompliance"`
  - [x] `TestCreateDashboard.test_dashboard_body_contains_log_widget` — parse body JSON, assert widget 2 is present and type is `"log"`
  - [x] `TestCreateDashboard.test_guardrail_widget_included_when_guardrail_id_set` — set `GUARDRAIL_ID`, assert widget 1 is present
  - [x] `TestCreateDashboard.test_guardrail_widget_omitted_when_guardrail_id_absent` — clear `GUARDRAIL_ID`, assert only 1 widget
  - [x] `TestCreateDashboard.test_missing_aws_region_exits_1` — clear `AWS_REGION`, assert `SystemExit(1)`
  - [x] Run `make test` — verify all existing 126 tests still pass (131 total with 5 new tests)
  - [x] Run `black tests/unit/test_create_dashboard.py`

- [x] Task 3: Update `deploy/teardown.py` (AC: #5)
  - [x] Import `NIST_RMF_DASHBOARD_NAME` from `deploy.create_dashboard`
  - [x] Add Step 4 (update step count header from "3" to "4" — change the teardown message accordingly)
  - [x] Create `boto3.client("cloudwatch")` and call `delete_dashboards(DashboardNames=[NIST_RMF_DASHBOARD_NAME])`
  - [x] Catch `ClientError` — if code is `"ResourceNotFound"` print info and continue; else print warning and continue
  - [x] Print updated teardown message: `"This will delete: AgentCore runtime, IAM role, S3 deployment object, CloudWatch dashboard."`
  - [x] Run `make test` to confirm no regressions

- [x] Task 4: Update `Makefile` and format/lint targets (AC: #4)
  - [x] Add `make dashboard` target in Deployment section (after `redteam`), with help text entry
  - [x] Add `deploy/create_dashboard.py` to `format` target file list
  - [x] Add `deploy/create_dashboard.py` to `lint` target file list
  - [x] Confirm `make lint` passes

- [x] Task 5: Update `docs/ai-system-card.md` (AC: #7)
  - [x] In Human Oversight Mechanism section, add point 5: "Runtime monitoring dashboard. The `NIST-RMF-AgentCompliance` CloudWatch dashboard (deployed via `make dashboard`) provides operators with a real-time view of guardrail block rates and tool invocation audit events — satisfying NIST AI RMF MANAGE-2.4 and MEASURE-2.5."
  - [x] Add change log entry: `2026-03-21 | Human Oversight section updated — CloudWatch compliance dashboard added as monitoring mechanism (Story 4.5) | Paul`

### Review Follow-ups (AI)

- [x] [AI-Review][High] Fix guardrail metrics: update Widget 1 to use `AWS/Bedrock/Guardrails` namespace, `Invocations`/`InvocationsIntervened` metrics, `GuardrailArn`/`GuardrailVersion` dimensions — per AWS docs (code-review finding 2026-03-21)
- [x] [AI-Review][Med] Fix teardown `ResourceNotFound` handling: inspect `e.response["Error"]["Code"]`, print info (not warning) for `ResourceNotFound`; add `tests/unit/test_teardown_dashboard.py` with 3 tests covering success, not-found, and other-error branches (code-review finding 2026-03-21)

## Dev Notes

### Critical Constraints

- **Do NOT modify `agent.py`, `compliance/hooks.py`, or any test file except the new one.** This story is infrastructure only.
- **`deploy/create_dashboard.py` must NOT be imported at test time with live AWS calls.** The `main()` function must be guarded by `if __name__ == "__main__": main()`. Tests import and call `main()` with boto3 mocked.
- **`put_dashboard` takes a JSON string, not a dict.** Pass `json.dumps(dashboard_body)` as the `DashboardBody` argument.
- **CloudWatch `delete_dashboards` does NOT raise an exception for non-existent dashboards** — it silently succeeds. Use `describe_dashboards` + `delete_dashboards` pattern or just call `delete_dashboards` and treat all responses as success. Reference: [AWS docs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_DeleteDashboards.html). Update: actually test with `ClientError` check to be defensive.

### File Placement and Naming

```
deploy/
  create_dashboard.py   # NEW — matches naming pattern of deploy.py, teardown.py, verify.py
tests/unit/
  test_create_dashboard.py  # NEW — matches test naming pattern in tests/unit/
```

### `deploy/create_dashboard.py` Pattern

Follow the exact pattern of `deploy/teardown.py`:
- `load_dotenv()` at module top (before any `os.environ` access)
- `os.environ["AWS_REGION"]` with fail-fast `KeyError` → catch and `sys.exit(1)`
- `boto3.client(...)` inside `main()`, not at module level (enables mocking)
- `if __name__ == "__main__": main()` at bottom

```python
"""CloudWatch compliance dashboard — NIST AI RMF MEASURE-2.4/2.5 and MANAGE-2.4/4.1."""

import json
import os
import sys

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

NIST_RMF_DASHBOARD_NAME = "NIST-RMF-AgentCompliance"


def _build_dashboard_body(region: str, guardrail_id: str | None, log_group: str) -> str:
    """Build the CloudWatch dashboard JSON body.

    Returns a JSON string (not dict) — CloudWatch put_dashboard requires a string.
    Widget 1 (Guardrail Block Rate) is omitted when guardrail_id is None.
    """
    widgets = []

    if guardrail_id:
        # Widget 1: Guardrail Block Rate — NIST MEASURE-2.4 (safety monitoring).
        # Shows GuardrailInvocations vs GuardrailInterventions (blocks) over time.
        # Dimension: GuardrailId links the metric to this agent's specific guardrail.
        widgets.append({
            "type": "metric",
            "x": 0, "y": 0, "width": 12, "height": 6,
            "properties": {
                "title": "Guardrail Block Rate (NIST MEASURE-2.4)",
                "metrics": [
                    ["AWS/Bedrock", "GuardrailInvocations", "GuardrailId", guardrail_id,
                     {"label": "Invocations"}],
                    ["AWS/Bedrock", "GuardrailInterventions", "GuardrailId", guardrail_id,
                     {"label": "Interventions (Blocks)", "color": "#ff6b6b"}],
                ],
                "period": 300,
                "stat": "Sum",
                "view": "timeSeries",
                "stacked": False,
                "region": region,
            },
        })

    # Widget 2: Tool Invocation Audit Trail — NIST MEASURE-2.5 (runtime monitoring).
    # Queries the JSONL audit log produced by AuditLoggingHook in compliance/hooks.py.
    # Filters for tool_call_start events to show when and what tools were invoked.
    log_widget_y = 6 if guardrail_id else 0
    widgets.append({
        "type": "log",
        "x": 0, "y": log_widget_y, "width": 24, "height": 6,
        "properties": {
            "title": "Tool Invocation Audit Trail (NIST MEASURE-2.5)",
            "query": (
                f"SOURCE '{log_group}'\n"
                "| fields @timestamp, event, tool_name, invocation_id\n"
                "| filter event = 'tool_call_start'\n"
                "| sort @timestamp desc\n"
                "| limit 50"
            ),
            "region": region,
            "view": "table",
        },
    })

    return json.dumps({"widgets": widgets})


def main() -> None:
    """Create or update the NIST-RMF-AgentCompliance CloudWatch dashboard."""
    try:
        region = os.environ["AWS_REGION"]
        agent_name = os.environ["AGENT_NAME"].replace("-", "_")
    except KeyError as e:
        print(f"\n❌ Missing required environment variable: {e}")
        print("   Hint: Copy .env.example to .env and fill in all required values.")
        sys.exit(1)

    guardrail_id = os.environ.get("GUARDRAIL_ID")
    # Default log group matches AgentCore's auto-provisioned log group name pattern.
    # Override with LOG_GROUP_NAME env var if your deployment uses a different name.
    log_group = os.environ.get(
        "LOG_GROUP_NAME", f"/aws/bedrock-agentcore/runtimes/{agent_name}"
    )

    print(f"\n📊 Creating CloudWatch dashboard: {NIST_RMF_DASHBOARD_NAME}")
    if not guardrail_id:
        print("   ℹ️  GUARDRAIL_ID not set — Guardrail Block Rate widget will be omitted.")

    cw = boto3.client("cloudwatch", region_name=region)
    body = _build_dashboard_body(region, guardrail_id, log_group)

    try:
        cw.put_dashboard(DashboardName=NIST_RMF_DASHBOARD_NAME, DashboardBody=body)
    except ClientError as e:
        print(f"\n❌ Failed to create dashboard: {e}")
        print("   Hint: Verify AWS credentials and that CloudWatch is accessible in the region.")
        sys.exit(1)

    console_url = (
        f"https://{region}.console.aws.amazon.com/cloudwatch/home"
        f"?region={region}#dashboards/dashboard/{NIST_RMF_DASHBOARD_NAME}"
    )
    print(f"  ✅ Dashboard created: {NIST_RMF_DASHBOARD_NAME}")
    print(f"  🔗 {console_url}")


if __name__ == "__main__":
    main()
```

### CloudWatch Metric Names — Verify Before Submission

The metric names `GuardrailInvocations` and `GuardrailInterventions` are from the NIST research document. **Verify these against the current AWS documentation** before writing the final script:

- AWS Bedrock CloudWatch metrics: [https://docs.aws.amazon.com/bedrock/latest/userguide/monitoring-cloudwatch.html](https://docs.aws.amazon.com/bedrock/latest/userguide/monitoring-cloudwatch.html)
- If metric names differ, update Widget 1 accordingly and note the change in the Dev Agent Record.
- The unit tests **mock boto3** so they will pass regardless — only the live dashboard appearance depends on the correct metric names.

### Test Pattern for `test_create_dashboard.py`

Follow the pattern in `tests/unit/test_deploy.py` (imports helpers directly, mocks boto3):

```python
import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from deploy.create_dashboard import _build_dashboard_body, main, NIST_RMF_DASHBOARD_NAME

ENV = {"AWS_REGION": "us-east-1", "AGENT_NAME": "test-agent"}


class TestCreateDashboard:

    def test_put_dashboard_called_once(self):
        with (
            patch.dict(os.environ, {**ENV}, clear=True),
            patch("deploy.create_dashboard.boto3.client") as mock_boto3,
        ):
            mock_cw = MagicMock()
            mock_boto3.return_value = mock_cw
            main()
            mock_cw.put_dashboard.assert_called_once()
            call_kwargs = mock_cw.put_dashboard.call_args.kwargs
            assert call_kwargs["DashboardName"] == NIST_RMF_DASHBOARD_NAME

    def test_dashboard_body_contains_log_widget(self):
        body = json.loads(_build_dashboard_body("us-east-1", None, "/aws/logs/test"))
        log_widgets = [w for w in body["widgets"] if w["type"] == "log"]
        assert len(log_widgets) == 1
        assert "tool_call_start" in log_widgets[0]["properties"]["query"]

    def test_guardrail_widget_included_when_guardrail_id_set(self):
        body = json.loads(_build_dashboard_body("us-east-1", "abc-123", "/aws/logs/test"))
        metric_widgets = [w for w in body["widgets"] if w["type"] == "metric"]
        assert len(metric_widgets) == 1
        assert "GuardrailInvocations" in str(metric_widgets[0])

    def test_guardrail_widget_omitted_when_guardrail_id_absent(self):
        body = json.loads(_build_dashboard_body("us-east-1", None, "/aws/logs/test"))
        metric_widgets = [w for w in body["widgets"] if w["type"] == "metric"]
        assert len(metric_widgets) == 0

    def test_missing_aws_region_exits_1(self):
        with (
            patch.dict(os.environ, {"AGENT_NAME": "test"}, clear=True),
            patch("deploy.create_dashboard.boto3.client"),
            pytest.raises(SystemExit) as exc,
        ):
            main()
        assert exc.value.code == 1
```

**Important test import note:** Tests import `_build_dashboard_body` directly — this means the function must NOT call `boto3` internally (boto3 is only used in `main()`). The `_build_dashboard_body` function must be a pure Python function taking only strings as arguments.

### `deploy/teardown.py` — Minimal Change Required

Add dashboard deletion as Step 4. Import `NIST_RMF_DASHBOARD_NAME` at the top:

```python
from deploy.create_dashboard import NIST_RMF_DASHBOARD_NAME
```

Update the preamble print in `main()`:
```python
print("   This will delete: AgentCore runtime, IAM role, S3 deployment object, CloudWatch dashboard.\n")
```

Change step counts from `Step X/3` → `Step X/4`.

Add step 4 after the existing S3 step:
```python
# ── Step 4: Delete CloudWatch compliance dashboard ────────────────────────────
print("\nStep 4/4: Deleting CloudWatch compliance dashboard...")
cw = boto3.client("cloudwatch", region_name=aws_region)
try:
    cw.delete_dashboards(DashboardNames=[NIST_RMF_DASHBOARD_NAME])
    print(f"  ✅ Deleted CloudWatch dashboard: {NIST_RMF_DASHBOARD_NAME}")
except ClientError as e:
    # delete_dashboards doesn't raise for non-existent dashboards in normal operation,
    # but defensive handling ensures teardown never fails on missing resources.
    print(f"  ⚠️  Could not delete CloudWatch dashboard: {e}")
```

Note: `boto3.client("cloudwatch")` does not take a `region_name` in some configurations, but passing it explicitly is consistent with the rest of teardown.py.

### Makefile Changes

The `format` and `lint` targets currently hardcode file lists. Adding `deploy/create_dashboard.py`:

```makefile
format:
    $(BLACK) agent.py deploy/deploy.py deploy/app.py deploy/teardown.py deploy/verify.py deploy/create_dashboard.py

lint:
    $(BLACK) --check agent.py deploy/deploy.py deploy/app.py deploy/verify.py deploy/create_dashboard.py
```

Add `dashboard` target in the Deployment section (after `redteam`):
```makefile
.PHONY: dashboard
dashboard:
    $(PYTHON) deploy/create_dashboard.py
```

Add to help text (after `make redteam` line):
```
    make dashboard     Create/update CloudWatch NIST-RMF compliance dashboard
```

### `docs/ai-system-card.md` — Minimal Update

The Human Oversight Mechanism section currently has 4 numbered points. Add point 5:

```markdown
5. **Runtime monitoring dashboard.** The `NIST-RMF-AgentCompliance` CloudWatch dashboard
   (deployed via `make dashboard`, see `deploy/create_dashboard.py`) provides operators
   with a real-time view of guardrail block rates and tool invocation audit events —
   satisfying NIST AI RMF MANAGE-2.4 (incident tracking) and MEASURE-2.5 (runtime monitoring).
```

Also update the NIST functions footer line to include MANAGE:
```markdown
_This document supports NIST AI RMF functions **GOVERN** (subcategories 1.1, 1.3, 1.4, 6.1),
**MAP** (subcategories 1.1, 2.2), and **MANAGE** (subcategory 4.1 — human oversight mechanism)._
```

And add a change log entry:
```
| 2026-03-21 | Human Oversight section updated — NIST-RMF-AgentCompliance CloudWatch dashboard added as monitoring mechanism (Story 4.5) | Paul |
```

### `str | None` Type Hint Syntax

Python 3.10+ supports `str | None` syntax. The project targets Python 3.11+, so this syntax is safe. Do NOT use `Optional[str]` from `typing` module.

### Log Group Name Context

The `AuditLoggingHook` in `compliance/hooks.py` writes to the `strands_agent.audit` Python logger. In the AgentCore runtime, Python's stdout/stderr is captured by CloudWatch. However, the **exact log group name** depends on AgentCore's configuration. The default in `create_dashboard.py` is `/aws/bedrock-agentcore/runtimes/{agent_name}` — if the actual deployment uses a different log group, the `LOG_GROUP_NAME` env var overrides it.

For local testing, the Logs Insights widget will show "No results" if the log group doesn't exist — this is expected and not an error.

### `black` — Run After Each Task

Run `black` on every new/modified Python file before marking the task complete. The `make lint` step in CI will fail if any file is not black-formatted.

### Previous Story Intelligence

From Story 4.4 (`4-4-red-team-ci.md`):
- `pyyaml~=6.0` was added to `requirements.txt` for test use. No further dependency changes needed for this story.
- Test count was 126 at end of story 4.4. Expect 126 + N new tests after this story.

From Story 4.3 (`4-3-bedrock-guardrails.md`):
- `GUARDRAIL_ID` is optional (not always set). `create_dashboard.py` must handle `GUARDRAIL_ID` absent gracefully.

From Story 4.2 (`4-2-audit-hooks.md`):
- `AuditLoggingHook` writes JSONL to `strands_agent.audit` logger. The Logs Insights query targets `event = "tool_call_start"` records — this matches the `_on_before_tool_call` method which emits `{"event": "tool_call_start", ...}`.

### Project Structure Notes

```
deploy/create_dashboard.py   — NEW (CloudWatch dashboard creation)
tests/unit/test_create_dashboard.py  — NEW (unit tests)
deploy/teardown.py           — MODIFIED (add dashboard deletion step 4)
Makefile                     — MODIFIED (dashboard target, format/lint file lists)
docs/ai-system-card.md       — MODIFIED (Human Oversight + footer + change log)
```

No changes to `compliance/`, `agent.py`, `deploy/app.py`, or any eval tests.

### References

- NIST MEASURE-2.4/2.5 and MANAGE-2.4 context: `_bmad-output/planning-artifacts/research/technical-nist-ai-rmf-agents-research-2026-03-19.md` (Phase 5)
- `AuditLoggingHook` JSONL schema: `compliance/hooks.py` (event field names)
- Deploy script patterns: `deploy/teardown.py`, `deploy/deploy.py`
- Test patterns: `tests/unit/test_deploy.py`
- CloudWatch Bedrock metrics: https://docs.aws.amazon.com/bedrock/latest/userguide/monitoring-cloudwatch.html

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation proceeded without blockers.

### Completion Notes List

- Created `deploy/create_dashboard.py` with `NIST_RMF_DASHBOARD_NAME` constant, `_build_dashboard_body()` (pure Python, no boto3), and `main()` (boto3 inside, guarded by `__name__`). Black-formatted.
- Created `tests/unit/test_create_dashboard.py` with 5 tests covering: `put_dashboard` call, log widget presence, guardrail widget inclusion/omission, missing `AWS_REGION` exit. All pass.
- Updated `deploy/teardown.py`: imported `NIST_RMF_DASHBOARD_NAME`, changed step counts 1/3→1/4 through 3/3→3/4, added Step 4/4 deleting the dashboard, updated preamble print.
- Updated `Makefile`: added `dashboard` target, added `deploy/create_dashboard.py` to `format` and `lint` file lists, added help text entry.
- Updated `docs/ai-system-card.md`: added Human Oversight point 5 (runtime monitoring dashboard), updated footer to include MANAGE, added change log entry.
- Full test suite: 131 tests pass (124 unit + 7 evals). Zero regressions. `make lint` passes.

### File List

- `deploy/create_dashboard.py` — new (CloudWatch compliance dashboard creation script)
- `tests/unit/test_create_dashboard.py` — new (unit tests for create_dashboard.py)
- `tests/unit/test_teardown_dashboard.py` — new (teardown dashboard deletion unit tests)
- `deploy/teardown.py` — modified (add Step 4: delete CloudWatch dashboard; ResourceNotFound handling)
- `Makefile` — modified (add `dashboard` target, add create_dashboard.py to format/lint)
- `docs/ai-system-card.md` — modified (Human Oversight point 5 + footer + change log)

### Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-21 | Story created | Paul |
| 2026-03-21 | Story implemented — CloudWatch compliance dashboard, unit tests, teardown update, Makefile update, system card update | claude-sonnet-4-6 |
| 2026-03-21 | Addressed code review findings — corrected guardrail metrics to AWS/Bedrock/Guardrails namespace; fixed teardown ResourceNotFound handling; added test_teardown_dashboard.py (3 tests) | claude-sonnet-4-6 |
