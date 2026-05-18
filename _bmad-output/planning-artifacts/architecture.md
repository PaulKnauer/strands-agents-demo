---
stepsCompleted: ['step-01-init', 'step-02-context', 'step-03-starter', 'step-04-decisions', 'step-05-patterns', 'step-06-structure', 'step-07-validation', 'step-08-complete']
lastStep: 8
status: 'complete'
completedAt: '2026-03-16'
inputDocuments: ['_bmad-output/planning-artifacts/prd.md']
workflowType: 'architecture'
project_name: 'strands-agents-demo'
user_name: 'Paul'
date: '2026-03-16'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**

29 FRs across 7 capability areas reveal a deliberately simple agent with a sophisticated deployment story:

- **Agent Conversation (FR1–FR5):** Single-purpose conversational agent. Accepts natural language date input, handles multiple formats, validates gracefully. No multi-turn state required for MVP.
- **Date Calculation (FR6–FR8):** Trivially simple logic — the complexity lies in the tool invocation pattern, not the calculation itself.
- **Tool Framework (FR9–FR11):** Core showcase capability — Strands `@tool` decorator pattern, tool invocation during conversation, observability of tool calls in AgentCore.
- **Configuration Management (FR12–FR15):** Fully env-var-driven. No config files, no hardcoded values. `.env.example` as the developer's contract.
- **Local Development (FR16–FR19):** Single-command run, VS Code F5 debug, `pip install -r requirements.txt`. Zero friction setup.
- **AgentCore Deployment (FR20–FR23):** Scripted IaC deployment to `us-east-1`. No manual console steps. Idempotent. Troubleshooting documented.
- **Project Documentation (FR26–FR29):** Documentation is a first-class deliverable — README, inline comments, `.env.example`, self-explanatory structure.

**Non-Functional Requirements:**

| NFR | Architectural Implication |
|---|---|
| 5s response time (deployed) | AgentCore-managed; no custom caching or optimization needed |
| 10s local startup | Minimal dependencies; fast import time critical |
| No hardcoded credentials | `python-dotenv` or `os.environ`; no config files committed |
| Minimum IAM permissions | Deployment script must define least-privilege IAM policy |
| PEP 8 compliance | Code formatting tool (e.g. `black`) recommended |
| <150 lines agent file | Architecture must enforce single-responsibility — agent logic file stays lean |
| Forkable via single file change | Clean separation between agent logic and infrastructure |

**Scale & Complexity:**

- **Primary domain:** Developer tool / SDK reference implementation
- **Complexity level:** Low (intentional) — the simplicity of the agent IS the product quality signal
- **Estimated architectural components:** 4 — Agent module, Tool module, Configuration loader, Deployment script
- **Runtime environments:** 2 — Local (Python CLI) and Production (AWS AgentCore)

### Technical Constraints & Dependencies

- **Language:** Python 3.11+
- **Agent framework:** Strands Agents SDK (version to be pinned in `requirements.txt`)
- **LLM:** Capability-driven model abstraction with Amazon Bedrock as the primary inference and deployment-aligned control plane for MVP. Initial local adapters support Bedrock and Gemini; the architecture is designed for staged expansion toward Gemma, Moonshot AI, Llama, Qwen, and DeepSeek.
- **Deployment target:** AWS AgentCore, `us-east-1`
- **IDE:** VS Code — `.vscode/launch.json` and `extensions.json` required
- **Dependency management:** `requirements.txt` + `venv`
- **IaC technology:** AgentCore CLI (`agentcore configure` / `agentcore deploy`) with boto3 fallback — resolved in step 3

### Cross-Cutting Concerns Identified

1. **Environment variable management** — affects local dev, CI, and deployment; must be consistent across all runtime contexts
2. **Model provider abstraction** — LLM selection logic touches agent config and potentially tool invocation; must be swappable via env var without code changes
3. **Error handling strategy** — agent conversation errors, tool failures, and deployment errors all need consistent handling patterns
4. **Documentation quality** — every file is a teaching artifact; code style, commenting standards, and README structure are architectural concerns, not afterthoughts

