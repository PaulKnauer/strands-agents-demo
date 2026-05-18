---
stepsCompleted: [1, 2, 3]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'multi-provider model support'
research_goals: 'Determine the best architecture for replacing the current Claude-centric setup with support for Gemma, Moonshot AI, Llama, Qwen, and DeepSeek across local Strands execution and deployed AgentCore execution; identify required abstraction changes across code, tests, docs, and deployment; surface integration, compatibility, and operational tradeoffs before a brownfield kickoff.'
user_name: 'Paul'
date: '2026-05-07'
web_research_enabled: true
source_verification: true
---

# Research Report: technical

**Date:** 2026-05-07
**Author:** Paul
**Research Type:** technical

---

## Research Overview

## Technical Research Scope Confirmation

**Research Topic:** multi-provider model support
**Research Goals:** Determine the best architecture for replacing the current Claude-centric setup with support for Gemma, Moonshot AI, Llama, Qwen, and DeepSeek across local Strands execution and deployed AgentCore execution; identify required abstraction changes across code, tests, docs, and deployment; surface integration, compatibility, and operational tradeoffs before a brownfield kickoff.

**Technical Research Scope:**

- Architecture Analysis - provider abstraction, runtime separation, deployment compatibility
- Implementation Approaches - adapter design, environment configuration, and testing strategy
- Technology Stack - model access paths, SDKs, APIs, and hosting options
- Integration Patterns - tool calling, protocol compatibility, and authentication paths
- Performance Considerations - latency, portability, operational complexity, and lock-in tradeoffs

**Research Methodology:**

- Current web data with rigorous source verification
- Multi-source validation for critical technical claims
- Confidence-based interpretation where provider capabilities differ
- Repo-specific analysis grounded in the existing `agent.py`, `deploy/app.py`, tests, and deployment path

**Scope Confirmed:** 2026-05-07

---

## Technology Stack Analysis

### Programming Languages

The implementation language does not need to change. The decisive technology choice is the model-access layer, not Python itself. Your repo already uses Python for both the local Strands path and the AgentCore runtime path, and current Strands Python docs expose multiple provider integrations: Bedrock is built in, Gemini is available as a provider, and LiteLLM is available as an optional provider for broader model coverage. That means a brownfield migration can keep Python and introduce a more flexible provider adapter rather than rewriting the agent surface.

For this project, the practical language implication is that Python remains the stable base while provider coverage can be widened through either:
- native Strands providers where available, or
- Strands `LiteLLMModel` when you want one abstraction over OpenAI-compatible or other LiteLLM-supported backends.

_Popular Languages: Python remains sufficient for both local and deployed paths in this repo._
_Emerging Languages: not relevant to the migration decision; the leverage is at the provider layer._
_Language Evolution: current Strands provider docs show growing model-provider optionality without requiring language change._
_Performance Characteristics: the main performance differences will come from provider/API choice and model capability, not from Python._
_Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/_
_Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/litellm/_
_Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html_

### Development Frameworks and Libraries

The most important framework finding is that the current repo is split across two different model-integration approaches:
- local path: Strands agent abstractions in `agent.py`
- deployed path: direct `boto3` Bedrock Converse loop in `deploy/app.py`

That split matters because Strands already supports interchangeable model providers, while the deployed runtime is currently hard-wired to Bedrock. Official AgentCore docs now describe Runtime as framework-agnostic and model-flexible, including models inside or outside Bedrock. This means AgentCore is not the blocker; the blocker is the repo’s current Bedrock-specific deployed implementation.

There are two credible framework/library options for the brownfield change:

1. **Stay Bedrock-centric and broaden model IDs**  
Use `BedrockModel` locally and keep the deployed runtime on Bedrock APIs. This is the lowest-friction path if you are comfortable consuming Gemma, Moonshot/Kimi, Llama, Qwen, and DeepSeek via Bedrock rather than each vendor’s direct API.

2. **Introduce a provider abstraction for non-Bedrock APIs**  
Use Strands `LiteLLMModel` locally and either LiteLLM or vendor SDKs in the deployed runtime. This increases flexibility but also expands env vars, auth paths, testing matrix, and operational failure modes.

