# Story 3.2: Inline Code Documentation & Project Structure Finalization

Status: review

## Story

As a developer reading the codebase for the first time,
I want every non-obvious code block to have an inline comment explaining *why* it exists, and the project structure to be self-explanatory from file and folder names alone,
So that I can understand the entire project within 5 minutes and confidently fork it to build my own agent.

## Acceptance Criteria

1. **Given** I read `agent.py`, **When** I encounter non-obvious blocks (e.g. `load_dotenv()` call, `os.environ[]` vs `os.environ.get()`, model provider branching, `@tool` docstring, REPL exit conditions), **Then** each has an inline comment explaining *why* — not just restating what the code does.

2. **Given** I read `deploy/deploy.py`, **When** I encounter non-obvious blocks (e.g. idempotency check, IAM policy construction, AgentCore registration call, error hint printing), **Then** each has an inline comment explaining *why*.

3. **Given** I look at the project root directory listing, **When** I read the file and folder names, **Then** I can immediately identify the purpose of each — without needing to open them.

4. **Given** I run `black agent.py` and `black deploy/deploy.py`, **When** black completes, **Then** it reports no changes — all files are PEP 8 compliant.

5. **Given** a developer wants to fork this project for a different use case, **When** they modify only `agent.py` (changing the tool and SYSTEM_PROMPT) and update `.env`, **Then** the rest of the project (deployment script, VS Code config, requirements) works without modification.

## Tasks / Subtasks

