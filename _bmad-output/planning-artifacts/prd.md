---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish', 'step-12-complete']
inputDocuments: []
workflowType: 'prd'
briefCount: 0
researchCount: 0
brainstormingCount: 0
projectDocsCount: 0
classification:
  projectType: developer_tool
  domain: scientific_ai
  complexity: medium
  projectContext: greenfield
---

# Product Requirements Document - strands-agents-demo

**Author:** Paul
**Date:** 2026-03-16

## Executive Summary

`strands-agents-demo` is a production-ready reference implementation demonstrating the complete lifecycle of AI agent development and deployment on AWS. It targets developers and solutions architects building AI agents with the Strands Agents SDK who need a credible, working path to production — not a toy example, but a fully observable, secure, and scalable agent running on AWS AgentCore.

The core problem: the gap between "I can build an agent" and "I can run an agent in production." Writing an agent is accessible; operating one with memory persistence, tool governance, observability, identity management, and scalable infrastructure is not. This demo bridges that gap with a concrete, runnable implementation developers can fork, explore, and build from with confidence.

The timing is deliberate: AWS AgentCore is newly available and early adopters lack trusted reference material. This project gives developers a head start rather than leaving them to assemble the pieces from scratch.

### What Makes This Special

Unlike generic agent tutorials, this showcase is end-to-end and opinionated. The Strands Agents SDK handles the development layer (agent logic, tool binding, prompting); AWS AgentCore handles the production layer (managed memory, execution environment, observability, security). Their integration is the differentiator — showing developers exactly how they fit together as a unified, coherent stack.

The "aha moment" is not just seeing an agent run — it's seeing it run *reliably*, with visibility into what it's doing, credentials handled properly, and infrastructure that scales. That's the moment developers realise what production agent development actually looks like.

**This project introduces a new paradigm: Strands + AgentCore as the default agent stack** — analogous to how CDK became the default for AWS infrastructure. It reframes the developer's mental model from *"I need to build and operate an agent"* to *"I need to define an agent — AgentCore operates it."*

## Project Classification

- **Project Type:** Developer Tool — SDK reference implementation with runnable code, patterns, and documentation
- **Domain:** AI/ML — agent development and cloud-native deployment
- **Complexity:** Medium — novel technology stack, no regulatory constraints, real architectural decisions around cloud infrastructure and agent lifecycle
- **Project Context:** Greenfield

## Success Criteria

### User Success

- A developer clones the repo, follows the README, and runs the age-in-days agent locally with zero undocumented steps
- The developer deploys the agent to AWS AgentCore without manual console steps
- The developer observes the running agent — tool calls, logs, traces — and understands what it's doing and why
- The developer leaves with a clear mental model of how Strands + AgentCore fit together and can apply the pattern to their own use case

### Business Success

- The demo serves as a credible, forkable reference implementation for early AWS AgentCore adopters
- Developers who complete it end-to-end gain confidence in the Strands + AgentCore stack as a production path
- The showcase is appropriate for event/conference presentation and developer-facing content

### Technical Success

- Agent executes correctly: accepts a date of birth, retrieves today's date via a tool, returns age in days
- Deployment to AgentCore is scripted and reproducible — no manual console steps
- Observability is demonstrably working: tool calls and results are visible in AgentCore
- Code is clean, well-documented, and follows Strands SDK best practices

### Measurable Outcomes

- End-to-end setup (local run → AgentCore deployment) completable by a developer following the README alone
- Agent produces correct age-in-days calculation for any valid date of birth
- Zero manual AWS console steps required to deploy

## User Journeys

### Journey 1: Alex — The Developer (Happy Path)

**Who is Alex?** A mid-level backend developer at a company exploring AI agents. She's used the OpenAI API before but has never built a structured agent, never used Strands SDK, and never touched AWS AgentCore. Her team lead sent her a link to this repo: "take a look, see if we could build something like this."

**Opening Scene:** Alex opens the README with a coffee. She clones the repo, follows the local setup instructions, runs the agent, types her date of birth. It answers: *"You are 12,847 days old."* She smiles. That was fast.

**Rising Action:** She follows the deployment section — infrastructure as code, no console clicking. She runs the deploy command. It provisions. Same question to the deployed endpoint, same answer, but now it's *running on AWS*. She opens the AgentCore console and sees her agent's tool calls logged — the date tool firing, the calculation, the response.

**Climax:** She clicks into the observability dashboard. Every interaction is traced. She realises: *"If this were a production agent handling real user data, I'd have complete visibility right now."* Not just "the agent runs" — "I understand how to operate it."

