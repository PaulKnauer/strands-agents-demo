---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'NIST AI RMF considerations for AI agents on AWS AgentCore with Strands SDK'
research_goals: 'Understand what NIST AI RMF requires/recommends for AI agents and how those considerations could be implemented in the strands-agents-demo project as a new phase'
user_name: 'Paul'
date: '2026-03-19'
web_research_enabled: true
source_verification: true
---

# NIST AI RMF for Production AI Agents: A Practical Technical Research Report for Strands Agents SDK + AWS AgentCore

**Date:** 2026-03-20
**Author:** Paul
**Research Type:** Technical

---

## Executive Summary

The NIST AI Risk Management Framework (AI RMF 1.0) is a voluntary, technology-agnostic governance framework organised around four functions — GOVERN, MAP, MEASURE, and MANAGE — that together create a continuous risk lifecycle for AI systems. It does not prescribe specific tools or code patterns; instead it defines the *outcomes* that organisations must achieve. For AI agent systems, the most directly applicable document is **NIST AI 600-1** (the Generative AI Profile, July 2024), which maps twelve generative AI-specific risk categories — including prompt injection, hallucination, and data poisoning — to AI RMF sub-category controls.

The `strands-agents-demo` project is well-positioned for NIST AI RMF alignment. The Strands Agents SDK provides a five-layer guardrail architecture (lifecycle hooks, steering handlers, Bedrock Guardrails, AgentCore Policy, and Agent Control) that maps cleanly onto all four NIST functions. AWS AgentCore provides the observability, identity, session isolation, and version management capabilities that NIST MEASURE and MANAGE require. The gap is not in the available tooling — it is in the absence of compliance infrastructure: no governance documentation, no audit logging, no guardrails, no automated safety testing.

A new compliance phase can close all four NIST function gaps in approximately 25 hours of engineering work at under $10/month in incremental AWS cost. The work decomposes into five concrete deliverables: foundation governance documentation, structured audit hooks, Bedrock Guardrails provisioning, automated red-team CI testing, and a CloudWatch compliance dashboard. Critically, none of these changes modify the agent's business logic — they attach to the agent via Strands hooks and the BedrockModel guardrail configuration, keeping risk controls in a separate `compliance/` layer.

**Key Technical Findings:**

- NIST AI RMF is outcome-based, not tool-prescriptive. The framework tells you *what* to control; the Strands SDK + AgentCore stack tells you *how*.
- The Strands hook event taxonomy (`BeforeInvocationEvent` through `AfterInvocationEvent`) covers every NIST control attachment point in the agent request lifecycle.
- The `ApplyGuardrail` API can be called independently at any pipeline point, producing structured compliance evidence in its `assessments` response block — but this data must be explicitly persisted by application code.
- NIST AI RMF MANAGE 4.1 requires human-override mechanisms. Strands implements this via `InterruptException` raised inside a `BeforeInvocationEvent` hook.
- NIST agent-specific technical standards are still forming — the NIST AI Agent Standards Initiative launched February 2026, with technical overlays in-progress. The framework's directional requirements are clear; specific prescriptions are not yet finalised.
- Promptfoo provides NIST AI RMF-mapped automated red-team test plugins (`excessive-agency`, `prompt-injection`, `pii:direct`, `harmful:hate`) suitable for CI integration.

**Top Technical Recommendations:**

1. Create Phase 1 foundation documentation first (`ai-system-card.md`, `risk-register.md`) — these are zero-cost, define the risk boundary, and are required before any tooling decisions.
2. Implement audit hooks as a `HookProvider` in a separate `compliance/` directory — one line addition to `create_agent()`, zero impact on business logic.
3. Provision Bedrock Guardrails via CloudFormation — two env vars in `.env.example`, no enforcement code.
4. Add promptfoo red-team and deterministic pytest boundary tests to CI — evidence of NIST MEASURE compliance generated automatically on every merge.
5. Track the NIST AI Agent Standards Initiative — technical overlays and agent-specific prescriptive guidance are expected from NIST in 2026; the current architecture will accommodate them without structural rework.

---

## Table of Contents