_Major Frameworks: Strands Agents SDK for local agent logic; Bedrock Runtime APIs for current deployed logic._
_Micro-frameworks: LiteLLM is the main unification option if you want direct-provider flexibility without five bespoke SDK integrations._
_Evolution Trends: Strands has moved toward interchangeable providers, while Bedrock has expanded model choice enough that “single-cloud, multi-model” is now realistic._
_Ecosystem Maturity: BedrockModel and LiteLLM are both documented paths; LiteLLM adds breadth, Bedrock adds operational simplicity inside AWS._
_Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/_
_Source: https://strandsagents.com/docs/api/python/strands.models.bedrock/_
_Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/litellm/_
_Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agents-tools-runtime.html_

### Model Platforms Relevant to This Migration

A major current-state change since this repo was originally designed is that **Amazon Bedrock now exposes all five target families you named**:
- Google Gemma
- Meta Llama
- Moonshot AI / Kimi
- Qwen
- DeepSeek

That materially changes the architectural decision. When this project was created, Claude plus Gemini fallback was a sensible split. As of May 7, 2026, Bedrock’s model catalog and model-card docs show Bedrock as a viable single control plane for the exact provider mix you want to investigate.

This matters because it creates a new low-complexity option:
- keep one authentication domain (`AWS_REGION`, IAM, Bedrock quotas)
- keep one deployed runtime protocol family
- vary `MODEL_ID` across providers inside Bedrock

The alternative is a direct-provider strategy where:
- Gemma can be accessed via the Gemini API or open-weight deployment paths
- Moonshot AI exposes an OpenAI-compatible Kimi API
- DeepSeek exposes multiple API compatibility formats
- Qwen exposes an OpenAI-compatible API platform

That direct-provider route is still viable, but it is no longer the only way to get the model diversity you want.

_Source: https://docs.aws.amazon.com/bedrock/latest/userguide/models.html_
_Source: https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards-google.html_
_Source: https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards-meta.html_
_Source: https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards-qwen.html_
_Source: https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards-deepseek.html_
_Source: https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards-moonshot-ai.html_
_Source: https://api-docs.deepseek.com/_
_Source: https://platform.kimi.ai/docs/api/overview_
_Source: https://qwen.ai/apiplatform_
_Source: https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api_

### Development Tools and Platforms

For local development, the repo’s current tooling stays valid: `pytest`, `Makefile`, `.env`, and Strands. The tooling question is really about how many provider-specific client stacks you want to support.

If you adopt **Bedrock as the shared platform**, the tooling delta is moderate:
- update model enumeration and validation
- broaden tests for model capability differences
- possibly move local Gemini-specific code to Bedrock or to a common abstraction

If you adopt **direct vendor APIs**, the tooling delta is larger:
- per-provider API keys and env management
- more mocking surfaces in tests
- more complex CI and secrets handling
- likely introduction of LiteLLM or OpenAI-compatible clients for normalization

LiteLLM’s official docs describe it as a unified OpenAI-format interface over many providers, with consistent response formatting and exception mapping. Strands’ LiteLLM provider is the cleanest documented way to exploit that from the current codebase.

_IDE and Editors: unchanged; current repo assumptions remain valid._
_Version Control: unchanged; repo workflow remains Python-first._
_Build Systems: unchanged for Bedrock-first migration; expanded dependency and secret management for direct-provider migration._
_Testing Frameworks: existing pytest suite remains usable but must grow capability-based coverage._
_Source: https://docs.litellm.ai/_
_Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/litellm/_

### Cloud Infrastructure and Deployment

AgentCore Runtime is not limited to Bedrock models. Official AWS docs describe it as working with any LLM, including Bedrock-hosted models and providers outside Bedrock such as Gemini and OpenAI. It also notes that Runtime only initiates outbound connections and that private VPC deployment removes internet access unless you configure for it.

This creates two infrastructure patterns:

