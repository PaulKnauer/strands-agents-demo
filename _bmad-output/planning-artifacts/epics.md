---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
---

# strands-agents-demo - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for strands-agents-demo, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

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
FR12: A developer configures the model provider and model identifier via environment variables and adapter-based model selection without modifying application logic
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
NFR8: The agent functions correctly with Bedrock-backed model support for MVP
NFR9: Initial non-Bedrock local adapter support may be provided where documented
NFR10: Model switching requires configuration changes only when the selected model/runtime combination is supported by the configured adapter path
NFR11: AgentCore deployment is idempotent — re-running the script does not create duplicate resources or errors
NFR12: Agent code is contained in a single readable file of under 150 lines
NFR13: All files follow PEP 8
NFR14: No external dependencies beyond the Strands SDK, LLM client libraries, and Python standard library
NFR15: A developer unfamiliar with the codebase understands each file's purpose within 5 minutes of reading it
NFR16: The project can be forked and adapted to a different use case by modifying only the agent logic file and environment variables

### Additional Requirements

- Python 3.11+ required
- Local runtime uses `strands-agents==1.26.0`, `strands-agents-tools`, `python-dotenv>=1.0.0`, and `boto3>=1.34.0`
- `bedrock-agentcore` is required for deployment/runtime packaging and should be treated as a deploy dependency
- AgentCore runtime target is `PYTHON_3_12`
- Project context is greenfield; initial implementation should create the scaffold directly rather than clone a starter template
- Deployment target is AWS AgentCore in `us-east-1`
- IaC path is AgentCore CLI with boto3 fallback in `deploy/deploy.py`
- `agent.py` must stay lean and under 150 lines; model construction should delegate behind adapter boundaries
- `model_adapters.py` owns local adapter selection and capability metadata
- `deploy/app.py` owns the deployed runtime adapter contract and Bedrock Converse path
- Local and deployed runtimes must remain separate; do not collapse Strands local execution and deployed Bedrock runtime into one path
- `load_dotenv()` must run before any `os.environ` access in local and deploy entrypoints
- Required configuration uses fail-fast `os.environ[...]`; optional values may use `os.environ.get()`
- All `@tool` functions must return strings, not dicts or raised exceptions
- All `@tool` functions must have clear imperative docstrings because Strands uses them as tool descriptions
- `SYSTEM_PROMPT` must be an inline constant in `agent.py`
- `app.run(host="0.0.0.0")` in AgentCore runtime must remain unconditional
- Bedrock is the primary MVP inference and deployment-aligned control plane
- Initial local adapters support `bedrock` and `gemini`
- Planned staged expansion path includes Gemma, Moonshot AI, Llama, Qwen, and DeepSeek
- Provider expansion is cross-cutting: code, tests, docs, `.env.example`, deployment assumptions, and IAM scoping must move together
- If provider support differs between local and deployed runtimes, that boundary must be documented explicitly
- Bedrock guardrails are optional and only wired when `GUARDRAIL_ID` is set
- Deployment packaging must bundle `deploy/app.py` and Linux wheels, not `agent.py`
- The manylinux/cp312 wheel install logic in `deploy/deploy.py` must be preserved
- Deploy flow must remain idempotent and least-privilege
- `README.md`, inline comments, `.env.example`, and troubleshooting guidance are first-class deliverables
- Use `black` before completing implementation work
- Preserve the contract-test mindset: static tests enforce scaffold and convention rules, unit tests mock cloud SDKs, and live evals remain opt-in

### UX Design Requirements

Not applicable — this is a CLI/API developer tool with no visual interface. Developer experience requirements are fully captured in the FRs, NFRs, and architecture constraints above.

### FR Coverage Map

FR1: Epic 1 - natural language date input
FR2: Epic 1 - multi-format date parsing
FR3: Epic 1 - ambiguous format clarification
FR4: Epic 1 - friendly conversational response
FR5: Epic 1 - graceful invalid input handling
FR6: Epic 1 - dedicated date tool
FR7: Epic 1 - age-in-days calculation
FR8: Epic 1 - whole-number day output
FR9: Epic 1 - custom Strands tool definition
FR10: Epic 1 - tool invocation during conversation
FR11: Epic 2 - AgentCore observability capture
FR12: Epic 1 and Epic 4 - adapter-based model configuration and later expansion
FR13: Epic 1 - AWS region configuration
FR14: Epic 1 - credentials via environment variables
FR15: Epic 1 - documented `.env.example`
FR16: Epic 1 - local setup from README
FR17: Epic 1 - single-command local run
FR18: Epic 1 - VS Code F5 debugging
FR19: Epic 1 - dependency installation in venv
FR20: Epic 2 and Epic 4 - deployment path plus expanded supported model paths
FR21: Epic 2 and Epic 4 - deployed verification path plus expanded model validation
FR22: Epic 2 - infrastructure in `us-east-1`
FR23: Epic 2 - troubleshooting for deployment issues
FR24: Epic 2 - tool-call traces in AgentCore
FR25: Epic 2 - tool I/O visibility without custom logging
FR26: Epic 3 - project understanding from README
FR27: Epic 3 - required README structure
FR28: Epic 3 - inline explanation comments
FR29: Epic 3 - self-explanatory structure