1. [Technical Research Introduction and Methodology](#1-technical-research-introduction-and-methodology)
2. [NIST AI RMF Technical Landscape and Architecture Analysis](#2-nist-ai-rmf-technical-landscape-and-architecture-analysis)
3. [Integration and Control Pipeline Patterns](#3-integration-and-control-pipeline-patterns)
4. [Architectural Design for NIST-Aligned Agent Systems](#4-architectural-design-for-nist-aligned-agent-systems)
5. [Implementation Approaches and Phased Roadmap](#5-implementation-approaches-and-phased-roadmap)
6. [Security and Compliance Considerations](#6-security-and-compliance-considerations)
7. [Future Technical Outlook](#7-future-technical-outlook)
8. [Strategic Recommendations for strands-agents-demo](#8-strategic-recommendations-for-strands-agents-demo)
9. [Source References](#9-source-references)

---

## 1. Technical Research Introduction and Methodology

### Research Significance

AI agents operating in production — autonomously calling tools, handling user input, generating responses — introduce risk categories that traditional software systems do not. Unlike a deterministic API, an agent's behaviour is partially emergent: shaped by a language model, a system prompt, and a tool surface, but not fully predictable from those inputs alone. This non-determinism is precisely what NIST AI RMF was designed to address.

The timing is significant. AWS AgentCore reached general availability in 2025, giving the Strands + AgentCore stack a credible production path. Simultaneously, NIST launched its AI Agent Standards Initiative in February 2026, formally acknowledging that the existing AI RMF 1.0 requires extensions for agentic systems. Early adopters who build NIST alignment into their architecture now will require no structural rework when those extensions are published.

For `strands-agents-demo` specifically, NIST AI RMF alignment serves a dual purpose: it makes the demo more credible as a production reference for regulated industries, and it demonstrates an emerging best practice that few existing Strands reference implementations show.

### Research Methodology

- **Scope:** NIST AI RMF 1.0, NIST AI 600-1 (Generative AI Profile), NIST IR 8596 (draft), NIST AI Agent Standards Initiative; mapped to Strands Agents SDK and AWS AgentCore capabilities
- **Data Sources:** NIST official publications, AWS official documentation and sample repositories, Strands SDK documentation and GitHub, peer-reviewed third-party analyses (Enkrypt AI, CSA, Arize AI, Promptfoo)
- **Analysis Framework:** Four-function NIST AI RMF structure (GOVERN, MAP, MEASURE, MANAGE) mapped to concrete software components and API calls
- **Confidence Framework:** High (official documentation), Medium (inferred mappings or in-progress standards), Low (speculative)
- **Date of Research:** 2026-03-19 to 2026-03-20

### Research Goals Achieved

**Original goal:** Understand what NIST AI RMF requires/recommends for AI agents and how those considerations could be implemented in this project as a new phase.

**Achieved:**
- All four NIST AI RMF functions mapped to specific Strands SDK hooks, AWS APIs, and configuration patterns
- A five-phase, 25-hour implementation roadmap produced with concrete code patterns and file structures
- Known gaps and limitations documented (agent-specific standards still in-progress, guardrail audit data not auto-persisted, no native red-team tooling in AgentCore)
- Architectural separation of concerns pattern established: risk controls in `compliance/` layer, business logic in `agents/` — zero cross-dependency

---

## Technical Research Scope Confirmation

**Research Topic:** NIST AI RMF considerations for AI agents on AWS AgentCore with Strands SDK
**Research Goals:** Understand what NIST AI RMF requires/recommends for AI agents and how those considerations could be implemented in the strands-agents-demo project as a new phase

**Technical Research Scope:**

- Architecture Analysis - design patterns, frameworks, system architecture
- Implementation Approaches - development methodologies, coding patterns
- Technology Stack - languages, frameworks, tools, platforms
- Integration Patterns - APIs, protocols, interoperability
- Performance Considerations - scalability, optimization, patterns

**Research Methodology:**

- Current web data with rigorous source verification
- Multi-source validation for critical technical claims
- Confidence level framework for uncertain information
- Comprehensive technical coverage with architecture-specific insights

**Scope Confirmed:** 2026-03-19

---

## Technology Stack Analysis

### The NIST AI RMF: Framework Scope and Nature

NIST AI RMF 1.0 (released January 2023) is a **voluntary, technology-agnostic governance framework**. It does not prescribe specific programming languages, SDKs, or developer tools — it defines *what* risk categories must be managed, not *how* to implement them. The framework targets governance teams, CISOs, and technical architects. NIST is actively developing agent-specific overlays (in-progress as of 2026) and has issued two RFIs specifically on AI agent security and identity/authorization.

_Confidence: High_
_Source: [NIST AI RMF Homepage](https://www.nist.gov/itl/ai-risk-management-framework), [NIST AI 100-1](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf)_

### The Four Core Functions and Their Technical Implications

**GOVERN** (cross-cutting — infused into all other functions):
- Establish policies, roles, and accountability for AI risk
- Document legal/regulatory compliance (GOVERN 1.1)
- Define organisational risk tolerance (GOVERN 1.3)
- Manage third-party/supply-chain AI risk

**MAP** (risk identification — before and during deployment):
- Document intended use cases, deployment contexts, and user populations
- Categorise AI system capabilities and limitations
- Identify risks across all system components (data, model, tooling, APIs)

**MEASURE** (quantitative/qualitative risk analysis):
- Select and apply metrics for trustworthiness, safety, security, fairness, privacy
- MEASURE 2.11 specifically requires evaluation of fairness and bias
- Establish continuous monitoring (benchmarking, red-teaming, evaluation datasets)

**MANAGE** (risk response and operational continuity):
- Prioritise and treat mapped/measured risks
- MANAGE 4.1 requires: post-deployment monitoring, appeal/override mechanisms, decommissioning procedures, change management
- Maintain incident response and recovery plans

_Confidence: High_
_Source: [NIST AI RMF Playbook](https://www.nist.gov/itl/ai-risk-management-framework/nist-ai-rmf-playbook), [NIST AI RMF Core Functions](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)_

### Agent-Specific Controls: NIST AI 600-1 and Emerging Guidance

**NIST AI 600-1** (released July 2024) is the *Generative AI Profile* — the most directly applicable document. It maps 12 generative AI-specific risk categories to AI RMF sub-category controls, including:
- Prompt injection
- Data poisoning
- Confabulation / hallucination
- Harmful content generation

**Core technical controls implied for agentic AI systems** (from NIST AI 600-1, MAESTRO threat model Feb 2025, and CSA AAGATE governance platform):
- Authentication and authorisation for every agent-to-tool interaction
- Comprehensive audit logging of all decisions and tool invocations
- Human oversight: appeal and override mechanisms (MANAGE 4.1)
- Prompt injection defences: input/output validation at every step
- Sandboxed tool execution to limit blast radius
- Continuous behavioural monitoring and anomaly detection

_Confidence: High for NIST AI 600-1; Medium for agent-specific controls (NIST overlays still in-progress)_
_Source: [NIST AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf), [CSA: AAGATE](https://cloudsecurityalliance.org/blog/2025/12/22/aagate-a-nist-ai-rmf-aligned-governance-platform-for-agentic-ai), [Nemko Digital](https://digital.nemko.com/news/ai-agent-standards-navigating-new-nist-governance)_

### AWS AgentCore: RMF-Relevant Platform Capabilities

AWS Bedrock AgentCore provides technical capabilities that directly support NIST AI RMF functions, even though AWS does not publish an explicit NIST AI RMF control mapping:

**Observability (MEASURE + MANAGE):**
- OpenTelemetry (OTEL) compliant — traces the complete decision and tool invocation chain
- Integrates with platforms like Arize AX for agent metrics dashboards
- CloudWatch dashboards track guardrail invocations and block rates

**Security (GOVERN + MAP):**
- IAM roles for fine-grained agent-to-tool permissions
- VPC support for network isolation
- Token vault for secure credential management (AgentCore Identity)
- SOC, ISO 27001, and HIPAA compliance certifications

**Responsible AI pattern (MEASURE + MANAGE):**
- The `aws-samples/sample-agentcore-rai-strands-agents` reference repository demonstrates:
  - Bedrock Guardrails for content safety filtering and PII/credential redaction
  - AWS CDK for IaC deployment of guardrail configurations
  - AWS Parameter Store for dynamic guardrail configuration
  - Per-agent customised guardrail profiles

_Confidence: Medium — AgentCore capabilities are well-documented; explicit NIST RMF mapping is inferred, not officially published by AWS_
_Source: [AWS Sample: AgentCore RAI with Strands](https://github.com/aws-samples/sample-agentcore-rai-strands-agents), [Arize AI: AgentCore Observability](https://arize.com/blog/aws-bedrock-agentcore-observability-operationalizing-ai-agents-at-scale/)_

### Strands Agents SDK: Guardrail Architecture

Strands provides a five-layer safety architecture that maps to NIST AI RMF functions:

| Layer | Mechanism | NIST Mapping |
|---|---|---|
| 1 | Lifecycle hooks (non-invasive observability) | MEASURE — continuous monitoring |
| 2 | Steering handlers (corrective guidance) | MANAGE — override mechanisms |
| 3 | Amazon Bedrock Guardrails (content, PII, prompt injection) | MEASURE + MANAGE |
| 4 | AgentCore Policy (declarative tool access control) | GOVERN — policy enforcement |
| 5 | Agent Control / Galileo (central rules engine, Deny + Steer modes) | GOVERN + MANAGE |

Bedrock Guardrails integration requires minimal code change:
```python
bedrock_model = BedrockModel(
    model_id=BEDROCK_MODEL_ID,
    guardrail_id=GUARDRAIL_ID,
    guardrail_version=GUARDRAIL_VERSION,
)
```
Guardrail capabilities include: violent/harmful content filtering, prompt attack detection, denied topics, PII redaction (email, phone, SSN, credentials), custom word filters, and hallucination/grounding checks.

_Confidence: High_
_Source: [Strands Agents: Runtime Guardrails](https://strandsagents.com/blog/strands-agents-with-agent-control/), [DEV.to: Bedrock Guardrails with Strands](https://dev.to/aws-builders/add-guardrails-to-your-strands-agent-in-zero-time-with-amazon-bedrock-guardrails-1gam)_

### NIST AI RMF → AWS/Python Tooling Control Mapping

| NIST AI RMF Function | Control Area | AWS/Python Tooling |
|---|---|---|
| GOVERN | Policy enforcement, access control | AgentCore Policy, IAM roles |
| GOVERN | Third-party risk management | AWS CDK IaC, Parameter Store |
| MAP | Threat/risk identification | OWASP Top 10 for LLMs, MITRE ATLAS |
| MAP | System capability documentation | Strands tool registry, MCP |
| MEASURE | Continuous monitoring + tracing | AgentCore OTEL, CloudWatch |
| MEASURE | Safety and bias evaluation | Bedrock Guardrails (content, grounding) |
| MANAGE | Incident response + override | Strands steering handlers |
| MANAGE | PII/sensitive data protection | Bedrock Guardrails PII redaction |
| MANAGE | Audit logging | CloudWatch dashboards, OTEL spans |
| MANAGE | Change management | AWS CDK, Parameter Store |

**Important caveat:** NIST AI RMF does not mandate specific tools. This mapping represents best-practice alignment between NIST risk management outcomes and available AWS/Python tooling — not formal NIST certification.

_Source: [NIST AI Resource Center](https://airc.nist.gov/airmf-resources/airmf/), [ActiveFence: AI Risk Frameworks](https://www.activefence.com/blog/ai-risk-management-frameworks-nist-owasp-mitre-atlas-iso/), [Giskard: OWASP, MITRE ATLAS, NIST AI RMF](https://www.giskard.ai/knowledge/risk-assessment-for-llms-and-ai-agents-owasp-mitre-atlas-and-nist-ai-rmf-explained)_

## Integration Patterns Analysis

### Agent Lifecycle Control Attachment Points

NIST's AI Agent Standards Initiative (launched February 2026) has identified five priority threat vectors requiring pipeline hook points: prompt injection, data poisoning, excessive write access, interaction with untrusted internet resources, and privilege escalation. Monitoring must span five concurrent domains: functionality, operational performance, security posture, compliance adherence, and human factors/anomaly detection.

Auditability requirements mandate records spanning: prompt instructions, retrieved context, tool invocations, approvals, execution results, and rollback activities — the full agent "thought chain."

_Confidence: High (directional); Medium (specific prescriptions still forming)_
_Source: [NIST AI Agent Standards Initiative](https://www.nist.gov/caisi/ai-agent-standards-initiative), [MetricStream: What CISOs Need to Know](https://www.metricstream.com/blog/nists-ai-agent-standards-initiative.html)_

### Bedrock Guardrails API Integration Pattern

The `ApplyGuardrail` API (`POST /guardrail/{id}/version/{version}/apply`) can be called independently at any pipeline point — not only on model invocations. This is the core mechanism for NIST GOVERN/MANAGE control injection.

**Three-point pipeline injection pattern:**
```
User Input
  → ApplyGuardrail(source=INPUT)     ← control point 1: input validation
  → [LLM Inference via Converse API]
  → ApplyGuardrail(source=OUTPUT)    ← control point 2: output validation
  → User
```

**Response outcomes and handling:**
- `NONE` — content clean, pass through
- `GUARDRAIL_INTERVENED` + masked text — PII redacted, continue with sanitised content
- `GUARDRAIL_INTERVENED` + canned message — policy violation, halt and return refusal

**Six policy types producing structured audit data per call:** Content Filters (with confidence levels), Denied Topics, PII Redaction (BLOCKED/ANONYMIZED per entity type), Custom Regexes, Contextual Grounding (grounding/relevance scores vs thresholds), and Automated Reasoning Checks (formal logic-based hallucination detection).

**Critical gap:** The `assessments` response block is structured but not auto-persisted. Application code must explicitly route it to CloudWatch Logs or an audit store for NIST MANAGE 4.3 compliance.

_Confidence: High — production AWS API documentation_
_Source: [ApplyGuardrail API](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-use-independent-api.html), [Associate guardrail with agent](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-guardrail.html), [How Bedrock Guardrails works](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-how.html)_

### Strands Hooks: Complete Pipeline Event Taxonomy

Strands `HookProvider` is the primary integration surface for attaching NIST controls without modifying core agent logic:

| Hook Event | Pipeline Position | NIST Control Use |
|---|---|---|
| `AgentInitializedEvent` | Agent startup | Load compliance config, initialise audit session |
| `BeforeInvocationEvent` | Pre-request | Input guardrail check, escalation trigger, PII scan |
| `MessageAddedEvent` | Per-message receipt | Audit log, memory sanitisation |
| `BeforeModelCallEvent` | Pre-LLM call | Token budget enforcement, prompt logging |
| `AfterModelCallEvent` | Post-LLM response | Cost tracking, response audit |
| `BeforeToolCallEvent` | Pre-tool execution | Tool authorisation gate, argument validation |
| `AfterToolCallEvent` | Post-tool execution | Result validation, side-effect audit |
| `AfterInvocationEvent` | Post-request completion | Full-cycle audit write, session summary |

**Human-in-the-loop escalation** uses `InterruptException` raised inside `BeforeInvocationEvent` or `BeforeToolCallEvent`:
```python
class ComplianceHooks(HookProvider):
    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeInvocationEvent, self.check_escalation)
        registry.add_callback(BeforeToolCallEvent, self.authorize_tool)
        registry.add_callback(AfterInvocationEvent, self.write_audit_log)
```
Multiple independent `HookProvider` instances compose on the same agent — compliance hooks stay separate from business logic.

_Confidence: High_
_Source: [Strands Hooks — dev.to](https://dev.to/sreeni5018/supercharge-your-aws-ai-agents-with-strands-hooks-2ppg), [Strands SDK GitHub](https://github.com/strands-agents/sdk-python)_

### OpenTelemetry Continuous Monitoring Integration

Strands has native OTel integration activated via `pip install 'strands-agents[otel]'`. Every agent run produces traces with spans for: LLM model calls (prompt, parameters, token counts, latency), tool invocations (name, input/output), and agent lifecycle events.

**NIST-relevant metrics derivable from OTel spans:**
- Tool invocation frequency per tool type
- Tool latency and success/failure rates
- Model call costs (token-based)
- Guardrail intervention rate
- Error rates per endpoint/tool

OTel backend connectors: AWS X-Ray, CloudWatch, Jaeger, Langfuse, Grafana, Opik — any OTel-compatible backend.

**AgentCore implicit audit points** (auto-configured CloudWatch logging):
- Authentication attempts and outcomes
- IAM/OAuth authorisation decisions
- Session lifecycle state transitions (ACTIVE → IDLE → TERMINATED)
- Outbound service call events
- Version deployments and rollbacks

_Confidence: High_
_Source: [Langfuse: Observability for Strands Agents](https://langfuse.com/integrations/frameworks/strands-agents), [OTel + Guardrails with MCP workflows](https://glama.ai/blog/2025-07-21-observability-and-governance-using-otel-guardrails-and-metrics-with-mcp-workflows)_

### Incident Response, Decommissioning and Change Management

**NIST MANAGE 4.1 and 2.4 control → AgentCore/Strands implementation mapping:**

| NIST Requirement | AgentCore/Strands Implementation |
|---|---|
| System bypass / decommissioning | `idleRuntimeSessionTimeout` + `maxLifetime` lifecycle config |
| Version history with rollback | AgentCore immutable versions; endpoint reversion |
| Session isolation for forensics | Each session runs in isolated microVM |
| Incident threshold → deactivation | `BeforeInvocationEvent` + `InterruptException`; `@app.ping` gating traffic |
| Change management / root cause | Version metadata in `CreateAgentRuntimeVersion`; CloudWatch logs per version |
| Red-teaming (MANAGE 4.1) | **Gap** — no native tooling; requires external test harness |

**Three-tier audit logging schema** (NIST MANAGE 4.3):
1. Decision logs — full reasoning chain with timestamps (OTel spans + `AfterInvocationEvent`)
2. Tool invocation logs — API calls, parameters, responses (`BeforeToolCallEvent` / `AfterToolCallEvent`)
3. Anomaly triggers — behavioral drift from baseline (CloudWatch Metrics Alarms on OTel metrics)

**Change management gap:** NIST requires documenting upstream/downstream consequences before deactivating an agent. This has no native AWS API support — must be implemented as a required CI/CD pipeline approval gate before `UpdateAgentRuntime`.

_Confidence: High for NIST requirements and AgentCore APIs; Medium for specific mapping_
_Source: [NIST AIRC Playbook — MANAGE](https://airc.nist.gov/airmf-resources/playbook/manage/), [AgentCore lifecycle settings](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-lifecycle-settings.html), [AgentCore runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-how-it-works.html)_

### Complete Control Pipeline Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  INBOUND REQUEST                                                  │
│  User ──→ AgentCore Auth (OAuth/IAM)    ← GOVERN: identity/access │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│  STRANDS AGENT PIPELINE                                           │
│                                                                   │
│  AgentInitializedEvent    ← load compliance config, audit init    │
│  BeforeInvocationEvent    ← ApplyGuardrail(INPUT), HITL escalate  │
│  MessageAddedEvent        ← memory sanitisation, audit entry      │
│  BeforeModelCallEvent     ← prompt logging, token budget          │
│  [LLM Inference]                                                  │
│  AfterModelCallEvent      ← cost tracking, response audit         │
│  BeforeToolCallEvent      ← tool auth gate, arg validation        │
│  [Tool Execution]                                                 │
│  AfterToolCallEvent       ← result validation, side-effect audit  │
│  AfterInvocationEvent     ← ApplyGuardrail(OUTPUT), write audit   │
│                             emit OTel spans                        │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│  CONTINUOUS MONITORING                                            │
│  CloudWatch Metrics  ← OTel spans (tools, latency, guardrails)   │
│  CloudWatch Alarms   ← threshold breaches → SNS → incident       │
│  CloudTrail          ← AgentCore control plane API calls          │
│  X-Ray / Langfuse    ← full audit trail per NIST MANAGE 4.3      │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│  LIFECYCLE / CHANGE MANAGEMENT                                    │
│  AgentCore versions  ← immutable; rollback via endpoint reversion │
│  lifecycleConfig     ← idleTimeout + maxLifetime                  │
│  CI/CD approval gate ← change management before UpdateAgentRuntime│
└──────────────────────────────────────────────────────────────────┘
```

### Known Gaps and Limitations

1. **NIST agent standards still forming** — NIST AI Agent Standards Initiative RFI closed March 9, 2026; technical overlays not yet published.
2. **`BeforeInvocationEvent` SDK version dependency** — verify installed SDK version exposes `event.user_input`; older versions require `MessageAddedEvent` workaround.
3. **AgentCore has no termination callback** — `maxLifetime` is silent; forensic preservation (NIST MANAGE 2.4) requires proactive logging throughout, not at termination.
4. **Guardrail audit data is not auto-persisted** — `assessments` blocks must be explicitly routed to CloudWatch or an audit store.
5. **Red-teaming has no native tooling** — requires an external test harness or CI/CD test suite.

## Architectural Patterns and Design

### System Architecture Patterns

The dominant pattern across AWS guidance and NIST-aligned implementations is a **four-layer vertically integrated stack** where each layer has a defined interface and a single responsibility:

```
┌──────────────────────────────────────────────────────┐
│  GOVERNANCE LAYER (Policy Engine)                    │
│  Risk tolerance config, accountability rules,        │
│  escalation thresholds — lives in code, not docs     │
├──────────────────────────────────────────────────────┤
│  ORCHESTRATION LAYER (Planner / Workflow Engine)     │
│  Task decomposition, subagent delegation,            │
│  event-based coordination, human-in-the-loop gates   │
├──────────────────────────────────────────────────────┤
│  EXECUTION LAYER (Tool Registry + Agent Runtime)     │
│  Tool invocation, credential management,             │
│  sandboxed execution, MCP/A2A protocol adapters      │
├──────────────────────────────────────────────────────┤
│  OBSERVABILITY LAYER (Telemetry Fabric)              │
│  OpenTelemetry spans, tamper-evident audit logs,     │
│  CloudWatch metrics, anomaly detection               │
└──────────────────────────────────────────────────────┘
```

**NIST functions map to distinct codebase components** — this is the key architectural insight for keeping risk controls from tangling with business logic:

| NIST Function | Software Component | Contents |
|---|---|---|
| **Govern** | Policy Engine / Config Layer | Risk thresholds, accountability rules, tool access policies as executable code |
| **Map** | System Inventory / Registry | Agent metadata, tool inventory, sensitivity tags, dependency graphs |
| **Measure** | Monitoring Pipeline | Automated drift/latency/output metrics + human-in-the-loop quality review |
| **Manage** | Response Orchestrator | Incident playbooks, mitigation routing, feedback loops back into governance |

_Confidence: High_
_Source: [NIST AI RMF: Agentic AI with NIST AI RMF (CloudMatos)](https://www.cloudmatos.ai/blog/aegis-aligning-agentic-ai-with-nist-ai-rmf/), [AWS Prescriptive Guidance: Agentic AI Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-patterns/introduction.html)_

### Design Principles and Best Practices

Six consolidated design principles for a NIST-aligned agent codebase:

1. **Risk controls live in the fabric, not the tools.** The agent↔tool boundary (AgentCore Gateway + Strands hooks) is the single enforcement point. Business logic tools have zero knowledge of compliance requirements.

2. **Policy is executable code, not documents.** Risk tolerance thresholds, tool allowlists, and escalation rules are configuration artifacts under version control, tested in CI, deployed with shadow mode before enforcement.

3. **Every function call produces a traceable span.** Telemetry is the evidence layer required by NIST Detect and Respond. Target: 100% of agent→tool calls traced with `agent_id`, `tool_id`, `policy_version`, `decision_reason`.

4. **Governance roles map to IAM principals.** Agent Owner (business stakeholder), Agent Operator (runtime on-call), and Agent Auditor (compliance, read-only audit trail) are distinct IAM roles — not job titles.

5. **Shadow mode before enforcement.** New policies run in would-deny mode first, tuning signal-to-noise before hard enforcement flip. This builds NIST evidence of policy testing.

6. **Horizontal scalability without governance drift.** New specialist agents register in the Agent Registry, inherit guardrail fabric via hooks automatically, and add no new enforcement code.

_Confidence: High_
_Source: [AI Agent Governance Architecture (Hendricks AI)](https://hendricks.ai/insights/ai-agent-governance-architecture), [NIST AI RMF Practical Implementation Guide (Swept AI)](https://www.swept.ai/post/nist-ai-rmf-implementation-guide)_

### Scalability and Performance Patterns

Three horizontal scalability patterns with distinct risk profiles:

**Pattern 1 — Hierarchical Delegation (Agents as Tools):**
Supervisor orchestrator routes to specialist sub-agents. New specialists added without modifying the orchestrator. Orchestrator owns planning risk controls; specialists own domain-specific tool risk controls. Maps cleanly to NIST separation of concerns.

**Pattern 2 — Parallel Swarm with Convergence:**
Multiple agents work concurrently, converging on synthesised output. Convergence layer applies conflict resolution and output guardrails. Bias detection lives at the convergence point.

**Pattern 3 — Graph-Structured Workflows:**
Deterministic DAG with pre-defined information pathways. Access validation and DLP nodes are explicit graph vertices — not bolted on, but structural. Highest auditability: every edge transition is a logged event.

**Operational readiness thresholds** (from Aegis reference implementation):
- Policy coverage: ≥80% of critical tools have enforced policies
- Decision latency (P99): ≤20ms for inline enforcement
- Telemetry completeness: 100% of agent→tool calls produce a traceable span
- Shadow-mode conversion: ≥90% of policies tuned in shadow mode before enforcement flip

_Confidence: High_
_Source: [Building Responsible Agentic AI Architecture](https://www.architectureandgovernance.com/applications-technology/building-responsible-agentic-ai-architecture/), [Strands Agents SDK Technical Deep Dive (AWS Blog)](https://aws.amazon.com/blogs/machine-learning/strands-agents-sdk-a-technical-deep-dive-into-agent-architectures-and-observability/)_

### Security Architecture Patterns

**The Four-Ring Guardrail Model** — each ring operates independently; failure in one does not cascade:

```
User Request
  → INPUT RING:        PII detection, prompt injection filter, intent classification
  → ORCHESTRATION:     Policy authorisation, HITL gates
  → TOOL/EXECUTION:    API parameter validation, sandboxed containers, circuit breakers
  → OUTPUT RING:       Hallucination detection, toxicity filter, bias check, data exfil scan
  → User Response
  (all rings emit telemetry throughout to Monitoring Layer)
```

**Control Plane / Data Plane separation** (Aegis pattern, NIST-aligned):

- **Control Plane** (offline, low-frequency): Policy authoring, version management, token issuance, approval workflows, shadow mode testing with signed policy manifests
- **Data Plane** (inline, ultra-low-latency): Decision enforcement via sidecars/proxies, prepared query caching for ≤20ms P99, optional WASM Rego compilation

**Deployment sequence for risk controls:**
1. Shadow mode — policies emit metrics without blocking
2. Approval-gated enforcement — high-risk actions require HITL
3. Automatic enforcement — low-risk policies block inline

Seven risk vectors and their architectural control locations:

| Vector | Architectural Control Ring |
|---|---|
| Governance / goal misalignment | Planning ring + policy engine |
| Output quality / hallucination | Output ring + measure pipeline |
| Tool misuse / supply-chain | Tool ring + dependency scanner |
| Privacy / data exposure | Input ring + output ring |
| Reliability / concept drift | Monitoring layer + measure pipeline |
| Agent behavior / manipulation | Input ring + HITL gate |
| Access control / privilege escalation | Tool ring + identity service |

_Confidence: High_
_Source: [Securing AI Agents: Comprehensive Framework for Guardrails (Enkrypt AI)](https://www.enkryptai.com/blog/securing-ai-agents-a-comprehensive-framework-for-agent-guardrails)_

### Data Architecture Patterns

**Three-tier audit logging schema** (required by NIST MANAGE 4.3 for full reasoning chain evidence):

1. **Decision logs** — full reasoning chain with timestamps; OTel spans enriched with `agent_id`, `tool_id`, `policy_version`, `decision_reason`, cryptographic attestation
2. **Tool invocation logs** — API calls, parameters, responses; `BeforeToolCallEvent` / `AfterToolCallEvent` hooks; append-only or hash-chained format
3. **Anomaly triggers** — behavioral drift from baseline; CloudWatch Metrics Alarms on OTel-derived metrics

**Evidence artifact storage by NIST function:**

| Function | Evidence Artifact | Storage Pattern |
|---|---|---|
| Govern | Signed policy manifests, accountability playbooks | CodeCommit + S3 |
| Map | Agent registry exports, tool inventory CSVs with metadata timestamps | S3 + versioning |
| Measure | Time-series dashboards, shadow-mode conversion metrics | CloudWatch Metrics |
| Manage | Approval records, replayable span bundles, incident trace replays | S3 + Athena queryable |

_Confidence: High_
_Source: [AI Agent Governance Architecture (Hendricks AI)](https://hendricks.ai/insights/ai-agent-governance-architecture), [NIST AI RMF Playbook — MANAGE](https://airc.nist.gov/airmf-resources/playbook/manage/)_

### Deployment and Operations Architecture

**AgentCore six managed capabilities and their NIST function:**

| AgentCore Capability | NIST RMF Function |
|---|---|
| Runtime (serverless, session isolation, tasks up to 8h) | Manage |
| Memory (persistent context, semantic/episodic tiers) | Map (lineage) |
| Identity (enterprise IdP integration: Okta, Azure AD, Cognito) | Govern / Protect |
| Gateway (unified tool connectivity: APIs, Lambda, MCP) | Govern / Map |
| Observability (CloudWatch + OTel metrics/logs/traces) | Measure |
| Evaluation (pre-deploy testing + continuous quality monitoring) | Measure |

**Reference codebase decomposition for a NIST-aligned Strands/AgentCore project:**

```
policies/                ← Governance plane: risk thresholds, tool allowlists
agents/orchestrator/     ← Orchestration: routing, HITL gates, planning guards
agents/specialists/      ← Business logic ONLY; system prompt = behavioral policy
guardrails/              ← Guardrail fabric: hooks, input/output filters, RBAC
  hooks/compliance.py    ← Strands HookProvider implementations
  bedrock_guardrails.py  ← ApplyGuardrail call wrapper + audit persistence
observability/           ← OTel config, CloudWatch alarms, incident playbooks
deploy/                  ← IaC (CDK/AgentCore CLI), CI/CD with approval gates
```

The critical structural rule: `agents/specialists/` has **no imports from `guardrails/`**. Controls are injected by the fabric, not called by business logic.

_Confidence: High_
_Source: [Architecting Enterprise-Grade Multi-Agent AI with Strands + AgentCore](https://dev.to/sreeni5018/architecting-enterprise-grade-multi-agent-ai-with-aws-strands-amazon-bedrock-agentcore-4o93), [AI Agents in Enterprises: Best Practices with AgentCore (AWS Blog)](https://aws.amazon.com/blogs/machine-learning/ai-agents-in-enterprises-best-practices-with-amazon-bedrock-agentcore/)_

## Implementation Approaches and Technology Adoption

### Technology Adoption Strategy

The phased adoption approach maps directly to the four NIST AI RMF functions, ordered by dependency:

| Phase | NIST Functions | Key Deliverable | Effort |
|---|---|---|---|
| 1 — Foundation docs | GOVERN + MAP | `ai-system-card.md`, `risk-register.md`, `governance-charter.md` | ~8 hrs |
| 2 — Audit hooks | MEASURE | `compliance/hooks.py` + JSONL audit log | ~4 hrs |
| 3 — Bedrock Guardrails | MANAGE | `deploy/guardrail.yaml` + env wiring | ~3 hrs |
| 4 — Red-team CI | MEASURE | `compliance/promptfoo-redteam.yaml` + CI safety job | ~6 hrs |
| 5 — Dashboard | MEASURE + MANAGE | CloudWatch compliance dashboard | ~4 hrs |
| **Total** | All 4 functions | Full NIST AI RMF coverage for a demo | **~25 hrs** |

Estimated incremental AWS cost at demo scale: **under $10/month**.

_Confidence: High_
_Source: [NIST AI RMF Playbook](https://airc.nist.gov/docs/AI_RMF_Playbook.pdf), [AI Governance Framework Adoption — CSA](https://cloudsecurityalliance.org/blog/2026/01/27/ai-governance-framework-adoption-in-cloud-native-ai-systems-phased-approach-and-considerations)_

### Phase 1: Foundation Documentation (GOVERN + MAP)

No code — produces the artifacts all later phases reference.

**`docs/ai-system-card.md`** — system-scoped analogue of a model card:
- System purpose and intended users
- Out-of-scope uses
- Third-party components (Strands SDK, Bedrock, AgentCore)
- Data flows (what enters and exits the agent)
- Harm categories considered with likelihood/severity ratings
- Risk tolerance statement
- Human oversight mechanism
- Review cadence

**`docs/risk-register.md`** — minimal tabular risk register:

| ID | Risk | Likelihood | Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|
| R-1 | Prompt injection | LOW | LOW | Narrow tool surface; guardrails | Dev | Open |
| R-2 | Incorrect date calculation | LOW | LOW | Unit tests on `get_today_date` | Dev | Open |
| R-3 | Model provider outage | MEDIUM | MEDIUM | Multi-provider env var switching | Dev | Open |
| R-4 | PII in user prompt | LOW | MEDIUM | Bedrock Guardrails PII filter | Dev | Open |
| R-5 | Hallucinated "today" date | LOW | LOW | Tool call forced by system prompt | Dev | Open |

**`docs/governance-charter.md`** — one-page statement of accountability, risk tolerance, and review cadence. Establishes the audit trail even for a single-developer project.

_Confidence: High_
_Source: [NIST AI RMF 1.0 — GOVERN subcategories](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf)_

### Phase 2: Audit Hooks Implementation (MEASURE)

A `compliance/hooks.py` module implementing `HookProvider` wires into the existing `create_agent()` function with a single line change. No core agent logic is modified.

**Hook events registered:** `BeforeInvocationEvent`, `AfterInvocationEvent`, `BeforeToolCallEvent`, `AfterToolCallEvent`, `MessageAddedEvent`.

**Output:** Structured JSONL audit trail (`audit_log.jsonl`):
```json
{"event": "invocation_start", "invocation_id": "a3f1...", "session_id": "b9e2...", "timestamp": "2026-03-20T14:30:01Z"}
{"event": "tool_call_start", "invocation_id": "a3f1...", "tool_name": "get_today_date", "tool_input": {}}
{"event": "tool_call_end", "invocation_id": "a3f1...", "tool_name": "get_today_date", "result_snippet": "2026-03-20"}
{"event": "invocation_end", "invocation_id": "a3f1...", "duration_seconds": 1.234}
```

**Wire-in to `agent.py`:**
```python
from compliance.hooks import AuditLoggingHook

def create_agent():
    ...
    return Agent(
        model=model,
        tools=[get_today_date],
        system_prompt=SYSTEM_PROMPT,
        hooks=[AuditLoggingHook()],  # NIST MEASURE-2.5 / MANAGE-2.4
    )
```

JSONL can be shipped to CloudWatch Logs via Python's `logging` module CloudWatch handler, or tailed by any OTel-compatible backend.

_Confidence: High_
_Source: [Strands Agents Hooks — DEV Community](https://dev.to/sreeni5018/supercharge-your-aws-ai-agents-with-strands-hooks-2ppg), [Strands SDK Hooks Events Reference](https://strandsagents.com/latest/documentation/docs/api-reference/python/hooks/events/)_

### Phase 3: Bedrock Guardrails (MANAGE)

Provision via CloudFormation (`deploy/guardrail.yaml`) with:
- `HATE` / `VIOLENCE` content filters at HIGH strength
- `PROMPT_ATTACK` filter at HIGH strength
- PII entities (EMAIL, PHONE) set to ANONYMIZE

Attach to the agent — zero additional enforcement logic required:
```python
model = BedrockModel(
    model_id=os.environ["MODEL_ID"],
    guardrail_id=os.environ.get("GUARDRAIL_ID"),
    guardrail_version=os.environ.get("GUARDRAIL_VERSION"),
)
```

Add `GUARDRAIL_ID` and `GUARDRAIL_VERSION` to `.env.example`. CloudWatch automatically emits `GuardrailInvocations` and `GuardrailBlocks` metrics with no additional instrumentation.

_Confidence: High_
_Source: [Add Guardrails to Strands Agent (AWS Builders)](https://dev.to/aws-builders/add-guardrails-to-your-strands-agent-in-zero-time-with-amazon-bedrock-guardrails-1gam), [aws-samples/sample-agentcore-rai-strands-agents](https://github.com/aws-samples/sample-agentcore-rai-strands-agents)_

### Phase 4: Automated Red-Team Testing in CI (MEASURE)

**Tool: Promptfoo** — open-source, with NIST AI RMF plugin mapping built in.

**`compliance/promptfoo-redteam.yaml`** targets:
- `excessive-agency` (MEASURE 2.4 — safety)
- `prompt-injection`, `shell-injection` (MEASURE 2.7 — security)
- `pii:direct`, `pii:social` (MEASURE 2.8 — privacy)
- `harmful:hate`, `harmful:harassment-bullying` (MEASURE 2.11 — fairness)
- Strategies: `jailbreak` (multi-turn adversarial), `prompt-injection`
- CI threshold: 90% of probes must be blocked/handled correctly

**GitHub Actions CI job:** runs after unit tests, uploads `redteam-report.json` as a CI artifact (evidence trail), fails build if pass rate < 90%.

**Deterministic pytest boundary tests** (no external API calls required for fast CI):
- Prompt injection attempts must not leak system prompt content
- Agent tool surface must equal exactly `["get_today_date"]` — adding tools requires a risk register update

_Confidence: High_
_Source: [Promptfoo NIST AI RMF Red-Team Docs](https://www.promptfoo.dev/docs/red-team/nist-ai-rmf/), [Amazon Bedrock Guardrails Docs](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html)_

### Phase 5: Compliance Metrics Dashboard (MEASURE + MANAGE)

CloudWatch dashboard (`deploy/create_dashboard.py`) with two widgets:
1. **Guardrail Block Rate** — `GuardrailBlocks` vs `GuardrailInvocations` time series (NIST MEASURE-2.4)
2. **Tool Invocation Audit Trail** — CloudWatch Logs Insights query on the JSONL audit log (NIST MEASURE-2.5)

Dashboard name: `NIST-RMF-AgentCompliance`. No ongoing maintenance required once deployed.

_Confidence: High_
_Source: [AWS Bedrock CloudWatch metrics](https://docs.aws.amazon.com/bedrock/latest/userguide/monitoring-cloudwatch.html)_

### Complete Compliance File Structure

```
strands-agents-demo/
  compliance/
    __init__.py
    hooks.py                    # AuditLoggingHook HookProvider
    guardrails.py               # Guardrail config helpers
    promptfoo-redteam.yaml      # NIST-mapped red-team config
  deploy/
    guardrail.yaml              # CloudFormation for Bedrock Guardrail
    create_dashboard.py         # CloudWatch dashboard
  docs/
    ai-system-card.md           # GOVERN artifact
    risk-register.md            # MAP artifact
    governance-charter.md       # GOVERN artifact
  tests/
    test_safety_boundaries.py   # MEASURE-2.4/2.7 pytest tests
    test_hooks.py               # Unit tests for audit hook
  .github/workflows/
    ci.yml                      # Extended with safety-scan job
```

### Risk Assessment and Mitigation

Key implementation risks and mitigations:

| Risk | Mitigation |
|---|---|
| Hook adds latency to agent responses | Profile: hooks are async-safe and negligible (<1ms); JSONL writes are buffered |
| Guardrail false positives block valid date queries | Start with MEDIUM strength content filters; tune based on CloudWatch block rate metrics |
| Promptfoo CI adds cost via OpenAI API | Use deterministic pytest tests for fast CI; run promptfoo only on merge to main |
| `BeforeInvocationEvent` SDK version dependency | Pin `strands-agents` version; verify `event.user_input` accessibility in tests |
| Audit log grows unboundedly | Add log rotation to `AuditLoggingHook`; use CloudWatch log retention policy (e.g., 90 days) |

---

## 6. Security and Compliance Considerations

### NIST AI 600-1: The Twelve Generative AI Risk Categories

For LLM-based agents, NIST AI 600-1 (July 2024) adds twelve risk categories on top of the base AI RMF controls:

| Risk Category | Relevance to Age-in-Days Agent | Mitigation |
|---|---|---|
| Confabulation / hallucination | Agent could hallucinate today's date instead of calling the tool | System prompt forces tool call; `get_today_date` is the authoritative source |
| Prompt injection | User could attempt to override system prompt | `PROMPT_ATTACK` Bedrock Guardrail at HIGH strength |
| Data poisoning | Training data risk (model-level, not app-level) | Model selection via trusted AWS Bedrock providers only |
| Harmful content | User could send harmful requests | Content filters (HATE, VIOLENCE) at HIGH strength |
| Data privacy | PII in user prompts | PII redaction (EMAIL, PHONE) via Bedrock Guardrails |
| Information integrity | Agent could return date as authoritative fact for legal purposes | System card explicitly documents out-of-scope uses |
| Excessive agency | Agent could take unsanctioned actions | Tool surface limited to `get_today_date` only; tested in CI |

_Source: [NIST AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)_

### Complementary Frameworks

NIST AI RMF does not stand alone. Three complementary frameworks provide the technical specificity NIST deliberately avoids:

- **OWASP Top 10 for LLMs** — vulnerability checklists and mitigations; maps directly to Bedrock Guardrail policy types
- **MITRE ATLAS** — adversarial threat modeling for AI/ML systems; informs red-team test case design
- **MAESTRO** (CSA, February 2025) — threat modeling framework for agentic AI covering autonomous reasoning, tool use, and multi-agent coordination

_Source: [Giskard: OWASP, MITRE ATLAS, and NIST AI RMF](https://www.giskard.ai/knowledge/risk-assessment-for-llms-and-ai-agents-owasp-mitre-atlas-and-nist-ai-rmf-explained), [ActiveFence: AI Risk Frameworks](https://www.activefence.com/blog/ai-risk-management-frameworks-nist-owasp-mitre-atlas-iso/)_

### AWS Compliance Certifications

AgentCore inherits AWS's platform compliance certifications: SOC 1/2/3, ISO 27001, ISO 27017, ISO 27018, HIPAA. These do not constitute NIST AI RMF compliance — they address infrastructure security, not AI-specific risk management — but they satisfy the supply-chain risk management requirements in GOVERN 6.1 for the infrastructure layer.

_Source: [AWS Compliance Programs](https://aws.amazon.com/compliance/programs/)_

---

## 7. Future Technical Outlook

### NIST AI Agent Standards Initiative (February 2026)

NIST launched its AI Agent Standards Initiative with three pillars: industry-led technical standards, open-source interoperability protocols, and security/identity research. Two active RFIs closed in early 2026:
- AI Agent Security (March 9, 2026)
- AI Agent Identity and Authorization (April 2, 2026)

Virtual listening sessions are scheduled for April 2026. Technical overlays specific to single-agent and multi-agent systems are in active development. The current architecture — hooks-based compliance layer, declarative guardrails, OTel observability — is positioned to absorb these standards without structural rework.

### Emerging Agent Identity Standards

The NIST RFI on agent identity signals convergence toward enterprise-grade agent credentials (DID/SPIFFE standards) rather than API keys. AgentCore Identity already integrates with enterprise IdPs (Okta, Azure AD, Cognito). This is the direction of travel; the demo should document IAM-based identity as the current best practice.

### MCP and A2A Protocol Maturation

The Model Context Protocol (MCP) and Agent-to-Agent (A2A) protocol are standardising how agents expose and consume tools. AgentCore Gateway already supports MCP servers as tool sources. As these protocols mature, the tool boundary — already identified as the primary NIST control enforcement point — becomes more formally defined and auditable.

_Source: [NIST AI Agent Standards Initiative](https://www.nist.gov/caisi/ai-agent-standards-initiative), [Nemko Digital: AI Agent Standards](https://digital.nemko.com/news/ai-agent-standards-navigating-new-nist-governance)_

---

## 8. Strategic Recommendations for strands-agents-demo

### Recommended New Phase: NIST AI RMF Compliance Layer

Based on this research, the recommended next phase for `strands-agents-demo` is a dedicated **Epic 4: NIST AI RMF Compliance Layer**, decomposing into five stories aligned to the phased implementation roadmap:

| Story | NIST Functions | Deliverable |
|---|---|---|
| 4.1 — Governance foundation | GOVERN + MAP | `docs/ai-system-card.md`, `docs/risk-register.md`, `docs/governance-charter.md` |
| 4.2 — Audit hooks | MEASURE | `compliance/hooks.py` (`AuditLoggingHook` HookProvider) + JSONL audit log |
| 4.3 — Bedrock Guardrails | MANAGE | `deploy/guardrail.yaml` + `BedrockModel` guardrail wiring + `.env.example` update |
| 4.4 — Red-team CI | MEASURE | `compliance/promptfoo-redteam.yaml` + `tests/test_safety_boundaries.py` + CI safety job |
| 4.5 — Compliance dashboard | MEASURE + MANAGE | `deploy/create_dashboard.py` + CloudWatch `NIST-RMF-AgentCompliance` dashboard |

### Structural Decision: `compliance/` as Separate Layer

The most important architectural decision for this phase is maintaining strict separation of concerns. The `compliance/` directory must have no imports from `agents/` and `agents/` must have no imports from `compliance/`. Risk controls attach to the agent via the hook registry — this is the Strands SDK's intended extension mechanism.

This structure means:
- A developer reading `agent.py` sees only business logic
- A compliance reviewer reads only `compliance/` to understand risk controls
- Adding a new tool to the agent automatically inherits the full guardrail fabric via hooks

### Positioning Value

Adding NIST AI RMF alignment to this demo creates a differentiated reference implementation. Most Strands and AgentCore examples show how to build an agent. This demo would show how to build an agent that is production-trustworthy — with documented risk controls, structured audit evidence, automated safety testing, and a compliance dashboard. That is the "aha moment" for enterprise developers evaluating the stack for regulated environments.

---

## 9. Source References

**NIST Official Publications**
- [NIST AI RMF Homepage](https://www.nist.gov/itl/ai-risk-management-framework)
- [NIST AI 100-1: AI Risk Management Framework 1.0](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf)
- [NIST AI 600-1: Generative AI Profile](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)
- [NIST AI RMF Playbook](https://www.nist.gov/itl/ai-risk-management-framework/nist-ai-rmf-playbook)
- [NIST AI RMF Core Functions](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)
- [NIST AIRC Playbook — MANAGE](https://airc.nist.gov/airmf-resources/playbook/manage/)
- [NIST AI Agent Standards Initiative](https://www.nist.gov/caisi/ai-agent-standards-initiative)
- [NIST IR 8596 Draft](https://nvlpubs.nist.gov/nistpubs/ir/2025/NIST.IR.8596.iprd.pdf)

**AWS Official Documentation and Samples**
- [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/)
- [Amazon Bedrock Guardrails](https://aws.amazon.com/bedrock/guardrails/)
- [ApplyGuardrail API](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-use-independent-api.html)
- [Associate guardrail with agent](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-guardrail.html)
- [AgentCore lifecycle settings](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-lifecycle-settings.html)
- [AWS Prescriptive Guidance: Agentic AI Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-patterns/introduction.html)
- [aws-samples/sample-agentcore-rai-strands-agents](https://github.com/aws-samples/sample-agentcore-rai-strands-agents)
- [Strands Agents SDK Technical Deep Dive (AWS Blog)](https://aws.amazon.com/blogs/machine-learning/strands-agents-sdk-a-technical-deep-dive-into-agent-architectures-and-observability/)
- [AI Agents in Enterprises: Best Practices with AgentCore (AWS Blog)](https://aws.amazon.com/blogs/machine-learning/ai-agents-in-enterprises-best-practices-with-amazon-bedrock-agentcore/)
- [Defense-in-Depth for Generative AI — OWASP Top 10 (AWS Blog)](https://aws.amazon.com/blogs/machine-learning/architect-defense-in-depth-security-for-generative-ai-applications-using-the-owasp-top-10-for-llms/)

**Strands Agents SDK**
- [Strands Agents: Runtime Guardrails with Agent Control](https://strandsagents.com/blog/strands-agents-with-agent-control/)
- [Add Guardrails to Strands Agent (AWS Builders — DEV Community)](https://dev.to/aws-builders/add-guardrails-to-your-strands-agent-in-zero-time-with-amazon-bedrock-guardrails-1gam)
- [Supercharge AWS AI Agents with Strands Hooks (DEV Community)](https://dev.to/sreeni5018/supercharge-your-aws-ai-agents-with-strands-hooks-2ppg)
- [Langfuse: Observability for Strands Agents](https://langfuse.com/integrations/frameworks/strands-agents)
- [OTel + Guardrails with MCP Workflows (Glama)](https://glama.ai/blog/2025-07-21-observability-and-governance-using-otel-guardrails-and-metrics-with-mcp-workflows)

**Third-Party Analysis and Frameworks**
- [Giskard: OWASP, MITRE ATLAS, and NIST AI RMF Explained](https://www.giskard.ai/knowledge/risk-assessment-for-llms-and-ai-agents-owasp-mitre-atlas-and-nist-ai-rmf-explained)
- [CSA: AAGATE Governance Platform for Agentic AI](https://cloudsecurityalliance.org/blog/2025/12/22/aagate-a-nist-ai-rmf-aligned-governance-platform-for-agentic-ai)
- [Enkrypt AI: Securing AI Agents — Comprehensive Guardrail Framework](https://www.enkryptai.com/blog/securing-ai-agents-a-comprehensive-framework-for-agent-guardrails)
- [CloudMatos: Aegis — Aligning Agentic AI with NIST AI RMF](https://www.cloudmatos.ai/blog/aegis-aligning-agentic-ai-with-nist-ai-rmf/)
- [Arize AI: AWS Bedrock AgentCore Observability](https://arize.com/blog/aws-bedrock-agentcore-observability-operationalizing-ai-agents-at-scale/)
- [Promptfoo: NIST AI RMF Red-Team Docs](https://www.promptfoo.dev/docs/red-team/nist-ai-rmf/)
- [Nemko Digital: AI Agent Standards and NIST Governance](https://digital.nemko.com/news/ai-agent-standards-navigating-new-nist-governance)
- [ActiveFence: AI Risk Frameworks That Matter](https://www.activefence.com/blog/ai-risk-management-frameworks-nist-owasp-mitre-atlas-iso/)
- [Architecting Trust: NIST-Based Security Governance for AI Agents (Microsoft)](https://techcommunity.microsoft.com/blog/microsoftdefendercloudblog/architecting-trust-a-nist-based-security-governance-framework-for-ai-agents/4490556)

---

**Technical Research Completion Date:** 2026-03-20
**Research Period:** 2026-03-19 to 2026-03-20
**Source Verification:** All technical facts cited with current sources
**Technical Confidence Level:** High (official documentation and AWS API references); Medium (NIST-to-AWS mapping inferences); noted where in-progress NIST standards affect certainty

_This research document serves as the technical foundation for an Epic 4: NIST AI RMF Compliance Layer in the strands-agents-demo project, providing actionable implementation guidance grounded in current standards and tooling._