1. **Single-platform AWS pattern**
- Bedrock for inference
- AgentCore Runtime for deployment
- one IAM/security domain
- no extra outbound vendor networking requirements beyond AWS

2. **Hybrid external-provider pattern**
- AgentCore Runtime still hosts the app
- runtime calls external APIs such as Kimi, DeepSeek, Qwen, or Gemini directly
- you must manage external auth, outbound networking, and more complex operational policy

For this repo, the Bedrock-first path is operationally cleaner because the deployed runtime is already Bedrock-centric and your deployment scripts, IAM scope, and verification flow all assume AWS-native inference.

_Major Cloud Providers: AWS remains the deployment anchor for this repo._
_Container Technologies: AgentCore abstracts most hosting concerns away from the app code._
_Serverless Platforms: AgentCore Runtime is the relevant serverless hosting platform here._
_CDN and Edge Computing: not central to this migration decision._
_Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agents-tools-runtime.html_
_Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-vpc.html_
_Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-how-it-works.html_

### Technology Adoption Trends

The strongest adoption signal relevant to this project is not a survey statistic; it is platform convergence:
- Bedrock’s current model catalog now spans proprietary and open/open-weight families from multiple vendors.
- Strands has explicit provider interchangeability and a LiteLLM bridge.
- Several direct providers in your target list now present OpenAI-compatible APIs, reducing integration friction if you choose a non-Bedrock path.

In practice, that means the brownfield decision is less about “can we access these models?” and more about “which control plane do we want to own?”:
- **Bedrock-first** optimizes for deployment simplicity and AWS alignment.
- **Direct-provider / LiteLLM-first** optimizes for portability and vendor-specific feature access.

For this repo, current evidence points to Bedrock-first as the lowest-risk migration starting point, with LiteLLM reserved for gaps Bedrock cannot close.

_Migration Patterns: centralize first, then selectively break out if a specific provider feature requires it._
_Emerging Technologies: OpenAI-compatible and unified-runtime interfaces are reducing provider-switching cost._
_Legacy Technology: the hard-coded `bedrock|gemini` split is now too narrow for the model landscape you want._
_Community Trends: platform-level model interchangeability is increasing across both Bedrock and LiteLLM ecosystems._
_Source: https://docs.aws.amazon.com/bedrock/latest/userguide/models.html_
_Source: https://docs.aws.amazon.com/bedrock/latest/userguide/models-api-compatibility.html_
_Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/_
_Source: https://docs.litellm.ai/_

---

## Integration Patterns Analysis

### API Design Patterns

This repo currently depends on a very specific interaction model: user prompt -> model response -> optional tool request -> tool result -> follow-up model response. That means the integration decision must be driven by **tool-calling semantics**, not just raw text generation access.

There are three relevant API patterns for the migration:

1. **Bedrock Converse / ConverseStream**
This is the closest match to the deployed runtime you already have. AWS documents a standardized conversation format and a tool-use pattern across supported models, which keeps the current `deploy/app.py` loop conceptually intact. The advantage is a single protocol surface. The limitation is that feature support still varies by model.

2. **OpenAI-compatible chat completions**
Several targets you named expose OpenAI-compatible APIs directly. This is important because it enables either:
- a direct OpenAI-style client integration, or
- a LiteLLM normalization layer.

3. **Provider-specific native APIs**
These can expose vendor-specific features earlier than Bedrock or OpenAI-compatible layers, but they increase branching in the codebase and test matrix.

For this repo, the cleanest integration pattern is to introduce a provider adapter that normalizes:
- input messages
- tool definition format
- tool call extraction
- final text extraction
- error classification

_RESTful APIs: current direct-provider options mostly surface HTTPS JSON APIs._
_GraphQL APIs: not relevant to the core model-inference path here._
_RPC and gRPC: not the mainstream path for the model providers under consideration in this repo._
_Webhook Patterns: not central to the current interactive agent loop._
_Source: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html_
_Source: https://docs.aws.amazon.com/bedrock/latest/userguide/tool-use.html_
_Source: https://api-docs.deepseek.com/_
_Source: https://platform.kimi.ai/docs/api/overview_
_Source: https://qwen.ai/apiplatform_

