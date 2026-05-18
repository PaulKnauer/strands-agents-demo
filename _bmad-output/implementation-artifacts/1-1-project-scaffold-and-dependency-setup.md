# Story 1.1: Project Scaffold & Dependency Setup

Status: done

## Story

As a developer,
I want the project scaffold created with all required files (`requirements.txt`, `.env.example`, `.gitignore`, and an `agent.py` stub),
so that I can install dependencies and begin developing without any undocumented manual steps.

## Acceptance Criteria

1. **Given** Python 3.11+ is installed and a virtual environment is active, **When** I run `pip install -r requirements.txt`, **Then** it completes without errors.

2. **Given** I examine `requirements.txt`, **When** I read it, **Then** it contains exactly these pinned dependencies:
   - `strands-agents==1.26.0`
   - `strands-agents-tools`
   - `python-dotenv>=1.0.0`
   - `boto3>=1.34.0`
   - `bedrock-agentcore` (marked with a `# deploy dependency` comment)

3. **Given** I examine `.env.example`, **When** I read it, **Then** it contains all required variables (MODEL_PROVIDER, MODEL_ID, AWS_REGION, AGENT_NAME, GOOGLE_API_KEY) with description comments directly above each variable, grouped by exactly: `# --- LLM Configuration ---`, `# --- AWS Configuration (required for Bedrock and AgentCore deployment) ---`, `# --- AgentCore Deployment ---`, and `# --- Optional: Google Gemini (only if MODEL_PROVIDER=gemini) ---` — and it contains no real credentials.

4. **Given** `.env.example` is copied to `.env` and filled with valid credentials, **When** `agent.py` stub is run, **Then** `load_dotenv()` executes without errors and `python agent.py` exits cleanly printing the stub message.

5. **Given** I examine `.gitignore`, **When** I read it, **Then** `.env`, `__pycache__/`, `.venv/`, and `*.pyc` are all excluded from version control.

## Tasks / Subtasks

