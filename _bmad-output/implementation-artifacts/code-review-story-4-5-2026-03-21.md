# Story 4.5 Code Review Findings

Date: 2026-03-21
Story: `4-5-compliance-dashboard`
Review mode: full
Review target: uncommitted story 4-5 working tree changes
Spec: `_bmad-output/implementation-artifacts/4-5-compliance-dashboard.md`

## Scope

- Files reviewed: `deploy/create_dashboard.py`, `tests/unit/test_create_dashboard.py`, `deploy/teardown.py`, `Makefile`, `docs/ai-system-card.md`, `sprint-status.yaml`
- Diff stats: 6 story files changed, 164 insertions, 9 deletions
- Verification run: `make test` passed (`124` unit tests, `7` eval tests)

## Notes

- The `bmad-code-review` workflow expects parallel reviewer subagents. This run used the same blind, edge-case, and acceptance-audit lenses locally because delegation was not available.
- I also checked current AWS documentation because the story explicitly says the CloudWatch metric names must be verified before final submission.

## Bad Spec

### 1. The story’s guardrail metric contract does not match current AWS CloudWatch metrics

The story and implementation both expect Bedrock guardrail metrics under `AWS/Bedrock` with metric names `GuardrailInvocations` and `GuardrailInterventions`, dimensioned by `GuardrailId`. Current AWS documentation says guardrail metrics live under the `AWS/Bedrock/Guardrails` namespace and use metrics such as `Invocations` and `InvocationsIntervened`, with dimensions such as `GuardrailArn` and `GuardrailVersion`. Because the code follows the story’s metric contract, the resulting widget is configured against the wrong metric surface and will not show the intended data.

Evidence:
- [`4-5-compliance-dashboard.md:40`](/Users/paul/github/strands-agents-demo/_bmad-output/implementation-artifacts/4-5-compliance-dashboard.md#L40)
- [`create_dashboard.py:39`](/Users/paul/github/strands-agents-demo/deploy/create_dashboard.py#L39)
- AWS docs: [Monitor Amazon Bedrock Guardrails using CloudWatch metrics](https://docs.aws.amazon.com/bedrock/latest/userguide/monitoring-guardrails-cw-metrics.html)

Suggested spec amendment: update AC #2 and the dashboard script guidance to use the documented namespace, metric names, and dimensions from AWS Bedrock Guardrails metrics.

## Patch

### 2. `teardown.py` does not implement the story’s graceful `ResourceNotFound` handling

AC #5 says teardown should handle dashboard `ResourceNotFound` gracefully by printing an informational message and continuing. The current implementation catches every `ClientError` the same way and emits a warning. That means the explicit not-found behavior required by the story is still missing, and there is no unit test covering that branch.

Evidence:
- [`4-5-compliance-dashboard.md:50`](/Users/paul/github/strands-agents-demo/_bmad-output/implementation-artifacts/4-5-compliance-dashboard.md#L50)
- [`teardown.py:113`](/Users/paul/github/strands-agents-demo/deploy/teardown.py#L113)
- AWS docs: [DeleteDashboards - Amazon CloudWatch](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_DeleteDashboards.html)

Recommended fix: inspect `e.response["Error"]["Code"]`, print an `info` message for `ResourceNotFound`, and add a teardown unit test that exercises that path.

## Summary

0 intent_gap, 1 bad_spec, 1 patch, 0 defer findings. 0 findings rejected as noise.

## Next Steps

- Amend the story and implementation together for the Bedrock guardrail metrics issue, because the code is currently following an incorrect spec contract.
- Fix the teardown `ResourceNotFound` handling in a follow-up patch and add regression coverage for it.