### Communication Protocols

The deployed runtime does not need exotic protocols. The main protocol question is whether the runtime talks only to AWS endpoints or also to external vendor APIs over outbound HTTPS.

Official AgentCore docs state that Runtime initiates outbound connections and that VPC mode removes internet access unless you configure for it. That means external-provider designs are operationally possible, but they are not “free”:
- public-runtime mode can call external APIs directly
- private/VPC mode may require deliberate networking configuration to reach them

That is a meaningful integration difference versus Bedrock-first design, where all inference stays within AWS service patterns already assumed by the repo.

_HTTP/HTTPS Protocols: the relevant protocol for Bedrock and direct-provider inference paths._
_WebSocket Protocols: not required for the current request/response agent loop._
_Message Queue Protocols: not relevant to the current architecture._
_gRPC and Protocol Buffers: not part of the current integration path for the named providers in this repo._
_Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-vpc.html_
_Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-how-it-works.html_

### Data Formats and Standards

The repo currently depends on structured JSON-like message content with explicit tool-use blocks. That standardization is stronger in Bedrock Converse than across raw provider APIs.

A direct-provider strategy should not let each provider’s wire format leak into business logic. Instead, the adapter layer should normalize into one internal structure, for example:
- `messages`
- `tool_specs`
- `tool_requests`
- `tool_results`
- `final_text`

This is especially important because some providers emphasize OpenAI-compatible formats, while DeepSeek also documents alternate compatibility interfaces. Supporting multiple external vendors without a canonical internal message contract would make the brownfield change brittle.

_JSON and XML: JSON is the relevant interchange format._
_Protobuf and MessagePack: not central to the current model-inference path._
_CSV and Flat Files: irrelevant to runtime inference._
_Custom Data Formats: internal canonical model-message schema is recommended even if external providers differ._
_Source: https://api-docs.deepseek.com/_
_Source: https://platform.kimi.ai/docs/api/overview_
_Source: https://docs.litellm.ai/_

### System Interoperability Approaches

The repo needs interoperability at the **model gateway layer**, not between many business systems. The core pattern options are:

1. **Single gateway via Bedrock**
- one auth model
- one runtime API family
- lower operational branching

2. **Unified adapter via LiteLLM**
- broader provider reach
- one app-facing interface
- extra dependency and an additional abstraction to debug

3. **Per-provider adapters**
- highest flexibility
- highest maintenance cost

For this repo, Bedrock-first and LiteLLM-second is the most defensible sequence. Starting with five bespoke provider clients would create unnecessary complexity before you know where Bedrock’s feature coverage actually falls short.

_Point-to-Point Integration: acceptable only for a single-provider design, not for five providers._
_API Gateway Patterns: conceptually useful as an internal model-gateway abstraction in code._
_Service Mesh: not relevant at this repo’s scale._
_Enterprise Service Bus: not relevant._
_Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/litellm/_
_Source: https://docs.litellm.ai/_
_Source: https://docs.aws.amazon.com/bedrock/latest/userguide/models-api-compatibility.html_

### Microservices Integration Patterns

This repo is not a microservices system, but the same design principle applies: hide provider variability behind a stable boundary.

The practical boundary here should be something like a `ModelAdapter` contract with capability flags:
- `supports_tool_use`
- `supports_streaming`
- `supports_structured_output`
- `supports_reasoning_mode`
- `supports_bedrock_deploy_path`

That capability registry matters because Bedrock feature support varies by model. AWS’ supported-model features tables and model cards show that capabilities such as tool use are model-specific, not just provider-specific. Likewise, direct-provider APIs may be OpenAI-compatible without matching every feature your loop expects.

_API Gateway Pattern: good analogy for a local in-process provider abstraction._
_Service Discovery: not relevant._
_Circuit Breaker Pattern: useful if external-provider APIs are added._
_Saga Pattern: not relevant._
_Source: https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-supported-models-features.html_
_Source: https://docs.aws.amazon.com/bedrock/latest/userguide/tool-use-supported-models.html_

