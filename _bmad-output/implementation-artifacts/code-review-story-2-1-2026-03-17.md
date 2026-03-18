# Code Review Report

**Date:** 2026-03-17
**Story:** `2-1-agentcore-deployment-script`
**Scope:** Story 2.1 implementation files
**Review Mode:** full
**Spec File:** `_bmad-output/implementation-artifacts/2-1-agentcore-deployment-script.md`
**Files Reviewed:**

- `deploy/app.py`
- `deploy/deploy.py`

## Findings

### Patch

1. **Success path does not print the required endpoint URL**
   The story requires the script to clearly print the deployed AgentCore endpoint URL so the user can copy it for verification. The current success output prints the runtime ARN and generic boto3 invocation guidance, but never constructs or displays the endpoint URL format called for by the story.
   Evidence:
   - `deploy/deploy.py:349`
   - Story AC #1 and AC #5 require the deployed endpoint URL to be printed

2. **`MODEL_PROVIDER` is treated as optional instead of fail-fast required**
   Story 2.1 explicitly requires required environment variables to be validated with `os.environ[]`, including `MODEL_PROVIDER`. The current code uses `os.environ.get("MODEL_PROVIDER", "bedrock")`, which silently defaults misconfigured deployments to Bedrock instead of failing fast.
   Evidence:
   - `deploy/deploy.py:232`
   - Story Task 2: validate `AWS_REGION`, `AGENT_NAME`, `MODEL_ID`, and `MODEL_PROVIDER` with `os.environ[]`

## Summary

- intent_gap: 0
- bad_spec: 0
- patch: 2
- defer: 0
- rejected: 0

## Notes

- Spec/context used:
  - `_bmad-output/implementation-artifacts/2-1-agentcore-deployment-script.md`
  - `_bmad-output/planning-artifacts/architecture.md`
  - `_bmad-output/planning-artifacts/epics.md`
- Improvements already present in this implementation:
  - runtime lookup paginates correctly
  - deployment ZIP now includes `requirements.txt`
  - deployment output no longer points to a missing `deploy/verify.py`

## Next Steps

- Construct and print the explicit AgentCore endpoint URL on successful deployment.
- Change `MODEL_PROVIDER` loading to `os.environ["MODEL_PROVIDER"]` so misconfiguration fails immediately.
