# Story 4.2: Audit Hooks — Structured Invocation and Tool Call Logging

Status: review

## Story

As a developer or compliance reviewer,
I want every agent invocation and tool call to produce a structured audit record,
So that the project has a tamper-evident, machine-readable log that satisfies NIST AI RMF MEASURE-2.5 (runtime monitoring) and MANAGE-2.4 (incident tracking) — without modifying any agent business logic.

## Context

This story is the second story of **Epic 4: NIST AI RMF Compliance Layer**.

Story 4.1 created the governance documentation (system card, risk register, governance charter). Story 4.2 delivers the first runtime control: a `HookProvider` that attaches to the Strands Agent via the SDK's hook registry and writes a structured JSONL audit trail of every invocation and tool call.

**Design principle (from research):** Risk controls must live in the compliance layer, not in business logic. `agent.py` should have no knowledge of what the audit hook does — it only passes `hooks=[AuditLoggingHook()]` to the `Agent` constructor. All audit logic lives in `compliance/hooks.py`.

**NIST AI RMF functions addressed:**
- **MEASURE-2.5** — Runtime monitoring: the audit log captures every invocation with timing, every tool call with inputs/outputs, and every message added to the conversation.
- **MANAGE-2.4** — Incident tracking and forensics: the JSONL audit trail provides the full reasoning chain (invocation start/end, tool calls, message history) needed for post-incident analysis.

## Acceptance Criteria

1. **Given** `compliance/` directory exists with `__init__.py` and `hooks.py`,
   **When** I import `from compliance.hooks import AuditLoggingHook`,
   **Then** the import succeeds without errors.

2. **Given** `AuditLoggingHook` is instantiated,
   **When** I call `agent.hooks.registry` or inspect the Agent's registered hooks,
   **Then** `AuditLoggingHook` is registered on all five hook events:
   `BeforeInvocationEvent`, `AfterInvocationEvent`, `BeforeToolCallEvent`,
   `AfterToolCallEvent`, `MessageAddedEvent`.

3. **Given** an agent invocation runs to completion,
   **When** I read the audit log output,
   **Then** it contains at minimum these structured records (one JSON object per line):
   - `{"event": "invocation_start", "invocation_id": "<uuid>", "session_id": "<uuid>", "timestamp": "<iso8601>"}`
   - `{"event": "tool_call_start", "invocation_id": "<uuid>", "tool_name": "get_today_date", ...}`
   - `{"event": "tool_call_end", "invocation_id": "<uuid>", "tool_name": "get_today_date", ...}`
   - `{"event": "invocation_end", "invocation_id": "<uuid>", "duration_seconds": <float>, ...}`

4. **Given** a `BeforeToolCallEvent` fires,
   **When** the audit record is written,
   **Then** the record contains `tool_name` (from `event.tool_use["name"]`) and `tool_input` (from `event.tool_use["input"]`).

5. **Given** an `AfterToolCallEvent` fires,
   **When** the audit record is written,
   **Then** the record contains `tool_name` and `result_snippet` (the first 200 characters of `str(event.result)` to prevent unbounded log growth).

6. **Given** a `MessageAddedEvent` fires,
   **When** the audit record is written,
   **Then** the record contains `role` and `content_length` (the character count of the message content) — but NOT the raw message content, to avoid inadvertently logging PII in the audit trail.

7. **Given** `agent.py`'s `create_agent()` function,
   **When** I read `agent.py`,
   **Then** it imports `AuditLoggingHook` from `compliance.hooks` and passes `hooks=[AuditLoggingHook()]` to the `Agent` constructor.

8. **Given** `AuditLoggingHook` writes audit records,
   **When** it emits each record,
   **Then** it uses Python's `logging` module (logger name `strands_agent.audit`) at `DEBUG` level — not direct file I/O — so the output destination is configurable by the caller without modifying the hook.

9. **Given** all existing tests in the test suite,
   **When** I run `make test` or `pytest`,
   **Then** all pre-existing tests continue to pass (zero regressions).

10. **Given** `tests/unit/test_hooks.py` exists,
    **When** I run `pytest tests/unit/test_hooks.py`,
    **Then** all tests pass, covering:
    - Hook registers callbacks on all five expected event types
    - `invocation_start` record contains `event`, `invocation_id`, `session_id`, `timestamp`
    - `tool_call_start` record contains `tool_name` and `tool_input`
    - `tool_call_end` record contains `tool_name` and `result_snippet` (truncated to 200 chars)
    - `message_added` record contains `role` and `content_length`, but NOT raw content
    - `invocation_end` record contains `duration_seconds`
    - All records contain `timestamp` in ISO 8601 format and `session_id`

## Tasks / Subtasks

