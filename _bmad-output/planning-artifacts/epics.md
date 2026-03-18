---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
---

# strands-agents-demo - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for strands-agents-demo, decomposing the requirements from the PRD and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: A user can provide their date of birth in natural language and receive their age in days
FR2: A user can provide a date of birth in multiple formats (natural language, ISO 8601, DD/MM/YYYY) and the agent correctly interprets it
FR3: The agent asks a clarifying question when date format is ambiguous rather than returning an incorrect result
FR4: The agent provides a friendly, conversational response that includes the age in days
FR5: The agent gracefully handles invalid or unparseable date inputs with a helpful error message
FR6: The agent retrieves the current date using a dedicated date tool
FR7: The agent calculates the difference in days between today's date and a given date of birth
FR8: The agent returns the age as a whole number of days
FR9: A developer can define a custom tool using the Strands `@tool` decorator
FR10: The agent invokes a registered tool during a conversation turn and uses the result in its response
FR11: Tool invocations and results are captured and visible in AgentCore observability
FR12: A developer configures the LLM provider (Claude via Bedrock or Gemini) via environment variables without modifying code
FR13: A developer configures the AWS region via environment variable
FR14: A developer configures all required API keys and credentials via environment variables
FR15: The project provides a `.env.example` documenting every required variable with description and example value
FR16: A developer sets up the local environment by following the README without undocumented steps
FR17: A developer runs the agent locally with a single command after environment setup
FR18: A developer runs and debugs the agent in VS Code using F5 with a provided launch configuration
FR19: A developer installs all dependencies via `pip install -r requirements.txt` in a Python virtual environment
FR20: A developer deploys the agent to AWS AgentCore by running a provided script — no manual console steps required
FR21: A developer verifies the deployed agent by invoking it via the AgentCore endpoint
FR22: The deployment script provisions all required infrastructure in `us-east-1`
FR23: A developer follows the README troubleshooting section to diagnose and resolve common deployment errors (IAM permissions, missing env vars, wrong region)
FR24: A developer views the agent's tool call traces in the AgentCore console after interacting with the deployed agent
FR25: A developer sees inputs and outputs of each tool invocation in AgentCore without writing custom logging code
FR26: A developer new to Strands and AgentCore understands the project purpose, architecture, and setup from the README alone
FR27: The README includes table of contents, prerequisites, local setup, AgentCore deployment, project structure, how it works, troubleshooting, and contributing
FR28: Every non-obvious code block in the agent and deployment scripts includes an inline comment explaining its purpose
FR29: The project structure is self-explanatory — file and folder names reflect their purpose without documentation to navigate

### NonFunctional Requirements

NFR1: The deployed agent responds to a date of birth query within 5 seconds under normal load
NFR2: Local agent startup completes within 10 seconds of invoking the run command
NFR3: AWS credentials and API keys are never hardcoded — environment variables only
NFR4: `.env` is excluded from version control; `.env.example` contains no real credentials
NFR5: No user input is logged in plaintext outside of AgentCore's managed observability context
NFR6: The deployment script requests only the minimum IAM permissions required for AgentCore operation
NFR7: README includes an explicit warning against committing credentials to version control
NFR8: The agent functions correctly with Claude 3 Sonnet or Haiku via Amazon Bedrock
NFR9: The agent functions correctly with Gemini free tier as the documented fallback
NFR10: Model switching requires only an environment variable change — no code modification
NFR11: AgentCore deployment is idempotent — re-running the script does not create duplicate resources or errors
NFR12: Agent code is contained in a single readable file of under 150 lines
NFR13: All files follow PEP 8
NFR14: No external dependencies beyond the Strands SDK, LLM client libraries, and Python standard library
NFR15: A developer unfamiliar with the codebase understands each file's purpose within 5 minutes of reading it
NFR16: The project can be forked and adapted to a different use case by modifying only the agent logic file and environment variables

### Additional Requirements

