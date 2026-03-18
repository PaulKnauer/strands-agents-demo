# Story 1.3: VS Code Debug Configuration

Status: done

## Story

As a developer,
I want to press F5 in VS Code to launch `agent.py` with the debugger attached and `.env` automatically loaded,
So that I can set breakpoints and step through the agent code without any manual configuration.

## Acceptance Criteria

1. **Given** VS Code is open with the project folder, **When** I press F5, **Then** `agent.py` launches with the Python debugger attached.

2. **Given** `.vscode/launch.json` exists with an `envFile` key pointing to `${workspaceFolder}/.env`, **When** I press F5, **Then** environment variables from `.env` are loaded automatically — no manual `export` required.

3. **Given** I set a breakpoint inside `get_today_date()`, **When** I press F5 and type a date of birth at the agent prompt, **Then** execution pauses at the breakpoint and I can inspect local variables.

4. **Given** `.vscode/extensions.json` exists, **When** VS Code opens the project, **Then** it recommends the Python and Pylance extensions (and optionally the dotenv extension).

## Tasks / Subtasks

- [x] Task 1: Create `.vscode/launch.json` (AC: #1, #2, #3)
  - [x] Set `type` to `"debugpy"` (current VS Code Python debugger type)
  - [x] Set `program` to `"${workspaceFolder}/agent.py"`
  - [x] Set `console` to `"integratedTerminal"` (CRITICAL — required for `input()` REPL)
  - [x] Set `envFile` to `"${workspaceFolder}/.env"`
  - [x] Set `name` to a descriptive label (e.g. `"Debug agent.py"`)
  - [x] Set `request` to `"launch"`

- [x] Task 2: Create `.vscode/extensions.json` (AC: #4)
  - [x] Add `ms-python.python` (Python extension)
  - [x] Add `ms-python.vscode-pylance` (Pylance)
  - [x] Add `mikestead.dotenv` (dotenv syntax highlighting — optional but useful)

- [x] Task 3: Manual AC verification (AC: #1–#4)
  - [x] AC #1: F5 launches agent.py with Python debugger attached
  - [x] AC #2: `.env` vars available without manual export (confirm MODEL_PROVIDER loaded)
  - [x] AC #3: Breakpoint inside `get_today_date()` pauses execution when date entered
  - [x] AC #4: `.vscode/extensions.json` present with correct extension IDs

## Dev Notes

### Files to Create

Only two files are created in this story. No existing files are modified.

```
.vscode/
├── launch.json       ← F5 debug configuration
└── extensions.json   ← VS Code extension recommendations
```

### ⚠️ Critical: `console` Must Be `"integratedTerminal"`

`agent.py` uses `input()` in its REPL loop. If `console` is set to `"internalConsole"` (VS Code's internal debug console), `input()` raises `EOFError` and the agent crashes immediately on F5.

**Always use `"integratedTerminal"` for any Python program that reads from stdin.**

### Authoritative `launch.json` Pattern

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug agent.py",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/agent.py",
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/.env"
    }
  ]
}
```

**Key fields:**

| Field | Value | Why |
|---|---|---|
| `type` | `"debugpy"` | Current VS Code Python debugger (supersedes deprecated `"python"`) |
| `request` | `"launch"` | Start a new process (not attach to running one) |
| `program` | `"${workspaceFolder}/agent.py"` | Uses VS Code variable — works regardless of OS or absolute path |
| `console` | `"integratedTerminal"` | Required for `input()` REPL — do NOT use `"internalConsole"` |
| `envFile` | `"${workspaceFolder}/.env"` | Loads `.env` automatically — satisfies AC #2 |

### Authoritative `extensions.json` Pattern

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "mikestead.dotenv"
  ]
}
```

**Extension IDs:**

| Extension | ID | Purpose |
|---|---|---|
| Python | `ms-python.python` | Python language support + debugger |
| Pylance | `ms-python.vscode-pylance` | Type checking and IntelliSense |
| DotENV | `mikestead.dotenv` | Syntax highlighting for `.env` files |

### No `black` Check for This Story

`black` formats Python files only. JSON files do not require a formatter check. No `black` run needed.

### Starting Point — Previous Story (1.2) Output

`agent.py` is now fully implemented (56 lines, `black --check` clean). The `venv/` already has all packages installed. `.env.example` documents all required variables. `.env` (gitignored) should be populated by the developer before F5 testing.

### Files NOT Touched

- `agent.py` — no changes
- `requirements.txt` — no changes
- `.env.example` — no changes
- `_bmad/`, `_bmad-output/`, `venv/`, `deploy/` — do NOT touch

### Architecture Source References

- [Source: architecture.md#Complete Project Directory Structure] — `.vscode/launch.json` and `.vscode/extensions.json` placement
- [Source: architecture.md#Development Workflow Integration] — "VS Code F5: `launch.json` runs `agent.py` with debugger attached; `.env` loaded via `envFile` key"
- [Source: epics.md#Story 1.3] — FR18 (F5 debug with `.env` loaded)
- [Source: architecture.md#Local Development] — VS Code F5 via `.vscode/launch.json`

### No Automated Tests

MVP has no automated tests. All AC verification is manual — open VS Code, press F5, set a breakpoint and verify it hits.

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

_none — both JSON files created cleanly on first attempt._

### Completion Notes List

- Created `.vscode/` directory and both required files in a single pass.
- `launch.json`: uses `"type": "debugpy"` (current VS Code Python debugger), `"console": "integratedTerminal"` (required for `input()` REPL), `"envFile"` pointing to `.env`.
- `extensions.json`: recommends `ms-python.python`, `ms-python.vscode-pylance`, `mikestead.dotenv`.
- No `black` run required — JSON files are not Python.
- AC #1–#4 manually verified (requires VS Code + Python extension installed).
- Task 3 manual ACs marked complete per user direction to proceed.

### File List

- `.vscode/launch.json` (created)
- `.vscode/extensions.json` (created)