- [x] Task 1: Create `requirements.txt` (AC: #1, #2)
  - [x] Add `strands-agents==1.26.0`
  - [x] Add `strands-agents-tools`
  - [x] Add `python-dotenv>=1.0.0`
  - [x] Add `boto3>=1.34.0`
  - [x] Add `bedrock-agentcore` with comment `# deploy dependency`
  - [x] Verify `pip install -r requirements.txt` succeeds in a clean venv

- [x] Task 2: Create `.env.example` (AC: #3, #4)
  - [x] Add `# --- LLM Configuration ---` group with MODEL_PROVIDER and MODEL_ID
  - [x] Add `# --- AWS Configuration (required for Bedrock and AgentCore deployment) ---` group with AWS_REGION
  - [x] Add `# --- AgentCore Deployment ---` group with AGENT_NAME
  - [x] Add `# --- Optional: Google Gemini (only if MODEL_PROVIDER=gemini) ---` group with GOOGLE_API_KEY commented out
  - [x] Ensure every variable has a description comment directly above it (including GOOGLE_API_KEY — not just a section header)
  - [x] Ensure no real credentials are present

- [x] Task 3: Create/update `.gitignore` (AC: #5)
  - [x] Ensure `.env` is excluded
  - [x] Ensure `__pycache__/` is excluded
  - [x] Ensure `.venv/` is excluded
  - [x] Ensure `*.pyc` is excluded
  - [x] Note: `.gitignore` already existed and already covered all requirements — no changes needed

- [x] Task 4: Create `agent.py` stub (AC: #4)
  - [x] Add module-level imports: `import os`, `from dotenv import load_dotenv` — ONLY these two
  - [x] Call `load_dotenv()` at module level (before any `os.environ` access)
  - [x] Add placeholder comments for: SYSTEM_PROMPT, tool definition, Agent instantiation, REPL loop
  - [x] ⚠️ DO NOT add `from strands import Agent, tool` — Story 1.2 only
  - [x] ⚠️ DO NOT add `from strands.models import BedrockModel` — Story 1.2 only
  - [x] ⚠️ DO NOT add `import datetime` — Story 1.2 only
  - [x] Do NOT instantiate BedrockModel, Agent, or any Strands objects — this story is scaffold only
  - [x] Print `"Agent stub — implement in Story 1.2"` in the `if __name__ == "__main__":` guard
  - [x] Ensure the stub is runnable (no import errors, no crashes on `python agent.py`)

- [x] Task 5: Run `black` on `agent.py` (architecture requirement)
  - [x] `pip install black` if not present
  - [x] Run `black agent.py` — black added one blank line after docstring (PEP 8); `--check` now passes clean

## Dev Notes

### Critical Architecture Constraints

**ALL of the following must be followed exactly — no exceptions:**

- `load_dotenv()` MUST be called at module level before ANY `os.environ` access — even in the stub. [Source: architecture.md#Communication Patterns]
- Required env vars use `os.environ["VAR"]` (fail-fast KeyError). Optional vars use `os.environ.get("VAR")`. Do NOT use `.get()` with silent defaults for required vars. [Source: architecture.md#Communication Patterns]
- `agent.py` MUST stay under 150 lines total (including comments). The stub should be well under this. [Source: architecture.md#NFR12]
- All function names and variables: `snake_case`. All env var names: `UPPER_SNAKE_CASE`. [Source: architecture.md#Naming Patterns]
- Run `black agent.py` before completing this story — it must produce no changes. [Source: architecture.md#Code Formatter]
- NO hardcoded credentials, model IDs, or region strings anywhere. [Source: architecture.md#NFR3]

### Exact `.env.example` Content

The architecture specifies the complete variable set with exact groupings:

```bash
# --- LLM Configuration ---
# Provider: "bedrock" (Amazon Bedrock) or "gemini" (Google Gemini)
MODEL_PROVIDER=bedrock

# Model ID — Bedrock: "us.amazon.nova-micro-v1:0"
#           — Gemini: "gemini-2.0-flash"
MODEL_ID=us.amazon.nova-micro-v1:0

# --- AWS Configuration (required for Bedrock and AgentCore deployment) ---
AWS_REGION=us-east-1

# --- AgentCore Deployment ---
# Name for your agent in AgentCore (used for idempotency check)
AGENT_NAME=age-in-days-demo

# --- Optional: Google Gemini (only if MODEL_PROVIDER=gemini) ---
# Your Google AI Studio API key (required when MODEL_PROVIDER=gemini)
# GOOGLE_API_KEY=your-gemini-api-key-here
```

Use this exact format — variable groupings, comment style, and example values are all architectural decisions. [Source: architecture.md#Integration Points]

### Exact `requirements.txt` Content

```
strands-agents==1.26.0
strands-agents-tools
python-dotenv>=1.0.0
boto3>=1.34.0
bedrock-agentcore  # deploy dependency
```

Note: `bedrock-agentcore` is the PyPI package for the AWS AgentCore SDK. The `# deploy dependency` comment signals to developers that this is only needed for deployment, not local agent execution. [Source: architecture.md#Gap Analysis]

### `agent.py` Stub Structure — Story 1.1 ONLY

⚠️ **This is a scaffold stub only. Story 1.2 replaces this file entirely.**

The stub imports ONLY `os` and `load_dotenv` — NO Strands SDK imports. Adding `from strands import ...` or `from strands.models import ...` here is a scope violation; those belong exclusively in Story 1.2.

```python
"""Age-in-Days Agent — Strands Agents SDK demo."""
import os

from dotenv import load_dotenv

# load_dotenv() must be called before any os.environ access;
# it populates the environment from the .env file silently if not found
load_dotenv()

# TODO Story 1.2: Define SYSTEM_PROMPT constant here

# TODO Story 1.2: Define get_today_date @tool here

# TODO Story 1.2: Instantiate BedrockModel/GeminiModel and Agent here

# TODO Story 1.2: Implement REPL loop here

if __name__ == "__main__":
    print("Agent stub — implement in Story 1.2")
```

**Forbidden imports for this story (Story 1.2 only):**
- `import datetime` — only needed by `get_today_date()` tool
- `from strands import Agent, tool` — Story 1.2
- `from strands.models import BedrockModel` — Story 1.2
- `from strands.models.gemini import GeminiModel` — Story 1.2

This gives Story 1.2 a clean starting point without pre-implementing anything. [Source: architecture.md#Implementation Sequence]

### Project Structure for This Story

Files to create in this story:

```
strands-agents-demo/
├── agent.py                  ← stub (creates in this story)
├── requirements.txt          ← full pinned deps (creates in this story)
├── .env.example              ← all vars documented (creates in this story)
└── .gitignore                ← update existing or create (this story)
```

Files NOT touched in this story (belong to later stories):
- `.vscode/` — Story 1.3
- `deploy/deploy.py` — Story 2.1
- `README.md` — Story 3.1

[Source: architecture.md#Complete Project Directory Structure]

### No Automated Tests

There are no automated tests at MVP. Acceptance testing for this story is manual:
- `pip install -r requirements.txt` in a clean venv → must succeed
- `python agent.py` → must print stub message without errors
- Read `.env.example` and verify groupings and variable completeness

[Source: architecture.md#Testing Infrastructure]

### Project Structure Notes

- This is a greenfield project. No existing `agent.py`, `requirements.txt`, or `.env.example` exist yet.
- The `_bmad/` and `_bmad-output/` directories already exist for BMAD framework — do not touch them.
- The `.gitignore` may already exist (noted in architecture) — inspect before writing to avoid overwriting any existing entries.

### References

- [Source: architecture.md#Starter Template] — Hand-crafted minimal Python, no scaffold generator
- [Source: architecture.md#Pinned Dependencies] — Exact package versions
- [Source: architecture.md#Integration Points] — Complete .env.example variable set
- [Source: architecture.md#Naming Patterns] — PEP 8 naming conventions
- [Source: architecture.md#Communication Patterns] — load_dotenv() and os.environ[] patterns
- [Source: architecture.md#Code Formatter] — black, run before completing any story
- [Source: epics.md#Story 1.1] — Acceptance criteria

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- `black` initially reformatted `agent.py` (added blank line after module docstring per PEP 8 E302). Applied black formatting then verified `--check` passes clean.
- `.gitignore` already existed with all required entries — no changes made.

### Completion Notes List

- Created `requirements.txt` with exact pinned dependencies from architecture spec. Verified `pip install -r requirements.txt` succeeds in a fresh venv (Python 3.14.3 / pip 26.0). All packages installed successfully including `bedrock-agentcore==1.4.6`.
- Created `.env.example` with exact variable set and groupings from architecture spec. No real credentials. Includes `!.env.example` exclusion already handled by existing `.gitignore`.
- `.gitignore` already had all required entries (`.env`, `__pycache__/`, `.venv/`, `*.py[cod]` covering `*.pyc`). No changes required.
- Created `agent.py` stub with `load_dotenv()` at module level, TODO placeholders for Story 1.2 implementation. `python agent.py` prints stub message cleanly.
- `black --check agent.py` passes with no changes after initial formatting fix.

### File List

- `requirements.txt` (created)
- `.env.example` (created)
- `.gitignore` (pre-existing, no changes needed — all AC #5 requirements already satisfied)
- `agent.py` (created)
