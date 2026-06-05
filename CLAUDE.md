# CLAUDE.md — strands-agents-demo

This file is loaded as persistent context by AI agents. It supplements BMAD configuration and AGENTS.md.

## Quick Start

```bash
make install        # create venv + pip install
make run            # python agent.py (local REPL)
make lint           # black --check
make test           # pytest (unit + evals)
make format         # black auto-format
make deploy         # deploy/app.py → AgentCore
make verify         # smoke test deployed agent
make teardown       # clean up deployed resources
```

## Key Architecture

- **Dual runtime**: `agent.py` (Strands SDK) ↔ `deploy/app.py` (boto3). Keep in sync.
- **Model providers**: `model_adapters.py` — Bedrock (default), Gemini (local), LiteLLM (eval)
- **Compliance**: Audit hooks in `compliance/hooks.py`, Guardrails in `deploy/guardrail.yaml`, red-team in `compliance/promptfoo-redteam.yaml`
- **CDK stacks**: `infra/` — AgentCore runtime role, Transaction Search, GitHub OIDC

## Rules

1. Every tool change → update BOTH `agent.py` AND `deploy/app.py`
2. Never deploy without `AuditLoggingHook` attached
3. All env vars come from `.env` — never hardcode
4. Format: `make format` before commit (black)

## BMAD Context

BMAD artifacts under `_bmad-output/planning-artifacts/`:
- `prd.md`, `epics.md`, `architecture.md`
- `sprint-status.yaml`, `project-context.md`

BMAD skills in `.claude/skills/` and `.cursor/skills/`.
