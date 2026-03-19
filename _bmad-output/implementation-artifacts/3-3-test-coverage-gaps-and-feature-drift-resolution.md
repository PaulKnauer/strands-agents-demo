# Story 3.3: Test Coverage Gaps & Feature Drift Resolution

Status: done

## Story

As a developer maintaining this codebase,
I want the test suite to accurately cover every specified AC and have no orphaned or misleading tests,
So that CI failures are trustworthy signals and the suite reflects the actual implementation contract.

## Acceptance Criteria

1. **Given** Story 2.1 and Story 2.2 story files exist, **When** I read their `Status:` field, **Then** both show `done` — not `review`. *(Finding 11)*

2. **Given** `deploy/app.py` validates `handle_invocation` input at the cloud boundary, **When** I read Story 2.1's AC list, **Then** a new AC #7 documents: empty/whitespace prompt → error string; prompt >4000 chars → error string; no Bedrock call made in either case. Tests `test_oversized_prompt_returns_error` and `test_empty_prompt_returns_error` cite this AC in their docstrings. *(Finding 3)*

3. **Given** `deploy/deploy.py` exists with error-handling, idempotency, env-var validation, and READY-polling logic, **When** I run `make test`, **Then** a new `tests/unit/test_deploy.py` covers: missing env var exits with code 1; `_handle_client_error` prints correct hint for each documented error code (AccessDeniedException, ResourceNotFoundException, InvalidClientTokenId, InvalidParameterException, unknown); `_find_existing_runtime` found/not-found/pagination; `_wait_for_ready` READY/FAILED/timeout; `_ensure_s3_bucket` us-east-1 vs other region; create vs update idempotency branch. *(Finding 4 — highest priority)*

4. **Given** `deploy/app.py` defines a `TOOLS` list with a `get_today_date` tool schema, **When** I run `make test`, **Then** `tests/evals/test_prompt_parity.py` includes a test asserting the tool name in `TOOLS[0]` matches the string `"get_today_date"`. *(Finding 10)*