## Starter Template Evaluation

### Primary Technology Domain

Python CLI/SDK tool — no web framework, frontend, or routing layer. Project scaffolding is hand-crafted; the structure itself is a teaching artifact (NFR16: forkable by modifying one file).

### Starter Options Considered

| Option | Assessment |
|---|---|
| Community starter (`labeveryday/strands-agents-template`) | Reference only — patterns owned by demo, not inherited |
| AWS CDK (Python) | Over-engineered for a simple demo; adds CDK learning curve |
| AWS SAM | Wrong abstraction — not a serverless function architecture |
| AgentCore CLI (`aws/bedrock-agentcore-sdk-python`) | ✅ Selected — purpose-built, single-command deploy |
| boto3 direct API scripting | ✅ Fallback — transparent, zero extra dependencies |

### Selected Approach: Hand-Crafted Minimal Python + AgentCore CLI

**Rationale:** The project structure IS the product. A scaffold generator would obscure the intentional simplicity. AgentCore CLI is the canonical deployment path — it satisfies FR20 (no console steps) with minimal code and maximum clarity.

**Initialization:** No CLI command. First implementation story creates the project structure directly.

**Pinned Dependencies (`requirements.txt`):**

```
strands-agents==1.26.0
strands-agents-tools
python-dotenv>=1.0.0
boto3>=1.34.0
```

**Gemini fallback extra (documented in README, optional install):**

```
pip install strands-agents[gemini]
```

**Recommended Project Structure:**

```
strands-agents-demo/
├── agent.py                  # < 150 lines — agent definition + @tool + main loop
├── requirements.txt          # pinned dependencies
├── .env.example              # MODEL_ID, AWS_REGION, GOOGLE_API_KEY (Gemini optional)
├── deploy/
│   └── deploy.py             # AgentCore deployment script (AgentCore CLI / boto3)
├── .vscode/
│   ├── launch.json           # F5 debug configuration
│   └── extensions.json       # Recommended VS Code extensions
└── README.md                 # Comprehensive — FR26–FR29
```

**Architectural Decisions Established:**

- **Language & Runtime:** Python 3.11+ (above SDK minimum of 3.10; aligns with PRD requirement)
- **Dependency Management:** `requirements.txt` + `venv` — no Poetry or pipenv; maximum accessibility for new developers
- **Deployment Tooling:** AgentCore CLI (`agentcore configure` / `agentcore deploy`) with boto3 scripting fallback in `deploy/deploy.py`
- **Configuration:** `python-dotenv` loads `.env`; `os.environ` used directly in code — no config file layer
- **IaC Decision Resolved:** AgentCore CLI satisfies FR20/FR22 and NFR11 (idempotent) with the simplest possible script
- **Code Organization:** `agent.py` stays lean and delegates model construction; `model_adapters.py` owns local adapter selection and capabilities; `deploy/app.py` owns deployed runtime adapter behavior; `deploy/` remains isolated for infrastructure concerns
- **Testing Infrastructure:** No automated tests at MVP — agent logic is intentionally trivial; acceptance testing is manual run + AgentCore console verification
- **Development Experience:** VS Code F5 via `.vscode/launch.json`; hot reload not applicable for CLI tool

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Model provider switching pattern — `MODEL_PROVIDER` + `MODEL_ID` env vars
- CLI interaction mode — interactive REPL loop

**Important Decisions (Shape Architecture):**
- IAM permissions scope — least-privilege service role
- Error handling strategy — LLM-native for input; minimal try/except for tools
- Observability approach — AgentCore built-in only

**Deferred Decisions (Post-MVP):**
- CI/CD pipeline — Phase 2
- Multi-turn memory/state — Phase 2

### Model Provider Abstraction

**Decision:** Environment-variable-driven provider and model selection remains, but provider choice is routed through adapters behind a `Model` interface with explicit capability metadata rather than direct vendor branching in app logic.