- [x] Task 1: Audit and complete inline comments in `agent.py` (AC: #1, #4)
  - [x] Verify `load_dotenv()` comment explains *why* it must precede `os.environ` access (already present — confirm it's clear)
  - [x] Add comment on `os.environ["MODEL_PROVIDER"]` explaining why `[]` not `.get()`: fail-fast on misconfiguration exposes problems immediately rather than silently falling back to a wrong default
  - [x] Verify BedrockModel credential chain comment is clear (already present)
  - [x] Add comment on `if user_input.lower() in ("exit", "quit", "q")`: explains why three aliases — covers natural user variations without adding complexity
  - [x] Add comment on `if not user_input: continue`: explains why empty input is silently skipped rather than forwarded to the LLM (avoids a no-op API call)
  - [x] Run `black agent.py --check` — must pass clean

- [x] Task 2: Audit and complete inline comments in `deploy/deploy.py` (AC: #2, #4)
  - [x] Verify `_find_existing_runtime` docstring explains the *why* of client-side pagination filter (already present — confirm)
  - [x] Verify idempotency comment on the create-vs-update branch is clear (already present)
  - [x] Verify IAM least-privilege comment explains *why* resources are scoped to specific ARNs (already present)
  - [x] Verify `put_role_policy` comment explains *why* it runs on every deploy not just creation (already present)
  - [x] Verify `agent_name.replace("-", "_")` comment explains the AgentCore naming constraint (already present)
  - [x] Run `black deploy/deploy.py --check` — must pass clean

- [x] Task 3: Fix wrong default model ID in `deploy/app.py` (housekeeping, not an AC but a correctness issue)
  - [x] Line: `model_id = os.environ.get("MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")`
  - [x] Change default to `anthropic.claude-3-haiku-20240307-v1:0` — matches confirmed working model and `.env.example`
  - [x] Also note: this `os.environ.get()` with a fallback contradicts the architecture's fail-fast principle for required vars; add a comment explaining the deliberate exception — in cloud context MODEL_ID is always injected by deploy.py, so the default only fires in misconfigured test scenarios
  - [x] Run `black deploy/app.py --check` — must pass clean

- [x] Task 4: Run full test suite to confirm no regressions (AC: #4, #5)
  - [x] `make lint` — must pass on all files
  - [x] `make test` — all 43 tests must pass

## Dev Notes

### What Already Has Good Comments

Do NOT add redundant comments to blocks that are already well-explained. The goal is *why*, not *what*. These are already covered:

**agent.py:**
- `load_dotenv()` (line 11) — has comment: "must be called before any os.environ access; it populates the environment from the .env file silently if not found" ✅
- BedrockModel credential chain (line 44-45) — has comment: "uses the default boto3 credential chain — no explicit credential passing needed" ✅
- Gemini import comment (line 40) — explains the optional extra requirement ✅
- `get_today_date` docstring — clear imperative docstring used by Strands as tool description ✅

**deploy/deploy.py:**
- `_find_existing_runtime` docstring — explains no server-side filter + pagination ✅
- `us-east-1` bucket creation branch (line 32) — explains `InvalidLocationConstraint` reason ✅
- `__pycache__` / `.pyc` exclusion (lines 93-101) — explains bytecode version-specificity ✅
- IAM resource scoping (line 137) — "no wildcard Resources (least-privilege)" ✅
- `put_role_policy` (line 172) — "Always update the inline policy so any permission changes take effect on re-deploy" ✅
- IAM propagation retry comment — "IAM roles are eventually consistent" ✅
- `agent_name.replace("-", "_")` (line ~282) — explains AgentCore naming constraint ✅

**deploy/app.py:**
- Module docstring — explains why boto3 not Strands SDK ✅
- `MAX_TURNS` / `MAX_PROMPT_CHARS` constants — have inline comments ✅
- `app.run(host="0.0.0.0")` — has comment explaining loopback vs 0.0.0.0 ✅
- `app.run()` unconditional call — has comment explaining `__main__` guard problem ✅

### What Needs Adding

**agent.py — two comment gaps:**

```python
# BEFORE (line 36):
provider = os.environ["MODEL_PROVIDER"]

# AFTER — add comment above:
# os.environ[] raises KeyError on missing vars — fail-fast surfaces misconfiguration
# immediately rather than silently running with a wrong provider or unexpected default
provider = os.environ["MODEL_PROVIDER"]
```

```python
# BEFORE (line 60):
if user_input.lower() in ("exit", "quit", "q"):
    break
if not user_input:
    continue

# AFTER — add comments:
# Accept common exit variations — users naturally type any of these
if user_input.lower() in ("exit", "quit", "q"):
    break
# Skip empty input silently — forwarding a blank string to the LLM wastes an API call
if not user_input:
    continue
```

### Wrong Default Model ID in app.py (Pre-existing Bug)

`deploy/app.py:59`:
```python
# CURRENT (wrong — sonnet is not available on standard accounts):
model_id = os.environ.get("MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

# CORRECT — haiku confirmed working (Story 2.2 debug log):
# MODEL_ID is always set by deploy.py's environmentVariables injection — the
# default here only fires in local test runs without .env, so we use haiku
# (confirmed available on standard accounts without Marketplace subscription)
model_id = os.environ.get("MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
```

This is NOT covered by the ACs but is a correctness fix that prevents a confusing silent failure if MODEL_ID is ever missing in the runtime environment.

### Architecture Compliance

- Comment the *why*, not the *what* (architecture.md §Process Patterns)
- `os.environ[]` for required vars — fail-fast (architecture.md §Communication Patterns)
- `os.environ.get()` only for optional vars — with explicit note when used for required vars
- `black` formatting must pass before marking any task complete (architecture.md §Enforcement Guidelines)

### Forkability Verification (AC #5)

The fork test is documentation-only — no code changes needed. Verify the claim holds by reading:
- `deploy/deploy.py` reads `MODEL_PROVIDER`, `MODEL_ID`, `AWS_REGION`, `AGENT_NAME` from env — no agent-specific logic hardcoded ✅
- `deploy/app.py` reads `MODEL_ID`, `AWS_REGION` from env — only the TOOLS list and SYSTEM_PROMPT are agent-specific ✅
- `.vscode/launch.json` runs `agent.py` — no tool-specific config ✅
- `requirements.txt` — no agent-specific dependencies ✅

Conclusion: A fork only needs `agent.py` (tool + SYSTEM_PROMPT) + `.env` changes. Confirm this is true and note it in the Dev Agent Record.

### Previous Story Learnings (from Story 3.1)

- Only modify `README.md` was the scope for 3.1. This story's scope is `agent.py`, `deploy/deploy.py`, `deploy/app.py` — do NOT touch README.md.
- `black --check` must pass on all modified files before marking tasks complete.
- The test suite covers agent.py and app.py behavior — run `make test` after any code change.

### Files to Create / Modify

```
agent.py            ← add 2 inline comments (why os.environ[], why exit aliases, why empty skip)
deploy/app.py       ← fix default model ID + add comment explaining .get() exception
deploy/deploy.py    ← audit only, likely no changes needed
```

No other files should be touched.

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Completion Notes List

- Added 3 inline comments to `agent.py`: fail-fast `os.environ[]` rationale, REPL exit alias rationale, empty input skip rationale.
- Fixed pre-existing bug in `deploy/app.py` line 59: wrong default model ID changed from `claude-3-sonnet-20240229-v1:0` to `claude-3-haiku-20240307-v1:0`; added comment explaining the deliberate `.get()` exception.
- Audited `deploy/deploy.py` — all required "why" comments already present, no changes needed.
- `black --check` passes clean on all three files.
- All 43 tests pass.

### File List

- `agent.py` (3 comments added)
- `deploy/app.py` (default model ID fixed + comment added)