## Epic List

### Epic 1: Local Agent Experience

A developer can clone the repo, configure the environment, run the age-in-days agent locally, and validate the core Strands tool-driven experience with adapter-based local model selection.

**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8, FR9, FR10, FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19

### Epic 2: AgentCore Deployment and Observability

A developer can deploy the agent to AWS AgentCore, verify the deployed endpoint, and observe tool activity and responses through managed AgentCore traces.

**FRs covered:** FR11, FR20, FR21, FR22, FR23, FR24, FR25

### Epic 3: Developer Documentation and Project Finalization

A developer new to Strands and AgentCore can understand, run, troubleshoot, and fork the project from the documentation and code structure alone.

**FRs covered:** FR26, FR27, FR28, FR29

### Epic 4: Multi-Provider Model Expansion

A developer can extend the project beyond the initial supported model paths through the adapter architecture, with staged support for additional model families and clearly documented local versus deployed runtime boundaries.

**FRs covered:** FR12, FR20, FR21

## Epic 1: Local Agent Experience

A developer can clone the repo, configure the environment, run the age-in-days agent locally, and validate the core Strands tool-driven experience with adapter-based local model selection.

### Story 1.1: Project Scaffold and Configuration Contract

As a developer,
I want the local project scaffold and configuration contract in place,
So that I can install dependencies, configure supported model paths, and start development without undocumented setup work.

**Acceptance Criteria:**

**Given** I have cloned the repository and have Python 3.11+ installed
**When** I create a virtual environment and run `pip install -r requirements.txt`
**Then** the dependencies install successfully
**And** the requirements file includes the local runtime packages plus deployment-related dependency notes required by the architecture

**Given** I inspect `.env.example`
**When** I review the configuration sections
**Then** I see documented variables for model selection, AWS settings, deployment naming, and optional local-adapter credentials
**And** the file contains no real credentials

**Given** I inspect the root scaffold
**When** I review the project layout
**Then** the expected files and folders for local agent work, deployment, and editor support are present
**And** `.gitignore` excludes `.env`, Python cache artifacts, and local virtual environment files

### Story 1.2: Local Age-in-Days Agent

As a developer and evaluator,
I want a working local agent that accepts date-of-birth input and responds conversationally,
So that I can validate the core Strands agent pattern and user-facing behavior end to end.

**Acceptance Criteria:**

**Given** `agent.py` is implemented with `SYSTEM_PROMPT`, the `get_today_date` tool, model construction, and a REPL loop
**When** I run `python agent.py` with a supported local model path configured
**Then** the agent starts within 10 seconds
**And** it displays an interactive prompt

**Given** the agent is running
**When** I enter a natural-language birth date such as `I was born on 14th March 1990`
**Then** the agent invokes `get_today_date`
**And** it returns the correct age in days in a friendly response

**Given** the agent is running
**When** I enter a supported structured date format such as `1990-03-14` or `14/03/1990`
**Then** the agent interprets the input correctly
**And** returns the age in days without crashing

**Given** the agent is running
**When** I enter an ambiguous date such as `3/4/1990`
**Then** the agent asks a clarifying question before calculating
**And** it does not guess silently

**Given** the agent is running
**When** I enter clearly invalid input
**Then** the agent responds with a helpful error message
**And** the process continues running

### Story 1.3: Adapter-Based Local Model Selection

As a developer,
I want local model selection routed through the adapter abstraction,
So that I can switch between supported local model paths without editing application logic.

**Acceptance Criteria:**

**Given** the local runtime supports the initial `bedrock` and `gemini` adapter paths
**When** I configure `MODEL_PROVIDER` and `MODEL_ID` for one of those supported paths
**Then** the local agent builds the model through the adapter boundary
**And** no application-logic code changes are required

**Given** an unsupported provider or unsupported local/runtime combination is configured
**When** the local agent starts
**Then** it fails clearly with an explicit configuration error
**And** it does not silently fall back to another provider