```
# Amazon Bedrock (primary MVP path)
MODEL_PROVIDER=bedrock
MODEL_ID=us.amazon.nova-micro-v1:0
AWS_REGION=us-east-1

# Initial local Gemini adapter path
MODEL_PROVIDER=gemini
MODEL_ID=gemini-2.0-flash
GOOGLE_API_KEY=your-key-here
```

**Rationale:** Explicit `MODEL_PROVIDER` and `MODEL_ID` variables remain self-documenting, but the implementation now needs a stable abstraction boundary that can support Bedrock-first deployment, local adapter flexibility, and staged expansion toward Gemma, Moonshot AI, Llama, Qwen, and DeepSeek. Model switching remains configuration-driven only when the selected model/runtime combination is supported by the configured adapter path.

**Agent code pattern:**
```python
adapter = create_local_model_adapter(os.environ["MODEL_PROVIDER"], os.environ)
model = adapter.build()
agent = Agent(model=model, tools=[get_today_date], ...)
```

**Runtime architecture pattern:**
- local path uses Strands-backed model adapters
- deployed AgentCore path uses a runtime adapter contract
- provider/model differences are normalized behind adapter boundaries
- capability checks determine whether a given model/runtime combination is supported

### CLI Interaction Mode

**Decision:** Interactive REPL loop

```python
while True:
    user_input = input("You: ")
    if user_input.lower() in ("exit", "quit"):
        break
    response = agent(user_input)
    print(f"Agent: {response}")
```

**Rationale:** Matches the conversational agent framing in PRD user journeys (Jamie types "I was born on 14th March 1990", agent responds naturally). Strands `Agent()` handles this natively. Single-shot mode would undercut the "conversational agent" positioning.

### Authentication & Security

**Local development:** AWS credentials via `~/.aws/credentials` or `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` env vars. No credentials in code.

**AgentCore deployment:** Deployment script provisions a least-privilege IAM service role scoped to:
- `bedrock:InvokeModel` on the specific model ARN
- `bedrock-agentcore:*` on the specific agent resource

**API keys:** `GOOGLE_API_KEY` in `.env` (gitignored). `.env.example` documents the variable with no real value. README includes explicit credential warning (NFR7).

### Error Handling Strategy

| Error Surface | Strategy | Code Location |
|---|---|---|
| Invalid/ambiguous date input | LLM handles naturally — no custom code | None (model capability) |
| Ambiguous date format | Agent asks clarifying question (FR3) | System prompt instruction |
| Tool failure (`get_today_date`) | try/except returns error string; unreachable in practice | `agent.py` tool definition |
| Deployment errors | README troubleshooting section | Documentation only |

**Principle:** Minimum defensive code in `agent.py`. The LLM is the primary error handler for conversational errors. Python stdlib reliability handles tool errors. This keeps the file under 150 lines (NFR12).

### Observability & Monitoring

**Decision:** Zero custom logging code — AgentCore built-in observability only.

**Rationale:** This is the core demo value proposition (FR24, FR25). AgentCore automatically captures tool call traces, inputs/outputs, and latency for every invocation. The "aha moment" for Morgan (Journey 4) is precisely that zero logging code was written. Adding custom `logging.basicConfig` calls would undercut this narrative.

**What AgentCore provides automatically:** Tool call traces with input/output, invocation latency, agent session history, error traces.

### Infrastructure & Deployment

**Deployment script (`deploy/deploy.py`) responsibilities:**
1. Check for existing AgentCore agent (idempotency — NFR11)
2. Create/update IAM service role with least-privilege policy
3. Register agent with AgentCore via CLI or boto3
4. Output the agent endpoint URL for verification (FR21)
5. Print troubleshooting hints on common errors (FR23)

**Idempotency approach:** Script checks if agent with the configured name already exists before creating. Update if exists, create if not.

### Decision Impact Analysis

**Implementation Sequence:**
1. `agent.py` — agent definition, `@tool`, REPL loop, model provider branching
2. `requirements.txt` + `.env.example` — dependency pins and variable documentation
3. `.vscode/` — F5 debug config
4. `deploy/deploy.py` — AgentCore deployment script with IAM provisioning
5. `README.md` — comprehensive documentation (last, written against working code)

