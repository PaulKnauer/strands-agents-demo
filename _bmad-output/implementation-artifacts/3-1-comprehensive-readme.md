# Story 3.1: Comprehensive README

Status: review

## Story

As a developer new to Strands and AgentCore,
I want a README that guides me from zero to a running local agent and deployed AgentCore instance — covering all prerequisites, steps, and troubleshooting — without requiring any prior knowledge of Strands or AgentCore,
So that I can follow it alone and reach a working, observable production agent.

## Acceptance Criteria

1. **Given** a developer new to Strands and AgentCore opens the README, **When** they read it, **Then** they understand the project's purpose, architecture, and what Strands + AgentCore provides — within the first screen of content.

2. **Given** the README exists, **When** I check its structure, **Then** it contains all of: table of contents, prerequisites (Python 3.11+, AWS account, Bedrock/Gemini access, AWS CLI), local setup (clone → venv → pip install → .env → run), AgentCore deployment, project structure, how it works (data flow diagram or description), troubleshooting, and contributing.

3. **Given** the troubleshooting section exists, **When** I read it, **Then** it covers at minimum: missing IAM permissions for AgentCore, wrong AWS region, missing or misconfigured env vars, and model access not enabled in Bedrock.

4. **Given** the README includes a credential warning, **When** I read the setup section, **Then** there is an explicit warning against committing `.env` or any credentials to version control.

5. **Given** a developer follows the README local setup section step by step, **When** they complete all steps, **Then** they can run `python agent.py` and interact with the agent — with no additional steps required beyond what is documented.

6. **Given** a developer follows the README AgentCore deployment section, **When** they complete all steps, **Then** they can run `python deploy/deploy.py` and have a working deployed agent — with no manual AWS console steps.

## Tasks / Subtasks

