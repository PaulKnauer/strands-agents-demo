## Deferred from: code review of 2-3-endpoint-verification-and-observability-confirmation (2026-05-09)

- `make create-role` can expose raw stack traces on IAM policy update failures [deploy/create_role.py:87]. This is deferred because `Makefile`/`deploy/create_role.py` were identified as unrelated pre-existing local work for story 2.3. Future cleanup: wrap `iam.put_role_policy(...)` in `ClientError` handling and print an actionable IAM hint before exiting.

## Deferred from: code review of 2-3-endpoint-verification-and-observability-confirmation (2026-05-10)

- Project artifacts contradict each other on AgentCore wheel architecture. Current AWS evidence shows AgentCore requires Linux ARM64-compatible binaries, while older implementation artifacts still reference or warn against `aarch64`. Future cleanup: update historical/generated guidance or project context so ARM64 packaging is canonical for AgentCore direct-code deployment.