**Cross-Component Dependencies:**
- `agent.py` depends on `MODEL_PROVIDER` and `MODEL_ID` env vars being set → `.env.example` must document these
- `deploy/deploy.py` depends on `AWS_REGION` env var → same `.env.example`
- README troubleshooting depends on deployment script error surfaces → write after `deploy.py`

## Implementation Patterns & Consistency Rules

### Critical Conflict Points: 8 areas addressed

### Naming Patterns

**Python Conventions (PEP 8 — NFR13):**
- Functions and variables: `snake_case` (e.g. `get_today_date`, `user_input`)
- Constants: `UPPER_SNAKE_CASE` (e.g. `MODEL_ID`, `AWS_REGION`)
- Module files: `snake_case.py` (e.g. `agent.py`, `deploy.py`)
- No classes required at MVP — agent and tools are module-level functions

**Environment Variable Names:**
- All caps, underscore-separated: `MODEL_PROVIDER`, `MODEL_ID`, `AWS_REGION`, `GOOGLE_API_KEY`
- Every variable in `.env.example` with a description comment above it

### Structure Patterns

**Tool Definition Location:**
All tools defined in `agent.py` at MVP — one file, all logic visible together.
If tools exceed 3 or the file approaches 150 lines, extract to `tools.py`.
Never split before that threshold — premature extraction obscures the demo's simplicity.

**File Organization Rules:**

```
agent.py        → tool definitions, agent creation, REPL loop, main guard
deploy/
  deploy.py     → all deployment logic; no agent logic here
.env.example    → all env vars documented; grouped by: LLM config, AWS config, optional
```

### Format Patterns

**Tool Return Format — String only:**
Strands tools must return a string (the model receives it as a string in context).

```python
# CORRECT
@tool
def get_today_date() -> str:
    """Returns today's date in ISO 8601 format (YYYY-MM-DD)."""
    return datetime.date.today().isoformat()

# WRONG — do not return dict/object
@tool
def get_today_date() -> dict:
    return {"date": datetime.date.today().isoformat()}
```

**Tool Error Return — String, not exception:**
Tools should return a descriptive error string rather than raising exceptions,
so the model can incorporate the error into its response.

```python
@tool
def get_today_date() -> str:
    try:
        return datetime.date.today().isoformat()
    except Exception as e:
        return f"Error retrieving today's date: {str(e)}"
```

**Tool Docstrings — Required:**
Strands uses the docstring as the tool's description for the model. Every `@tool`
function must have a clear, imperative docstring explaining what it returns.

```python
# CORRECT — model sees this description
def get_today_date() -> str:
    """Returns today's date in ISO 8601 format (YYYY-MM-DD)."""

# WRONG — missing or vague docstring
def get_today_date() -> str:
    """Gets date."""
```

**System Prompt — Inline constant in agent.py:**

```python
SYSTEM_PROMPT = """You are a helpful assistant that calculates a person's age in days.
When given a date of birth, use the get_today_date tool to retrieve today's date,
then calculate and return the age in days in a friendly, conversational response.
If the date format is ambiguous, ask for clarification before calculating."""
```

Named constant at the top of the file. Not a separate file. Not a multi-line f-string.

### Communication Patterns

**Environment Variable Access Pattern:**
Load `.env` at module level once; access via `os.environ` with clear `KeyError` on missing vars.

```python
from dotenv import load_dotenv
load_dotenv()  # Load .env at startup — must be before any os.environ access

# Access — let KeyError surface naturally (fail fast, clear error)
model_provider = os.environ["MODEL_PROVIDER"]
```

Do not use `os.environ.get()` with silent defaults for required vars — fail loudly on misconfiguration.
Use `os.environ.get()` only for genuinely optional vars.

**REPL Loop Pattern:**

