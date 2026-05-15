## Deferred from: code review of 2-3-endpoint-verification-and-observability-confirmation (2026-05-09)

- `make create-role` can expose raw stack traces on IAM policy update failures [deploy/create_role.py:87]. This is deferred because `Makefile`/`deploy/create_role.py` were identified as unrelated pre-existing local work for story 2.3. Future cleanup: wrap `iam.put_role_policy(...)` in `ClientError` handling and print an actionable IAM hint before exiting.

## Deferred from: code review of 2-3-endpoint-verification-and-observability-confirmation (2026-05-10)

- Project artifacts contradict each other on AgentCore wheel architecture. Current AWS evidence shows AgentCore requires Linux ARM64-compatible binaries, while older implementation artifacts still reference or warn against `aarch64`. Future cleanup: update historical/generated guidance or project context so ARM64 packaging is canonical for AgentCore direct-code deployment.

## Deferred from: code review of 3-2-inline-explanation-and-structure-clarity (2026-05-13)

- Future DOB returns negative age [deploy/app.py:167]. `_format_age_response()` computes `(today - dob).days` without guarding `dob > today`, so a future birth date can produce a negative age. Deferred because the behavior predates this documentation/comment clarity story and is outside the Story 3.2 change scope.

## Deferred from: code review of 4-2-capability-registry-and-adapter-extension (2026-05-14)

- `create_local_model_adapter()` if/elif dispatch is hardcoded; enabling a registry entry `enabled=True` alone does not make the provider dispatchable [model_adapters.py:195-215]. Deferred as Story 4.3 scope — natural to address when the first new Bedrock family is enabled.
- `ModelCapabilities.runtimes` field accepts any string; no validation against allowed values (`"local"`, `"deployed"`, `"planned"`) [model_adapters.py:14]. Deferred to Story 4.3 when concrete values are validated and Literal/Enum types can be defined without speculative abstraction.
- Six planned-family rejection tests are copy-pasted rather than `@pytest.mark.parametrize` [tests/unit/test_model_adapters.py]. Deferred as routine maintenance cleanup.
- `TestPlannedFamilyProviderRejection._env` is a mutable shared class-level dict; future test edits could corrupt the fixture [tests/unit/test_model_adapters.py]. Deferred as test hygiene.
- Empty string `""` provider falls through to a misleading unknown-provider `ValueError` [model_adapters.py:195]. Deferred as low-priority input validation — env-driven callers typically produce non-empty values.
- `supported_local_providers()` called inside a `ValueError` f-string; a registry iteration failure would replace the outer error with the inner one [model_adapters.py:206]. Deferred as defensive hygiene with very low real-world probability.
- `planned_model_families()` filters on `enabled=False` only, not `runtimes=("planned",)` [model_adapters.py:143]. No real case today; deferred until a disabled-but-local provider entry arises.
- Provider lookup is case-sensitive; `"Bedrock"` falls to unknown-provider error [model_adapters.py:197]. Deferred — `os.environ` is the caller and already produces exact strings; normalization is low-priority.
- No `__all__` defined; `_REGISTRY` and `_REGISTRY_BY_PROVIDER` are importable as apparent public symbols [model_adapters.py]. Deferred as project-wide convention work.
- No test verifies the duplicate-key guard (`assert len(_REGISTRY_BY_PROVIDER) == len(_REGISTRY)`) actually fires on a malformed registry [model_adapters.py:143-145]. Deferred as low-priority guard coverage.