5. **Given** `agent.py` REPL exits when user types "exit", "quit", or "q", **When** I run `make test`, **Then** a test exercises this path using mocked `input()` and a mocked agent. `agent.py` exposes a `run_repl(agent)` function (extracted from `__main__`) to make this testable without `runpy`. *(Finding 2 / Story 1.2 AC #9)*

6. **Given** static file contracts from Stories 1.1 and 1.3, **When** I run `make test`, **Then** `tests/unit/test_static.py` asserts: `requirements.txt` contains all five pinned/minimum deps from Story 1.1 AC #2; `.env.example` contains all four section headers and all five variable names from Story 1.1 AC #3; `.gitignore` excludes `.env`, `__pycache__/`, `.venv/`, `*.pyc`; `.vscode/launch.json` has `type=debugpy`, `console=integratedTerminal`, `envFile` pointing to `.env`; `.vscode/extensions.json` lists `ms-python.python` and `ms-python.vscode-pylance`; `agent.py` is under 150 lines. *(Findings 5, 6, 7)*

7. **Given** `test_verify.py TestMain.test_happy_path_exits_cleanly` exercises `_decode_body`, **When** I read the test, **Then** `_make_data` returns a JSON-encoded body string (e.g. `'"You are 13149 days old."'`) so `_decode_body` is exercised on the happy path, not bypassed. *(Finding 12)*

8. **Given** `test_behavioral_contracts.py` tests unparseable input, **When** I read `test_unparseable_date_response_has_no_number`, **Then** the input is `"I was born on the moon"` (not `"I was born yesterday"`) and the assertion rejects any number `\d+` in the response (not just 4+ digit numbers). *(Finding 13)*

9. **Given** `agent.py` silently skips empty REPL input, **When** I run `make test`, **Then** a test verifies `run_repl` with empty string input does not call the agent mock. *(Finding 14)*

10. **Given** `tests/integration/test_agent_loop.py` tests only mocked boto3 behavior (not the Strands SDK), **When** I read the file, **Then** it has been moved to `tests/unit/test_agent_loop.py` with a module docstring update noting it tests `_run_agent` protocol with mocked boto3. The `tests/integration/` folder is removed or replaced with a `README.md` stub noting real SDK integration tests require live credentials. *(Finding 8)*

11. **Given** `test_agent_loop.py test_single_tool_call_message_sequence` checks accumulated messages, **When** I read the assertion, **Then** it uses `call_args_list[-1]` (final accumulated state) instead of `call_args_list[0]`, and a comment explains the in-place mutation semantics. *(Finding 9)*

12. **Given** Finding 1 (behavioral contract tests are tautological against live LLM behavior), **When** I read the story, **Then** this finding is explicitly deferred with rationale: live-LLM eval requires real credentials and a separate eval harness strategy outside the scope of this story. Existing scripted behavioral contract tests are retained as-is — they validate `_run_agent` plumbing, not LLM prompt engineering. *(Finding 1 — DEFERRED)*

## Tasks / Subtasks

- [x] Task 1: Fix story file statuses for 2.1 and 2.2 (AC: #1)
  - [x] Edit `_bmad-output/implementation-artifacts/2-1-agentcore-deployment-script.md`: `Status: review` → `Status: done`
  - [x] Edit `_bmad-output/implementation-artifacts/2-2-endpoint-verification-and-observability-confirmation.md`: `Status: review` → `Status: done`

- [x] Task 2: Add retrospective AC #7 to Story 2.1 + cite in test docstrings (AC: #2)
  - [x] In `2-1-agentcore-deployment-script.md`, append AC #7: "**Given** the deployed agent receives an HTTP invocation payload, **When** the prompt key is missing, empty/whitespace, or exceeds 4000 characters, **Then** `handle_invocation` returns an error string without invoking the Bedrock Converse API."
  - [x] In `tests/unit/test_app.py`, add docstring to `test_oversized_prompt_returns_error`: `"""AC #7 (Story 2.1): prompt > 4000 chars → error, no Bedrock call."""`
  - [x] In `tests/unit/test_app.py`, add docstring to `test_empty_prompt_returns_error` and `test_missing_prompt_key_returns_error`: `"""AC #7 (Story 2.1): missing/empty prompt → error, no Bedrock call."""`

- [x] Task 3: Create `tests/unit/test_deploy.py` (AC: #3 — highest priority)
  - [x] Test `main()` missing each required env var exits with code 1 and prints helpful hint (patch `load_dotenv`, clear env vars)
  - [x] Test `_handle_client_error` AccessDeniedException prints IAM permissions hint
  - [x] Test `_handle_client_error` ResourceNotFoundException prints region hint
  - [x] Test `_handle_client_error` InvalidClientTokenId prints credentials hint
  - [x] Test `_handle_client_error` InvalidParameterException prints AGENT_NAME hint
  - [x] Test `_handle_client_error` unknown code prints generic hint
  - [x] Test `_find_existing_runtime` found → returns (id, arn)
  - [x] Test `_find_existing_runtime` not found → returns (None, None)
  - [x] Test `_find_existing_runtime` pagination follows nextToken
  - [x] Test `_wait_for_ready` status READY → returns immediately
  - [x] Test `_wait_for_ready` status FAILED → raises RuntimeError
  - [x] Test `_wait_for_ready` timeout → raises TimeoutError (mock `time.sleep`)
  - [x] Test `_ensure_s3_bucket` us-east-1 calls `create_bucket` WITHOUT `CreateBucketConfiguration`
  - [x] Test `_ensure_s3_bucket` other region calls `create_bucket` WITH `CreateBucketConfiguration`
  - [x] Test `_ensure_s3_bucket` existing bucket (head_bucket succeeds) → skips create
  - [x] Test `main()` idempotency: `_find_existing_runtime` returns existing id → `update_agent_runtime` called, not `create_agent_runtime` (patch all boto3 clients and subprocess)
  - [x] Run `make test` — all new tests must pass

- [x] Task 4: Add TOOLS parity test (AC: #4)
  - [x] In `tests/evals/test_prompt_parity.py`, add `test_tools_parity`: import `deploy.app.TOOLS`, assert `TOOLS[0]["toolSpec"]["name"] == "get_today_date"`
  - [x] Run `make test` — must pass

- [x] Task 5: Extract `run_repl` from `agent.py` and add REPL tests (AC: #5, #9)
  - [x] In `agent.py`: extract the `while True` REPL body (lines currently in `if __name__ == "__main__":`) into `def run_repl(agent) -> None`
  - [x] Keep `if __name__ == "__main__":` calling `run_repl(create_agent())`
  - [x] Verify `agent.py` stays under 150 lines after extraction (74 lines)
  - [x] Run `black agent.py --check` — must pass
  - [x] In `tests/unit/test_agent_tool.py`, add `TestRunRepl` class:
    - `test_exit_keyword_exits_repl` — mock `input` returning `"exit"`, assert mock agent never called (AC #9)
    - `test_quit_keyword_exits_repl` — same for `"quit"`
    - `test_q_keyword_exits_repl` — same for `"q"`
    - `test_empty_input_not_forwarded_to_agent` — mock `input` returning `["", "exit"]`, assert mock agent never called (AC #14 / Finding 14)
    - `test_valid_input_forwarded_to_agent` — mock `input` returning `["I was born 1 Jan 1990", "exit"]`, assert mock agent called once with correct string
  - [x] Run `make test` — all pass

- [x] Task 6: Create `tests/unit/test_static.py` (AC: #6)
  - [x] Use `pathlib.Path` relative to project root (resolve from `tests/unit/test_static.py`'s `__file__`)
  - [x] `test_requirements_txt_contains_strands_agents_pinned` — asserts `strands-agents==1.26.0`
  - [x] `test_requirements_txt_contains_all_deps` — asserts `strands-agents-tools`, `python-dotenv`, `boto3`, `bedrock-agentcore`
  - [x] `test_env_example_has_required_section_headers` — asserts all four `# ---` section headers from Story 1.1 AC #3
  - [x] `test_env_example_has_required_variables` — asserts MODEL_PROVIDER, MODEL_ID, AWS_REGION, AGENT_NAME, GOOGLE_API_KEY
  - [x] `test_env_example_has_no_real_credentials` — asserts file does not contain patterns matching real key formats (no `AKIA`/`ASIA`/`AROA` prefixes)
  - [x] `test_gitignore_excludes_env` — asserts `.env` in `.gitignore`
  - [x] `test_gitignore_excludes_pycache` — asserts `__pycache__/`
  - [x] `test_gitignore_excludes_venv` — asserts `.venv/`
  - [x] `test_gitignore_excludes_pyc` — asserts `*.pyc` or `*.py[cod]`
  - [x] `test_vscode_launch_json_has_correct_config` — parse JSON, assert type=`debugpy`, console=`integratedTerminal`, envFile contains `.env`
  - [x] `test_vscode_extensions_json_has_required_extensions` — assert `ms-python.python` and `ms-python.vscode-pylance` in recommendations
  - [x] `test_agent_py_under_150_lines` — `len(lines) < 150`
  - [x] Run `make test` — all pass

- [x] Task 7: Fix `test_verify.py` happy path to exercise `_decode_body` (AC: #7)
  - [x] In `tests/unit/test_verify.py`, update `_make_data` to return `{"response": '"You are 13149 days old."'}` (JSON-encoded string as body)
  - [x] Update `test_happy_path_exits_cleanly` assertion: `"13149"` still in `captured.out` (unchanged, but now exercises `_decode_body` unwrapping)
  - [x] Run `make test` — all pass

- [x] Task 8: Fix behavioral contract test input and assertion (AC: #8)
  - [x] In `tests/evals/test_behavioral_contracts.py`, update `test_unparseable_date_response_has_no_number`:
    - Changed input from `"I was born yesterday"` to `"I was born on the moon"`
    - Changed assertion from `not re.search(r"\b\d{4,}\b", result)` to `not re.search(r"\d+", result)` (reject any number, not just 4+)
    - Added docstring: `"""AC #5 (Story 1.2): unparseable input must not yield any numeric calculation."""`
  - [x] Run `make test` — all pass

- [x] Task 9: Move `tests/integration/` to `tests/unit/` (AC: #10)
  - [x] Move `tests/integration/test_agent_loop.py` → `tests/unit/test_agent_loop.py`
  - [x] Updated module docstring — honest naming for mock-only tests, notes real SDK tests require live credentials
  - [x] Deleted `tests/integration/__init__.py` and `tests/integration/` folder
  - [x] Verified no import paths reference `tests.integration`
  - [x] Run `make test` — all pass

- [x] Task 10: Fix in-place mutation assertion in `test_agent_loop.py` (AC: #11)
  - [x] In `TestAgentLoopMessageSequence.test_single_tool_call_message_sequence`: changed `call_args_list[0]` to `call_args_list[-1]`
  - [x] Added comment explaining in-place mutation semantics
  - [x] In `test_two_tool_calls_message_sequence`: same fix `call_args_list[-1]`
  - [x] Run `make test` — all pass

- [x] Task 11: Final validation
  - [x] Run `make lint` — black --check passes on all modified files
  - [x] Run `make test` — 101 tests pass (up from 43)
  - [x] Confirmed `agent.py` is 74 lines (under 150)

## Dev Notes

### Finding 1 — Explicitly Deferred

Behavioral contract tests in `tests/evals/test_behavioral_contracts.py` are scripted mock tests: they validate that `_run_agent` correctly passes the mock's return value back to the caller. They do NOT validate that the real LLM would behave per the SYSTEM_PROMPT instructions (AC #2–#5 of Story 1.2). This requires a live eval harness with real credentials. This is out of scope for Story 3.3. **Do not remove or rewrite the existing behavioral contract tests** — they have value as plumbing tests. The gap is documented, not fixed.

### TOOLS Schema in deploy/app.py

The TOOLS list structure (for AC #4 parity test):
```python
TOOLS = [
    {
        "toolSpec": {
            "name": "get_today_date",
            "description": "...",
            "inputSchema": {"json": {"type": "object", "properties": {}, "required": []}},
        }
    }
]
```
Assert `TOOLS[0]["toolSpec"]["name"] == "get_today_date"`.

### Testing deploy.py — Import Side Effects

`deploy/deploy.py` calls `load_dotenv()` at module level. This is harmless (silently no-ops if `.env` is absent). Do NOT patch `load_dotenv` at import time — only patch it inside `main()` tests where you need clean env control. Use `patch.dict(os.environ, {...}, clear=True)` to isolate env vars in each test.

`_handle_client_error` calls `sys.exit(1)` — use `pytest.raises(SystemExit) as exc` and assert `exc.value.code == 1`.

`_wait_for_ready` calls `time.sleep(10)` — patch `deploy.deploy.time.sleep` to avoid real sleeps.

### run_repl Extraction — agent.py

Current `__main__` block:
```python
if __name__ == "__main__":
    agent = create_agent()
    print("Age-in-Days Agent (type 'exit' to quit)")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ("exit", "quit", "q"):
            break
        if not user_input:
            continue
        response = agent(user_input)
        print(f"\nAgent: {response}")
```

Extract to:
```python
def run_repl(agent) -> None:
    """Run the interactive REPL loop until the user exits."""
    print("Age-in-Days Agent (type 'exit' to quit)")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ("exit", "quit", "q"):
            break
        if not user_input:
            continue
        response = agent(user_input)
        print(f"\nAgent: {response}")

if __name__ == "__main__":
    run_repl(create_agent())
```

This keeps `agent.py` well under 150 lines.

### test_static.py — Project Root Resolution

```python
import pathlib
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent  # tests/unit/ → tests/ → project root
```

Verify with `assert (PROJECT_ROOT / "agent.py").exists()` at top of module.

### test_verify.py `_make_data` Fix

Current (bypasses `_decode_body`):
```python
mock.invoke_agent_runtime.return_value = {"response": "You are 13149 days old."}
```

Fix (exercises `_decode_body` JSON unwrapping):
```python
mock.invoke_agent_runtime.return_value = {"response": '"You are 13149 days old."'}
```

The double-quotes make this a valid JSON string that `_decode_body` will unwrap to `"You are 13149 days old."`. The `"13149"` assertion in `test_happy_path_exits_cleanly` still passes.

### Files to Create / Modify

```
tests/unit/test_deploy.py          ← NEW: deploy.py coverage
tests/unit/test_static.py          ← NEW: static file AC checks
tests/unit/test_agent_loop.py      ← MOVED from tests/integration/
tests/unit/test_agent_tool.py      ← ADD: TestRunRepl class
tests/unit/test_app.py             ← ADD: docstrings citing AC #7
tests/unit/test_verify.py          ← FIX: _make_data JSON-encoded body
tests/evals/test_behavioral_contracts.py  ← FIX: input + assertion
tests/evals/test_prompt_parity.py  ← ADD: TOOLS parity test
agent.py                           ← EXTRACT: run_repl() function
_bmad-output/implementation-artifacts/2-1-agentcore-deployment-script.md  ← Status + AC #7
_bmad-output/implementation-artifacts/2-2-endpoint-verification-and-observability-confirmation.md  ← Status
tests/integration/                 ← DELETE folder
```

## Dev Agent Record

### Agent Model Used

_to be filled_

### Completion Notes List

_to be filled_

### File List

_to be filled_