- [x] Task 1: Create `compliance/` package (AC: #1)
  - [x] Create `compliance/__init__.py` (empty file — marks directory as Python package)

- [x] Task 2: Create `compliance/hooks.py` with `AuditLoggingHook` (AC: #1, #2, #3, #4, #5, #6, #8)
  - [x] Import `HookProvider`, `HookRegistry` from `strands.hooks`
  - [x] Import `BeforeInvocationEvent`, `AfterInvocationEvent`, `BeforeToolCallEvent`, `AfterToolCallEvent`, `MessageAddedEvent` from `strands.hooks.events`
  - [x] Define `AuditLoggingHook(HookProvider)` class with `__init__(self, session_id: str | None = None)`
  - [x] In `__init__`: set `self.session_id = session_id or str(uuid.uuid4())`, `self._invocation_id: str | None = None`, `self._start_time: float | None = None`
  - [x] Implement `register_hooks(self, registry: HookRegistry) -> None` registering all 5 events
  - [x] Implement `_emit(self, record: dict) -> None`: adds `timestamp` (UTC ISO 8601), `session_id`, then calls `logger.debug(json.dumps(record))` — logger name `strands_agent.audit`
  - [x] Implement `_on_before_invocation(self, event: BeforeInvocationEvent)`: sets `self._invocation_id = str(uuid.uuid4())` and `self._start_time = time.monotonic()`, emits `invocation_start` record
  - [x] Implement `_on_after_invocation(self, event: AfterInvocationEvent)`: computes `duration_seconds`, emits `invocation_end` record
  - [x] Implement `_on_before_tool_call(self, event: BeforeToolCallEvent)`: emits `tool_call_start` with `tool_name=event.tool_use["name"]` and `tool_input=event.tool_use["input"]`
  - [x] Implement `_on_after_tool_call(self, event: AfterToolCallEvent)`: emits `tool_call_end` with `tool_name` and `result_snippet=str(event.result)[:200]`
  - [x] Implement `_on_message_added(self, event: MessageAddedEvent)`: emits `message_added` with `role` and `content_length` (no raw content)

- [x] Task 3: Wire `AuditLoggingHook` into `agent.py` (AC: #7, #9)
  - [x] Add import: `from compliance.hooks import AuditLoggingHook` at top of `agent.py`
  - [x] In `create_agent()`: add `hooks=[AuditLoggingHook()]` to the `Agent(...)` constructor call
  - [x] Run `black agent.py --check` — must pass; run `black agent.py` if not
  - [x] Run `make test` — all existing tests must pass (verify `test_bedrock_provider_constructs_bedrock_model` and others still pass)

- [x] Task 4: Write unit tests in `tests/unit/test_hooks.py` (AC: #10)
  - [x] Test: `test_hook_registers_all_five_event_types` — instantiate hook, call `register_hooks` with a real or mock registry, verify callbacks registered for all 5 event types
  - [x] Test: `test_invocation_start_record_structure` — fire `BeforeInvocationEvent` via hook, capture log output, assert record has `event=="invocation_start"`, `invocation_id` (UUID), `session_id` (UUID), `timestamp` (ISO 8601)
  - [x] Test: `test_tool_call_start_record_structure` — fire `BeforeToolCallEvent` with `tool_use={"name": "get_today_date", "input": {}, "toolUseId": "t1"}`, assert record has `tool_name=="get_today_date"` and `tool_input=={}`
  - [x] Test: `test_tool_call_end_result_truncated_to_200_chars` — fire `AfterToolCallEvent` with a result string of 300 chars, assert `result_snippet` in record is exactly 200 chars
  - [x] Test: `test_message_added_no_raw_content` — fire `MessageAddedEvent`, assert record has `role` and `content_length` but does NOT contain the key `"content"` or `"text"`
  - [x] Test: `test_invocation_end_has_duration` — fire `BeforeInvocationEvent` then `AfterInvocationEvent`, assert `invocation_end` record has `duration_seconds` as a float >= 0
  - [x] Test: `test_all_records_have_timestamp_and_session_id` — fire several events, assert every emitted record contains `timestamp` and `session_id`
  - [x] Run `make test` — all tests must pass

## Dev Notes

### Package Structure

```
strands-agents-demo/
  compliance/
    __init__.py          ← empty (Task 1)
    hooks.py             ← AuditLoggingHook (Task 2)
  agent.py               ← add import + hooks=[...] to create_agent() (Task 3)
  tests/
    unit/
      test_hooks.py      ← new (Task 4)
```

### Confirmed SDK API (verified via introspection against `strands-agents==1.26.0`)

```python
# Agent constructor accepts hooks parameter
Agent(model=model, tools=[...], system_prompt=SYSTEM_PROMPT, hooks=[AuditLoggingHook()])

# Hook registration pattern
class AuditLoggingHook(HookProvider):
    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeInvocationEvent, self._on_before_invocation)
        registry.add_callback(AfterInvocationEvent, self._on_after_invocation)
        registry.add_callback(BeforeToolCallEvent, self._on_before_tool_call)
        registry.add_callback(AfterToolCallEvent, self._on_after_tool_call)
        registry.add_callback(MessageAddedEvent, self._on_message_added)
```

**Confirmed event field names** (dataclass fields — use attribute access, not dict access):

| Event | Fields |
|---|---|
| `BeforeInvocationEvent` | `agent`, `invocation_state`, `messages` |
| `AfterInvocationEvent` | `agent`, `invocation_state`, `result: AgentResult \| None` |
| `BeforeToolCallEvent` | `agent`, `selected_tool`, `tool_use: ToolUse`, `invocation_state`, `cancel_tool` |
| `AfterToolCallEvent` | `agent`, `selected_tool`, `tool_use: ToolUse`, `invocation_state`, `result`, `exception`, `cancel_message`, `retry` |
| `MessageAddedEvent` | `agent`, `message` |

**`ToolUse` is a TypedDict** (not a dataclass): `{"name": str, "input": Any, "toolUseId": str}`
- Access tool name: `event.tool_use["name"]`
- Access tool input: `event.tool_use["input"]`

**`MessageAddedEvent.message`** — access role via `event.message.get("role", "unknown")` (Message is a TypedDict with `role` and `content` keys).

### `_emit` Implementation

```python
import json
import logging
import time
import uuid
from datetime import datetime, timezone

logger = logging.getLogger("strands_agent.audit")

def _emit(self, record: dict) -> None:
    record["timestamp"] = datetime.now(timezone.utc).isoformat()
    record["session_id"] = self.session_id
    logger.debug(json.dumps(record))
```

Using `logger.debug()` (not `print` or direct file I/O) means:
- In tests: capture with `caplog` or a `logging.Handler`
- In local runs: visible when `logging.basicConfig(level=logging.DEBUG)` is set
- In production (AgentCore): route via CloudWatch log handler without code changes

### `_on_message_added` — Role Extraction

`MessageAddedEvent.message` is a `Message` TypedDict with keys `role` and `content`. Extract safely:

```python
def _on_message_added(self, event: MessageAddedEvent) -> None:
    msg = event.message
    role = msg.get("role", "unknown") if isinstance(msg, dict) else getattr(msg, "role", "unknown")
    content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
    self._emit({
        "event": "message_added",
        "invocation_id": self._invocation_id,
        "role": role,
        "content_length": len(str(content)),
        # deliberately omit raw content to avoid logging PII
    })
```

### `agent.py` Change — Minimal Impact

The change to `agent.py` is two lines:

```python
# At top of file, after existing imports:
from compliance.hooks import AuditLoggingHook

# In create_agent(), change:
return Agent(model=model, tools=[get_today_date], system_prompt=SYSTEM_PROMPT)
# To:
return Agent(model=model, tools=[get_today_date], system_prompt=SYSTEM_PROMPT, hooks=[AuditLoggingHook()])
```

**Regression safety:** `tests/unit/test_agent_tool.py::TestCreateAgent::test_bedrock_provider_constructs_bedrock_model` uses `mock_agent_cls.assert_called_once()` (not `assert_called_once_with()`), so adding `hooks=[...]` to the Agent call will not break this test.

**Line count:** `agent.py` is currently 74 lines. Adding 1 import line keeps it well under the 150-line limit (NFR12).

### Test Patterns

For testing the hook, avoid actually constructing a full `Agent`. Instead:

```python
import json
import logging
from unittest.mock import MagicMock
from compliance.hooks import AuditLoggingHook
from strands.hooks import HookRegistry
from strands.hooks.events import BeforeToolCallEvent, AfterToolCallEvent, ...

def get_emitted_records(caplog_records):
    """Parse all DEBUG log records from strands_agent.audit into dicts."""
    return [json.loads(r.message) for r in caplog_records if r.name == "strands_agent.audit"]
```

Use `pytest`'s built-in `caplog` fixture to capture log output:

```python
def test_invocation_start_record_structure(self, caplog):
    with caplog.at_level(logging.DEBUG, logger="strands_agent.audit"):
        hook = AuditLoggingHook(session_id="test-session")
        event = BeforeInvocationEvent(agent=MagicMock(), messages=None)
        hook._on_before_invocation(event)
    records = get_emitted_records(caplog.records)
    assert len(records) == 1
    r = records[0]
    assert r["event"] == "invocation_start"
    assert "invocation_id" in r
    assert r["session_id"] == "test-session"
    assert "timestamp" in r
```

For `BeforeToolCallEvent`, construct with `tool_use` as a dict:

```python
from strands.types.tools import ToolUse
tool_use: ToolUse = {"name": "get_today_date", "input": {}, "toolUseId": "t-001"}
event = BeforeToolCallEvent(
    agent=MagicMock(),
    selected_tool=None,
    tool_use=tool_use,
    invocation_state={},
)
```

For `AfterToolCallEvent`, include `result`:

```python
event = AfterToolCallEvent(
    agent=MagicMock(),
    selected_tool=None,
    tool_use=tool_use,
    invocation_state={},
    result="2026-03-20",
    exception=None,
    cancel_message=None,
    retry=False,
)
```

For `MessageAddedEvent`, `message` is a dict:

```python
event = MessageAddedEvent(
    agent=MagicMock(),
    message={"role": "user", "content": "I was born on 14th March 1990"},
)
```

### No New Dependencies

The hook implementation uses only Python stdlib (`json`, `logging`, `uuid`, `time`, `datetime`) and the already-installed `strands-agents==1.26.0` SDK. No new entries in `requirements.txt`.

### Style and Quality

- PEP 8 / `black` formatting required on `compliance/hooks.py` and `agent.py`
- Type annotations on all public methods
- Docstring on `AuditLoggingHook` class and `register_hooks` method
- Docstrings on each `_on_*` handler explaining which NIST AI RMF control it satisfies

### Relationship to Subsequent Stories

- **Story 4.3** (Bedrock Guardrails) will add a second `HookProvider` or extend `create_agent()` further — it does not modify `AuditLoggingHook`
- **Story 4.5** (Compliance Dashboard) will create a CloudWatch dashboard that queries the audit log output; the `strands_agent.audit` logger name is the stable interface it depends on
- The risk register (`docs/risk-register.md`) notes R-2 and R-5 as mitigated — the audit hook provides the evidence trail for those mitigations

## Architecture Compliance Notes

The `compliance/` directory is a new top-level package. It has:
- **No imports from `agent.py`** — the dependency is one-way: `agent.py` → `compliance.hooks`
- **No imports from `deploy/`** — compliance concerns are separate from deployment concerns
- **No imports from `tests/`** — tests import from compliance, not vice versa

The `compliance/` package must not be imported during `deploy/` module execution — it is only needed at agent runtime.

## Definition of Done

- [x] `compliance/__init__.py` exists (empty)
- [x] `compliance/hooks.py` exists with `AuditLoggingHook(HookProvider)` implementing all 5 hook events
- [x] `agent.py` imports `AuditLoggingHook` and passes `hooks=[AuditLoggingHook()]` to `Agent()`
- [x] `tests/unit/test_hooks.py` exists with minimum 7 test functions all passing
- [x] `make test` passes with zero failures and zero regressions
- [x] `black compliance/hooks.py --check` passes
- [x] `black agent.py --check` passes
- [x] No new dependencies added to `requirements.txt`
- [x] `agent.py` remains under 150 lines (NFR12)

## File List

- `compliance/__init__.py` — new (empty package marker)
- `compliance/hooks.py` — new (AuditLoggingHook implementation)
- `agent.py` — modified (added AuditLoggingHook import and hooks=[...] to Agent constructor)
- `tests/unit/test_hooks.py` — modified (fixed `_callbacks` → `_registered_callbacks` to match SDK API)

## Dev Agent Record

### Implementation Plan

All four tasks were pre-implemented before this dev session. The only code change required was a one-line fix in `tests/unit/test_hooks.py`: the test for hook registration was accessing `registry._callbacks` (non-existent) instead of the correct `registry._registered_callbacks` attribute in `strands-agents==1.26.0`.

### Completion Notes

- `compliance/__init__.py` — empty package marker, confirms AC #1 ✅
- `compliance/hooks.py` — `AuditLoggingHook(HookProvider)` registers all 5 events, emits structured JSONL via `strands_agent.audit` logger at DEBUG level. Uses Python stdlib only (no new dependencies). ✅
- `agent.py` — imports `AuditLoggingHook` and passes `hooks=[AuditLoggingHook()]` to Agent constructor. File is 81 lines (under 150 NFR12 limit). ✅
- `tests/unit/test_hooks.py` — 10 test functions across 6 test classes; fixed `_callbacks` → `_registered_callbacks` to match SDK. All 104 unit tests + 7 eval tests pass. ✅
- `black` formatting checks pass on both `compliance/hooks.py` and `agent.py`. ✅

### Change Log

- 2026-03-20: Fixed `registry._callbacks` → `registry._registered_callbacks` in `test_hook_registers_all_five_event_types` (SDK API mismatch). All 111 tests now pass.
