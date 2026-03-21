# Story 4.3: Bedrock Guardrails — Content Safety and PII Protection

Status: review

## Story

As a developer or compliance reviewer,
I want Amazon Bedrock Guardrails provisioned and attached to the agent's BedrockModel,
So that the project has automated content safety filtering, prompt-injection defence, and PII anonymisation — addressing NIST AI RMF MANAGE-2.2 (harmful content) and MANAGE-1.3 (PII protection) — without modifying agent business logic.

## Context

This story is the third story of **Epic 4: NIST AI RMF Compliance Layer**.

Story 4.1 created the governance documentation. Story 4.2 delivered the JSONL audit hook. Story 4.3 delivers the first preventive runtime control: a Bedrock Guardrail that filters harmful content, blocks prompt-injection attacks, and anonymises PII in every request and response.

**Design principle (from research):** Guardrails attach to the model layer, not the application layer. `agent.py` only adds two optional env var lookups to the existing `BedrockModel(...)` call. All guardrail policy decisions are managed by AWS; no enforcement logic lives in application code.

**NIST AI RMF functions addressed:**
- **MANAGE-2.2** — Harmful content filtering: the guardrail blocks violent and hate content at HIGH strength on every invocation.
- **MANAGE-1.3** — PII protection: email and phone entities are anonymised (not blocked) so the agent can still respond, but sensitive values are redacted before reaching the LLM or the user.
- **GOVERN-1.1** — Prompt injection defence: the PROMPT_ATTACKS content filter at HIGH strength detects and blocks jailbreak attempts.

**Risk register impact:** This story closes R-1 (Prompt injection) and R-4 (PII in user prompt) from Open → Mitigated in `docs/risk-register.md`.

## Acceptance Criteria

1. **Given** `deploy/guardrail.yaml` exists,
   **When** I run `aws cloudformation deploy --template-file deploy/guardrail.yaml --stack-name strands-demo-guardrail`,
   **Then** the stack creates successfully and outputs `GuardrailId` and `GuardrailVersion`.

2. **Given** `deploy/guardrail.yaml` is read,
   **When** I inspect the guardrail resource,
   **Then** it configures:
   - Content filter: `HATE` at `HIGH` strength (INPUT and OUTPUT)
   - Content filter: `VIOLENCE` at `HIGH` strength (INPUT and OUTPUT)
   - Content filter: `PROMPT_ATTACKS` at `HIGH` strength (INPUT only)
   - Sensitive information policy: `EMAIL` entity → `ANONYMIZE`
   - Sensitive information policy: `PHONE` entity → `ANONYMIZE`

3. **Given** `GUARDRAIL_ID` and `GUARDRAIL_VERSION` are set in `.env`,
   **When** `create_agent()` runs with `MODEL_PROVIDER=bedrock`,
   **Then** `BedrockModel` is constructed with `guardrail_id` and `guardrail_version` keyword arguments matching those env var values.

4. **Given** `GUARDRAIL_ID` is NOT set in `.env`,
   **When** `create_agent()` runs with `MODEL_PROVIDER=bedrock`,
   **Then** `BedrockModel` is constructed without `guardrail_id` or `guardrail_version` arguments — the agent runs without guardrails (local dev mode, no error raised).

5. **Given** `MODEL_PROVIDER=gemini` is set,
   **When** `create_agent()` runs (with or without `GUARDRAIL_ID`),
   **Then** no guardrail arguments are passed to `GeminiModel` — guardrail wiring is Bedrock-only.

6. **Given** `.env.example` is read,
   **When** I check the Bedrock Guardrails section,
   **Then** it contains `GUARDRAIL_ID` and `GUARDRAIL_VERSION` as commented-out optional variables with description comments and example values.

7. **Given** `docs/risk-register.md` is read after this story is complete,
   **When** I check rows R-1 and R-4,
   **Then** both have `Status = Mitigated` and the `Mitigation` column references Bedrock Guardrails.

8. **Given** `docs/ai-system-card.md` is read after this story is complete,
   **When** I check the Third-Party Components section,
   **Then** it includes `Amazon Bedrock Guardrails` as a new entry.

9. **Given** all existing tests in the test suite,
   **When** I run `make test` or `pytest`,
   **Then** all pre-existing tests continue to pass (zero regressions).

10. **Given** `tests/unit/test_agent_tool.py` is updated,
    **When** I run `pytest tests/unit/test_agent_tool.py`,
    **Then** all tests pass, covering:
    - `BedrockModel` is constructed with `guardrail_id` and `guardrail_version` when both env vars are set
    - `BedrockModel` is constructed without guardrail kwargs when `GUARDRAIL_ID` is not set
    - Gemini path does not receive guardrail kwargs regardless of `GUARDRAIL_ID`

