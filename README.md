# strands-agents-demo

A minimal, forkable reference implementation of an AI agent built with the [Strands Agents SDK](https://strandsagents.com) and deployed to [AWS AgentCore](https://aws.amazon.com/bedrock/agentcore/). The agent calculates a person's age in days from their date of birth — a deliberately simple use case that keeps the focus on the framework patterns, not the business logic.

This project also ships a complete **NIST AI RMF compliance layer** (Epic 4) — governance documentation, audit logging, Bedrock Guardrails, automated red-team CI, and a CloudWatch compliance dashboard. See [NIST AI RMF Compliance](#nist-ai-rmf-compliance) below.

## What This Demonstrates

**Agent patterns:**

| Pattern | Where |
|---------|-------|
| `@tool` decorator — defining a custom tool the LLM can call | `agent.py` |
| Model provider switching via env vars (Bedrock ↔ Gemini, no code change) | `agent.py`, `.env.example` |
| Conversational REPL loop with Strands `Agent()` | `agent.py` |
| One-command AgentCore deployment with IAM provisioning | `deploy/deploy.py` |
| Automatic tool-call observability — zero custom logging code | AgentCore console |
| Single-file agent that can be forked by changing one file | `agent.py` |

**NIST AI RMF responsible-AI patterns:**

| Pattern | Where |
|---------|-------|
| AI system card, risk register, and governance charter | `docs/` |
| Audit logging hook — JSONL tool-call trail via Strands lifecycle | `compliance/hooks.py` |
| Bedrock Guardrails — PII redaction, prompt-injection defence, content filtering | `deploy/guardrail.yaml` |
| Automated red-team CI — deterministic safety boundary tests + promptfoo adversarial probes | `tests/unit/test_safety_boundaries.py`, `compliance/promptfoo-redteam.yaml` |
| CloudWatch compliance dashboard — guardrail block rate + audit trail | `deploy/create_dashboard.py` |

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
- [VS Code Debugging](#vs-code-debugging)
- [AgentCore Deployment](#agentcore-deployment)
- [NIST AI RMF Compliance](#nist-ai-rmf-compliance)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Make Targets](#make-targets)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Prerequisites

**Required for local run:**

- Python 3.11+ ([download](https://www.python.org/downloads/))
- AWS account with Amazon Bedrock enabled
- Bedrock model access granted for **`anthropic.claude-3-haiku-20240307-v1:0`** in `us-east-1`
  _(Console → Amazon Bedrock → Model access → Request access)_
- AWS credentials configured — either `aws configure` (CLI) or environment variables:
  ```bash
  export AWS_ACCESS_KEY_ID=...
  export AWS_SECRET_ACCESS_KEY=...
  ```

**Additional requirements for AgentCore deployment:**

- AWS CLI installed and configured
- IAM user/role with these permissions:
  - `bedrock-agentcore-control:*`
  - `s3:CreateBucket`, `s3:PutObject`, `s3:HeadBucket`, `s3:PutEncryptionConfiguration`
  - `iam:CreateRole`, `iam:GetRole`, `iam:PutRolePolicy`
  - `sts:GetCallerIdentity`

**Optional (Gemini fallback only):**

- Google AI Studio API key ([get one free](https://aistudio.google.com/apikey))

---

## Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/PaulKnauer/strands-agents-demo.git
cd strands-agents-demo

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
```

> ⚠️ **NEVER commit `.env` to version control.** It contains credentials. `.env` is already in `.gitignore` — keep it that way.

Edit `.env` and fill in your values:

```bash
MODEL_PROVIDER=bedrock
MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
AWS_REGION=us-east-1
AGENT_NAME=age-in-days-demo
```

```bash
# 5. Run the agent
python agent.py
```

**Example interaction:**

```
Age-in-Days Agent (type 'exit' to quit)

You: I was born on 14th March 1990

Agent: You were born 13,149 days ago! That's quite a journey — you've
       lived through some remarkable decades. 🎂

You: exit
```

**Shortcut:** `make install && make run`

---

## VS Code Debugging

Press **F5** — the included `.vscode/launch.json` launches `agent.py` with the debugger attached and `.env` loaded automatically. No manual `export` required.

To verify: set a breakpoint inside `get_today_date()`, press F5, type a date of birth, and execution will pause at the breakpoint.

---

## AgentCore Deployment

AgentCore runs the agent as a managed cloud runtime with automatic tool-call tracing. The deployment script provisions all AWS infrastructure — no console steps required.

**Step 1:** Confirm local agent works first (complete [Local Setup](#local-setup)).

**Step 2:** Deploy:

```bash
python deploy/deploy.py
# or: make deploy
```

The script runs 5 steps and prints the endpoint URL on completion:

```
🚀 Deploying agent 'age_in_days_demo' to AgentCore in us-east-1...

Step 1/5: Ensuring S3 bucket...
  Created S3 bucket: bedrock-agentcore-code-123456789012-us-east-1
Step 2/5: Packaging and uploading agent code...
  Uploaded 4,231,847 bytes → s3://...
Step 3/5: Ensuring IAM execution role...
  Created IAM role: AmazonBedrockAgentCoreRuntime_age_in_days_demo
Step 4/5: Deploying AgentCore runtime (idempotent)...
  Creating new AgentCore runtime 'age_in_days_demo'...
Step 5/5: Waiting for runtime to be ready...
  Waiting for agent to be ready ........... ✅

🎉 Agent deployed successfully!
   Endpoint URL: https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/.../invocations
```

**Step 3:** Verify the deployed agent responds:

```bash
python deploy/verify.py
# or: make verify
```

Expected output:

```
Verifying deployed agent 'age_in_days_demo' in us-east-1...
  Runtime ARN: arn:aws:bedrock-agentcore:...
  Test prompt: "I was born on 14th March 1990"

Agent responded (in 3.2s):

You were born 13,149 days ago! ...

Verification complete.
Next: open the AgentCore console to confirm get_today_date tool traces are visible.
```

**Step 4:** View tool traces in the [AgentCore console](https://console.aws.amazon.com/bedrock-agentcore/) → your agent → Invocation history. Every `get_today_date` call is traced with its input and output — no logging code written.

**Teardown** (when done):

```bash
python deploy/teardown.py
# or: make teardown
```

---

## NIST AI RMF Compliance

Epic 4 of this project implements a complete [NIST AI Risk Management Framework (AI RMF 1.0)](https://airc.nist.gov/RMF) compliance layer. The four NIST AI RMF functions are addressed as follows:

| NIST Function | Subcategories | Artifact | `make` command |
|---|---|---|---|
| **GOVERN** | 1.1, 1.3, 1.4, 1.7, 6.1 | [`docs/governance-charter.md`](docs/governance-charter.md) — roles, risk tolerance, review cadence | — |
| **GOVERN** | 1.1, 1.3, 1.4, 6.1 | [`docs/ai-system-card.md`](docs/ai-system-card.md) — system purpose, harm categories, third-party components | — |
| **MAP** | 1.1, 2.2, 5.1 | [`docs/risk-register.md`](docs/risk-register.md) — risk identification and mitigation status | — |
| **MAP** | 1.1, 2.2 | [`docs/ai-system-card.md`](docs/ai-system-card.md) — data flows and harm analysis | — |
| **MEASURE** | 2.4 | [`deploy/guardrail.yaml`](deploy/guardrail.yaml) + [`deploy/create_dashboard.py`](deploy/create_dashboard.py) — guardrail block rate monitoring | `make dashboard` |
| **MEASURE** | 2.5 | [`compliance/hooks.py`](compliance/hooks.py) + [`deploy/create_dashboard.py`](deploy/create_dashboard.py) — tool invocation audit trail | `make dashboard` |
| **MANAGE** | 1.3, 2.2 | [`deploy/guardrail.yaml`](deploy/guardrail.yaml) — Bedrock Guardrails (PII redaction, prompt-injection defence, content filtering) | `make deploy` |
| **MANAGE** | 2.4 | [`docs/risk-register.md`](docs/risk-register.md) + CloudWatch dashboard — incident tracking and audit trail | `make dashboard` |
| **MANAGE** | 4.1 | [`docs/ai-system-card.md`](docs/ai-system-card.md) — human oversight mechanisms | — |
| **MEASURE** | 2.4, 2.5 (automated) | [`tests/unit/test_safety_boundaries.py`](tests/unit/test_safety_boundaries.py), [`compliance/promptfoo-redteam.yaml`](compliance/promptfoo-redteam.yaml) — red-team CI | `make redteam` |

**Key compliance files:**

- `docs/` — three governance documents (system card, risk register, governance charter)
- `compliance/hooks.py` — `AuditLoggingHook` attaches to the Strands lifecycle and emits a JSONL audit record on every tool call
- `deploy/guardrail.yaml` — Bedrock Guardrails policy applied to both the local REPL (`agent.py`) and the AgentCore cloud runtime (`deploy/app.py`)
- `deploy/create_dashboard.py` — deploys the `NIST-RMF-AgentCompliance` CloudWatch dashboard; run `make dashboard` after deploying the agent

---

## Project Structure

```
strands-agents-demo/
│
├── agent.py              # The agent — @tool, model config, Agent(), REPL loop
│                         # < 150 lines; local development only (Strands SDK)
│
├── requirements.txt      # Pinned dependencies
│
├── .env.example          # Environment variable template — copy to .env
│
├── deploy/
│   ├── app.py            # Cloud runtime entrypoint (boto3 direct, no Strands SDK)
│   ├── deploy.py         # Provisions S3, IAM role, AgentCore runtime (idempotent)
│   ├── verify.py         # Post-deploy smoke test — invokes the live endpoint
│   ├── teardown.py       # Deletes AgentCore runtime, IAM role, and CloudWatch dashboard
│   ├── guardrail.yaml    # Bedrock Guardrails policy — PII redaction, prompt-injection defence
│   ├── create_dashboard.py  # CloudWatch NIST-RMF-AgentCompliance dashboard (idempotent)
│   └── start.sh          # (unused locally) dependency install + launch for runtime
│
├── compliance/
│   ├── hooks.py          # AuditLoggingHook — JSONL tool-call audit trail (NIST MEASURE-2.5)
│   └── promptfoo-redteam.yaml  # Adversarial probe suite for red-team CI
│
├── docs/
│   ├── ai-system-card.md    # System card — purpose, data flows, harm categories (GOVERN, MAP)
│   ├── risk-register.md     # Risk register — identified risks and mitigations (MAP)
│   └── governance-charter.md  # Governance charter — roles, risk tolerance, review cadence (GOVERN)
│
├── tests/
│   ├── unit/             # Unit tests for agent.py, app.py, deploy scripts, compliance hooks
│   ├── integration/      # Integration tests for the agentic tool-calling loop
│   └── evals/            # Deterministic behavioural contract tests
│
├── .vscode/
│   ├── launch.json       # F5 debug config — loads .env automatically
│   └── extensions.json   # Recommended VS Code extensions
│
├── Makefile              # Shortcuts: install, run, deploy, verify, test, lint, redteam, dashboard
│
├── _bmad/                # BMAD framework core — agents, skills, workflows (not agent code)
└── _bmad-output/         # BMAD planning artifacts (PRD, architecture, stories)
                          # Not part of the agent implementation
```

### Why are there two Python files for the agent?

`agent.py` uses the **Strands Agents SDK** — the clean, high-level API that makes this demo readable and forkable. It runs as a local interactive REPL.

`deploy/app.py` uses **boto3 directly** for the AgentCore cloud runtime. The Strands SDK cannot be pip-installed within AgentCore's 30-second startup window, so `app.py` reimplements the same agent behaviour (identical system prompt and tool) using the Bedrock Converse API. This is a deployment constraint, not an architectural preference.

**The agent behaves identically in both environments.** If you fork this project and add tools, add them to both `agent.py` (`@tool` decorator) and `deploy/app.py` (`TOOLS` list + handler in `_run_agent`).

---

## How It Works

```
User types: "I was born on 14th March 1990"
    │
    ▼
REPL loop (agent.py) passes input to Strands Agent()
    │
    ▼
Agent sends to LLM (Bedrock / Gemini) with system prompt + tool list
    │
    ▼
LLM decides: I need today's date → calls get_today_date tool
    │
    ▼
get_today_date() returns: "2026-03-18"   ← stdlib datetime, no network call
    │
    ▼
LLM calculates: days between 1990-03-14 and 2026-03-18 = 13,149
    │
    ▼
LLM responds: "You were born 13,149 days ago! 🎂"
    │
    ▼
Response printed to terminal
```

In AgentCore (cloud), the same flow runs inside `deploy/app.py` via the Bedrock Converse API. Every step where the LLM calls `get_today_date` is automatically captured in the AgentCore console — input, output, and latency — with zero custom logging code.

### Model provider switching

Change two env vars in `.env` — no code modification required:

```bash
# Amazon Bedrock (default)
MODEL_PROVIDER=bedrock
MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# Google Gemini (free tier fallback)
MODEL_PROVIDER=gemini
MODEL_ID=gemini-2.0-flash
GOOGLE_API_KEY=your-key-here
# Also: pip install strands-agents[gemini]
```

---

## Make Targets

```bash
make install        # Create venv and install dependencies
make run            # Run the agent locally (python agent.py)
make deploy         # Deploy to AgentCore (python deploy/deploy.py)
make verify         # Verify deployed agent (python deploy/verify.py)
make teardown       # Delete AgentCore runtime, IAM role, and CloudWatch dashboard
make dashboard      # Create/update CloudWatch NIST-RMF compliance dashboard
make redteam        # Run promptfoo adversarial red-team scan (requires Node.js + AWS creds)
make test           # Run unit + eval tests (134 tests)
make test-unit      # Unit tests only
make lint           # Check formatting with black (no changes made)
make format         # Auto-format all Python files with black
```

---

## Troubleshooting

**`AccessDeniedException` during deployment**

Your IAM user is missing permissions. Check the [Prerequisites](#prerequisites) section for the required policy actions. See the [AgentCore permissions guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html).

**`ResourceNotFoundException` — wrong region**

AgentCore is available in select regions. Confirm `AWS_REGION=us-east-1` in `.env` (or `us-west-2`).

**`KeyError: 'MODEL_PROVIDER'` or similar on startup**

`.env` is missing or the variable isn't set. Run `cp .env.example .env` and fill in all required values.

**Model access error from Bedrock**

`anthropic.claude-3-haiku-20240307-v1:0` must be enabled in your account. Go to AWS Console → Amazon Bedrock → Model access → find Claude 3 Haiku → Request access.

**`venv/bin/python: No such file or directory`**

You haven't created the virtual environment yet. Run `python -m venv venv && source venv/bin/activate` first.

**`make verify` fails — agent deployed but no response**

Check the runtime status in the [AgentCore console](https://console.aws.amazon.com/bedrock-agentcore/). If status is not `READY`, re-run `make deploy`. If it shows `FAILED`, check the CloudWatch logs linked from the console.

**Deployment succeeds but verify times out**

The default verify timeout is 30 seconds. Set `VERIFY_TIMEOUT_SECONDS=60` in `.env` and retry.

---

## Contributing

1. All Python files must pass `make lint` (black formatting).
2. All tests must pass: `make test`.
3. Never commit `.env`, AWS credentials, or API keys.
4. To add a new tool: update both `agent.py` (`@tool` decorator) and `deploy/app.py` (`TOOLS` list + tool handler in `_run_agent`).
5. Keep `agent.py` under 150 lines — extract to `tools.py` if it grows beyond that.
6. This repo uses the [BMAD methodology](https://github.com/bmad-agents/bmad-method) — use `/bmad-create-story` before implementing changes and `/bmad-code-review` before submitting.