### Event-Driven Integration

Event-driven patterns are secondary here. Your current runtime is synchronous request/response. The migration should preserve that simplicity unless a provider feature materially requires async workflows.

The only event-like concern worth noting is observability:
- if you stay on Bedrock in AgentCore, you preserve a more AWS-native operational path
- if you shift to direct external APIs, you may need more explicit logging and tracing around provider failures and rate limits

_Publish-Subscribe Patterns: not central to the current design._
_Event Sourcing: not relevant._
_Message Broker Patterns: not relevant._
_CQRS Patterns: not relevant._
_Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agents-tools-runtime.html_

### Integration Security Patterns

Security posture differs sharply between Bedrock-first and direct-provider paths.

**Bedrock-first**
- IAM-based access control
- AWS-native secret minimization
- existing deployment scripts and least-privilege patterns remain mostly aligned

**Direct-provider path**
- multiple vendor API keys
- more secret distribution in local dev and CI
- more outbound network exposure from Runtime
- more complex failure and rotation handling

This is a major reason Bedrock-first is attractive for the brownfield change: it keeps the security model closer to what the repo already implements.

_OAuth 2.0 and JWT: not the primary auth model for the current AWS-native path._
_API Key Management: becomes central only if you add direct-provider APIs._
_Mutual TLS: not a primary concern in the current repo design._
_Data Encryption: standard TLS transport applies across all options._
_Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-vpc.html_
_Source: https://docs.aws.amazon.com/bedrock/latest/userguide/models-api-compatibility.html_
_Source: https://api-docs.deepseek.com/_
_Source: https://platform.kimi.ai/docs/api/overview_

---

## Architectural Patterns and Design

### System Architecture Patterns

The repo should move from a **provider-conditional architecture** to a **capability-driven model gateway**. Right now, the architecture is effectively:
- local: `if provider == gemini` else `bedrock`
- deployed: always Bedrock Converse

That design does not scale to five new model families. The replacement pattern should be:
- one internal `ModelAdapter` interface
- one capability registry per model/runtime combination
- multiple concrete adapters behind that contract

The most defensible target architecture is:

1. **Application layer**
- agent prompt
- tool definitions
- conversation logic

2. **Model gateway layer**
- adapter selection
- capability checks
- message normalization
- tool-call/result normalization
- fallback/routing policy

3. **Provider transport layer**
- Bedrock adapter
- LiteLLM adapter
- optional direct-provider adapters only where justified

This keeps the app code stable while letting model/provider differences evolve underneath it.

_Dominant Patterns: adapter plus capability registry is the right fit for multi-model support in a brownfield codebase._
_Architectural Evolution: move from provider-name branching to transport-agnostic gateway design._
_Architectural Trade-offs: Bedrock-first reduces operational complexity; LiteLLM/direct adapters increase flexibility but widen the test and secret surface._
_Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/_
_Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agents-tools-runtime.html_

### Design Principles and Best Practices

The governing design principles for this migration should be:

- **Capability over branding**: choose behavior by what a model can do, not by its vendor label.
- **Single internal message contract**: never let Bedrock, OpenAI-compatible, or vendor-native payloads leak through the codebase.
- **Preserve runtime separation**: keep local Strands concerns separate from deployed AgentCore transport concerns.
- **Default to lowest-complexity transport**: use Bedrock where it satisfies requirements; add other transports only for verified gaps.
- **Test the contract, not just the provider**: assert tool-use semantics, prompt parity, and fallback behavior across adapters.

Strands’ BedrockModel already encapsulates Bedrock-specific concerns such as tool configuration, guardrails, caching points, streaming, and context-overflow handling. That is a strong signal to avoid re-implementing Bedrock behavior in many places unless you need a different transport entirely.

_Design Principles: adapter isolation, capability checks, and transport normalization._
_Best Practice Patterns: centralize provider selection; keep application logic unaware of wire-format specifics._
_Architectural Quality Attributes: maintainability and correctness are more important than maximizing provider optionality on day one._
_Source: https://strandsagents.com/docs/api/python/strands.models.bedrock/_
_Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/litellm/_

