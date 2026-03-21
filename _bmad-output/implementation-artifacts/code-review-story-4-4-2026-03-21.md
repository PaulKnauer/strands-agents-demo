# Story 4.4 Code Review Findings

Date: 2026-03-21 09:23:16 SAST
Story: `4-4-red-team-ci`
Review target: commit `8f1dab3` against `8fd0a4b`
Spec: `_bmad-output/implementation-artifacts/4-4-red-team-ci.md`

## Scope

- Files reviewed: `.github/workflows/ci.yml`, `Makefile`, `compliance/promptfoo-redteam.yaml`, `docs/risk-register.md`, `tests/unit/test_safety_boundaries.py`
- Diff stats: 7 files changed, 605 insertions, 6 deletions
- Review mode: full

## Notes

- The `bmad-code-review` workflow expects parallel reviewer subagents. This environment did not permit delegation for this run, so the blind, edge-case, and acceptance-audit passes were performed locally.
- Verification completed:
  - `make test` passed (`117` unit tests + `7` eval tests)
  - `venv/bin/python -m pytest tests/evals/test_prompt_parity.py -q` passed

## Patch

### 1. Promptfoo system prompt can silently drift out of sync with the agent prompt

The new promptfoo config explicitly relies on manual synchronization with `agent.py` instead of a CI-enforced check. `compliance/promptfoo-redteam.yaml` says the `systemPrompt` "must match" `SYSTEM_PROMPT` and calls the YAML sync manual, but the test suite only checks parity between `agent.py` and `deploy/app.py`, not the promptfoo config. That means a later prompt edit can leave the red-team suite probing stale instructions while CI still passes, which undermines the story's stated goal that every push enforces the safety contract.

Evidence:
- [`compliance/promptfoo-redteam.yaml:16`](/Users/paul/github/strands-agents-demo/compliance/promptfoo-redteam.yaml#L16)
- [`compliance/promptfoo-redteam.yaml:38`](/Users/paul/github/strands-agents-demo/compliance/promptfoo-redteam.yaml#L38)
- [`tests/evals/test_prompt_parity.py:8`](/Users/paul/github/strands-agents-demo/tests/evals/test_prompt_parity.py#L8)

Recommended fix: add a deterministic test that parses `compliance/promptfoo-redteam.yaml` and asserts `defaultTest.options.systemPrompt == agent.SYSTEM_PROMPT`.

### 2. The new CI safety gate still does not fully protect the deployed tool surface

Story 4.4 positions the deterministic suite as the CI gate for the agent's safety contract, but the new tests only assert `create_agent()` has one tool in `agent.py`. The deployed runtime path in `deploy/app.py` is excluded from the new safety tests, and the existing parity test only checks that the first cloud tool is named `get_today_date`, not that it is the only tool. If someone adds a second tool to the deployed runtime, CI can remain green even though the production capability surface has expanded.

Evidence:
- [`tests/unit/test_safety_boundaries.py:13`](/Users/paul/github/strands-agents-demo/tests/unit/test_safety_boundaries.py#L13)
- [`tests/unit/test_safety_boundaries.py:39`](/Users/paul/github/strands-agents-demo/tests/unit/test_safety_boundaries.py#L39)
- [`tests/evals/test_prompt_parity.py:19`](/Users/paul/github/strands-agents-demo/tests/evals/test_prompt_parity.py#L19)
- [`deploy/app.py:33`](/Users/paul/github/strands-agents-demo/deploy/app.py#L33)

Recommended fix: extend the deterministic suite to assert `len(deploy.app.TOOLS) == 1` and that the sole tool name is `get_today_date`.

## Bad Spec

### 3. `npx promptfoo@latest` makes compliance evidence generation non-reproducible

The story spec requires `npx promptfoo@latest` in both CI and `make redteam`, and the implementation follows it. For a compliance evidence path, pinning to `latest` is a weak requirement because scheduled runs can change behavior without any repository diff, making failures harder to attribute and evidence harder to compare over time.

Evidence:
- [`_bmad-output/implementation-artifacts/4-4-red-team-ci.md:73`](/Users/paul/github/strands-agents-demo/_bmad-output/implementation-artifacts/4-4-red-team-ci.md#L73)
- [`_bmad-output/implementation-artifacts/4-4-red-team-ci.md:228`](/Users/paul/github/strands-agents-demo/_bmad-output/implementation-artifacts/4-4-red-team-ci.md#L228)
- [`Makefile:99`](/Users/paul/github/strands-agents-demo/Makefile#L99)
- [`ci.yml:59`](/Users/paul/github/strands-agents-demo/.github/workflows/ci.yml#L59)

Suggested spec amendment: pin a known-good promptfoo version in the story and update it deliberately when the team wants new red-team behavior.

## Summary

0 intent_gap, 1 bad_spec, 2 patch, 0 defer findings. 0 findings rejected as noise.

## Next Steps

- The patch findings can be addressed in a follow-up implementation pass or manually.
- The spec finding should be amended before relying on the red-team job as stable compliance evidence.
