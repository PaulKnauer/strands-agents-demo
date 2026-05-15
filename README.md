# strands-agents-demo

A minimal, forkable reference implementation of an AI agent built with the [Strands Agents SDK](https://strandsagents.com) and deployed to [AWS AgentCore](https://aws.amazon.com/bedrock/agentcore/). The agent calculates a person's age in days from their date of birth — a deliberately simple use case that keeps the focus on the framework patterns, not the business logic.

This project also ships a complete **NIST AI RMF compliance layer** — governance documentation, audit logging, Bedrock Guardrails, automated red-team CI, and a CloudWatch compliance dashboard. See [NIST AI RMF Compliance](#nist-ai-rmf-compliance) below.

Epic 4 added **multi-provider model expansion** — Bedrock-first staged support for additional model families. See [Model expansion roadmap](#model-expansion-roadmap) below.

## What This Demonstrates

**Agent patterns:**

| Pattern | Where |
|---------|-------|
| `@tool` decorator — defining a custom tool the LLM can call | `agent.py` |
| Model provider switching via env vars (Bedrock ↔ Gemini, local only) | `agent.py`, `.env.example` |
| Conversational REPL loop with Strands `Agent()` | `agent.py` |
| One-command AgentCore deployment with IAM provisioning | `deploy/deploy.py` |
| AgentCore observability via ADOT bootstrap + Transaction Search | `deploy/bootstrap.py`, CloudWatch |
| Transaction Search enablement via CDK | `infra/transaction_search_stack.py` |
| Use-case behavior fork points for local and cloud runtimes | `agent.py`, `deploy/app.py` |

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
- [Model expansion roadmap](#model-expansion-roadmap)
- [Make Targets](#make-targets)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Prerequisites

**Required for local run:**

- Python 3.11+ ([download](https://www.python.org/downloads/))
- AWS account with Amazon Bedrock enabled
- Bedrock model access granted for **`us.amazon.nova-micro-v1:0`** in `us-east-1`
  _(Console → Amazon Bedrock → Model access → Request access)_
- AWS credentials configured locally via the AWS CLI, IAM Identity Center, or another standard AWS SDK credential provider.

**Additional requirements for AgentCore deployment:**

- AWS CLI installed and configured
- IAM user/role with these permissions:
  - `bedrock-agentcore-control:*`
  - `s3:CreateBucket`, `s3:PutObject`, `s3:HeadBucket`, `s3:PutEncryptionConfiguration`
  - `iam:CreateRole`, `iam:GetRole`, `iam:PutRolePolicy`
  - `sts:GetCallerIdentity`

**Additional requirements for scheduled red-team CI:**

- Node.js 20+ for `npx aws-cdk`
- AWS credentials with permission to deploy IAM resources via CDK
- Run `make redteam-role`, then store the `GitHubActionsRoleArn` output as the repository secret `AWS_ROLE_TO_ASSUME`
- AgentCore deployment is not required for red-team CI; promptfoo invokes the Bedrock model target directly.

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
MODEL_ID=us.amazon.nova-micro-v1:0
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

AgentCore runs the agent as a managed cloud runtime with automatic tool-call tracing. The runtime IAM role and Transaction Search are CDK-managed; `deploy.py` packages code, uploads the artifact, and creates or updates the runtime.

**Step 1:** Confirm local agent works first (complete [Local Setup](#local-setup)).

**Step 2:** Provision the CDK-managed runtime role:

```bash
make create-role
```

If this is the first run after migrating from the older direct-IAM flow and
`make create-role` fails with `AWS::IAM::Role ... already exists`, the legacy
unmanaged runtime role is still present in the account with the same fixed name.
Remove that legacy role once, then rerun `make create-role` so CloudFormation/CDK
becomes the sole owner of `AmazonBedrockAgentCoreRuntime_<agent>`.

**Step 3:** Enable CloudWatch Transaction Search once per account/region:

```bash
make transaction-search
```

This deploys an idempotent CDK stack that creates the required CloudWatch Logs resource policy and `AWS::XRay::TransactionSearchConfig` for Transaction Search. Re-running `make transaction-search` updates the same stack in place. The stack defaults to `100%` indexing so low-volume demo traffic is actually searchable in CloudWatch `Sessions` and `Traces`. AWS documents this as the supported CloudFormation/CDK path. If Transaction Search was previously enabled manually in this region, disable it before the first CDK deploy of this stack, then let this stack become the owner.

To remove the IaC-managed Transaction Search configuration later:

```bash
make teardown-transaction-search
```

**Step 4:** Deploy:

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
  IAM role exists (CDK-managed): AmazonBedrockAgentCoreRuntime_age_in_days_demo
Step 4/5: Deploying AgentCore runtime (idempotent)...
  Creating new AgentCore runtime 'age_in_days_demo'...
Step 5/5: Waiting for runtime to be ready...
  Waiting for agent to be ready ........... ✅

🎉 Agent deployed successfully!
   Endpoint URL: https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/.../invocations
```

**Step 5:** Verify the deployed agent responds:

```bash
python deploy/verify.py
# or: make verify
```

Expected output (the age in days will reflect today's date when you run it):

```
Verifying deployed agent 'age_in_days_demo' in us-east-1...
  Expected age: <computed> days  (DOB: 1990-03-14 → today, UTC)

Observability preflight:
  StrandsDemoAgentCoreRuntimeRoleStack: CREATE_COMPLETE
  StrandsDemoTransactionSearchStack: CREATE_COMPLETE
  Transaction Search: CloudWatchLogs / ACTIVE

  Runtime: age_in_days_demo
  Runtime ARN: arn:aws:bedrock-agentcore:...
  Test prompt: "I was born on 14th March 1990"

Agent responded (in 3.2s):

You were born <computed> days ago! ...

  Expected: <computed> days  |  Elapsed: 3.2s (within 7s budget)  |  Result: PASS

Verification complete.
Next: open CloudWatch GenAI observability or Transaction Search to confirm get_today_date tool traces and the final response are visible.
  https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#gen-ai-observability:
  https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#xray:traces
```

The verifier checks that the response contains the correct UTC-based age in days (not just any number) and that the response arrives within the 7-second performance budget. To override the budget: `VERIFY_PERF_BUDGET_SECONDS=10 python deploy/verify.py`. To extend the transport timeout for slow networks: set `VERIFY_TIMEOUT_SECONDS=60` in `.env`.

Before invocation, the verifier also prints a non-fatal observability preflight for the CDK-managed runtime role stack, the CDK-managed Transaction Search stack, and X-Ray's trace-segment destination. If a prerequisite is missing, run the printed `make create-role` or `make transaction-search` command in the same AWS account and `AWS_REGION`; if the X-Ray destination is not `CloudWatchLogs / ACTIVE`, check for manual Transaction Search drift and follow the Step 3 caveat.

**Step 6:** Confirm AgentCore observability:

1. Open the region-scoped CloudWatch GenAI observability link printed by `make verify`.
2. Open the session that corresponds to the `Runtime session ID` printed by `make verify`, or use the region-scoped CloudWatch Transaction Search link to inspect traces in `/aws/spans/default`.
3. The AgentCore console invocation history is also useful for runtime-level context, but CloudWatch is the acceptance surface for this observability check.
4. Confirm the trace includes:
   - A `get_today_date` **tool invocation** with its input and output (today's UTC date in ISO format).
   - The **final text response** containing the age in days.
5. If traces are not visible immediately after enablement, wait a few minutes, re-run `make verify`, and check CloudWatch again. AWS notes it can take about ten minutes for spans to become searchable after Transaction Search is enabled.
6. `deploy/bootstrap.py` starts the runtime under AWS Distro for OpenTelemetry (ADOT), and `make verify` sends an explicit `runtimeSessionId` so CloudWatch can group the invocation predictably under `Sessions`.

> **Note:** Transaction Search alone is not enough for AgentCore-hosted agent traces. The deployed runtime must start with ADOT instrumentation enabled. This repo does that through `deploy/bootstrap.py` and the bundled `aws-opentelemetry-distro` dependency.

**Teardown** (when done):

```bash
python deploy/teardown.py
# or: make teardown
```

To remove the CDK-managed runtime role as well:

```bash
make teardown-role
```

---

## NIST AI RMF Compliance

This project includes a complete [NIST AI Risk Management Framework (AI RMF 1.0)](https://airc.nist.gov/RMF) compliance layer from earlier work. The four NIST AI RMF functions are addressed as follows:

| NIST Function | Subcategories | Artifact | `make` command |
|---|---|---|---|
| **GOVERN** | 1.1, 1.3, 1.4, 1.7, 6.1 | [`docs/governance-charter.md`](docs/governance-charter.md) — roles, risk tolerance, review cadence | — |
| **GOVERN** | 1.1, 1.3, 1.4, 6.1 | [`docs/ai-system-card.md`](docs/ai-system-card.md) — system purpose, harm categories, third-party components | — |
| **MAP** | 1.1, 2.2, 5.1 | [`docs/risk-register.md`](docs/risk-register.md) — risk identification and mitigation status | — |
| **MAP** | 1.1, 2.2 | [`docs/ai-system-card.md`](docs/ai-system-card.md) — data flows and harm analysis | — |
| **MEASURE** | 2.4 | [`deploy/guardrail.yaml`](deploy/guardrail.yaml) + [`deploy/create_dashboard.py`](deploy/create_dashboard.py) — guardrail block rate monitoring | `make dashboard` |
| **MEASURE** | 2.5 | [`compliance/hooks.py`](compliance/hooks.py) + [`deploy/create_dashboard.py`](deploy/create_dashboard.py) — tool invocation audit trail | `make dashboard` |
| **MEASURE** | 2.5 | [`infra/transaction_search_stack.py`](infra/transaction_search_stack.py) — CloudWatch Transaction Search enablement for AgentCore spans | `make transaction-search` |
| **MEASURE** | 2.7 | [`infra/github_actions_stack.py`](infra/github_actions_stack.py) + [`.github/workflows/redteam.yml`](.github/workflows/redteam.yml) — short-lived GitHub OIDC credentials for red-team CI | `make redteam-role` |
| **MANAGE** | 1.3, 2.2 | [`deploy/guardrail.yaml`](deploy/guardrail.yaml) — Bedrock Guardrails (PII redaction, prompt-injection defence, content filtering) | `make deploy` |
| **MANAGE** | 2.4 | [`docs/risk-register.md`](docs/risk-register.md) + CloudWatch dashboard — incident tracking and audit trail | `make dashboard` |
| **MANAGE** | 4.1 | [`docs/ai-system-card.md`](docs/ai-system-card.md) — human oversight mechanisms | — |
| **MEASURE** | 2.4, 2.5 (automated) | [`tests/unit/test_safety_boundaries.py`](tests/unit/test_safety_boundaries.py), [`compliance/promptfoo-redteam.yaml`](compliance/promptfoo-redteam.yaml) — red-team CI | `make redteam` |

**Key compliance files:**

- `docs/` — three governance documents (system card, risk register, governance charter)
- `compliance/hooks.py` — `AuditLoggingHook` attaches to the Strands lifecycle and emits a JSONL audit record on every tool call
- `deploy/guardrail.yaml` — Bedrock Guardrails policy applied to both the local REPL (`agent.py`) and the AgentCore cloud runtime (`deploy/app.py`)
- `deploy/create_dashboard.py` — deploys the `NIST-RMF-AgentCompliance` CloudWatch dashboard; run `make dashboard` after deploying the agent
- `infra/` — AWS CDK stacks for the AgentCore runtime role, GitHub Actions OIDC, and CloudWatch Transaction Search

---

## Project Structure

```
strands-agents-demo/
│
├── agent.py              # The agent — @tool, model config, Agent(), REPL loop
│                         # < 150 lines; local development only (Strands SDK)
│
├── model_adapters.py     # Local provider adapter factory (Bedrock, Gemini); local-only,
│                         # not imported by deploy/app.py
│
├── requirements.txt      # Pinned dependencies
│
├── .env.example          # Environment variable template — copy to .env
│
├── deploy/
│   ├── app.py            # Cloud runtime entrypoint (boto3 direct, no Strands SDK)
│   ├── deploy.py         # Provisions S3 and AgentCore runtime (idempotent); expects CDK-managed role
│   ├── verify.py         # Post-deploy smoke test — invokes the live endpoint
│   ├── teardown.py       # Deletes AgentCore runtime, S3 object, and CloudWatch dashboard
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
├── infra/                # AWS CDK stacks — runtime IAM role, GitHub Actions OIDC,
│                         # CloudWatch Transaction Search (deployment support only)
│
├── tests/
│   ├── unit/             # Unit tests for agent.py, app.py, deploy scripts, compliance hooks
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

The deployment scaffolding, VS Code configuration, Makefile targets, and dependency scaffolding are reusable unless your new use case changes runtime dependencies or AWS resource requirements.

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

In AgentCore (cloud), the same flow runs inside `deploy/app.py` via the Bedrock Converse API. `deploy/bootstrap.py` starts the runtime under ADOT so CloudWatch can capture the `get_today_date` span, its output, and the final response text without adding ad hoc log statements.

### Model provider switching (local only)

Change two env vars in `.env` — no code modification required:

```bash
# Amazon Bedrock (default)
MODEL_PROVIDER=bedrock
MODEL_ID=us.amazon.nova-micro-v1:0

# Google Gemini (free tier fallback)
MODEL_PROVIDER=gemini
MODEL_ID=gemini-2.0-flash
GOOGLE_API_KEY=your-key-here
# Also: pip install strands-agents[gemini]
```

> **Note:** Provider switching applies to `agent.py` (local development). The AgentCore deployed runtime (`deploy/app.py`) uses Bedrock Converse directly and supports only Bedrock-backed providers: `MODEL_PROVIDER=bedrock` and `MODEL_PROVIDER=llama`.

### Model expansion roadmap

Epic 4 adds Bedrock-first staged support for additional model families. The table below shows what is currently implemented versus what is planned.

| Stage | Providers / families | Status |
|-------|---------------------|--------|
| Production-aligned | `bedrock` (local + deployed), `llama` (local + deployed, Bedrock-backed) | ✅ |
| Supported local-only | `gemini` (local only, Google API) | ✅ |
| Exploratory local-only evaluation | `litellm` (direct-provider via LiteLLM, e.g. Kimi; **not deployable through AgentCore**) | 🔭 |
| Planned — Bedrock-first | Gemma, Moonshot/Kimi, Qwen, DeepSeek via Amazon Bedrock | 🔜 Planned — not yet enabled |

Setting `MODEL_PROVIDER` to a planned family name today (e.g. `gemma`, `qwen`) will fail explicitly because those paths are not yet implemented. Local adapter selection raises `ValueError`; AgentCore deployment preflight rejects non-Bedrock-backed providers; and an already-running deployed runtime returns an unsupported-provider error before invoking Bedrock.

The `litellm` path is an evaluation boundary, not a default alternative to Bedrock. It requires an optional dependency (`pip install 'strands-agents[litellm]'`), provider-specific credentials (e.g. `MOONSHOT_API_KEY`), and outbound network access to the chosen provider. AgentCore deployment in this repo remains Bedrock-backed only (`bedrock` or `llama`) even when the local `litellm` path is used.

`MODEL_PROVIDER=llama` is Bedrock-backed — it routes through Amazon Bedrock Converse, not a direct Meta API. The concrete supported model is `us.meta.llama3-1-70b-instruct-v1:0` (Meta Llama 3.1 70B Instruct) for `us-east-1` deployments. Llama model access must be granted in your Bedrock account (Console → Amazon Bedrock → Model access) before using this path.

#### Verification strategy

Run the deterministic suite at any time — no live credentials needed:

```bash
venv/bin/python -m pytest tests/unit/test_model_adapters.py tests/unit/test_app.py tests/unit/test_deploy.py tests/unit/test_static.py
```

| Provider | Verification level | Notes |
|----------|--------------------|-------|
| `bedrock` | Unit + static verified; live smoke optional | Live smoke requires AWS credentials and `us.amazon.nova-micro-v1:0` Bedrock access |
| `llama` | Unit + static verified; live smoke optional | Live smoke requires Bedrock access for `us.meta.llama3-1-70b-instruct-v1:0` |
| `gemini` | Unit + static verified; live smoke optional | Live smoke requires `GOOGLE_API_KEY` and `pip install 'strands-agents[gemini]'` |
| `litellm` | Unit + static verified only; live smoke explicitly not required in CI | Live smoke requires `pip install 'strands-agents[litellm]'`, provider credentials (e.g. `MOONSHOT_API_KEY`), and outbound network access |
| `gemma`, `moonshot`, `qwen`, `deepseek` | Unit tests verify explicit rejection | Planned registry entries — not runnable provider keys |

Deployed runtime verification (via `make verify`) applies only to `MODEL_PROVIDER=bedrock` and `MODEL_PROVIDER=llama`. All other provider values return an unsupported-provider error from the deployed runtime before Bedrock is invoked.

---

## Make Targets

```bash
make install        # Create venv and install dependencies
make run            # Run the agent locally (python agent.py)
make redteam-role   # Deploy GitHub Actions OIDC role for scheduled red-team CI
make create-role    # Deploy the AgentCore runtime IAM role via CDK
make transaction-search  # Enable CloudWatch Transaction Search for AgentCore traces
make deploy         # Deploy to AgentCore (python deploy/deploy.py)
make verify         # Verify deployed agent (python deploy/verify.py)
make teardown       # Delete AgentCore runtime, S3 deployment object, and CloudWatch dashboard
make teardown-role  # Destroy the AgentCore runtime IAM role stack
make teardown-redteam-role  # Destroy the GitHub Actions OIDC role stack
make teardown-transaction-search  # Destroy the Transaction Search CDK stack
make dashboard      # Create/update CloudWatch NIST-RMF compliance dashboard
make redteam        # Run promptfoo adversarial red-team scan
make test           # Run unit + eval tests (329 tests)
make test-unit      # Unit tests only
make lint           # Check formatting with black (no changes made)
make format         # Auto-format all Python files with black
```

---

## Troubleshooting

**`AccessDeniedException` during deployment**

Your IAM user is missing permissions. Check the [Prerequisites](#prerequisites) section for the required policy actions. See the [AgentCore permissions guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html).

**Scheduled Redteam workflow fails with `Missing AWS_ROLE_TO_ASSUME secret`**

Deploy the GitHub Actions OIDC role and store its ARN in GitHub Secrets:

```bash
make redteam-role
gh secret set AWS_ROLE_TO_ASSUME --repo PaulKnauer/strands-agents-demo --body <GitHubActionsRoleArn>
```

The workflow uses GitHub OIDC and short-lived AWS credentials. It does not require long-lived AWS access key repository secrets.

**`ResourceNotFoundException` — wrong region**

AgentCore is available in select regions. Confirm `AWS_REGION=us-east-1` in `.env` (or `us-west-2`).

**`KeyError: 'MODEL_PROVIDER'` or similar on startup**

`.env` is missing or the variable isn't set. Run `cp .env.example .env` and fill in all required values.

**Model access error from Bedrock**

`us.amazon.nova-micro-v1:0` must be enabled in your account. Go to AWS Console → Amazon Bedrock → Model access → find Amazon Nova Micro → Request access.

If you see `This Model is marked by provider as Legacy`, your `.env` still points at an older Anthropic Claude model. Update `MODEL_ID` to the Amazon Nova Micro inference profile above, then re-run `make deploy` so AgentCore receives the new environment variable and IAM policy.

**`venv/bin/python: No such file or directory`**

You haven't created the virtual environment yet. Run `python -m venv venv && source venv/bin/activate` first.

**`make verify` fails — agent deployed but no response**

Check the runtime status in the [AgentCore console](https://console.aws.amazon.com/bedrock-agentcore/). If status is not `READY`, re-run `make deploy`.

If the runtime shows `CREATE_FAILED` or `UPDATE_FAILED`, inspect the runtime details first. These failures can happen before the app starts, so CloudWatch logs may not exist yet. A failure reason like `binary files that are incompatible with Linux ARM64` means the deployment package contains the wrong wheel architecture; rebuild with the AgentCore ARM64 packaging path in `deploy/deploy.py`, then deploy again.

Only check CloudWatch logs after the runtime has started or AgentCore links logs from the runtime details page.

**`make verify` fails — wrong age or `FAIL — response does not contain the expected age-in-days value`**

The verifier computes the expected age in days from DOB `1990-03-14` to today's UTC date at run time and checks that the response contains that exact value. Common causes:

- `MODEL_PROVIDER` is not set to a Bedrock-backed provider in `.env`. The AgentCore deployed runtime supports `MODEL_PROVIDER=bedrock` and `MODEL_PROVIDER=llama`; local-only values such as `gemini` or `litellm` return an error response.
- `MODEL_ID` is incorrect or Bedrock model access has not been granted. See the **Model access error** entry below.
- The runtime is deployed in a different region than `AWS_REGION` in `.env` — the invocation reaches the wrong endpoint.

**`make verify` fails — `FAIL — elapsed time … exceeded … performance budget`**

The default performance budget is 7 seconds. To override: `VERIFY_PERF_BUDGET_SECONDS=15 python deploy/verify.py`. To extend the transport (hang) timeout: set `VERIFY_TIMEOUT_SECONDS=60` in `.env`.

**Deployment succeeds but verify times out**

The default transport timeout is 30 seconds. Set `VERIFY_TIMEOUT_SECONDS=60` in `.env` and retry. If the runtime is still starting up, wait a minute and re-run `make verify`.

---

## Contributing

1. All Python files must pass `make lint` (black formatting).
2. All tests must pass: `make test`.
3. Never commit `.env`, AWS credentials, or API keys.
4. To add a new tool: update both `agent.py` (`@tool` decorator) and `deploy/app.py` (`TOOLS` list + tool handler in `_run_agent`).
5. Keep `agent.py` under 150 lines — extract to `tools.py` if it grows beyond that.
6. This repo uses the [BMAD methodology](https://github.com/bmad-agents/bmad-method) — use `/bmad-create-story` before implementing changes and `/bmad-code-review` before submitting.