- [x] Task 1: Replace the existing BMAD boilerplate `README.md` with the Strands agent demo README (AC: #1, #2, #5, #6)
  - [x]Open with a concise project summary — what it is, what it demonstrates, and who it's for — visible without scrolling
  - [x]Include a table of contents linking to all major sections
  - [x]Provide a "What This Demonstrates" section calling out: `@tool` decorator pattern, AgentCore automatic observability, model provider switching, zero custom logging
  - [x]Write the data flow clearly — user input → REPL → Agent() → LLM → tool call → `get_today_date` → LLM response → terminal

- [x] Task 2: Write the Prerequisites section (AC: #2)
  - [x]Python 3.11+ (with install link)
  - [x]AWS account with Bedrock access enabled for `anthropic.claude-3-haiku-20240307-v1:0` in `us-east-1`
  - [x]AWS CLI configured (`aws configure`) OR `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` env vars
  - [x]For AgentCore deployment: IAM permissions listed (bedrock-agentcore-control:*, s3:*, iam:CreateRole, iam:PutRolePolicy, sts:GetCallerIdentity)
  - [x]Optional: Google Gemini API key (for Gemini fallback path only)

- [x] Task 3: Write the Local Setup section (AC: #2, #4, #5)
  - [x]Step 1: Clone the repo
  - [x]Step 2: Create and activate venv — exact commands for macOS/Linux and Windows
  - [x]Step 3: `pip install -r requirements.txt`
  - [x]Step 4: Copy `.env.example` to `.env`, fill in required vars — with a clear ⚠️ **CREDENTIAL WARNING** block explicitly warning against committing `.env`
  - [x]Step 5: `python agent.py` — with an example interaction showing real output
  - [x]Note the `make` shortcuts: `make install`, `make run`

- [x] Task 4: Write the AgentCore Deployment section (AC: #2, #6)
  - [x]Prerequisites: confirm Story 2.1 is complete (local agent working first)
  - [x]Step 1: Ensure `AGENT_NAME` and `AWS_REGION` are set in `.env`
  - [x]Step 2: `python deploy/deploy.py` (or `make deploy`) — describe the 5-step output
  - [x]Step 3: `python deploy/verify.py` (or `make verify`) — describe expected output
  - [x]Step 4: Open AgentCore console to confirm tool traces are visible
  - [x]Teardown: `python deploy/teardown.py` (or `make teardown`) to delete resources

- [x] Task 5: Write the Project Structure section (AC: #2)
  - [x]Annotated directory tree with one-line purpose for every file
  - [x]Explain the local vs cloud split: `agent.py` (Strands SDK, local REPL) vs `deploy/app.py` (boto3 direct, cloud runtime)
  - [x]Note `_bmad-output/` and `_bmad/` are BMAD planning artifacts, not part of the agent implementation

- [x] Task 6: Write the How It Works section (AC: #1, #2)
  - [x]Data flow: user input → REPL loop → `Agent()` → Bedrock/Gemini LLM → tool call decision → `get_today_date()` returns ISO date → LLM calculates days → response printed
  - [x]Why tool use matters: explains the @tool decorator pattern and why AgentCore traces it automatically
  - [x]Model provider switching: show the two-variable env var pattern, confirm no code changes required

- [x] Task 7: Write the Troubleshooting section (AC: #3)
  - [x]`AccessDeniedException` / missing IAM permissions — link to bedrock-agentcore devguide
  - [x]Wrong AWS region — AgentCore only available in select regions
  - [x]`KeyError: MODEL_PROVIDER` or similar — missing `.env` or vars not set
  - [x]Model access not enabled in Bedrock — how to enable `anthropic.claude-3-haiku-20240307-v1:0`
  - [x]`venv/bin/python: No such file or directory` — reminder to create and activate venv first
  - [x]Agent deployed but verify fails — check runtime status in AgentCore console

- [x] Task 8: Write the Contributing section (AC: #2)
  - [x]Brief — follow BMAD workflow; `make lint` and `make test` must pass; no credential commits

- [x] Task 9: VS Code F5 note (brief, under Local Setup or separate sub-section)
  - [x]Mention `.vscode/launch.json` enables F5 debug with `.env` auto-loaded

## Dev Notes

### Overwrite the Existing README

The current `README.md` is BMAD framework boilerplate — it describes the BMAD methodology and agent team roster. It must be **replaced entirely** with the Strands agent demo README. Do NOT append to it. The BMAD framework documentation is already in `_bmad/` and does not need to be preserved in `README.md`.

### Actual Tested Values — Use These Exactly

These are the verified working values from Story 2.2 implementation:

```bash
MODEL_PROVIDER=bedrock
MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0   # NOT claude-3-sonnet — haiku is confirmed working
AWS_REGION=us-east-1
AGENT_NAME=age-in-days-demo
```

**Important:** Earlier planning artifacts reference `anthropic.claude-3-sonnet-20240229-v1:0` but this model requires AWS Marketplace subscription. The working model is haiku. Use haiku in all README examples. See `.env.example` for the canonical values.

### Platform Architecture Note

`deploy/deploy.py` downloads `manylinux2014_x86_64` wheels (fixed during security review session — was incorrectly aarch64). The AgentCore PYTHON_3_12 runtime is x86_64. Do NOT mention aarch64 in the README.

### Local vs Cloud Architecture Split — Explain This

A key point of confusion for new developers: `agent.py` and `deploy/app.py` serve different roles:

| File | Runtime | Framework | Purpose |
|------|---------|-----------|---------|
| `agent.py` | Local | Strands Agents SDK | Interactive REPL, demonstrates @tool pattern |
| `deploy/app.py` | AWS AgentCore | boto3 direct | Cloud entrypoint, uses Bedrock Converse API directly |

The README should explain *why* they differ: Strands SDK cannot be pip-installed within AgentCore's 30-second startup window, so `app.py` uses boto3 directly. But the agent behaviour (system prompt, tool logic) is identical.

### Test Suite Exists

The project has 43 passing tests. Mention `make test` in the contributing section and README. The CI badge can be included if desired.

### Make Targets Available

Document these in the README:
```
make install   # create venv + pip install
make run       # python agent.py
make deploy    # python deploy/deploy.py
make verify    # python deploy/verify.py
make teardown  # python deploy/teardown.py
make lint      # black --check all files
make test      # unit + integration + eval tests
```

### Data Flow (for "How It Works" section)

```
User types: "I was born on 14th March 1990"
    ↓
REPL loop (agent.py) passes to Strands Agent()
    ↓
Strands sends to LLM (Bedrock/Gemini) with system prompt + tool list
    ↓
LLM decides: call get_today_date tool
    ↓
get_today_date() returns: "2026-03-18"
    ↓
LLM calculates: days between 1990-03-14 and 2026-03-18
    ↓
LLM responds: "You were born 13,149 days ago! 🎂"
    ↓
Response printed to terminal
```

In AgentCore (cloud), the same flow happens via `app.py` with the Bedrock Converse API, and every tool call step is automatically traced and visible in the console.

### Architecture References

- [Source: architecture.md#Requirements Overview] — NFR14, NFR15, NFR16 (forkable, self-explanatory, <5 min to understand)
- [Source: architecture.md#Authentication & Security] — credential pattern documentation requirements
- [Source: epics.md#Story 3.1] — FR26 (complete understanding from README alone), FR27 (required sections)
- [Source: epics.md#NFR7] — explicit credential warning required
- [Source: deploy/deploy.py] — 5-step deployment sequence for documentation accuracy
- [Source: .env.example] — canonical variable names and descriptions

### Previous Story Learnings

From Story 2.2 debug log (critical for README accuracy):
- `anthropic.claude-3-sonnet-20240229-v1:0` does NOT work on standard accounts — requires Marketplace subscription
- `anthropic.claude-3-haiku-20240307-v1:0` is the confirmed working model
- AgentCore runtime names forbid hyphens — `age-in-days-demo` → `age_in_days_demo` automatically
- boto3 must be bundled in the deployment ZIP (it is NOT pre-installed in AgentCore PYTHON_3_12 despite documentation suggesting otherwise)
- `host="0.0.0.0"` is required in `app.run()` — default 127.0.0.1 causes health check timeout

### Files to Create / Modify

```
README.md    ← overwrite entirely — replace BMAD boilerplate with Strands agent demo README
```

No other files should be touched in this story.

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Completion Notes List

- Replaced BMAD framework boilerplate README entirely with Strands agent demo README.
- All 9 tasks and all subtasks completed in a single pass.
- README covers all required AC sections: ToC, prerequisites, local setup, AgentCore deployment, project structure, how it works (ASCII data flow), make targets, troubleshooting (7 scenarios), contributing.
- Credential warning (⚠️) present in Local Setup before `.env` editing step — satisfies NFR7 / AC #4.
- Uses confirmed working model `anthropic.claude-3-haiku-20240307-v1:0` throughout (not sonnet).
- Explains local/cloud split (`agent.py` vs `deploy/app.py`) with rationale — key developer insight.
- All 43 existing tests pass; `make lint` clean; only `README.md` modified.

### File List

- `README.md` (replaced)