- Python 3.11+ required (Strands SDK minimum is 3.10; demo pins to 3.11+ for clarity)
- Pinned dependencies: `strands-agents==1.26.0`, `strands-agents-tools`, `python-dotenv>=1.0.0`, `boto3>=1.34.0`, `bedrock-agentcore` (deploy dependency, comment-marked in requirements.txt)
- Gemini fallback requires optional extra: `pip install strands-agents[gemini]` (documented in README)
- IaC technology: AgentCore CLI (`agentcore configure` / `agentcore deploy`) with boto3 fallback in `deploy/deploy.py`
- All `@tool` functions must return a string (not dict/object); tool errors returned as string, not raised as exceptions
- All `@tool` functions must have a clear imperative docstring (Strands uses it as the model's tool description)
- System prompt defined as inline constant `SYSTEM_PROMPT` at top of `agent.py`
- Required env vars accessed via `os.environ[]` (fail-fast); optional vars via `os.environ.get()`
- `load_dotenv()` called at module level before any `os.environ` access
- `deploy/deploy.py` must: check for existing agent (idempotency), create least-privilege IAM service role, register agent with AgentCore, output endpoint URL, print troubleshooting hints on common errors
- Code formatter: `black` — run before completing any story
- No automated tests at MVP — acceptance testing is manual run + AgentCore console verification
- `.env.example` must group variables by: LLM Config, AWS Config, Optional (Gemini)
- `.vscode/launch.json` must use `envFile` key to load `.env` for F5 debugging
- Implementation sequence: agent.py → requirements.txt + .env.example → .vscode/ → deploy/deploy.py → README.md (last, written against working code)

### UX Design Requirements

Not applicable — this is a CLI/API developer tool with no visual interface. Developer experience requirements are fully captured in the FRs and NFRs above (FR16–FR29, NFR12–NFR16).

### FR Coverage Map

FR1: Epic 1 — Natural language date input, conversational agent response
FR2: Epic 1 — Multi-format date parsing (natural language, ISO 8601, DD/MM/YYYY)
FR3: Epic 1 — Ambiguous format clarification (via SYSTEM_PROMPT instruction)
FR4: Epic 1 — Friendly, conversational response including age in days
FR5: Epic 1 — Invalid/unparseable input handled gracefully (via SYSTEM_PROMPT + LLM)
FR6: Epic 1 — `get_today_date()` @tool retrieves current date
FR7: Epic 1 — LLM calculates days difference using tool result
FR8: Epic 1 — Agent returns age as whole number of days
FR9: Epic 1 — @tool decorator pattern demonstrated
FR10: Epic 1 — Tool invoked during conversation turn, result used in response
FR11: Epic 2 — AgentCore captures tool invocations and results automatically (zero custom code)
FR12: Epic 1 — MODEL_PROVIDER + MODEL_ID env var pattern for LLM switching
FR13: Epic 1 — AWS_REGION env var
FR14: Epic 1 — All API keys and credentials via env vars (.env + load_dotenv)
FR15: Epic 1 — .env.example with every variable documented (description + example)
FR16: Epic 1 — README setup instructions with zero undocumented steps
FR17: Epic 1 — Single-command run: `python agent.py`
FR18: Epic 1 — .vscode/launch.json for F5 debugging with .env loaded
FR19: Epic 1 — `pip install -r requirements.txt` in venv
FR20: Epic 2 — `deploy/deploy.py` one-command AgentCore deployment (no console steps)
FR21: Epic 2 — Deployed endpoint verification after deployment
FR22: Epic 2 — All infrastructure provisioned in us-east-1
FR23: Epic 2 — README troubleshooting section (IAM, env vars, wrong region)
FR24: Epic 2 — AgentCore console shows tool call traces
FR25: Epic 2 — Tool I/O visible in AgentCore without custom logging code
FR26: Epic 3 — README: complete project understanding for developers new to Strands/AgentCore
FR27: Epic 3 — README sections: ToC, prerequisites, setup, deployment, structure, how it works, troubleshooting, contributing
FR28: Epic 3 — Inline comments throughout all files explaining the why
FR29: Epic 3 — Self-explanatory project structure and file/folder names

## Epic List

### Epic 1: Local Agent — Working Age-in-Days Calculator

A developer can clone the repo, install dependencies, configure the environment, and run a fully functional age-in-days agent locally — complete with a custom `get_today_date` Strands tool, natural language date input handling, multi-provider model configuration (Bedrock primary, Gemini fallback), and VS Code F5 debugging.

**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8, FR9, FR10, FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19

---

### Epic 2: AgentCore Production Deployment & Observability

A developer can deploy the agent to AWS AgentCore with a single script command, verify it responds correctly via the deployed endpoint, and observe every tool call trace and invocation detail in the AgentCore console — with zero custom logging code written.

**FRs covered:** FR11, FR20, FR21, FR22, FR23, FR24, FR25

---

### Epic 3: Developer Documentation & Project Finalization

A developer new to Strands and AgentCore can understand the complete project — purpose, architecture, local setup, deployment, and how it works — from the README and inline code documentation alone, and can fork and adapt it to a new use case by changing one file.

**FRs covered:** FR26, FR27, FR28, FR29

---

## Epic 1: Local Agent — Working Age-in-Days Calculator

A developer can clone the repo, install dependencies, configure the environment, and run a fully functional age-in-days agent locally — complete with a custom `get_today_date` Strands tool, natural language date input handling, multi-provider model configuration (Bedrock primary, Gemini fallback), and VS Code F5 debugging.

### Story 1.1: Project Scaffold & Dependency Setup

As a developer,
I want the project scaffold created with all required files (`requirements.txt`, `.env.example`, `.gitignore`, and an `agent.py` stub),
So that I can install dependencies and begin developing without any undocumented manual steps.

**Acceptance Criteria:**

**Given** I have cloned the repository and Python 3.11+ is installed
**When** I create a virtual environment with `python -m venv venv` and activate it
**Then** I can run `pip install -r requirements.txt` without errors

**Given** I examine `requirements.txt`
**When** I read it
**Then** it contains pinned dependencies: `strands-agents==1.26.0`, `strands-agents-tools`, `python-dotenv>=1.0.0`, `boto3>=1.34.0`, with `bedrock-agentcore` marked with a `# deploy dependency` comment

**Given** I examine `.env.example`
**When** I read it
**Then** it contains all required variables (MODEL_PROVIDER, MODEL_ID, AWS_REGION, AGENT_NAME) with description comments above each, grouped by: LLM Config, AWS Config, and Optional (Gemini) — and contains no real credentials

**Given** `.env.example` exists
**When** I copy it to `.env` and fill in my credentials
**Then** `agent.py` can load the environment via `load_dotenv()` without errors

**Given** I examine `.gitignore`
**When** I read it
**Then** `.env`, `__pycache__/`, `.venv/`, and `*.pyc` are excluded from version control

### Story 1.2: Working Age-in-Days Agent

As a developer (and as an end user),
I want a fully functional agent in `agent.py` that accepts a date of birth in natural language or structured format and returns the age in days,
So that I can run `python agent.py`, type my date of birth, and receive a correct, friendly response — demonstrating the complete Strands `@tool` and `Agent()` pattern.

**Acceptance Criteria:**

**Given** `agent.py` is implemented with `get_today_date` @tool, SYSTEM_PROMPT constant, model config, and REPL loop
**When** I run `python agent.py` with MODEL_PROVIDER=bedrock and valid AWS credentials
**Then** the agent starts within 10 seconds and displays an interactive prompt

**Given** the agent is running
**When** I type "I was born on 14th March 1990"
**Then** the agent invokes `get_today_date`, calculates the difference, and responds with the correct age in days in a friendly, conversational tone

**Given** the agent is running
**When** I type a date in DD/MM/YYYY format (e.g. "14/03/1990")
**Then** the agent correctly interprets the date and returns the age in days

**Given** the agent is running
**When** I type an ambiguous date (e.g. "3/4/1990" — could be March 4 or April 3)
**Then** the agent asks a clarifying question rather than returning a potentially incorrect result

**Given** the agent is running
**When** I type an unparseable or clearly invalid input (e.g. "I was born on the moon")
**Then** the agent returns a helpful error message — it does not crash or return a wrong calculation

**Given** I examine `agent.py`
**When** I read the file
**Then** it is under 150 lines, all functions use `snake_case`, `get_today_date` returns a `str` (not dict or exception), and `get_today_date` has a clear imperative docstring

**Given** I examine the env var access pattern in `agent.py`
**When** I read it
**Then** `load_dotenv()` is called at module level before any `os.environ` access, required vars use `os.environ[]` (fail-fast), and `SYSTEM_PROMPT` is defined as an inline constant at the top of the file

**Given** MODEL_PROVIDER=gemini is set in `.env` with a valid GOOGLE_API_KEY
**When** I run `python agent.py`
**Then** the agent starts and responds to date queries using the Gemini model — no code modification required

**Given** the agent is running
**When** I type "exit", "quit", or "q"
**Then** the REPL loop exits cleanly

### Story 1.3: VS Code Debug Configuration

As a developer,
I want to press F5 in VS Code to launch `agent.py` with the debugger attached and `.env` automatically loaded,
So that I can set breakpoints and step through the agent code without any manual configuration.

**Acceptance Criteria:**

**Given** VS Code is open with the project folder
**When** I press F5
**Then** `agent.py` launches with the Python debugger attached

**Given** `.vscode/launch.json` exists with an `envFile` key pointing to `${workspaceFolder}/.env`
**When** I press F5
**Then** environment variables from `.env` are loaded automatically — no manual `export` required

**Given** I set a breakpoint inside `get_today_date()`
**When** I press F5 and type a date of birth at the agent prompt
**Then** execution pauses at the breakpoint and I can inspect local variables

**Given** `.vscode/extensions.json` exists
**When** VS Code opens the project
**Then** it recommends Python and Pylance extensions (and optionally the dotenv extension)

---

## Epic 2: AgentCore Production Deployment & Observability

A developer can deploy the agent to AWS AgentCore with a single script command, verify it responds correctly via the deployed endpoint, and observe every tool call trace and invocation detail in the AgentCore console — with zero custom logging code written.

### Story 2.1: AgentCore Deployment Script

As a developer,
I want to run `python deploy/deploy.py` to provision all required AWS infrastructure and deploy the agent to AgentCore in `us-east-1`,
So that my agent is running in production without any manual AWS console steps.

**Acceptance Criteria:**

**Given** I have valid AWS credentials and `AWS_REGION=us-east-1` and `AGENT_NAME` set in `.env`
**When** I run `python deploy/deploy.py`
**Then** the script completes without errors, provisions the infrastructure, and prints the deployed AgentCore endpoint URL

**Given** the deployment script runs
**When** it executes
**Then** it creates a least-privilege IAM service role scoped only to `bedrock:InvokeModel` on the specific model ARN and `bedrock-agentcore:*` on the specific agent resource — no over-provisioned permissions

**Given** the agent has already been deployed once
**When** I run `python deploy/deploy.py` again
**Then** the script detects the existing agent, updates it rather than creating a duplicate, and exits cleanly — idempotent behaviour

**Given** `deploy/deploy.py` executes
**When** it encounters a common error (missing IAM permission, wrong region, missing env var)
**Then** it prints a descriptive troubleshooting hint specific to that error — not a raw AWS exception traceback

**Given** `deploy/deploy.py` completes successfully
**When** I read the console output
**Then** the deployed agent endpoint URL is clearly displayed and I can copy it for verification

**Given** I examine `deploy/deploy.py`
**When** I read it
**Then** all non-obvious blocks have inline comments explaining the *why*, it follows PEP 8, and `black deploy/deploy.py` produces no changes

### Story 2.2: Endpoint Verification & Observability Confirmation

As a developer,
I want to invoke the deployed AgentCore agent via its endpoint and then view the tool call traces in the AgentCore console,
So that I can verify the production deployment works and demonstrate that AgentCore provides full observability with zero custom logging code.

**Acceptance Criteria:**

**Given** the agent has been deployed successfully (Story 2.1 complete)
**When** I invoke the agent via the AgentCore endpoint (CLI or console) with a date of birth query
**Then** the agent responds with the correct age in days within 5 seconds

**Given** I have invoked the deployed agent at least once
**When** I open the AgentCore console and navigate to the agent's invocation history
**Then** I can see the `get_today_date` tool call traced — including its input and output

**Given** I examine the tool call trace in the AgentCore console
**When** I inspect the trace detail
**Then** I can see the exact string returned by `get_today_date` (e.g. "2026-03-16") and the agent's final response — without any custom logging code having been written

---

## Epic 3: Developer Documentation & Project Finalization

A developer new to Strands and AgentCore can understand the complete project — purpose, architecture, local setup, deployment, and how it works — from the README and inline code documentation alone, and can fork and adapt it to a new use case by changing one file.

### Story 3.1: Comprehensive README

As a developer new to Strands and AgentCore,
I want a README that guides me from zero to a running local agent and deployed AgentCore instance — covering all prerequisites, steps, and troubleshooting — without requiring any prior knowledge of Strands or AgentCore,
So that I can follow it alone and reach a working, observable production agent.

**Acceptance Criteria:**

**Given** a developer new to Strands and AgentCore opens the README
**When** they read it
**Then** they understand the project's purpose, architecture, and what Strands + AgentCore provides — within the first screen of content

**Given** the README exists
**When** I check its structure
**Then** it contains all of: table of contents, prerequisites (Python 3.11+, AWS account, Bedrock/Gemini access, AWS CLI), local setup (clone → venv → pip install → .env → run), AgentCore deployment, project structure, how it works (data flow diagram or description), troubleshooting, and contributing

**Given** the troubleshooting section exists
**When** I read it
**Then** it covers at minimum: missing IAM permissions for AgentCore, wrong AWS region, missing or misconfigured env vars, and model access not enabled in Bedrock

**Given** the README includes a credential warning
**When** I read the setup section
**Then** there is an explicit warning against committing `.env` or any credentials to version control

**Given** a developer follows the README local setup section step by step
**When** they complete all steps
**Then** they can run `python agent.py` and interact with the agent — with no additional steps required beyond what is documented

**Given** a developer follows the README AgentCore deployment section
**When** they complete all steps
**Then** they can run `python deploy/deploy.py` and have a working deployed agent — with no manual AWS console steps

### Story 3.2: Inline Code Documentation & Project Structure Finalization

As a developer reading the codebase for the first time,
I want every non-obvious code block to have an inline comment explaining *why* it exists, and the project structure to be self-explanatory from file and folder names alone,
So that I can understand the entire project within 5 minutes and confidently fork it to build my own agent.

**Acceptance Criteria:**

**Given** I read `agent.py`
**When** I encounter non-obvious blocks (e.g. `load_dotenv()` call, `os.environ[]` vs `os.environ.get()`, model provider branching, `@tool` docstring, REPL exit conditions)
**Then** each has an inline comment explaining *why* — not just restating what the code does

**Given** I read `deploy/deploy.py`
**When** I encounter non-obvious blocks (e.g. idempotency check, IAM policy construction, AgentCore registration call, error hint printing)
**Then** each has an inline comment explaining *why*

**Given** I look at the project root directory listing
**When** I read the file and folder names
**Then** I can immediately identify the purpose of each: `agent.py` (the agent), `deploy/` (deployment), `.env.example` (config template), `requirements.txt` (dependencies), `README.md` (documentation) — without needing to open them

**Given** I run `black agent.py` and `black deploy/deploy.py`
**When** black completes
**Then** it reports no changes — all files are PEP 8 compliant

**Given** a developer wants to fork this project for a different use case
**When** they modify only `agent.py` (changing the tool and SYSTEM_PROMPT) and update `.env`
**Then** the rest of the project (deployment script, VS Code config, requirements) works without modification
