# Code Review — Story 4.3

Date: 2026-03-21
Story: `4-3-bedrock-guardrails`
Review source: uncommitted Story 4.3 file-list diff
Spec: `_bmad-output/implementation-artifacts/4-3-bedrock-guardrails.md`

## Bad Spec

These findings suggest the spec should be amended. Consider regenerating or amending the spec with this context:

1. The story closes prompt-injection and PII risks for the project, but its acceptance criteria only wire guardrails into the local `agent.py` path and ignore the deployed AgentCore runtime in `deploy/app.py`.
   In this codebase, the production/deployed path is not `Agent(BedrockModel(...))`; it is [deploy/app.py](/Users/paul/github/strands-agents-demo/deploy/app.py#L59), which calls `bedrock.converse(...)` directly and never reads `GUARDRAIL_ID` / `GUARDRAIL_VERSION` or passes any guardrail configuration. By contrast, the Story 4.3 implementation only attaches guardrails in [agent.py](/Users/paul/github/strands-agents-demo/agent.py#L46). The story then updates [docs/risk-register.md](/Users/paul/github/strands-agents-demo/docs/risk-register.md#L25) and [docs/risk-register.md](/Users/paul/github/strands-agents-demo/docs/risk-register.md#L28) to mark R-1 and R-4 as mitigated, which overstates coverage for the deployed runtime. This is a spec hole rooted in the repo’s established local/cloud split: the story should have required equivalent guardrail wiring and verification for `deploy/app.py`, not just `agent.py`.
   Suggested spec amendment: add an AC and task requiring `deploy/app.py` to pass the provisioned guardrail identifier/version on every Bedrock Converse call, plus tests for the deployed runtime path and any needed `.env` / deployment wiring.

## Patch

These are fixable code or documentation issues:

1. The system card still describes Bedrock Guardrails as future/planned work even though this story claims they are now deployed.
   [docs/ai-system-card.md](/Users/paul/github/strands-agents-demo/docs/ai-system-card.md#L35) says “Story 4.3 adds Bedrock Guardrails PII redaction as a mitigation,” [docs/ai-system-card.md](/Users/paul/github/strands-agents-demo/docs/ai-system-card.md#L83) says Story 4.3 “adds” PII detection and redaction, and the harm table still says guardrails are “planned in Story 4.3” at [docs/ai-system-card.md](/Users/paul/github/strands-agents-demo/docs/ai-system-card.md#L97), [docs/ai-system-card.md](/Users/paul/github/strands-agents-demo/docs/ai-system-card.md#L99), and [docs/ai-system-card.md](/Users/paul/github/strands-agents-demo/docs/ai-system-card.md#L100). That conflicts with the new third-party component entry at [docs/ai-system-card.md](/Users/paul/github/strands-agents-demo/docs/ai-system-card.md#L53) and with the risk register’s “Mitigated / deployed in Story 4.3” language. The doc now mixes future-tense and completed-state descriptions for the same control.

## Summary

0 intent_gap, 1 bad_spec, 1 patch, 0 defer findings. 0 findings rejected as noise.

## Verification Notes

- `venv/bin/python -m pytest tests/unit/test_agent_tool.py -v` passed.
- `make test` passed.
- The review finding is not about a failing test; it is about uncovered deployed-runtime behavior and documentation consistency.

## Next Steps

- Amend Story 4.3 so it explicitly covers the deployed AgentCore runtime path in `deploy/app.py`.
- Update the system card to describe guardrails consistently as either deployed or planned, not both.