**Resolution:** Alex forks the repo, renames the agent, and starts sketching her team's use case. She Slacks her team lead: *"Yeah, I think we can do this."*

**Requirements revealed:** Local dev setup, Strands agent scaffolding, date tool implementation, AgentCore deployment scripts, observability integration, clean documented code.

---

### Journey 2: Alex — The Developer (Error Recovery)

**Opening Scene:** Alex tries to deploy but lacks the right IAM permissions for AgentCore. The deploy fails with an opaque AWS error.

**Rising Action:** She checks the README troubleshooting section — common IAM errors listed with required policy links. She updates her permissions, re-runs. This time it provisions, but she entered the date as DD/MM/YYYY instead of YYYY-MM-DD.

**Climax:** The agent asks her to confirm the date format rather than crashing or returning a wrong answer. She corrects it, gets the right result.

**Resolution:** She notes the agent has real input validation, not just happy-path logic. That's production-grade.

**Requirements revealed:** Meaningful error messages, IAM setup documentation, input validation and format handling, graceful error responses.

---

### Journey 3: Jamie — The End User

**Who is Jamie?** A non-technical user interacting with the deployed agent. Jamie doesn't know or care about Strands or AgentCore.

**Opening Scene:** Jamie types: *"I was born on 14th March 1990."*

**Climax:** The agent interprets the natural language date, fetches today's date, and responds: *"You are 13,150 days old! That's about 36 years and 1 day."* It understood natural language — it feels smart, not robotic.

**Requirements revealed:** Natural language date parsing, friendly response formatting, conversational tone.

---

### Journey 4: Morgan — The Demo Observer

**Who is Morgan?** A senior architect evaluating whether AgentCore is worth adopting. Technically sharp and skeptical.

**Opening Scene:** Morgan watches someone run the agent live. Unimpressed — seen it before.

**Rising Action:** The presenter switches to the AgentCore console. Shows the tool call trace — the date tool firing, exact input/output, latency. No custom auth code, no logging boilerplate — all managed.

**Climax:** Morgan asks: *"How much of that observability did you have to build?"* Answer: *"None. It's AgentCore."* Morgan leans forward.

**Resolution:** Morgan pulls up the repo. The agent code is 50 lines. The deployment script is straightforward IaC. *"We could have something like this running in a week."*

**Requirements revealed:** Clean minimal agent code, readable IaC deployment, zero-config AgentCore observability, presenter-friendly demo flow.

---

### Journey Requirements Summary

| Capability | Revealed By |
|---|---|
| Local dev setup (zero friction) | Alex happy path |
| Strands agent scaffolding with date tool | Alex happy path, Jamie |
| Natural language date input parsing | Jamie |
| Input validation and error handling | Alex error recovery |
| AgentCore deployment via IaC (no console) | Alex happy path |
| Observability — tool traces, logs, memory | Alex happy path, Morgan |
| IAM/permissions documentation + troubleshooting | Alex error recovery |
| Clean, minimal, readable code | Morgan |
| Friendly, conversational agent responses | Jamie |

## Domain-Specific Requirements

### Compliance & Regulatory

- **PII Handling:** Date of birth is PII but carries minimal risk — no name, email, or other identifying data collected alongside it. No PII masking or data retention controls required for MVP. README includes a note acknowledging this boundary.
- No regulatory compliance requirements (HIPAA, GDPR, PCI-DSS) apply to this demo scope.

### Technical Constraints

- **Credentials:** AWS credentials and LLM API keys managed via environment variables. `.env.example` provided; `.env` excluded from version control.
- **AWS Region:** `us-east-1` — primary deployment target.
- **Model Selection:** The project uses a capability-driven model abstraction. Amazon Bedrock is the primary model access plane for MVP, with model selection controlled via environment variables and adapter-based model wiring. Initial local adapters support Bedrock and Gemini; the architecture is designed to expand toward Gemma, Moonshot AI, Llama, Qwen, and DeepSeek in staged increments.

### Integration Requirements

- Amazon Bedrock as the primary LLM backend and deployment-aligned inference plane for MVP
- Strands model adapters for local model construction
- Optional future direct-provider or LiteLLM-based integrations where Bedrock capability gaps justify them
- AWS AgentCore for production deployment and managed capabilities
- Strands Agents SDK as the agent framework
- No external databases, queues, or third-party APIs beyond the above

## Innovation & Novel Patterns

### Detected Innovation Areas

