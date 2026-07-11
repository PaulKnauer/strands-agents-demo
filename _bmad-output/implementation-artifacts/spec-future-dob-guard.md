---
title: 'Date-ordering guard for _format_age_response()'
type: 'bugfix'
created: '2026-07-08'
status: 'blocked'
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: []
baseline_revision: '3d9d727abf1fc2e6dd8a36a8c6a49305da33f8f2'
---

<intent-contract>

## Intent

**Problem:** `_format_age_response()` in `deploy/app.py` computes `age_days = (today - dob).days` with no validation of date order, so a future date of birth silently produces a negative age instead of a clear error.

**Approach:** Add a guard at the top of `_format_age_response()` that raises `ValueError` with an actionable message (naming both dates) when `dob > today`, before any age arithmetic runs.

## Boundaries & Constraints

**Always:**
- The guard lives inside `_format_age_response()` in `deploy/app.py`, checked before the `age_days = (today - dob).days` line.
- The raised exception is `ValueError`, with a message that states the violated invariant and includes both `dob.isoformat()` and `today.isoformat()`.
- `dob == today` (age 0) remains valid and must not raise.
- Existing behavior for `dob < today` is unchanged (no regression to `test_formats_age_with_date_arithmetic`).

**Block If:** None identified — this is a narrowly scoped, self-contained guard.

**Never:**
- Do not modify `agent.py` — it has no equivalent deterministic age-formatting function; the local REPL path relies on the LLM directly.
- Do not add exception handling around the `_format_age_response()` call site in `_run_agent()` / `handle_invocation()` to convert the `ValueError` into a user-facing string — out of scope; the raise itself is the deliverable for this task.
- Do not change `_parse_date_of_birth()` parsing behavior.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Valid past dob | dob=1990-03-14, today=2026-05-10 | "You were born on 1990-03-14. As of 2026-05-10, you are 13,206 days old." | No error expected |
| Same-day dob (age zero) | dob=2026-05-10, today=2026-05-10 | "...you are 0 days old." | No error expected |
| Future dob (boundary: one day ahead) | dob=2026-05-11, today=2026-05-10 | No string returned | Raises `ValueError` naming both dates |

</intent-contract>

## Code Map

- `deploy/app.py` -- `_format_age_response(dob, today)` at ~line 170; add the ordering guard as the first statement in the function body.
- `tests/unit/test_app.py` -- `TestDateParsing` class (~line 80) holds the existing `_format_age_response` coverage (`test_formats_age_with_date_arithmetic`); add the new boundary test(s) here.

## Tasks & Acceptance

**Execution:**
- [x] `deploy/app.py` -- add `if dob > today: raise ValueError(f"...")` as the first line of `_format_age_response()`, before `age_days = (today - dob).days` -- prevents negative-age output for a future date of birth
- [x] `tests/unit/test_app.py` -- add a test in `TestDateParsing` asserting `_format_age_response` raises `ValueError` when `dob` is one day after `today`, and a test confirming `dob == today` returns `"...0 days old."` without raising -- covers both sides of the boundary

**Acceptance Criteria:**
- Given a `dob` one day after `today`, when `_format_age_response(dob, today)` is called, then it raises `ValueError` whose message includes both dates' ISO strings.
- Given `dob == today`, when `_format_age_response(dob, today)` is called, then it returns a string containing "0 days old" without raising.
- Given `dob` before `today`, when `_format_age_response(dob, today)` is called, then behavior is unchanged from before this change.

## Spec Change Log

## Review Triage Log

### 2026-07-08 — Review pass
- intent_gap: 2: (high 1, medium 1, low 0)
- bad_spec: 0
- patch: 2: (high 0, medium 0, low 2)
- defer: 1: (high 0, medium 1, low 0)
- reject: 4
- addressed_findings:
  - none

