# Story 2.4: AgentCore Observability Foundation and CDK Contract

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want AgentCore observability prerequisites and configuration owned by a repeatable CDK contract,
so that I can verify traces through a deterministic AWS setup instead of ad hoc console discovery.

## Acceptance Criteria

1. **Given** the repo provisions observability prerequisites for AgentCore
   **When** I inspect and run the supported infrastructure path
   **Then** CloudWatch Transaction Search enablement, runtime-role observability permissions, and related stack outputs are defined through the repo's CDK and Make targets
   **And** the setup is reproducible without manual console editing

2. **Given** I prepare to verify a deployed runtime
   **When** I follow the repo's documented observability flow
   **Then** I have an explicit checklist for runtime role, ADOT bootstrap, Transaction Search, session grouping, and AWS console locations
   **And** the guidance states exactly what must be visible for success: the `get_today_date` tool activity and the final response trace

3. **Given** observability prerequisites are missing or misconfigured
   **When** I run the supported preflight or verification path
   **Then** the repo surfaces actionable diagnostics for common blockers such as missing CDK stacks, manual Transaction Search drift, account/region mismatch, or missing runtime configuration
   **And** the resolution path is explicit enough for a new developer to follow

4. **Given** the observability infrastructure has already been provisioned once
   **When** I rerun the setup path
   **Then** the same CDK stacks are updated or reused idempotently
   **And** deterministic tests lock the policy, stack-shape, and make-target contract

## Tasks / Subtasks