**Given** I inspect the local model selection implementation
**When** I review the code
**Then** adapter selection logic is separated from the conversational REPL logic
**And** the implementation preserves the architecture rule that local and deployed runtimes remain distinct

### Story 1.4: VS Code Debug Experience

As a developer,
I want F5 debugging configured for the local agent path,
So that I can inspect tool execution and runtime behavior without manual debugger setup.

**Acceptance Criteria:**

**Given** the project is open in VS Code
**When** I press F5
**Then** `agent.py` launches with the Python debugger attached
**And** environment variables are loaded from `.env`

**Given** I set a breakpoint inside local agent execution
**When** I interact with the REPL
**Then** execution pauses at the breakpoint
**And** I can inspect local variables and tool flow

**Given** I inspect `.vscode/extensions.json`
**When** I review the recommended extensions
**Then** the file points developers to the required Python tooling
**And** it reflects the intended local development workflow

## Epic 2: AgentCore Deployment and Observability

A developer can deploy the agent to AWS AgentCore, verify the deployed endpoint, and observe tool activity and responses through managed AgentCore traces.

### Story 2.1: AgentCore Deployment Path

As a developer,
I want a one-command deployment path to AgentCore,
So that I can provision and publish the agent without manual console setup.

**Acceptance Criteria:**

**Given** I have valid AWS credentials, `AWS_REGION=us-east-1`, and deployment configuration set
**When** I run `python deploy/deploy.py`
**Then** the deployment completes successfully or fails with actionable diagnostics
**And** it prints the deployed endpoint details needed for verification

**Given** the deployment path provisions infrastructure
**When** it creates or updates AWS resources
**Then** it uses least-privilege IAM scoping
**And** it preserves the documented packaging approach for the AgentCore runtime

**Given** the agent has already been deployed once
**When** I run the deployment again
**Then** the process updates or reuses the existing resources idempotently
**And** it does not create duplicate agents unnecessarily

### Story 2.2: Deployed Runtime Adapter Contract

As a developer,
I want the deployed runtime to follow the documented Bedrock-first adapter contract,
So that the cloud path remains reliable and distinct from the local Strands path.

**Acceptance Criteria:**

**Given** the deployed runtime entrypoint is implemented
**When** I inspect `deploy/app.py`
**Then** it uses the deployed runtime contract rather than importing the local Strands runtime directly
**And** it preserves the required unconditional AgentCore startup behavior

**Given** provider support differs between local and deployed runtimes
**When** the deployed runtime is configured
**Then** supported and unsupported combinations are made explicit
**And** the implementation does not hide those boundaries with silent fallbacks

**Given** deployment packaging is prepared
**When** the artifact is assembled
**Then** it bundles the deployed runtime path and required Linux wheels
**And** it does not package `agent.py` as the production runtime entrypoint

### Story 2.3: Endpoint Verification and Observability Confirmation

As a developer,
I want to verify the deployed agent and inspect its traces,
So that I can prove the production path works and demonstrate managed observability.

**Acceptance Criteria:**

**Given** the agent has been deployed successfully
**When** I invoke the deployed endpoint with a date-of-birth query
**Then** the agent returns the correct age in days within the expected performance envelope
**And** the verification path is documented or reproducible

**Given** the deployed agent has processed at least one request
**When** I inspect the AgentCore observability surface
**Then** I can see the tool invocation trace and final response
**And** no custom logging code is required to surface that information

**Given** a common deployment or verification issue occurs
**When** I troubleshoot the failure
**Then** the documented guidance covers region, credentials, env vars, and model access boundaries
**And** the resolution path is explicit enough for a new developer to follow

## Epic 3: Developer Documentation and Project Finalization

A developer new to Strands and AgentCore can understand, run, troubleshoot, and fork the project from the documentation and code structure alone.

### Story 3.1: Comprehensive README

As a developer new to Strands and AgentCore,
I want a complete README covering setup, deployment, and troubleshooting,
So that I can get from clone to working agent without relying on unstated context.

**Acceptance Criteria:**

**Given** I open the README
**When** I read the opening sections
**Then** I understand the project purpose, architecture, and expected outcomes quickly
**And** the document is written for someone new to this stack

**Given** I inspect the README structure
**When** I review the headings and content
**Then** it includes prerequisites, local setup, deployment, project structure, how it works, troubleshooting, and contributing guidance
**And** it documents the supported configuration paths clearly

**Given** I follow the README step by step
**When** I complete the documented local and deployment flows
**Then** I can run the local agent and deploy the project without undocumented steps
**And** the troubleshooting guidance covers the most likely failure cases

