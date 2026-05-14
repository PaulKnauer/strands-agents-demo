# Story 3.2: Inline Explanation and Structure Clarity

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer reading the repo for the first time,
I want the code and structure to explain themselves,
so that I can confidently adapt the project for my own use case.

## Acceptance Criteria

1. Given I inspect the local and deployed runtime code, when I encounter non-obvious logic such as env loading, adapter boundaries, deployment packaging, guardrail wiring, observability instrumentation, or IAM setup, then I find concise inline comments explaining why the code exists, and the comments do not merely restate the syntax.

2. Given I inspect the project tree, when I review the top-level files and key folders, then their purposes are immediately understandable, and a developer can identify where to change agent behavior versus deployment behavior.

3. Given I run formatting or static convention checks aligned with the project rules, when I validate the maintained files, then the code remains PEP 8 compliant, and the project still respects the documented structural constraints such as the lean `agent.py` rule.

4. Given this repo has older Story 3.2 artifacts under a different title, when I implement this story, then I treat `3-2-inline-explanation-and-structure-clarity` and the current `sprint-status.yaml` entry as authoritative, and I do not overwrite unrelated legacy artifacts.

5. Given the local and cloud runtime paths intentionally duplicate some agent-specific surfaces, when I document or comment forkability, then the guidance explicitly says that a use-case fork must update both `agent.py` and `deploy/app.py` where behavior is duplicated, while keeping deployment scaffolding, VS Code config, Makefile targets, and dependency scaffolding reusable.

## Tasks / Subtasks

