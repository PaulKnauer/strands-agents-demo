# AI System Card — Age-in-Days Agent

_NIST AI RMF Functions: GOVERN, MAP_

This document describes the AI system deployed in the strands-agents-demo project. It serves as the primary GOVERN and MAP artifact for the NIST AI Risk Management Framework compliance layer introduced in Epic 4.

---

## System Purpose

The Age-in-Days Agent is a single-purpose conversational AI agent that accepts a date of birth provided by the user in natural language or a structured date format, and returns the user's age expressed as a whole number of days.

The agent has one registered tool — `get_today_date` — which retrieves the current date from the Python standard library. All date arithmetic is delegated to the language model, which uses the tool result as the authoritative "today" value. The agent does not store or persist any user input between sessions.

This agent is a developer reference implementation demonstrating the complete lifecycle of AI agent development and deployment using the Strands Agents SDK and AWS AgentCore. It is not intended for production or regulated use without additional controls.

---

## Intended Users

**Primary audience:** Developers and solutions architects evaluating the Strands Agents SDK and AWS AgentCore as a production AI agent stack.

**Secondary audience:** Technical leads and enterprise architects assessing the responsible-AI capabilities of the Strands + AgentCore platform.

**Assumed context:** The agent is run locally via the command line or deployed to AWS AgentCore for demonstration purposes. Users are expected to be technically proficient and aware they are interacting with a reference implementation.

---

## Out-of-Scope Uses

The following uses are explicitly out of scope for this reference implementation:

- **Medical or legal age determination.** The output of this agent must not be used as authoritative evidence in any medical, legal, or regulatory context. Date-of-birth calculations may have legal significance in age of majority, medical eligibility, or benefits determinations; this agent has not been assessed for those use cases.
- **Identity verification.** The agent does not verify the identity of the user or the authenticity of the date of birth provided.
- **Production PII handling without additional controls.** Users may inadvertently include personally identifiable information (e.g., a real date of birth) in their prompts. The agent has not been hardened for production environments where PII handling must meet regulatory requirements (GDPR, HIPAA, CCPA). Story 4.3 adds Bedrock Guardrails PII redaction as a mitigation.
- **Multi-turn stateful conversations.** The agent does not maintain memory between sessions. Each invocation is stateless.
- **High-volume or production workloads without performance assessment.** The demo configuration has not been load-tested or performance-profiled for production-scale traffic.

---

## Third-Party Components

_NIST AI RMF GOVERN-6.1: Third-party and supply-chain risk management._

| Component | Version | Role | Supply-Chain Risk |
|---|---|---|---|
| Strands Agents SDK | `strands-agents==1.26.0` | Agent framework — orchestrates tool calls and model invocations | LOW — open-source AWS project; pinned to a specific version |
| Strands Agents Tools | `strands-agents-tools` (latest) | Optional tool library — not used in core agent | LOW — same project family |
| Amazon Bedrock | Managed service | Language model inference — primary LLM provider | LOW — AWS managed; subject to AWS service terms and availability |
| AWS AgentCore | Managed service (preview/GA) | Agent deployment runtime — session isolation, observability, identity | MEDIUM — newly GA service; API surface may evolve |
| python-dotenv | `>=1.0.0` | Environment variable loading from `.env` file | LOW — stable, widely-used library |
| boto3 | `>=1.34.0` | AWS SDK — used by BedrockModel and deployment script | LOW — AWS first-party SDK |
| Google Gemini (optional) | Fallback via `strands-agents[gemini]` | Alternative LLM provider if Bedrock is unavailable | LOW — optional; not installed in default configuration |

**Note on versions:** This system card documents component versions at the time of Epic 4 implementation (2026-03-20). The Third-Party Components section must be updated whenever a dependency is upgraded, a new component is added, or a component is removed. See Review Cadence.

---

## Data Flows

_NIST AI RMF MAP-1.1: Deployment context and data handling._

```
User keyboard input (date of birth in natural language)
  → Strands Agent REPL loop (agent.py)
  → BedrockModel.converse() API call (HTTPS, encrypted in transit)
  → Amazon Bedrock (language model inference)
  → LLM decides to call get_today_date tool
  → get_today_date() (Python stdlib: datetime.date.today())
  → Tool result returned to LLM as context (ISO 8601 date string)
  → LLM computes age in days, composes natural language response
  → Response printed to terminal
```

**Data persistence:** None. No user input, model output, or tool result is written to disk or any persistent store by the agent code. AWS AgentCore may capture invocation traces and logs in CloudWatch as part of its managed observability features (see AgentCore documentation for retention policies).

**PII handling:** Users may include a real date of birth in their input. This value is:
- Sent to Amazon Bedrock for inference (subject to AWS data processing terms)
- Printed to the terminal as part of the agent's response
- Not stored or logged by the agent code itself

Story 4.3 (Bedrock Guardrails) adds PII detection and redaction as an additional control layer.

