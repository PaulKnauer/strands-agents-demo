---
name: sprint-status-to-openbrain
description: 'Run bmad-sprint-status for the current working folder and capture the sprint summary in OpenBrain. Use when the user says "post sprint status to OpenBrain", "sync sprint status to brain", "send sprint status to OpenBrain", or asks to run sprint status and save the result to OpenBrain.'
---

# Sprint Status to OpenBrain

**Goal:** Run `$bmad-sprint-status` against the current working directory and save a standalone sprint-status thought to OpenBrain.

## Rules

- Treat the current working directory as `{project-root}`. Do not switch folders unless the user explicitly gives a different path.
- Use `$bmad-sprint-status` in `mode=data` so the result is structured and non-interactive.
- Capture the result with the OpenBrain MCP capture tool. In Codex this is the OpenBrain `openbrain_capture_thought` tool; if it is not already available, discover/load it with `tool_search` using query `OpenBrain capture thought`.
- Do not capture anything if sprint status cannot be produced.

## Workflow

1. Invoke `$bmad-sprint-status` for `{project-root}` with `mode=data`.
2. Capture these fields from the structured output:
   - `next_workflow_id`, `next_story_id`
   - `count_backlog`, `count_ready`, `count_in_progress`, `count_review`, `count_done`
   - `epic_backlog`, `epic_in_progress`, `epic_done`
   - `risks`
3. Determine the workspace identity:
   - Prefer `project_name` and `project_key` from `{project-root}/_bmad/bmm/config.yaml` when present.
   - Otherwise use the current folder basename as `project_name` and leave `project_key` blank.
4. Compose a clear, standalone OpenBrain thought:

```text
Sprint Status Update - {project_name}{project_key_suffix}
Date: {current_date}
Workspace: {project-root}

Stories: backlog {count_backlog}, ready-for-dev {count_ready}, in-progress {count_in_progress}, review {count_review}, done {count_done}
Epics: backlog {epic_backlog}, in-progress {epic_in_progress}, done {epic_done}
Next recommended action: /bmad:bmm:workflows:{next_workflow_id} ({next_story_id})

Risks:
- {risk}
```

Use `project_key_suffix` only when `project_key` is available, formatted as ` ({project_key})`. Omit the `Risks:` section when there are no risks.

5. Call OpenBrain `openbrain_capture_thought` with the composed thought as `content`.
6. Confirm the capture result to the user, including the project name, story counts, next workflow, and whether OpenBrain accepted the thought.

## Failure Handling

- If `$bmad-sprint-status` reports `sprint-status.yaml` missing, tell the user to run `$bmad-sprint-planning` in the same folder first.
- If OpenBrain capture fails, report the sprint-status summary locally and state that the OpenBrain write failed.
- If the OpenBrain tool is unavailable, state that the OpenBrain MCP connector/tool is not available in this session.