### Story 3.2: Inline Explanation and Structure Clarity

As a developer reading the repo for the first time,
I want the code and structure to explain themselves,
So that I can confidently adapt the project for my own use case.

**Acceptance Criteria:**

**Given** I inspect the local and deployed runtime code
**When** I encounter non-obvious logic such as env loading, adapter boundaries, deployment packaging, or IAM setup
**Then** I find concise inline comments explaining why the code exists
**And** the comments do not merely restate the syntax

**Given** I inspect the project tree
**When** I review the top-level files and key folders
**Then** their purposes are immediately understandable
**And** a developer can identify where to change agent behavior versus deployment behavior

**Given** I run formatting or static convention checks aligned with the project rules
**When** I validate the maintained files
**Then** the code remains PEP 8 compliant
**And** the project still respects the documented structural constraints such as the lean `agent.py` rule

## Epic 4: Multi-Provider Model Expansion

A developer can extend the project beyond the initial supported model paths through the adapter architecture, with staged support for additional model families and clearly documented local versus deployed runtime boundaries.

### Story 4.1: Expansion Scope Alignment

As a developer extending model support,
I want the planning and configuration artifacts aligned to the adapter-expansion strategy,
So that implementation starts from a coherent contract rather than mixed legacy assumptions.

**Acceptance Criteria:**

**Given** the project supports a Bedrock-first architecture with staged expansion
**When** I inspect the planning artifacts and configuration scaffolding
**Then** they describe adapter-based provider selection consistently
**And** they distinguish initial support from future expansion targets

**Given** `.env.example`, README, and project context reference supported model paths
**When** I review those artifacts
**Then** they accurately reflect the supported local and deployed runtime boundaries
**And** they do not imply unsupported runtime symmetry

### Story 4.2: Capability Registry and Adapter Extension

As a developer,
I want the adapter layer extended with capability-aware model registration,
So that additional model families can be introduced in a controlled and explicit way.

**Acceptance Criteria:**

**Given** the adapter architecture currently supports the initial local model paths
**When** I extend the registry for new candidate model families
**Then** each supported path is represented through explicit capability-aware registration
**And** unsupported combinations fail clearly

**Given** new model families are being introduced
**When** I review the local adapter implementation
**Then** support is added without collapsing the separation between local and deployed runtime concerns
**And** the code remains consistent with the documented abstraction boundary

**Given** provider expansion affects more than one layer
**When** the implementation is updated
**Then** code, tests, configuration docs, and deployment assumptions are advanced together
**And** no hidden support gap is introduced

### Story 4.3: Bedrock-First Model Family Rollout

As a developer,
I want at least one staged expansion delivered through the Bedrock-first path,
So that the project demonstrates credible growth beyond the original supported models while preserving deployment alignment.

**Acceptance Criteria:**

**Given** candidate additional model families are available through the chosen rollout path
**When** one supported expansion family is enabled
**Then** it works through the adapter architecture using the documented configuration pattern
**And** the implementation preserves Bedrock-first deployment assumptions where required

**Given** the expanded model path is enabled
**When** I exercise the supported local or deployed validation flow for that path
**Then** the project demonstrates the new support successfully
**And** the supported boundary is documented clearly for developers

### Story 4.4: Optional Direct-Provider Evaluation Boundary

As a maintainer,
I want any non-Bedrock direct-provider or LiteLLM-style path treated as an explicit evaluated boundary,
So that optional expansion does not accidentally weaken the core architecture contract.

**Acceptance Criteria:**

**Given** a direct-provider or alternative gateway path is being considered
**When** I document or prototype that path
**Then** it is clearly marked as optional and justified by capability gaps
**And** it is not presented as default parity with the Bedrock-first path

**Given** optional direct-provider support differs from the primary deployed path
**When** I review the resulting docs and configuration guidance
**Then** the limitations and expected usage are explicit
**And** developers can tell which paths are production-aligned versus exploratory

### Story 4.5: Expansion Documentation and Verification

As a developer,
I want the expanded model-support surface documented and verified,
So that I can adopt supported new model paths with confidence.

**Acceptance Criteria:**

**Given** new model-support paths have been added or clarified
**When** I inspect the tests, verification notes, and documentation
**Then** each supported path has an explicit verification strategy
**And** local versus deployed runtime expectations are documented

**Given** the expansion changes affect setup or troubleshooting
**When** I review README and related docs
**Then** the new configuration and support boundaries are captured accurately
**And** the guidance remains usable for a developer new to the repository