**External network calls:** The agent makes one external HTTPS call per conversation turn — to the Amazon Bedrock endpoint in the configured AWS region. No other external services are contacted during normal operation.

---

## Harm Categories Considered

_NIST AI RMF MAP-2.2 and NIST AI 600-1 (Generative AI Profile): Risk identification across system components._

The following table maps NIST AI 600-1 risk categories to this agent's specific risk surface. Likelihood and Impact are rated LOW/MEDIUM/HIGH relative to a developer demonstration context.

| ID | Harm Category | NIST AI 600-1 Risk | Likelihood | Impact | Notes |
|---|---|---|---|---|---|
| H-1 | Prompt injection | Prompt Injection | LOW | LOW | Narrow tool surface (one deterministic tool); no external data retrieval or write operations. Bedrock Guardrails PROMPT_ATTACK filter planned in Story 4.3. |
| H-2 | Hallucinated date output | Confabulation / Hallucination | LOW | LOW | System prompt explicitly instructs the agent to call `get_today_date` before calculating. The calculation is verifiable by the user. |
| H-3 | Harmful or offensive content | Harmful Content Generation | LOW | LOW | The agent's task is date arithmetic; it has no natural surface for generating harmful content. Content filters planned in Story 4.3. |
| H-4 | PII exposure in prompts | Data Privacy | LOW | MEDIUM | Users may provide a real date of birth. This is sent to Bedrock for inference. No PII is stored by agent code; PII redaction planned in Story 4.3. |
| H-5 | Incorrect age calculation | Output Quality | LOW | LOW | Date arithmetic is deterministic once "today" is fixed by the tool. Incorrect output is immediately verifiable by the user. Unit tests cover `get_today_date` and REPL logic. |
| H-6 | Model provider dependency | System Reliability | MEDIUM | MEDIUM | If Amazon Bedrock is unavailable, the agent cannot respond. Mitigation: multi-provider switching (Bedrock → Gemini) via env vars. |
| H-7 | Supply-chain compromise | Data Poisoning / Supply Chain | LOW | LOW | Pinned dependency versions in `requirements.txt`; standard Python package supply-chain risk. No training data interaction at inference time. |

**Residual risk summary:** All identified risks are LOW or MEDIUM likelihood. No HIGH-likelihood or HIGH-impact risk categories have been identified for this agent in its intended use context. The most significant residual risk is H-4 (PII exposure), addressed in Story 4.3.

---

## Risk Tolerance Statement

_NIST AI RMF GOVERN-1.3: Risk tolerance documented._

This agent is a developer reference implementation. It is designed for demonstration and educational use. It has not been assessed for regulated industry use cases (healthcare, finance, legal) or for deployment contexts where incorrect date calculations could cause harm. Organisations deploying a fork of this agent in production must conduct their own risk assessment and implement additional controls appropriate to their deployment context and regulatory environment.

The acceptable risk level for this reference implementation is: **LOW to MEDIUM**. Risks rated MEDIUM are acceptable provided mitigations are documented and in-progress. No HIGH-rated risks are acceptable without immediate remediation.

---

## Human Oversight Mechanism

_NIST AI RMF MANAGE-4.1: Post-deployment monitoring and human oversight._

The agent's output is a single numeric value (age in days) derived from a date of birth provided by the user. Human oversight is straightforward:

1. **Verification by inspection.** Any user can independently verify the agent's output by calculating the date difference using a calendar or date calculator.
2. **Correction mechanism.** The user can immediately correct the agent by providing a different date or reformatting an ambiguous input. The agent handles clarification requests gracefully.
3. **Operator override.** The agent can be stopped at any time by typing `exit`, `quit`, or `q` in the REPL. When deployed via AgentCore, the runtime can be paused or decommissioned via the AWS console or CLI.
4. **No autonomous actions.** The agent does not take actions on behalf of the user beyond returning a text response. It cannot write files, call external APIs, or modify system state. Human intervention is never required to prevent an autonomous action.

---

## Review Cadence

_NIST AI RMF GOVERN-1.4: Documented risk management process._

This system card and the associated risk register and governance charter must be reviewed and updated when any of the following conditions occur:

1. A new dependency is added, removed, or upgraded in `requirements.txt`
2. The agent's model ID or model provider is changed
3. A new `@tool` function is added to the agent (expands the capability and risk surface)
4. A security incident or unexpected agent behaviour is observed in production or testing
5. A new epic or story materially changes the agent's data flows, tool surface, or deployment configuration
6. Annually, regardless of changes, as a scheduled review

The system card version should be updated by adding a dated comment to the Change Log section below when substantive changes are made.

---

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-20 | Initial system card created as part of Epic 4, Story 4.1 | Paul |

---

_This document supports NIST AI RMF functions **GOVERN** (subcategories 1.1, 1.3, 1.4, 6.1) and **MAP** (subcategories 1.1, 2.2)._

_Reference: NIST AI 100-1 (AI RMF 1.0), NIST AI 600-1 (Generative AI Profile, July 2024)._