11. **Given** `deploy/app.py` is the deployed AgentCore runtime entrypoint,
    **When** `GUARDRAIL_ID` and `GUARDRAIL_VERSION` are set in the environment,
    **Then** `bedrock.converse()` is called with `guardrailConfig` containing `guardrailIdentifier` and `guardrailVersion` on every turn of the agentic loop.

12. **Given** `GUARDRAIL_ID` is NOT set,
    **When** `_run_agent()` runs in `deploy/app.py`,
    **Then** `bedrock.converse()` is called without `guardrailConfig` (local/unprovisioned mode, no error raised).

13. **Given** `GUARDRAIL_VERSION` is not set but `GUARDRAIL_ID` is set,
    **When** `_run_agent()` runs in `deploy/app.py`,
    **Then** `guardrailConfig.guardrailVersion` defaults to `"DRAFT"`.

## Tasks / Subtasks

- [x] Task 1: Create `deploy/guardrail.yaml` CloudFormation template (AC: #1, #2)
  - [x] Define `AWS::Bedrock::Guardrail` resource with `Name: strands-demo-guardrail`
  - [x] Add `ContentPolicyConfig` with `HATE` HIGH, `VIOLENCE` HIGH (both INPUT and OUTPUT), `PROMPT_ATTACKS` HIGH (INPUT)
  - [x] Add `SensitiveInformationPolicyConfig` with `EMAIL` ANONYMIZE and `PHONE` ANONYMIZE
  - [x] Add `Outputs` section exporting `GuardrailId` (via `!GetAtt`) and `GuardrailVersion` (via `!GetAtt`)
  - [x] Add inline comments explaining the purpose of each policy block

- [x] Task 2: Wire guardrail into `agent.py` `BedrockModel` constructor (AC: #3, #4, #5, #9)
  - [x] In `create_agent()` bedrock branch: read `os.environ.get("GUARDRAIL_ID")` and `os.environ.get("GUARDRAIL_VERSION", "DRAFT")`
  - [x] Only pass `guardrail_id`/`guardrail_version` kwargs to `BedrockModel` when `GUARDRAIL_ID` is set (use conditional kwargs dict pattern)
  - [x] Gemini branch is unchanged — no guardrail wiring
  - [x] Run `black agent.py --check` — must pass; run `black agent.py` if not
  - [x] Run `make test` — all tests must pass (including updated tests from Task 4)

- [x] Task 3: Update `.env.example` and docs (AC: #6, #7, #8)
  - [x] Add `# --- Bedrock Guardrails (optional) ---` section to `.env.example` with commented-out `GUARDRAIL_ID` and `GUARDRAIL_VERSION` variables and description comments
  - [x] Update `docs/risk-register.md`: change R-1 Status from `Open` to `Mitigated`, update Mitigation to reference Bedrock Guardrails (PROMPT_ATTACKS filter); change R-4 Status from `Open` to `Mitigated`, update Mitigation to reference Bedrock Guardrails (PII ANONYMIZE)
  - [x] Update `docs/ai-system-card.md` Third-Party Components section: add `Amazon Bedrock Guardrails` entry

- [x] Task 5: Wire guardrails into `deploy/app.py` `_run_agent()` and add tests (AC: #11, #12, #13) — code review finding
  - [x] Read `GUARDRAIL_ID` and `GUARDRAIL_VERSION` from env in `_run_agent()`; build `guardrail_config` dict only when `GUARDRAIL_ID` is set
  - [x] Pass `guardrailConfig` to `bedrock.converse(**converse_kwargs)` on every loop turn when guardrail is configured
  - [x] Add `TestRunAgentGuardrails` class to `tests/unit/test_app.py` with 4 tests (with/without ID, version default, multi-turn)
  - [x] Run `make test` — all tests pass

- [x] Task 4: Update unit tests in `tests/unit/test_agent_tool.py` (AC: #10)
  - [x] Update `test_bedrock_provider_constructs_bedrock_model`: patched env has no `GUARDRAIL_ID`; asserts `BedrockModel` called with `model_id` and `region_name` only (verifies AC #4)
  - [x] Add `test_bedrock_with_guardrail_id_passes_guardrail_kwargs`: `GUARDRAIL_ID` and `GUARDRAIL_VERSION` set; asserts `BedrockModel` receives both kwargs
  - [x] Add `test_bedrock_without_guardrail_id_omits_guardrail_kwargs`: env has no `GUARDRAIL_ID`; asserts no guardrail kwargs in call
  - [x] Add `test_bedrock_guardrail_version_defaults_to_draft_when_unset`: `GUARDRAIL_ID` set but no `GUARDRAIL_VERSION`; asserts `guardrail_version=="DRAFT"`
  - [x] Add `test_gemini_provider_ignores_guardrail_env_var`: `GUARDRAIL_ID` set; asserts `GeminiModel` called with `model_id` only
  - [x] Run `make test` — all 116 tests pass

## Dev Notes

### `agent.py` Change — Conditional Guardrail Kwargs

The guardrail wiring uses a conditional kwargs dict pattern to keep the `BedrockModel` call clean and testable:

```python
# Bedrock Guardrails are optional — only wired when GUARDRAIL_ID is configured.
# When absent, the agent runs without content filtering (suitable for local dev).
# NIST MANAGE-2.2 / MANAGE-1.3: guardrails handle harmful content and PII
# at the model layer without any enforcement logic in application code.
guardrail_kwargs = {}
if guardrail_id := os.environ.get("GUARDRAIL_ID"):
    guardrail_kwargs = {
        "guardrail_id": guardrail_id,
        "guardrail_version": os.environ.get("GUARDRAIL_VERSION", "DRAFT"),
    }
model = BedrockModel(
    model_id=os.environ["MODEL_ID"],
    region_name=os.environ["AWS_REGION"],
    **guardrail_kwargs,
)
```

This pattern:
- Keeps `BedrockModel(...)` call readable (no `None` arguments)
- Is easily testable: assert `mock_bedrock_cls.call_args.kwargs` contains or does not contain `guardrail_id`
- Degrades gracefully: local dev without `GUARDRAIL_ID` set works without change

**Line count impact:** `agent.py` is currently 81 lines. Adding ~7 lines keeps it well under the 150-line limit (NFR12).

### `deploy/guardrail.yaml` Structure

CloudFormation resource type: `AWS::Bedrock::Guardrail`. Key properties:

```yaml
Resources:
  StrandsDemoGuardrail:
    Type: AWS::Bedrock::Guardrail
    Properties:
      Name: strands-demo-guardrail
      Description: "NIST AI RMF MANAGE-2.2/1.3 content safety and PII guardrail for strands-agents-demo"
      BlockedInputMessaging: "I cannot process that request."
      BlockedOutputsMessaging: "I cannot provide that response."
      ContentPolicyConfig:
        FiltersConfig:
          - Type: HATE
            InputStrength: HIGH
            OutputStrength: HIGH
          - Type: VIOLENCE
            InputStrength: HIGH
            OutputStrength: HIGH
          - Type: PROMPT_ATTACKS
            InputStrength: HIGH
            OutputStrength: NONE  # prompt attacks are input-only
      SensitiveInformationPolicyConfig:
        PiiEntitiesConfig:
          - Type: EMAIL
            Action: ANONYMIZE
          - Type: PHONE
            Action: ANONYMIZE

Outputs:
  GuardrailId:
    Value: !GetAtt StrandsDemoGuardrail.GuardrailId
    Export:
      Name: strands-demo-guardrail-id
  GuardrailVersion:
    Value: !GetAtt StrandsDemoGuardrail.Version
    Export:
      Name: strands-demo-guardrail-version
```

**Note on `PROMPT_ATTACKS`:** This filter is input-only by design — you want to detect when the user is trying to inject a prompt attack, not filter the model's own output. Set `OutputStrength: NONE` to avoid false positives on model responses.

**Note on `!GetAtt` output attributes:** The `GuardrailId` attribute is returned as `GuardrailId` and the version as `Version` from the `AWS::Bedrock::Guardrail` resource. Verify these against the CloudFormation docs if the stack fails — attribute names are case-sensitive.

### `.env.example` Addition

Add after the existing `AGENT_NAME` block, before the Gemini section:

```
# --- Bedrock Guardrails (optional — Bedrock provider only) ---
# Provision via: aws cloudformation deploy --template-file deploy/guardrail.yaml --stack-name strands-demo-guardrail
# Then retrieve the GuardrailId from the stack outputs and set here.
# When unset, the agent runs without content filtering (suitable for local development).
# GUARDRAIL_ID=your-guardrail-id-here
# GUARDRAIL_VERSION=DRAFT
```

### Test Pattern for Guardrail Kwargs

Use `call_args.kwargs` to inspect keyword arguments passed to `BedrockModel`:

```python
def test_bedrock_with_guardrail_id_passes_guardrail_kwargs(self):
    from agent import create_agent

    with (
        patch.dict(
            os.environ,
            {
                "MODEL_PROVIDER": "bedrock",
                "MODEL_ID": "some-model",
                "AWS_REGION": "us-east-1",
                "GUARDRAIL_ID": "test-guardrail-id",
                "GUARDRAIL_VERSION": "1",
            },
        ),
        patch("agent.BedrockModel") as mock_bedrock_cls,
        patch("agent.Agent"),
    ):
        create_agent()
        kwargs = mock_bedrock_cls.call_args.kwargs
        assert kwargs["guardrail_id"] == "test-guardrail-id"
        assert kwargs["guardrail_version"] == "1"


def test_bedrock_without_guardrail_id_omits_guardrail_kwargs(self):
    from agent import create_agent

    env = {"MODEL_PROVIDER": "bedrock", "MODEL_ID": "some-model", "AWS_REGION": "us-east-1"}
    with (
        patch.dict(os.environ, env, clear=True),
        patch("agent.BedrockModel") as mock_bedrock_cls,
        patch("agent.Agent"),
    ):
        # Remove GUARDRAIL_ID if present in environment
        os.environ.pop("GUARDRAIL_ID", None)
        create_agent()
        kwargs = mock_bedrock_cls.call_args.kwargs
        assert "guardrail_id" not in kwargs
        assert "guardrail_version" not in kwargs
```

**Important:** `test_bedrock_provider_constructs_bedrock_model` currently asserts:
```python
mock_bedrock_cls.assert_called_once_with(model_id="some-model", region_name="us-east-1")
```
After Task 2, with `GUARDRAIL_ID` set in env, this assertion will fail because `BedrockModel` will also receive `guardrail_id` and `guardrail_version`. Update this test to either add `GUARDRAIL_ID` to the patched env and assert with guardrail kwargs, or keep `GUARDRAIL_ID` absent and assert without guardrail kwargs. The second approach is simpler and verifies AC #4.

### Regression Risk

`test_bedrock_provider_constructs_bedrock_model` uses `assert_called_once_with(...)` which checks exact kwargs. This test **will fail** after Task 2 unless the test's patched env either (a) includes `GUARDRAIL_ID` and the assertion includes guardrail kwargs, or (b) excludes `GUARDRAIL_ID` and the assertion covers only `model_id` and `region_name`. Task 4 must update this test before running `make test`.

**Recommended approach for updated test:** patch env without `GUARDRAIL_ID` → assert `BedrockModel` called with `model_id` and `region_name` only. This verifies AC #4 directly and keeps the test minimal.

Use `patch.dict(os.environ, {...}, clear=True)` and call `os.environ.pop("GUARDRAIL_ID", None)` to guarantee `GUARDRAIL_ID` is absent regardless of the local environment.

### No New Python Dependencies

The guardrail integration uses only `os.environ.get()` (stdlib) and the existing `BedrockModel` constructor. No new entries in `requirements.txt`. The CloudFormation template is YAML-only (deployed via AWS CLI).

### Style and Quality

- `black` formatting required on `agent.py` after Task 2
- CloudFormation YAML: consistent 2-space indentation, inline comments on each policy block
- Doc updates: Markdown only, no formatter needed

### Relationship to Other Stories

- **Story 4.2** (Audit Hooks) is unaffected — `AuditLoggingHook` continues to log all events unchanged; guardrail interventions are transparent to the hook layer.
- **Story 4.4** (Red-Team CI) will validate that the guardrail configuration actually blocks prompt injection attempts via automated tests.
- **Story 4.5** (Compliance Dashboard) will add a CloudWatch widget displaying `GuardrailInvocations` and `GuardrailBlocks` metrics — these are emitted automatically by Bedrock when a guardrail is attached.

## Architecture Compliance Notes

- `agent.py` remains the sole entry point for `BedrockModel` construction. The guardrail wiring is two lines of conditional logic in the existing `create_agent()` bedrock branch — no new module, no new class.
- `deploy/guardrail.yaml` is a new file in the existing `deploy/` directory. It follows the same pattern as `deploy/deploy.py` — infrastructure provisioning, separate from agent runtime.
- `compliance/` is not modified by this story — guardrails live at the model layer, not the compliance hook layer.
- `docs/` updates are additive only — existing content is not removed, only the Status column of two risk rows and one component entry are updated.

## Definition of Done

- [x] `deploy/guardrail.yaml` exists with `AWS::Bedrock::Guardrail` resource, content filters (HATE HIGH, VIOLENCE HIGH, PROMPT_ATTACKS HIGH INPUT), and PII policies (EMAIL ANONYMIZE, PHONE ANONYMIZE)
- [x] `agent.py` bedrock branch passes `guardrail_id`/`guardrail_version` to `BedrockModel` when `GUARDRAIL_ID` env var is set; omits them when not set
- [x] `.env.example` includes commented-out `GUARDRAIL_ID` and `GUARDRAIL_VERSION` in a new optional section
- [x] `docs/risk-register.md` shows R-1 and R-4 as Mitigated
- [x] `docs/ai-system-card.md` Third-Party Components includes Bedrock Guardrails
- [x] `tests/unit/test_agent_tool.py` updated with guardrail presence/absence tests
- [x] `make test` passes with zero failures and zero regressions
- [x] `black agent.py --check` passes
- [x] No new entries in `requirements.txt`
- [x] `agent.py` remains under 150 lines (NFR12)

## File List

- `deploy/guardrail.yaml` — new (CloudFormation template for Bedrock Guardrail)
- `agent.py` — modified (conditional guardrail kwargs in bedrock branch of `create_agent()`)
- `deploy/app.py` — modified (guardrail wiring in `_run_agent()` via `guardrailConfig` on `bedrock.converse()`)
- `.env.example` — modified (added Bedrock Guardrails optional section with `GUARDRAIL_ID` and `GUARDRAIL_VERSION`)
- `docs/risk-register.md` — modified (R-1 and R-4 updated to Mitigated; Notes on Open Risks updated)
- `docs/ai-system-card.md` — modified (Amazon Bedrock Guardrails added to Third-Party Components; tense corrected to deployed; coverage extended to both runtime paths)
- `tests/unit/test_agent_tool.py` — modified (4 new guardrail tests, updated existing bedrock test)
- `tests/unit/test_app.py` — modified (4 new guardrail tests for deployed runtime path)

## Dev Agent Record

### Implementation Plan

Tasks executed in order: 1 (guardrail.yaml) → 4 (tests) → 2 (agent.py) → 3 (docs). Task 4 was done before Task 2 because the existing `test_bedrock_provider_constructs_bedrock_model` used `assert_called_once_with(...)` which would have failed after the `agent.py` change. Tests were updated first to remove the regression risk.

### Completion Notes

- `deploy/guardrail.yaml`: CloudFormation `AWS::Bedrock::Guardrail` resource with HATE HIGH, VIOLENCE HIGH (INPUT+OUTPUT), PROMPT_ATTACKS HIGH (INPUT only), EMAIL ANONYMIZE, PHONE ANONYMIZE. Outputs `GuardrailId` and `GuardrailVersion`. Inline comments on every policy block explain the NIST AI RMF control each satisfies. ✅
- `agent.py`: Conditional kwargs dict pattern in bedrock branch — `BedrockModel` receives `guardrail_id`/`guardrail_version` only when `GUARDRAIL_ID` env var is set; omits them otherwise. Gemini branch unchanged. `agent.py` is now 93 lines (under 150 NFR12 limit). `black --check` passes. ✅
- `.env.example`: New `--- Bedrock Guardrails (optional) ---` section with commented-out `GUARDRAIL_ID` and `GUARDRAIL_VERSION`, description comments, and NIST AI RMF annotations. ✅
- `docs/risk-register.md`: R-1 Status → Mitigated (references PROMPT_ATTACKS filter); R-4 Status → Mitigated (references PII ANONYMIZE). Notes section updated to separate Open and Mitigated risks. Change Log updated. ✅
- `docs/ai-system-card.md`: Amazon Bedrock Guardrails added to Third-Party Components table with role, version, and supply-chain risk rating. ✅
- `tests/unit/test_agent_tool.py`: 5 test additions/updates (4 new, 1 updated). All 116 tests pass (109 unit + 7 eval). ✅
- No new `requirements.txt` entries. All changes are stdlib, env vars, and existing SDK API.

### Change Log

| Date | Change |
|---|---|
| 2026-03-20 | Story 4.3 created |
| 2026-03-20 | Story 4.3 implemented — all 4 tasks complete, 116/116 tests passing |
| 2026-03-21 | Code review fixes: wired guardrails into `deploy/app.py` (bad spec finding); corrected future-tense guardrail references in `docs/ai-system-card.md` to deployed state (patch finding); added 4 tests for deployed runtime path; 120/120 tests passing |