```python
if __name__ == "__main__":
    print("Age-in-Days Agent (type 'exit' to quit)")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ("exit", "quit", "q"):
            break
        if not user_input:
            continue
        response = agent(user_input)
        print(f"\nAgent: {response}")
```

### Process Patterns

**Inline Comment Standard (FR28):**
Comment the *why*, not the *what*. Required for non-obvious blocks.

```python
# load_dotenv() must be called before any os.environ access;
# it populates the environment from the .env file silently if not found
load_dotenv()

# Strands BedrockModel uses the default boto3 credential chain —
# no explicit credential passing needed
model = BedrockModel(model_id=os.environ["MODEL_ID"], region=os.environ["AWS_REGION"])
```

**Code Formatter:** `black` (PEP 8 — NFR13). Run before committing. No config file needed — black defaults are correct.

### Enforcement Guidelines

**All implementation agents MUST:**
- Keep `agent.py` under 150 lines (NFR12) — if approaching limit, flag for architect review before adding more
- Never hardcode credentials or model IDs (NFR3) — `os.environ` only
- Return strings from `@tool` functions, not dicts or exceptions
- Include docstrings on every `@tool` function (Strands uses them as model context)
- Comment every non-obvious block with *why*, not *what* (FR28)
- Run `black agent.py` and `black deploy/deploy.py` before completing a story

**Anti-Patterns:**

```python
# ANTI-PATTERN: hardcoded credentials
model = BedrockModel(model_id="us.amazon.nova-micro-v1:0",
                     region="us-east-1")  # ❌ hardcoded

# ANTI-PATTERN: silent default for required config
model_provider = os.environ.get("MODEL_PROVIDER", "bedrock")  # ❌ hides misconfiguration

# ANTI-PATTERN: tool returns non-string
@tool
def get_today_date():
    return {"date": "2026-03-16", "epoch": 1742083200}  # ❌ model receives dict repr

# ANTI-PATTERN: vague tool docstring
def get_today_date():
    """Date tool."""  # ❌ model gets no useful description
```

## Project Structure & Boundaries

### Requirements → Files Mapping

| FR Category | Mapped To |
|---|---|
| FR1–FR5 (Agent Conversation) | `agent.py` — `SYSTEM_PROMPT` constant, model selection |
| FR6–FR8 (Date Calculation) | `agent.py` — `get_today_date()` tool |
| FR9–FR11 (Tool Framework) | `agent.py` — `@tool` decorator pattern |
| FR12–FR15 (Configuration Mgmt) | `.env.example` + `agent.py` `load_dotenv()` + `deploy/deploy.py` |
| FR16–FR19 (Local Development) | `README.md`, `requirements.txt`, `.vscode/` |
| FR20–FR23 (AgentCore Deployment) | `deploy/deploy.py`, `README.md` troubleshooting section |
| FR24–FR25 (Observability) | Zero code — AgentCore built-in |
| FR26–FR29 (Documentation) | `README.md`, inline comments throughout all files |

### Complete Project Directory Structure

```
strands-agents-demo/
│
├── agent.py                    # Core agent: @tool, model config, Agent(), REPL loop
│                               # < 150 lines (NFR12); single-file teaching artifact
│
├── requirements.txt            # Pinned: strands-agents==1.26.0, strands-agents-tools,
│                               # python-dotenv>=1.0.0, boto3>=1.34.0
│
├── .env.example                # Every env var documented with description + example
│                               # Groups: LLM Config, AWS Config, Optional (Gemini)
│
├── .gitignore                  # Excludes .env, __pycache__, .venv, *.pyc (already exists)
│
├── README.md                   # ToC, prerequisites, local setup, AgentCore deployment,
│                               # project structure, how it works, troubleshooting,
│                               # contributing (FR27)
│
├── deploy/
│   └── deploy.py               # AgentCore deployment: IAM role, agent registration,
│                               # idempotency check, endpoint output, error hints
│
└── .vscode/
    ├── launch.json             # F5 debug: runs agent.py with .env loaded (FR18)
    └── extensions.json         # Recommended: Python, Pylance, dotenv
```