Findings:
- `[high]` `[intent_gap]` The new `ValueError` in `_format_age_response()` is never caught anywhere in the call chain. `_run_agent()` calls it unguarded at deploy/app.py:280, and `handle_invocation()` (deploy/app.py:319-327) only catches `(ClientError, BotoCoreError)`. A future DOB now crashes the deployed AgentCore entrypoint with an unhandled exception, instead of returning a graceful `"Error: ..."` string like every other failure path in this file (missing MODEL_PROVIDER, unsupported provider, empty/oversized prompt, Bedrock ClientError). This also conflicts with the documented project convention "Return error strings rather than raising from tool helpers such as date retrieval paths" (project-context.md). Root cause: this spec's own `Never` clause under Boundaries & Constraints explicitly forbade adding call-site exception handling, which is what creates the crash regression. That clause was my own scoping decision during planning, not a literal instruction from the task text, and it now contradicts both the codebase's established error-handling convention and the practical goal of "preventing negative age output" gracefully. Needs a human decision: (a) keep the raise as literally requested and add a catch in `handle_invocation()`/`_run_agent()` that converts it to a graceful `"Error: ..."` string consistent with existing patterns, or (b) drop the raise and return an error string directly from `_format_age_response()` instead, matching project convention.
- `[medium]` `[intent_gap]` No test exercises the actual regression end-to-end (via `_run_agent`/`handle_invocation` with a future-DOB prompt) — both new tests call `_format_age_response` directly, so the unhandled-exception consequence at the entrypoint is unverified. Depends on the above decision before a meaningful end-to-end test can be written.
- `[low]` `[patch]` (not applied — moot, cascaded) `_format_age_response`'s docstring has no `Raises:` note documenting the new exception contract.
- `[low]` `[patch]` (not applied — moot, cascaded) No comment explaining why `dob == today` is valid but `dob == today + 1 day` is fatal (intentional asymmetry, but undocumented).
- `[medium]` `[defer]` `_parse_date_of_birth()` has no upper bound on parsed years, so implausible/future dates parse successfully with no earlier validation — pre-existing gap, not introduced by this change, but it's what allows a future DOB to reach the new guard at all.
- reject (noise, dropped silently): dual-runtime parity gap raised against `agent.py` (no equivalent function exists there to sync); request for a regression test locking down the old negative-day string; request that the `dob == today` test also drive the full agentic loop; black/lint compliance concern (already verified clean via `black --check` and `pytest`, both passing).

## Verification

**Commands:**
- `pytest tests/unit/test_app.py -q` -- expected: all tests pass, including the two new boundary tests.
- `make lint` -- expected: `black --check` passes with no diff.

## Auto Run Result

Status: blocked
Blocking condition: intent gap in intent contract

Code changes were implemented and unit-tested successfully (33/33 tests passing, `black --check` clean), then reverted per the intent_gap protocol after review surfaced a real defect in the spec's own scoping decision — see `## Review Triage Log` above for full detail. Summary for the human decision needed:

`_format_age_response()` was given a guard that raises `ValueError` on a future DOB, exactly as instructed. But nothing in the call chain (`_run_agent()` → `handle_invocation()`) catches anything except `(ClientError, BotoCoreError)`, so this now crashes the deployed AgentCore entrypoint on a future DOB instead of returning a graceful `"Error: ..."` string like every other failure path in `deploy/app.py`. This spec's `Never` clause explicitly forbade adding call-site handling to fix that, which was my own scoping choice during planning — not part of the literal task text — and it conflicts with the project's own documented convention ("Return error strings rather than raising from tool helpers").

Please choose one before re-running this spec:
- **(a)** Keep the raise as-is, and additionally catch it in `handle_invocation()` (or `_run_agent()`) to convert it into a graceful `"Error: ..."` string, consistent with every other error path in the file.
- **(b)** Drop the raise; have `_format_age_response()` return an `"Error: ..."` string directly instead, matching the project's error-string convention and avoiding the need for a new catch clause.

Once decided, resume this spec (`_bmad-output/implementation-artifacts/spec-future-dob-guard.md`) — its `status` is `blocked`.