- [x] Task 1: Audit local runtime explanation clarity (AC: #1, #3)
  - [x] Read `agent.py` completely before editing.
  - [x] Verify `load_dotenv()` is still explained as a required ordering constraint before `os.environ` access.
  - [x] Verify required env access uses `os.environ[...]` where misconfiguration should fail fast.
  - [x] Verify `create_agent()` comments or surrounding structure make clear that local model construction is delegated to `model_adapters.py`.
  - [x] Verify `get_today_date()` has a clear Strands tool docstring and returns strings, not dicts or raised exceptions.
  - [x] Verify `run_repl()` explains non-obvious behavior such as exit aliases and silently skipping empty input.
  - [x] Keep `agent.py` under 150 lines after any edits.

- [x] Task 2: Audit adapter boundary explanation clarity (AC: #1, #2)
  - [x] Read `model_adapters.py` completely before editing.
  - [x] Ensure the module-level docstring continues to say this is local-only and must not be imported by `deploy/app.py`.
  - [x] Ensure `BedrockAdapter` guardrail behavior is understandable without implying guardrails are mandatory.
  - [x] Ensure `GeminiAdapter` lazy import rationale is clear because the Gemini extra is optional.
  - [x] Do not add new providers in this story. Provider expansion belongs to Epic 4.

- [x] Task 3: Audit deployed runtime explanation clarity (AC: #1, #2, #5)
  - [x] Read `deploy/app.py` completely before editing.
  - [x] Verify the module docstring accurately explains why cloud runtime uses direct `boto3` Bedrock Converse calls instead of importing Strands or `agent.py`.
  - [x] Verify comments preserve the local/cloud split: `agent.py` is local REPL, `deploy/app.py` is AgentCore runtime.
  - [x] Verify system prompt parity is called out where useful, and do not change prompt text unless a test or story requirement demands it.
  - [x] Verify tool schema, tool result handling, `MAX_TURNS`, `MAX_PROMPT_CHARS`, guardrail config, OTEL spans, deterministic age response path, and `app.run(host="0.0.0.0")` have comments only where the "why" is not obvious.
  - [x] Remove or correct any stale comment that conflicts with current behavior, tests, or README.

- [x] Task 4: Audit deployment and verification script explanation clarity (AC: #1, #2)
  - [x] Read `deploy/deploy.py` and `deploy/verify.py` before editing either file.
  - [x] In `deploy/deploy.py`, verify comments/docstrings accurately explain S3 bucket creation in `us-east-1`, deployment ZIP contents, bundled Linux wheels, runtime entrypoint, idempotent create/update behavior, runtime role lookup, least-privilege model ARNs, and AgentCore name sanitization.
  - [x] In `deploy/verify.py`, verify comments/docstrings accurately explain JSON response decoding, runtime READY waiting, prompt age assertion, observability preflight, and non-fatal diagnostics.
  - [x] If comments disagree with actual code or tests, update the comments rather than changing behavior unless a real bug is discovered.

- [x] Task 5: Audit project structure clarity surfaces (AC: #2, #5)
  - [x] Compare `README.md` project structure guidance with the actual top-level files and key folders.
  - [x] Confirm a reader can tell that `agent.py` and `model_adapters.py` are local runtime surfaces, `deploy/` is cloud runtime/deployment, `infra/` is CDK support, `compliance/` is governance/audit support, and `_bmad-output/` contains planning/implementation artifacts.
  - [x] If README structure guidance is stale, update only the relevant lines and keep the README concise.
  - [x] Do not rename files or move folders unless existing names actively contradict their purpose; this story is mainly clarity, not restructuring.

- [x] Task 6: Validate formatting and contract tests (AC: #3)
  - [x] Run `make lint`.
  - [x] Run `make test`.
  - [x] If edits touch deployment packaging or runtime behavior, pay special attention to `tests/unit/test_deploy.py`, `tests/unit/test_app.py`, `tests/evals/test_prompt_parity.py`, and `tests/unit/test_static.py`.
  - [x] Confirm `agent.py` remains below the static-test line limit.

### Review Findings

- [x] [Review][Patch] Story status history is inconsistent [_bmad-output/implementation-artifacts/3-2-inline-explanation-and-structure-clarity.md:150]
- [x] [Review][Patch] README project tree still lists missing integration tests folder [README.md:330]
- [x] [Review][Patch] Overlong new inline comment [deploy/app.py:253]
- [x] [Review][Patch] Forkability guidance remains contradictory [README.md:19]
- [x] [Review][Defer] Future DOB returns negative age [deploy/app.py:167] — deferred, pre-existing

### Re-Review Findings

- [x] [Review][Patch] Story artifact misstates the final sprint-status change [_bmad-output/implementation-artifacts/3-2-inline-explanation-and-structure-clarity.md:158]
- [x] [Review][Patch] Epic 3 left in-progress after final required story is done [_bmad-output/implementation-artifacts/sprint-status.yaml:61]
- [x] [Review][Patch] Forkability guidance does not fully meet AC5 [README.md:19]

## Dev Notes

### Authoritative Scope

The current sprint status entry is `3-2-inline-explanation-and-structure-clarity`. There is an older completed artifact named `3-2-inline-code-documentation-and-project-structure-finalization.md`; use it only as historical context. Do not overwrite it, and do not assume its old completion state satisfies this current sprint entry without auditing current code.

### Critical Architecture Guardrails

- `agent.py` and `deploy/app.py` are intentionally separate runtime paths.
- `agent.py` uses Strands abstractions and the local REPL.
- `deploy/app.py` uses direct `boto3` Bedrock Converse calls for AgentCore and must not import `agent.py`, `model_adapters.py`, or `strands-agents`.
- Keep local and cloud `SYSTEM_PROMPT` behavior aligned unless there is an explicit, tested reason to diverge.
- `app.run(host="0.0.0.0")` in `deploy/app.py` must remain unconditional.
- `load_dotenv()` must run before `os.environ` access in local and deploy entrypoints.
- Required config should fail fast with `os.environ[...]`; optional config may use `os.environ.get()`.
- `agent.py` must remain lean and under 150 lines.
- Do not add new provider support in this story; Epic 4 owns provider expansion.
- Use comments sparingly and explain why a block exists. Avoid syntax narration.

### Current Repo Surfaces to Inspect

- `agent.py`: local Strands agent, `SYSTEM_PROMPT`, `get_today_date`, `create_agent()`, `run_repl()`.
- `model_adapters.py`: local-only provider adapter boundary for Bedrock and Gemini.
- `deploy/app.py`: AgentCore runtime entrypoint, direct Bedrock Converse protocol, cloud tool schema, OTEL spans, guardrail wiring, payload validation, unconditional `app.run`.
- `deploy/deploy.py`: deployment ZIP assembly, S3 artifact handling, AgentCore create/update, runtime role lookup, model ARN scoping, environment injection.
- `deploy/verify.py`: deployed runtime smoke test, expected age assertion, response decoding, observability diagnostics.
- `README.md`: project structure and forkability guidance.
- `tests/unit/test_static.py`: static contract checks, especially `agent.py` line count and project scaffold contracts.

### Previous Story Intelligence

Story 3.1 replaced the README with complete setup, deployment, project structure, troubleshooting, and contributing guidance. It also established that:

- The confirmed working deployed model examples use `us.amazon.nova-micro-v1:0` in the current code and `.env.example`, not legacy Sonnet values.
- Local and cloud paths differ by design: `agent.py` demonstrates Strands locally, while `deploy/app.py` handles AgentCore with direct Bedrock Converse.
- README accuracy matters because new developers rely on it without extra context.

Older Story 3.2 and its code review surfaced an important lesson: misleading comments are worse than missing comments. The dev agent must correct stale comments if they no longer match the code, deployment behavior, or tests.

Story 3.3 expanded tests substantially. Before changing behavior, inspect the current tests and prefer comment/doc updates where the issue is explanation drift rather than runtime logic.

### Testing Requirements

- Run `make lint` after any Python edits.
- Run `make test` before marking this story complete.
- If only Markdown changes are made, still run `make test` unless there is a clear environmental blocker, because static tests enforce documentation and scaffold contracts.
- Do not claim tests passed unless the commands were actually run in this workspace.

### Source References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 3.2: Inline Explanation and Structure Clarity`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Process Patterns`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries`]
- [Source: `_bmad-output/planning-artifacts/prd.md#Documentation Standards`]
- [Source: `_bmad-output/project-context.md#Critical Implementation Rules`]
- [Source: `_bmad-output/implementation-artifacts/3-1-comprehensive-readme.md#Previous Story Learnings`]
- [Source: `_bmad-output/implementation-artifacts/code-review-story-3-2-2026-03-18.md#Findings`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Task 1: `agent.py` already fully clear — `load_dotenv()` ordering comment, fail-fast `os.environ[]`, delegating `create_agent()`, string-returning tool docstring, and `run_repl()` exit/empty-input comments all present. No edits needed; 64 lines (well under 150).
- Task 2: Added inline comment to `BedrockAdapter.__init__` clarifying guardrails are optional (`# Guardrails are optional — only wired when GUARDRAIL_ID is configured`). Module docstring and GeminiAdapter lazy-import comment already present and correct.
- Task 3: Added comment to the deterministic short-circuit path in `deploy/app.py` explaining why the second LLM call is skipped when DOB and today's date are both resolved. All other surfaces (module docstring, system prompt parity, MAX_TURNS, guardrail config, OTEL spans, `app.run`) already well-commented.
- Task 4: `deploy/deploy.py` and `deploy/verify.py` fully clear — no stale or missing comments found. All non-obvious behaviors (us-east-1 S3 special case, manylinux wheels, JSON decode wrapping, non-fatal observability preflight) already explained.
- Task 5: Added `model_adapters.py` and `infra/` entries to the README project structure tree. Forkability guidance (update both `agent.py` and `deploy/app.py`) already present in the Why section.
- Task 6: `make lint` — 9 files unchanged. `make test` — 250 tests passed (243 unit + 7 eval). `agent.py` static-test line limit confirmed passing.

### File List

- `model_adapters.py` — added optional guardrail comment to `BedrockAdapter.__init__`
- `deploy/app.py` — added deterministic short-circuit comment before `if dob and today`
- `README.md` — added `model_adapters.py` and `infra/` entries to project structure tree
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — story status updated from backlog to done; epic-3 marked done after all Epic 3 stories completed

## Change Log

- 2026-05-13: Story 3.2 implemented — audited all 6 code surfaces for inline clarity; added 3 targeted comments (BedrockAdapter optional guardrails, app.py deterministic short-circuit, README structure tree), all 250 tests passing.