### Scalability and Performance Patterns

There are two distinct scalability questions:

1. **Inference scalability**
- Bedrock already gives you managed inference endpoints and a stable AWS control plane.
- LiteLLM can help with routing, fallbacks, retries, and cost/latency-aware selection if you need multi-endpoint orchestration.

2. **Codebase scalability**
- without an internal gateway, every new provider multiplies code branches, mocks, env vars, and docs
- with a gateway, adding a new model is usually registry and adapter work, not a cross-repo rewrite

LiteLLM’s router docs explicitly support fallbacks, retries, timeouts, cooldowns, and multiple routing strategies such as latency-based and cost-based selection. That makes LiteLLM a strong secondary architecture choice if you need runtime routing across providers, but it should sit behind your own gateway contract rather than becoming the whole architecture.

_Scalability Patterns: central gateway plus optional routed backend._
_Capacity Planning: simpler with Bedrock-first because quotas and auth remain concentrated in AWS._
_Elasticity and Auto-scaling: handled primarily by Bedrock/AgentCore platform behavior rather than custom app code._
_Source: https://docs.litellm.ai/docs/routing_
_Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agents-tools-runtime.html_

### Integration and Communication Patterns

The architecture should standardize on a **canonical conversation contract** independent of transport. A minimal internal contract should include:
- normalized `messages`
- normalized `system_prompt`
- normalized `tool_specs`
- normalized `tool_calls`
- normalized `tool_results`
- normalized `final_response`
- normalized `usage/metrics`

Then each adapter maps:
- Bedrock Converse <-> internal contract
- LiteLLM/OpenAI-compatible <-> internal contract
- provider-native API <-> internal contract

This pattern minimizes the blast radius of future provider additions and keeps tests stable around one internal protocol.

_Source: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html_
_Source: https://docs.litellm.ai/_

### Security Architecture Patterns

Security architecture is a major reason not to start with direct-provider sprawl.

Recommended security pattern:
- **Primary path**: Bedrock-first with IAM and current deployment guardrails preserved
- **Secondary path**: direct-provider adapters only where needed, isolated behind dedicated env vars and secrets handling

If you add direct providers, isolate them operationally:
- separate secret names per provider
- explicit allowlist of enabled providers/models
- outbound auth and networking documented per runtime mode
- adapter-level error classification that avoids leaking secrets in logs

Because AgentCore supports any framework and any model, the security constraint is mostly self-imposed by your architecture choices. That is useful, but it means poor boundary design will create avoidable exposure.

_Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agents-tools-runtime.html_
_Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-how-it-works.html_

### Data Architecture Patterns

There is no large application data model here; the critical “data architecture” is the conversation and tool-call representation.

The architecture should preserve:
- one authoritative system prompt
- one tool schema source of truth
- one conversation-state representation

Then render those into each provider transport as needed. This is especially important because structured output in LiteLLM depends on underlying provider support for tool calling, and Bedrock feature support varies by model. A single authoritative internal schema prevents silent drift between transports.

_Source: https://strandsagents.com/docs/user-guide/concepts/model-providers/litellm/_
_Source: https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-supported-models-features.html_

### Deployment and Operations Architecture

The best deployment architecture is **two-phase**:

1. **Phase 1: Bedrock-first expansion**
- keep AgentCore deployment path
- broaden `MODEL_ID` coverage inside Bedrock
- add capability registry and adapter boundary
- keep the current AWS-native operational model

2. **Phase 2: Optional external-provider expansion**
- introduce LiteLLM and/or direct adapters only where Bedrock lacks needed capabilities, economics, or specific models
- add provider-specific secrets and operational controls deliberately

This staged architecture matches the repo’s brownfield reality. It reduces migration risk and lets you learn where real capability gaps are before taking on the cost of multi-vendor runtime operations.

_Source: https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards.html_
_Source: https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-supported-models-features.html_
_Source: https://docs.litellm.ai/docs/routing_


<!-- Content will be appended sequentially through research workflow steps -->