This project establishes **Strands + AgentCore as the default agent stack** for production AI development on AWS — analogous to CDK for infrastructure or Amplify for frontend. The innovation is not the age-in-days calculation; it's the proof that a developer can go from zero to a production-grade, observable, scalable agent on AWS without assembling custom infrastructure, writing logging boilerplate, or managing agent lifecycle concerns manually.

### Market Context

AWS AgentCore is sufficiently differentiated that comparison to alternatives (LangChain + LangSmith, CrewAI, AutoGen) is not the point. Those require developers to assemble and operate their own production stack. AgentCore is a managed production environment. This demo is the first credible reference implementation that demonstrates that distinction end-to-end.

### Validation Approach

- If a developer new to both Strands and AgentCore can follow the README and reach a deployed, observable production agent, the paradigm claim holds
- Secondary validation: developers who fork the repo and adapt it to their own use case — the pattern transfers

### Risk Mitigation

- **AgentCore maturity:** Documented as a new service; demo pins to a tested SDK version and notes known limitations
- **Paradigm adoption:** Opinionated but not prescriptive — code structure is clear enough that developers can deviate where needed

## Developer Tool Specific Requirements

### Technical Architecture

- **Language:** Python 3.11+ (aligns with Strands Agents SDK)
- **Package Management:** `requirements.txt` for simplicity and broad compatibility
- **IDE:** VS Code — `.vscode/` folder with recommended extensions and F5 launch configuration
- **Virtual environment:** `venv` — setup documented step-by-step in README

### Installation Methods

1. **Local:** Clone → create venv → `pip install -r requirements.txt` → configure `.env` → run
2. **Production:** Configure AWS credentials → run deployment script → verify via AgentCore endpoint

Both paths documented with copy-paste commands. No assumed knowledge beyond basic Python and AWS CLI familiarity.

### API Surface

- **Input:** Natural language or structured date of birth
- **Tool:** `get_today_date()` — Strands `@tool` returning current date
- **Output:** Conversational response with age in days
- **Configuration:** Environment variables for model, region, and API keys

### Code Examples Required

| Example | Purpose |
|---|---|
| Agent definition | How to define an agent with Strands SDK |
| Tool definition | How to write and register a `@tool` |
| Environment config | How to load env vars for model/credentials |
| AgentCore registration | How to register and deploy to AgentCore |
| Local invocation | How to run and test the agent locally |

### Documentation Standards

Documentation is a first-class deliverable:

- **README:** Comprehensive, table of contents, covers overview, prerequisites, local setup, AgentCore deployment, project structure, how it works, troubleshooting, and contributing. Written for a developer new to Strands and AgentCore.
- **Inline comments:** Every non-obvious code block annotated with *why*, not just *what*.
- **`.env.example`:** Every variable documented with description, expected format, and example value.
- **Troubleshooting section:** Common errors (IAM permissions, wrong region, missing env vars, model access) with diagnosis and fix steps.
- **Tone:** Direct, clear, assumes competence but not prior Strands/AgentCore knowledge.

## Project Scoping & Phased Development

### MVP Strategy

**Approach:** Problem-solving MVP — the simplest agent that fully demonstrates the Strands + AgentCore production lifecycle. Agent logic is intentionally trivial (age in days) so developers focus on the *pattern*, not the problem domain.

**Resource Requirements:** Single developer, Python proficiency, AWS account with AgentCore access, and credentials for the selected configured model path.

### MVP Feature Set (Phase 1)

**Must-Have Capabilities:**

- Age-in-days agent built with Strands Agents SDK
- `get_today_date()` tool via Strands `@tool` decorator
- Natural language date of birth input handling
- Graceful input validation and error responses
- Environment-variable-driven configuration (model, region, API keys)
- Capability-driven model abstraction for local model selection
- Bedrock-first model support for MVP
- Gemini retained as an initial local adapter path
- Planned staged expansion path toward Gemma, Moonshot AI, Llama, Qwen, and DeepSeek
- AgentCore deployment via IaC script — no manual console steps
- VS Code launch configuration for local F5 debugging
- Comprehensive README with ToC, setup, deployment, troubleshooting
- `.env.example` with all variables documented
- Inline code comments throughout

### Post-MVP Features

**Phase 2 (Growth):**

- Additional output modes: age in weeks, months, years
- Multi-turn memory — agent remembers previously entered dates
- Agent-to-agent orchestration example using AgentCore routing
- CI/CD pipeline for automated AgentCore deployment

**Phase 3 (Expansion):**

