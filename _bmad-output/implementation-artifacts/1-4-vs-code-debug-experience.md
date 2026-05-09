# Story 1.4: VS Code Debug Experience

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want F5 debugging configured for the local agent path,
so that I can inspect tool execution and runtime behavior without manual debugger setup.

## Acceptance Criteria

1. **Given** the project is open in VS Code
   **When** I press F5
   **Then** `agent.py` launches with the Python debugger attached
   **And** environment variables are loaded from `.env`

2. **Given** I set a breakpoint inside local agent execution
   **When** I interact with the REPL
   **Then** execution pauses at the breakpoint
   **And** I can inspect local variables and tool flow

## Tasks / Subtasks

- [x] Task 1: Reconcile the existing VS Code debug configuration with the current Story 1.4 contract (AC: #1, #2)
  - [x] Inspect `.vscode/launch.json`; keep `type: "debugpy"`, `request: "launch"`, `program: "${workspaceFolder}/agent.py"`, `console: "integratedTerminal"`, and `envFile: "${workspaceFolder}/.env"`
  - [x] Do not switch to `internalConsole`; `agent.py` uses `input()` and needs an interactive terminal
  - [x] Keep the configuration focused on the local `agent.py` REPL path; do not point F5 at `deploy/app.py`, `deploy/start.sh`, or AgentCore runtime files

- [x] Task 2: Preserve VS Code extension recommendations (AC: #1, #2)
  - [x] Inspect `.vscode/extensions.json`; keep `ms-python.python` and `ms-python.vscode-pylance`
  - [x] Keep `mikestead.dotenv` unless there is a concrete reason to remove it; it supports `.env` readability and does not affect runtime

- [x] Task 3: Update stale Story 1.3 references in static debug tests if still present (AC: #1, #2)
  - [x] In `tests/unit/test_static.py`, update VS Code debug docstrings/comments that refer to historical Story 1.3 so they reference Story 1.4
  - [x] Do not weaken assertions for `debugpy`, `integratedTerminal`, `envFile`, or `agent.py`
  - [x] Keep the tests JSON-based; no live VS Code dependency belongs in unit tests

- [x] Task 4: Confirm README developer guidance still matches the final debug config (AC: #1, #2)
  - [x] Ensure README VS Code guidance says F5 launches `agent.py` with debugger attached and `.env` loaded
  - [x] Ensure README verification guidance tells the developer to set a breakpoint in local agent execution, then interact with the REPL
  - [x] Avoid adding long VS Code troubleshooting content unless the current README guidance is inaccurate

- [x] Task 5: Run deterministic checks and record manual validation status (AC: #1, #2)
  - [x] Run `venv/bin/python -m pytest tests/unit/test_static.py`
  - [x] If Python files were edited, run `venv/bin/black` on those files
  - [x] Manually validate in VS Code when available: open the repo folder, select the Python interpreter/venv, press F5, enter a date at the REPL, and confirm a breakpoint in `get_today_date()` or `run_repl()` is hit
  - [x] If manual VS Code validation cannot be performed in the agent environment, state that explicitly in Dev Agent Record instead of claiming it passed

### Review Findings

- [x] [Review][Patch] Add a static assertion for `request: "launch"` [tests/unit/test_static.py:187]
- [x] [Review][Patch] Tighten the `envFile` assertion to exactly `${workspaceFolder}/.env` [tests/unit/test_static.py:195]
- [x] [Review][Patch] Tighten the `program` assertion to exactly `${workspaceFolder}/agent.py` [tests/unit/test_static.py:200]

## Dev Notes

### Story Intent

This story makes the current sprint's VS Code debug experience explicit and verifiable. The repo already contains a working `.vscode/launch.json` and `.vscode/extensions.json` from an older historical story file, but the active Epic 1 sequence now assigns VS Code debugging to Story 1.4. Implementation should reconcile the current files and tests with Story 1.4, not recreate the feature from scratch or broaden it into deployment/debug tooling.

The developer's goal is a reliable local F5 path for `agent.py`: start the REPL under VS Code's Python debugger, load `.env`, accept terminal input, and allow breakpoints inside local agent/tool execution.

### Current State Of Files Being Modified

- `.vscode/launch.json`: already exists and currently launches `${workspaceFolder}/agent.py` with `type: "debugpy"`, `request: "launch"`, `console: "integratedTerminal"`, and `envFile: "${workspaceFolder}/.env"`. This shape satisfies the intended debug contract; preserve it unless validation reveals a concrete defect. [Source: .vscode/launch.json]
- `.vscode/extensions.json`: already exists and recommends `ms-python.python`, `ms-python.vscode-pylance`, and `mikestead.dotenv`. Preserve the Python and Pylance recommendations as required; dotenv is useful and harmless. [Source: .vscode/extensions.json]
- `tests/unit/test_static.py`: already enforces the debug config contract, but its VS Code comments/docstrings currently refer to historical Story 1.3. Update those references to Story 1.4 without weakening the assertions. [Source: tests/unit/test_static.py]
- `README.md`: already includes a `VS Code Debugging` section saying F5 launches `agent.py`, attaches the debugger, and loads `.env`, plus a verification instruction to set a breakpoint in `get_today_date()`. Keep it aligned with final config. [Source: README.md#VS Code Debugging]

### What Must Be Preserved

- `agent.py` remains the only local REPL entrypoint for this story. It calls `load_dotenv()` before any `os.environ` access, constructs the model through `create_local_model_adapter(os.environ["MODEL_PROVIDER"], os.environ)`, registers `get_today_date`, and runs `run_repl(create_agent())` under the main guard. [Source: agent.py]
- `model_adapters.py` owns local provider selection for `bedrock` and `gemini`. Do not move provider logic into VS Code config, shell scripts, or README examples. [Source: model_adapters.py]
- Local and cloud runtime separation remains strict: `deploy/app.py` is the AgentCore cloud runtime using direct Bedrock Converse through `boto3`; the VS Code F5 path must not target or import the cloud runtime. [Source: _bmad-output/project-context.md#Framework-Specific Rules]
- Required environment variables should still come from `.env`/process environment and fail fast through `os.environ[...]`; do not add silent defaults in `launch.json` or Python code. [Source: _bmad-output/project-context.md#Language-Specific Rules]

### Architecture Compliance Guardrails

- Use `.vscode/launch.json` for debugger configuration; VS Code stores workspace debug configurations under `.vscode/launch.json`. [Source: https://code.visualstudio.com/docs/python/debugging]
- Keep `"type": "debugpy"`; VS Code's Python debugger docs identify `debugpy` as the debugger type and warn that deprecated `"python"` launch types should be replaced. [Source: https://code.visualstudio.com/docs/python/debugging]
- Keep `"request": "launch"`; the story starts a new local `agent.py` process rather than attaching to an existing process. [Source: https://code.visualstudio.com/docs/python/debugging]
- Keep `"program": "${workspaceFolder}/agent.py"`; this pins F5 to the repo's local agent entrypoint instead of whichever file is active in the editor. [Source: https://code.visualstudio.com/docs/python/debugging]
- Keep `"console": "integratedTerminal"`; the REPL uses `input()`, and the integrated terminal is the correct output/input surface for interactive Python debugging. [Source: https://code.visualstudio.com/docs/python/debugging]
- Keep `"envFile": "${workspaceFolder}/.env"`; VS Code supports `envFile` as the launch configuration path for environment variable definitions. [Source: https://code.visualstudio.com/docs/python/debugging]

### Regression Risks To Avoid

- Changing `console` to `internalConsole`, which can break `input()`-driven REPL interaction.
- Using `${file}` instead of `${workspaceFolder}/agent.py`, which makes F5 depend on the active editor tab and can launch tests, deployment scripts, or planning artifacts by accident.
- Committing `.env` or embedding credentials/model IDs in `launch.json`; `.env` is intentionally gitignored and `.env.example` contains placeholders only.
- Adding a separate debug-only entrypoint or shell wrapper that bypasses `load_dotenv()`, `create_agent()`, `run_repl()`, or adapter-based local model selection.
- Treating manual VS Code breakpoint validation as an automated pytest concern. Unit tests should validate the JSON contract; F5 behavior requires VS Code.

### Previous Story Intelligence

- Story 1.3 completed adapter-based local model selection and reduced `agent.py` to a lean local entrypoint that delegates model construction to `model_adapters.py`. The VS Code debug path must continue to exercise that entrypoint rather than reintroducing inline provider branching. [Source: _bmad-output/implementation-artifacts/1-3-adapter-based-local-model-selection.md]
- Story 1.3 established evidence discipline: record commands actually run, and distinguish deterministic tests from live/manual validation. Apply the same standard here for VS Code validation.
- Historical `_bmad-output/implementation-artifacts/1-3-vs-code-debug-configuration.md` created the same `.vscode` files before the current sprint numbering changed. Use it as implementation background only; do not overwrite it and do not confuse it with the active Story 1.4 artifact.
- The historical code review for VS Code debug configuration found no actionable issues. Remaining risk was manual validation: confirm F5, breakpoint behavior, and `.env` loading in VS Code on the target machine. [Source: _bmad-output/implementation-artifacts/code-review-story-1-3-2026-03-16.md]

### Git Intelligence

- `c29607d` - Add adapter-based local model selection. Relevant because it changed `agent.py`, added `model_adapters.py`, and updated local adapter tests. The F5 path should launch the current `agent.py` and therefore exercise this adapter boundary.
- `5fc1cea` - Add Story 1.2 review artifacts. Background only.
- `1b0a675` - Add Story 1.1 review follow-up. Background only.
- `634b5b9` - Update planning artifacts and add implementation readiness report. Background only.
- `ec17f5e` - Add multi-provider model planning artifacts. Background only; do not broaden this story into provider expansion.

There were no uncommitted changes at story creation time.

### Latest Technical Information

- Official VS Code Python debugging docs currently show Python debug configurations in `.vscode/launch.json`, with `"type": "debugpy"`, `"request": "launch"`, `"program"`, and `"console": "integratedTerminal"` as standard fields. [Source: https://code.visualstudio.com/docs/python/debugging]
- The same docs describe `envFile` as an optional path to environment variable definitions for a debug configuration. This supports the existing `"envFile": "${workspaceFolder}/.env"` contract. [Source: https://code.visualstudio.com/docs/python/debugging]
- This story should not upgrade Python packages or Strands dependencies. It is a local editor/debug configuration story; dependency versions remain governed by `requirements.txt`, `_bmad-output/project-context.md`, and existing tests.

### Project Structure Notes

- Expected files for this story:
  - `.vscode/launch.json` (existing; preserve or minimally correct)
  - `.vscode/extensions.json` (existing; preserve or minimally correct)
  - `tests/unit/test_static.py` (possible comment/docstring update only)
  - `README.md` (only if current VS Code guidance no longer matches config)
- Files that should not be modified for this story unless a discovered defect directly requires it:
  - `agent.py`
  - `model_adapters.py`
  - `deploy/app.py`
  - `deploy/deploy.py`
  - `requirements.txt`
  - `.env.example`

### Testing Requirements

- Required deterministic validation: `venv/bin/python -m pytest tests/unit/test_static.py`
- If `tests/unit/test_static.py` is edited, run `venv/bin/black tests/unit/test_static.py`
- Manual validation target: VS Code F5 launches `agent.py` in the integrated terminal, `.env` variables are available to `agent.py`, REPL input works, and a breakpoint in `get_today_date()` or `run_repl()` is hit during interaction
- Do not claim manual VS Code validation if this environment cannot open VS Code; record it as not run with the reason

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.4]
- [Source: _bmad-output/planning-artifacts/prd.md#Developer Tool Specific Requirements]
- [Source: _bmad-output/planning-artifacts/prd.md#User Success]
- [Source: _bmad-output/planning-artifacts/architecture.md#Development Experience]
- [Source: _bmad-output/planning-artifacts/architecture.md#Development Workflow Integration]
- [Source: _bmad-output/planning-artifacts/architecture.md#Complete Project Directory Structure]
- [Source: _bmad-output/project-context.md#Language-Specific Rules]
- [Source: _bmad-output/project-context.md#Framework-Specific Rules]
- [Source: _bmad-output/implementation-artifacts/1-3-adapter-based-local-model-selection.md]
- [Source: _bmad-output/implementation-artifacts/1-3-vs-code-debug-configuration.md]
- [Source: _bmad-output/implementation-artifacts/code-review-story-1-3-2026-03-16.md]
- [Source: .vscode/launch.json]
- [Source: .vscode/extensions.json]
- [Source: tests/unit/test_static.py]
- [Source: README.md#VS Code Debugging]
- [Source: https://code.visualstudio.com/docs/python/debugging]

## Change Log

- 2026-05-09: Ultimate context engine analysis completed - comprehensive developer guide created.
- 2026-05-09: Story 1.4 implementation — updated Story 1.3 AC references to Story 1.4 in `tests/unit/test_static.py` docstrings; all other VS Code config files verified correct and unchanged.
- 2026-05-09: Code review follow-up — tightened static VS Code launch assertions for `request`, `program`, and `envFile`.

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

No debug issues encountered. All files were already in the correct state for Story 1.4 compliance.

### Completion Notes List

- Task 1: `.vscode/launch.json` already correct — `type: "debugpy"`, `request: "launch"`, `program: "${workspaceFolder}/agent.py"`, `console: "integratedTerminal"`, `envFile: "${workspaceFolder}/.env"`. No changes needed.
- Task 2: `.vscode/extensions.json` already correct — `ms-python.python`, `ms-python.vscode-pylance`, `mikestead.dotenv` all present. No changes needed.
- Task 3: Updated all Story 1.3 AC references in `tests/unit/test_static.py` docstrings to Story 1.4. Module docstring lines 7–8 updated; six test method docstrings updated. Assertions unchanged — all still enforce `debugpy`, `integratedTerminal`, `envFile`, and `agent.py`.
- Task 4: `README.md` VS Code Debugging section already accurate — states F5 launches `agent.py` with debugger attached and `.env` loaded, and instructs developer to set a breakpoint in `get_today_date()`. No changes needed.
- Task 5: All 32 tests in `tests/unit/test_static.py` pass after code review follow-up. `black` confirmed formatting. Manual VS Code validation not performed — this environment does not have access to VS Code. Breakpoint and F5 behavior must be validated by the developer in a VS Code session.

### File List

- tests/unit/test_static.py
