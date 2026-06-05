# AGENTS.md
## AI Agent Operating Contract — strands-agents-demo

This document defines **strict operating rules** for any AI agent (e.g. Claude Code, Codex, Cursor) working in this repository.
The goal is **safe, compliant, forkable** reference implementation of an AI agent on AWS.

---

## 1. Project Intent (Read First)

This repository is a **forkable reference implementation** demonstrating the complete lifecycle of AI agent development and deployment on AWS using the [Strands Agents SDK](https://strandsagents.com) and [AWS AgentCore](https://aws.amazon.com/bedrock/agentcore/).

The agent itself is deliberately simple (age-in-days calculator) — the focus is on the **framework patterns, deployment scaffolding, and NIST AI RMF compliance layer**.

### Key architectural commitments

- **Dual runtime**: `agent.py` (Strands SDK, local REPL) and `deploy/app.py` (boto3, AgentCore cloud). Both must implement identical behaviour — every new tool must be added to both files.
- **NIST AI RMF compliance**: governance docs, audit hooks, Bedrock Guardrails, red-team CI, and CloudWatch dashboard are not optional extras — they are core deliverables.
- **Model provider abstraction**: Provider switching via `model_adapters.py` factory. Bedrock is the production path; Gemini and LiteLLM are local-only evaluation paths.
- **ADOT instrumentation**: AgentCore deployments use AWS Distro for OpenTelemetry for trace visibility in CloudWatch.

---

## 2. Source of Truth

### Single sources of truth (DO NOT DUPLICATE)

| Concern | Location |
|---|---|
| Agent logic (local) | `agent.py` — `@tool` decorator, system prompt, REPL loop |
| Agent logic (cloud) | `deploy/app.py` — identical behaviour via boto3 Converse API |
| Model provider factory | `model_adapters.py` |
| Deployment script | `deploy/deploy.py` |
| Post-deploy verification | `deploy/verify.py` |
| Teardown | `deploy/teardown.py` |
| Bedrock Guardrails policy | `deploy/guardrail.yaml` |
| Audit logging hook | `compliance/hooks.py` — `AuditLoggingHook` |
| Red-team probes | `compliance/promptfoo-redteam.yaml` |
| CloudWatch dashboard | `deploy/create_dashboard.py` |
| Governance docs | `docs/ai-system-card.md`, `docs/risk-register.md`, `docs/governance-charter.md` |
| CDK stacks | `infra/agentcore_runtime_role_stack.py`, `infra/transaction_search_stack.py`, `infra/github_actions_stack.py` |
| BMAD planning artifacts | `_bmad-output/planning-artifacts/` |
| BMAD implementation artifacts | `_bmad-output/implementation-artifacts/` |
| Environment template | `.env.example` |
| CI/CD | `.github/workflows/ci.yml`, `.github/workflows/redteam.yml` |

❌ **Never hardcode AWS account IDs, agent IDs, or API keys in code.**

---

## 3. Non-Negotiable Rules

### Dual-file parity (CRITICAL)

Every tool or behaviour change MUST be implemented in **both** `agent.py` and `deploy/app.py`. The system prompt, tool definitions, and response format must be identical. Use the README diff as a checklist.

### Compliance

- Audit hooks MUST be attached to the agent via `hooks=[AuditLoggingHook()]` — never deploy without audit.
- Bedrock Guardrails policy in `deploy/guardrail.yaml` MUST be applied in both local REPL and AgentCore runtime.
- Never lower the coverage floor without explicit approval.

### Secrets

- Never commit `.env` — it's gitignored.
- Never commit AWS credentials, API keys, or tokens.
- Always use environment variables for configuration.

### Testing

- All tests must pass before merging to `main`: `make test` (unit + evals).
- `make lint` must pass (black formatting check).
- Safety boundary tests in `tests/unit/test_safety_boundaries.py` must always pass.

---

## 4. BMAD Integration

This project is BMAD-native. The `_bmad/` directory at project root contains the BMAD framework core configuration.

### BMAD workflows use these files

- **`_bmad/bmm/config.yaml`** — project name, artifact paths, communication language
- **`_bmad/config.toml`** — installer-managed module configuration
- **`_bmad/config.user.toml`** — personal overrides (gitignored)
- **`_bmad-output/project-context.md`** — project overview and status (loaded by BMAD skills on activation)
- **`_bmad-output/planning-artifacts/prd.md`** — product requirements document
- **`_bmad-output/planning-artifacts/epics.md`** — epic and story breakdown
- **`_bmad-output/planning-artifacts/architecture.md`** — system architecture
- **`_bmad-output/implementation-artifacts/sprint-status.yaml`** — current sprint state
- **`.claude/skills/`** — BMAD agent skills for Claude Code (analyst, architect, dev, tech-writer, etc.)
- **`.cursor/skills/`** — BMAD agent skills for Cursor (mirrors `.claude/skills/`)

### On activation, BMAD skills will

1. Load BMAD config from `_bmad/bmm/config.yaml`
2. Load `_bmad-output/project-context.md` if it exists
3. Load `_bmad-output/implementation-artifacts/sprint-status.yaml` if it exists
4. Load this AGENTS.md and CLAUDE.md as persistent facts
5. Load BMAD agent persona from `_bmad/config.toml` agent definitions

---

## 5. CI/CD Quality Gates

Before any merge to `main`:

- [ ] `make lint` passes (black formatting check)
- [ ] `make test` passes (unit + eval tests)
- [ ] `.env` is not committed
- [ ] `agent.py` and `deploy/app.py` are in sync (same tools, same system prompt)