- Multi-agent showcase — orchestrator + specialist agents managed by AgentCore
- Architecture decision records documenting production agent patterns
- Community contribution guide for additional agent examples

### Risk Mitigation

- **Technical:** Pin to tested SDK versions; document known AgentCore limitations; prefer Bedrock-first support for deployment-aligned stability; expand provider support in staged increments behind the adapter layer
- **Market:** Reference implementation — success is developer adoption, not revenue
- **Resource:** Phase 2 and 3 defer cleanly without affecting MVP value

## Functional Requirements

### Agent Conversation

- **FR1:** A user can provide their date of birth in natural language and receive their age in days
- **FR2:** A user can provide a date of birth in multiple formats (natural language, ISO 8601, DD/MM/YYYY) and the agent correctly interprets it
- **FR3:** The agent asks a clarifying question when date format is ambiguous rather than returning an incorrect result
- **FR4:** The agent provides a friendly, conversational response that includes the age in days
- **FR5:** The agent gracefully handles invalid or unparseable date inputs with a helpful error message

### Date Calculation

- **FR6:** The agent retrieves the current date using a dedicated date tool
- **FR7:** The agent calculates the difference in days between today's date and a given date of birth
- **FR8:** The agent returns the age as a whole number of days

### Tool Framework

- **FR9:** A developer can define a custom tool using the Strands `@tool` decorator
- **FR10:** The agent invokes a registered tool during a conversation turn and uses the result in its response
- **FR11:** Tool invocations and results are captured and visible in AgentCore observability

### Configuration Management

- **FR12:** A developer configures the model provider and model identifier via environment variables and adapter-based model selection without modifying application logic
- **FR13:** A developer configures the AWS region via environment variable
- **FR14:** A developer configures all required API keys and credentials via environment variables
- **FR15:** The project provides a `.env.example` documenting every required variable with description and example value

### Local Development

- **FR16:** A developer sets up the local environment by following the README without undocumented steps
- **FR17:** A developer runs the agent locally with a single command after environment setup
- **FR18:** A developer runs and debugs the agent in VS Code using F5 with a provided launch configuration
- **FR19:** A developer installs all dependencies via `pip install -r requirements.txt` in a Python virtual environment

### AgentCore Deployment

- **FR20:** A developer deploys the agent to AWS AgentCore by running a provided script — no manual console steps required
- **FR21:** A developer verifies the deployed agent by invoking it via the AgentCore endpoint
- **FR22:** The deployment script provisions all required infrastructure in `us-east-1`
- **FR23:** A developer follows the README troubleshooting section to diagnose and resolve common deployment errors (IAM permissions, missing env vars, wrong region)

### Observability

- **FR24:** A developer views the agent's tool call traces in the AgentCore console after interacting with the deployed agent
- **FR25:** A developer sees inputs and outputs of each tool invocation in AgentCore without writing custom logging code

### Project Documentation

- **FR26:** A developer new to Strands and AgentCore understands the project purpose, architecture, and setup from the README alone
- **FR27:** The README includes table of contents, prerequisites, local setup, AgentCore deployment, project structure, how it works, troubleshooting, and contributing
- **FR28:** Every non-obvious code block in the agent and deployment scripts includes an inline comment explaining its purpose
- **FR29:** The project structure is self-explanatory — file and folder names reflect their purpose without documentation to navigate

## Non-Functional Requirements

### Performance

- The deployed agent responds to a date of birth query within 5 seconds under normal load
- Local agent startup completes within 10 seconds of invoking the run command

### Security

- AWS credentials and API keys are never hardcoded — environment variables only
- `.env` is excluded from version control; `.env.example` contains no real credentials
- No user input is logged in plaintext outside of AgentCore's managed observability context
- The deployment script requests only the minimum IAM permissions required for AgentCore operation
- README includes an explicit warning against committing credentials to version control

### Integration

- The agent functions correctly with Bedrock-backed model support for MVP
- Initial non-Bedrock local adapter support may be provided where documented
- Model switching requires configuration changes only when the selected model/runtime combination is supported by the configured adapter path
- AgentCore deployment is idempotent — re-running the script does not create duplicate resources or errors

### Code Quality & Maintainability

- Agent code is contained in a single readable file of under 150 lines
- All files follow PEP 8
- No external dependencies beyond the Strands SDK, LLM client libraries, and Python standard library
- A developer unfamiliar with the codebase understands each file's purpose within 5 minutes of reading it
- The project can be forked and adapted to a different use case by modifying only the agent logic file and environment variables