**Note:** `_bmad/` and `_bmad-output/` directories already exist in the repo for BMAD framework and planning artifacts. They are not part of the agent implementation.

### Architectural Boundaries

**Agent Boundary (`agent.py`):**
- Owns: tool definitions, model instantiation, agent creation, REPL loop
- Reads: `MODEL_PROVIDER`, `MODEL_ID`, `AWS_REGION`, `GOOGLE_API_KEY` from env
- Depends on: `strands-agents`, `python-dotenv`, `boto3` (via BedrockModel)
- Does NOT contain: deployment logic, IAM provisioning, AgentCore registration

**Deployment Boundary (`deploy/deploy.py`):**
- Owns: AgentCore registration, IAM service role creation, idempotency check, endpoint output
- Reads: `AWS_REGION`, `AGENT_NAME` from env
- Depends on: `boto3`, AgentCore CLI or `bedrock-agentcore-sdk`
- Does NOT contain: agent logic, tool definitions, conversation handling

**Configuration Boundary (`.env` / `.env.example`):**
- Single source of truth for all runtime configuration
- Both `agent.py` and `deploy/deploy.py` read independently from env — no shared config module
- `.env.example` is the developer contract (FR15)

### Integration Points

**Internal Data Flow:**

```
User input (terminal)
    → REPL loop (agent.py)
    → Strands Agent() — sends to LLM
    → LLM decides to call get_today_date tool
    → Tool returns ISO date string (e.g. "2026-03-16")
    → LLM calculates days, composes response
    → Response printed to terminal
```

**External Integrations:**

| Integration | Library | Config |
|---|---|---|
| Amazon Bedrock (primary LLM) | `strands-agents` `BedrockModel` | `MODEL_ID`, `AWS_REGION`, AWS credentials |
| Google Gemini (fallback LLM) | `strands-agents[gemini]` `GeminiModel` | `MODEL_ID`, `GOOGLE_API_KEY` |
| AWS AgentCore (deployment) | `bedrock-agentcore-sdk` or boto3 | `AWS_REGION`, AWS credentials |
| VS Code debugger | `.vscode/launch.json` | No additional config |

**`.env.example` Complete Variable Set:**

```bash
# --- LLM Configuration ---
# Provider: "bedrock" (Amazon Bedrock) or "gemini" (Google Gemini)
MODEL_PROVIDER=bedrock

# Model ID — Bedrock: "us.amazon.nova-micro-v1:0"
#           — Gemini: "gemini-2.0-flash"
MODEL_ID=us.amazon.nova-micro-v1:0

# --- AWS Configuration (required for Bedrock and AgentCore deployment) ---
AWS_REGION=us-east-1

# --- AgentCore Deployment ---
# Name for your agent in AgentCore (used for idempotency check)
AGENT_NAME=age-in-days-demo

# --- Optional: Google Gemini (only if MODEL_PROVIDER=gemini) ---
# GOOGLE_API_KEY=your-gemini-api-key-here
```

### Development Workflow Integration

**Local run:** `python agent.py` — loads `.env`, starts interactive REPL

**VS Code F5:** `launch.json` runs `agent.py` with debugger attached; `.env` loaded via `envFile` key

**Deployment:** `python deploy/deploy.py` — idempotency check → IAM role → AgentCore registration → prints endpoint URL

**Verification:** Invoke deployed endpoint via AgentCore console or CLI (FR21)

## Architecture Validation Results

### Coherence Validation ✅

All technology decisions are compatible with each other and with the Strands SDK. No contradictory choices identified. Implementation patterns are aligned with both PEP 8 and the Strands SDK public API. Project structure enables all defined patterns without conflict.

### Requirements Coverage Validation ✅

**Functional Requirements:** 29/29 covered