- [ ] Task 1: Reconcile the observability infrastructure contract across CDK entrypoints and stacks (AC: #1, #4)
  - [ ] Inspect `infra/app.py`, `infra/transaction_search_stack.py`, and `infra/agentcore_runtime_role_stack.py` before editing; preserve the current CDK ownership model rather than reintroducing direct IAM or console-only setup
  - [ ] Confirm the CDK app loads `.env` before reading `AGENT_NAME` and `MODEL_ID`, and keep runtime-role stack creation conditional on those values being present
  - [ ] Tighten stack outputs or comments where needed so a developer can tell which stack enables Transaction Search and which stack owns the AgentCore runtime role
  - [ ] Preserve least-privilege intent in the runtime role stack and avoid broadening resources to `"*"` unless an AWS requirement makes it unavoidable and is documented

- [ ] Task 2: Make the observability setup and preflight path explicit in developer-facing commands and docs (AC: #1, #2, #3)
  - [ ] Inspect `Makefile`, `README.md`, `deploy/verify.py`, and `deploy/bootstrap.py` before editing; preserve the current deploy/verify/bootstrap split
  - [ ] Define the exact supported setup order for observability prerequisites, including role provisioning, Transaction Search provisioning, deployment, verification, and trace inspection
  - [ ] Add or tighten preflight checks or guidance so the verification flow calls out missing CDK-managed prerequisites before a developer assumes AgentCore itself is broken
  - [ ] Document the expected success evidence precisely: `get_today_date` tool activity, final response visibility, and the console or CloudWatch surfaces where they should appear
  - [ ] Document the one-time/manual caveat AWS calls out for Transaction Search so the repo explains how to handle pre-existing manual enablement or drift

- [ ] Task 3: Preserve the runtime/observability boundary and avoid misleading shortcuts (AC: #2, #3)
  - [ ] Do not add custom application logging solely to satisfy observability; managed AgentCore and CloudWatch remain the acceptance surface
  - [ ] Do not collapse local Strands execution and deployed AgentCore verification into one path; keep `agent.py` out of scope unless a proven defect forces a synchronized prompt note
  - [ ] Preserve `deploy/bootstrap.py` as the ADOT bootstrap entrypoint and ensure any documentation changes still describe why it exists
  - [ ] Keep the trace-verification contract specific to deployed AgentCore runtime behavior, not local REPL behavior

- [ ] Task 4: Add deterministic tests for the observability foundation contract (AC: #1, #3, #4)
  - [ ] Extend `tests/unit/test_transaction_search_stack.py` for any new stack outputs, validation, or drift-protection behavior
  - [ ] Extend `tests/unit/test_agentcore_runtime_role_stack.py` for any runtime-role observability permission or output changes
  - [ ] Add or tighten tests for `infra/app.py` and `Makefile` if the observability stack wiring or targets change
  - [ ] If `deploy/verify.py` gains preflight logic, add focused unit coverage without turning mock-only tests into fake integration tests

- [ ] Task 5: Run deterministic validation and record remaining live-verification boundaries (AC: #1, #2, #3, #4)
  - [ ] Run `venv/bin/black --check infra/app.py infra/transaction_search_stack.py infra/agentcore_runtime_role_stack.py`
  - [ ] Run `venv/bin/python -m pytest tests/unit/test_transaction_search_stack.py tests/unit/test_agentcore_runtime_role_stack.py`
  - [ ] Run any additional targeted test files changed by this story
  - [ ] Run `venv/bin/python -m pytest`
  - [ ] If live AWS validation is not performed for this story, state plainly that Story 2.3 remains the place where final runtime invocation and trace confirmation are proven

## Dev Notes

### Story Intent

Story 2.3 currently mixes two kinds of work: deterministic hardening of the verifier and AWS-dependent proof that managed observability is visible in practice. The repo now already contains CDK-managed observability foundations such as `TransactionSearchStack` and `AgentCoreRuntimeRoleStack`, but that foundation is not yet treated as its own explicit story contract. Story 2.4 exists to make the infrastructure and developer workflow around observability first-class before more time is spent chasing live console symptoms.

This is a brownfield reconciliation story. The likely implementation shape is not greenfield CDK creation; it is tightening and documenting the current CDK stacks, make targets, and verification preflight so the later live trace confirmation path is deterministic and repeatable.

### Current State Of Files Likely To Be Modified

- `infra/app.py`: current CDK entrypoint that loads `.env`, always synthesizes GitHub Actions and Transaction Search stacks, and conditionally synthesizes the AgentCore runtime role stack when `AGENT_NAME` and `MODEL_ID` are present. This is the primary wiring file for the observability foundation. [Source: infra/app.py]
- `infra/transaction_search_stack.py`: current CloudWatch/X-Ray infrastructure for Transaction Search. It provisions a Logs resource policy plus `AWS::XRay::TransactionSearchConfig`, and supports a context override for indexing percentage. [Source: infra/transaction_search_stack.py]
- `infra/agentcore_runtime_role_stack.py`: current CDK runtime-role stack with Bedrock invocation permissions, CloudWatch Logs permissions, X-Ray permissions, and `cloudwatch:PutMetricData` scoped to the `bedrock-agentcore` namespace. [Source: infra/agentcore_runtime_role_stack.py]
- `tests/unit/test_transaction_search_stack.py`: current stack-shape tests for resource policy, transaction-search config, dependency ordering, and make targets. Extend this if the contract becomes more explicit. [Source: tests/unit/test_transaction_search_stack.py]
- `tests/unit/test_agentcore_runtime_role_stack.py`: current tests for named role creation, outputs, observability permissions, and make targets. Use it to lock any role/output changes exactly. [Source: tests/unit/test_agentcore_runtime_role_stack.py]
- `README.md`: current deploy/verify/Transaction Search guidance already explains ADOT bootstrap, `make transaction-search`, and the expected trace content. Tighten only the parts needed to make observability setup deterministic. [Source: README.md#AgentCore Deployment]
- `Makefile`: current `create-role`, `transaction-search`, and teardown targets are part of the repo contract; keep docs and test expectations aligned with it. [Source: Makefile]
- `deploy/verify.py`: current live verifier already checks response correctness and latency. If this story adds preflight checks, keep them focused on observability prerequisites and avoid conflating them with live AWS proof. [Source: deploy/verify.py]
- `deploy/bootstrap.py`: current ADOT bootstrap entrypoint is part of the observability story boundary and should usually be inspect-only unless a concrete defect is found. [Source: deploy/bootstrap.py]

### Files To Avoid Unless A Concrete Defect Requires Them

- `agent.py`: local Strands REPL path; do not change it for this observability-foundation story. [Source: _bmad-output/project-context.md]
- `model_adapters.py`: local adapter factory; out of scope for CDK observability prerequisites. [Source: _bmad-output/project-context.md]
- `deploy/app.py`: deployed runtime behavior is already covered by Stories 2.2 and 2.3; avoid edits unless a proven observability-boundary defect requires one. [Source: _bmad-output/implementation-artifacts/2-2-deployed-runtime-adapter-contract.md]
- `_bmad-output/implementation-artifacts/2-3-endpoint-verification-and-observability-confirmation.md`: treat as previous-story intelligence, not the file to keep editing during this story. [Source: _bmad-output/implementation-artifacts/2-3-endpoint-verification-and-observability-confirmation.md]

### What Must Be Preserved

- Local and deployed runtimes remain separate. `agent.py` is the local Strands path; deployed AgentCore behavior stays in `deploy/app.py` and `deploy/bootstrap.py`. [Source: _bmad-output/project-context.md#Framework-Specific Rules]
- `deploy/bootstrap.py` exists so ADOT instrumentation starts before the runtime imports boto3 or the AgentCore SDK. Do not remove or trivialize that boundary in docs or code. [Source: deploy/deploy.py]
- The runtime IAM role stays least-privilege and scoped to the configured model/runtime resources rather than broad wildcard policies. [Source: infra/agentcore_runtime_role_stack.py]
- Transaction Search remains CDK-managed through `AWS::Logs::ResourcePolicy` and `AWS::XRay::TransactionSearchConfig`, not through undocumented manual console drift. [Source: infra/transaction_search_stack.py]
- Managed observability is the product message. Do not add custom app logging or trace wrappers solely to make the story pass. [Source: _bmad-output/planning-artifacts/architecture.md#Observability & Monitoring]
- The final trace proof still belongs to a live AgentCore invocation path. This story should make that path deterministic, not falsely claim the live proof was completed. [Source: _bmad-output/implementation-artifacts/2-3-endpoint-verification-and-observability-confirmation.md]

### Architecture Compliance Guardrails

- `infra/app.py` is the single CDK composition point for this repo's observability stacks. Prefer tightening it over creating parallel stack entrypoints unless a new stack boundary is clearly justified. [Source: infra/app.py]
- `TransactionSearchStack` currently assumes one-time per account/region enablement and supports context-based indexing percentage. Any new validation or outputs should preserve idempotent re-deploy behavior. [Source: infra/transaction_search_stack.py]
- `AgentCoreRuntimeRoleStack` already includes the observability-related permissions the runtime needs: CloudWatch Logs write permissions, X-Ray segment/telemetry permissions, and `cloudwatch:PutMetricData` under the `bedrock-agentcore` namespace. Any changes should refine this contract, not dilute it. [Source: infra/agentcore_runtime_role_stack.py]
- The Make targets are part of the contract. If stack names or workflows change, update both the Makefile and the corresponding unit tests together. [Source: tests/unit/test_transaction_search_stack.py] [Source: tests/unit/test_agentcore_runtime_role_stack.py]
- `deploy/verify.py` should remain the data-plane verifier. If it grows preflight checks, they should report missing prerequisites cleanly without turning the verifier into a replacement deployment tool. [Source: deploy/verify.py]

### Latest Technical Information

- AWS says AgentCore service-provided observability data is visible through CloudWatch-backed surfaces, but a one-time CloudWatch Transaction Search setup is required before metrics, spans, and traces can be viewed. [Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability-service-provided.html]
- AWS documents AgentCore Observability as providing dashboards and telemetry for operational visibility, with trace viewing flowing through CloudWatch Transaction Search. [Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability.html]
- AWS documents the view path for AgentCore observability data and notes the CloudWatch generative AI observability page and Transaction Search console as the primary surfaces for session and trace inspection. [Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability-view.html]
- CloudWatch Transaction Search ingests X-Ray spans into the `aws/spans` log group and unlocks search/analytics over spans and traces. [Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search.html]
- AWS documents `AWS::XRay::TransactionSearchConfig` as the CloudFormation resource for setting the percentage of spans indexed for transaction search, with values from 0 to 100 and no interruption on update. [Source: https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-xray-transactionsearchconfig.html]
- AWS also documents a CloudFormation/CDK caveat: if Transaction Search was already enabled manually, disable it before enabling it through CloudFormation/CDK for the first time. Preserve this warning in repo guidance. [Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search-Cloudformation.html]
- AWS CDK exposes Transaction Search through `aws_cdk.aws_xray.CfnTransactionSearchConfig`, which matches the repo's current stack design. [Source: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_xray/CfnTransactionSearchConfig.html]

### Regression Risks To Avoid

- Adding a second, conflicting observability provisioning path outside CDK and leaving future developers to guess which one is authoritative.
- Weakening the runtime-role policy to broad wildcards just to make setup easier.
- Treating Transaction Search enablement as sufficient by itself and forgetting the ADOT bootstrap/runtime-session requirements already encoded in the repo.
- Claiming observability is fully proven without a live deployed invocation after the infrastructure prerequisites are in place.
- Regressing Makefile or stack-name contracts that existing unit tests already lock.
- Turning `deploy/verify.py` into a deployment/orchestration script instead of keeping it a verification tool with focused preflight checks.

### Previous Story Intelligence

- Story 2.2 established the deployed-runtime boundary: deployed AgentCore stays Bedrock-first and must not import local Strands runtime modules. Preserve that separation in all observability guidance. [Source: _bmad-output/implementation-artifacts/2-2-deployed-runtime-adapter-contract.md]
- Story 2.3 already hardened the verifier, ADOT bootstrap usage, runtime-session grouping, README observability checklist, and troubleshooting for missing traces. Reuse that work instead of recreating a second observability explanation path. [Source: _bmad-output/implementation-artifacts/2-3-endpoint-verification-and-observability-confirmation.md]
- Recent code work introduced CDK-managed runtime role and Transaction Search stacks plus tests around their make targets and resource shapes. This story should treat those as the foundation, not as optional sidecars. [Source: 2456bb9]

### Git Intelligence

- `2456bb9` - Harden AgentCore deploy/verify flow and add CDK observability foundations. Relevant because it introduced the current observability foundation code and tests this story will refine.
- `43eff0c` - Record BMAD sprint artifacts and story state. Relevant because it preserved the current 2.3 artifact without splitting the new observability story yet.
- `425810e` - Complete Story 2.2 runtime contract. Relevant because it locked the deployed-runtime boundary that observability guidance must preserve.

### Project Structure Notes

- Expected UPDATE files:
  - `infra/app.py`
  - `infra/transaction_search_stack.py`
  - `infra/agentcore_runtime_role_stack.py`
  - `tests/unit/test_transaction_search_stack.py`
  - `tests/unit/test_agentcore_runtime_role_stack.py`
  - `README.md`
  - `Makefile`
  - `deploy/verify.py` only if focused observability preflight checks are added
- Expected INSPECT-only files unless a defect is found:
  - `deploy/bootstrap.py`
  - `deploy/deploy.py`
  - `deploy/app.py`
  - `agent.py`
  - `model_adapters.py`

### Testing Requirements

- Required deterministic validation:
  - `venv/bin/black --check infra/app.py infra/transaction_search_stack.py infra/agentcore_runtime_role_stack.py`
  - `venv/bin/python -m pytest tests/unit/test_transaction_search_stack.py tests/unit/test_agentcore_runtime_role_stack.py`
  - `venv/bin/python -m pytest` for full regression protection
- If `README.md`, `Makefile`, or `deploy/verify.py` change, run the relevant targeted tests that lock those contracts.
- Live AWS validation is optional for this story. If not performed, record that this story only establishes the observability foundation and that Story 2.3 still owns final live trace confirmation.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 2: AgentCore Deployment and Observability]
- [Source: _bmad-output/planning-artifacts/prd.md#Technical Success]
- [Source: _bmad-output/planning-artifacts/prd.md#Journey 4: Morgan — The Demo Observer]
- [Source: _bmad-output/planning-artifacts/architecture.md#Observability & Monitoring]
- [Source: _bmad-output/project-context.md#Framework-Specific Rules]
- [Source: _bmad-output/project-context.md#Deployment Workflow Rules]
- [Source: _bmad-output/implementation-artifacts/2-2-deployed-runtime-adapter-contract.md]
- [Source: _bmad-output/implementation-artifacts/2-3-endpoint-verification-and-observability-confirmation.md]
- [Source: infra/app.py]
- [Source: infra/transaction_search_stack.py]
- [Source: infra/agentcore_runtime_role_stack.py]
- [Source: tests/unit/test_transaction_search_stack.py]
- [Source: tests/unit/test_agentcore_runtime_role_stack.py]
- [Source: README.md#AgentCore Deployment]
- [Source: Makefile]
- [Source: deploy/verify.py]
- [Source: deploy/deploy.py]
- [Source: deploy/bootstrap.py]
- [Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability-service-provided.html]
- [Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability.html]
- [Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability-view.html]
- [Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search.html]
- [Source: https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-xray-transactionsearchconfig.html]
- [Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search-Cloudformation.html]
- [Source: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_xray/CfnTransactionSearchConfig.html]

## Change Log

- 2026-05-12: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

### Completion Notes List

- Created Story 2.4 to separate deterministic observability-foundation work from Story 2.3 live trace confirmation.
- Pointed implementation toward the existing CDK stacks, Make targets, and ADOT/verify workflow already present in the repo.

### File List

- `_bmad-output/implementation-artifacts/2-4-agentcore-observability-foundation-and-cdk-contract.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