| FR Range | Coverage | Location |
|---|---|---|
| FR1–FR5 (Agent Conversation) | ✅ | `agent.py` SYSTEM_PROMPT + Strands Agent() |
| FR6–FR8 (Date Calculation) | ✅ | `agent.py` `get_today_date()` @tool |
| FR9–FR11 (Tool Framework) | ✅ | `agent.py` @tool decorator; FR11 = AgentCore built-in |
| FR12–FR15 (Configuration) | ✅ | `MODEL_PROVIDER`/`MODEL_ID` pattern + `.env.example` |
| FR16–FR19 (Local Development) | ✅ | `requirements.txt`, `README.md`, `.vscode/` |
| FR20–FR23 (AgentCore Deployment) | ✅ | `deploy/deploy.py` + README troubleshooting |
| FR24–FR25 (Observability) | ✅ | Zero code — AgentCore managed observability |
| FR26–FR29 (Documentation) | ✅ | `README.md` + inline comments throughout |

**Non-Functional Requirements:** 16/16 covered

| NFR Group | Coverage |
|---|---|
| NFR1–2 (Performance) | ✅ AgentCore-managed; minimal deps for fast startup |
| NFR3–7 (Security) | ✅ `.env` pattern, least-privilege IAM, README credential warning |
| NFR8–11 (Integration) | ✅ Both model paths defined; idempotency in deploy.py |
| NFR12–16 (Code Quality) | ✅ Pattern rules enforce <150 lines, PEP 8, single-file fork |

### Implementation Readiness ✅

All critical decisions documented with verified versions. Implementation patterns include concrete examples and anti-patterns. Project structure is specific — no placeholder directories. Component boundaries clearly defined with explicit "does NOT contain" rules.

### Gap Analysis

**Important (resolve before implementation):**
- `bedrock-agentcore` PyPI package needed by `deploy/deploy.py` — add to `requirements.txt` with `# deploy dependencies` comment marker

**Minor (resolve during implementation):**
- `black` formatter: document `pip install black` in README contributing section
- FR3/FR5 boundary: resolve explicitly in SYSTEM_PROMPT constant wording (ask for clarification on ambiguous formats; return error message for unparseable inputs)

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed (Low — intentional)
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped (4 identified)

**✅ Architectural Decisions**
- [x] IaC technology resolved (AgentCore CLI)
- [x] Model provider switching pattern defined
- [x] CLI interaction mode defined (REPL)
- [x] Error handling strategy defined
- [x] Observability approach defined (zero custom code)
- [x] All versions verified via web search

**✅ Implementation Patterns**
- [x] Naming conventions: `snake_case`, `UPPER_SNAKE_CASE`
- [x] Tool return format: string-only rule with examples and anti-patterns
- [x] Tool docstring requirement: mandatory
- [x] System prompt: inline constant pattern
- [x] Env var access: fail-fast on missing required vars
- [x] REPL loop: standard pattern defined
- [x] Comment standard: why, not what
- [x] Code formatter: `black`

**✅ Project Structure**
- [x] Complete directory tree defined
- [x] All files and responsibilities specified
- [x] Component boundaries defined (agent / deploy / config)
- [x] Integration points mapped
- [x] Data flow documented
- [x] `.env.example` complete variable set defined

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High

**Key Strengths:**
- Zero ambiguity in core architectural choices — every decision has a clear rationale tied to specific FR/NFR
- "Zero custom observability" is architecturally documented — prevents developers from adding logging that undercuts the demo narrative
- Tool return format rule with anti-patterns prevents the most common Strands SDK mistake
- Fail-fast env var pattern prevents silent misconfiguration bugs
- Single-file structure makes the architecture inherently verifiable against NFR12

**Areas for Future Enhancement (Phase 2):**
- Multi-turn memory using AgentCore managed memory
- CI/CD pipeline for automated deployment
- Additional tools (age in weeks, months, years)
- `tests/` directory with acceptance tests

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented
- Apply implementation patterns consistently — especially tool return format and env var access rules
- Keep `agent.py` under 150 lines; flag before adding beyond that
- Refer to this document for all architectural questions during implementation

**First Implementation Story:** Create the project scaffold — `agent.py` stub, `requirements.txt`, `.env.example`, `.vscode/` config files, `deploy/deploy.py` stub.
