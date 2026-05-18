---
workflowType: 'correct-course'
project_name: 'strands-agents-demo'
user_name: 'Paul'
date: '2026-05-07'
change_trigger: 'Replace the current Claude-centric / bedrock|gemini model design with a capability-driven model adapter architecture, then expand support toward Gemma, Moonshot AI, Llama, Qwen, and DeepSeek.'
mode: 'incremental'
status: 'draft'
scope_classification: 'moderate'
artifacts_impacted:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
  - '_bmad-output/planning-artifacts/epics.md'
  - 'README.md'
  - '.env.example'
  - 'deploy/deploy.py'
  - '_bmad-output/implementation-artifacts/sprint-status.yaml'
---

# Sprint Change Proposal

## 1. Issue Summary

The project was originally planned around a narrow model-provider strategy: Claude on Amazon Bedrock as the primary path and Gemini as the documented fallback. That assumption is now out of date technically and architecturally.

The triggering issue is a combination of:
- a technical limitation discovered in the original provider design
- a strategic shift enabled by the current model landscape

The current codebase and research now justify a capability-driven model adapter architecture rather than direct `bedrock|gemini` branching. Research also showed that Amazon Bedrock now exposes the target model families under consideration for future support: Gemma, Moonshot AI, Llama, Qwen, and DeepSeek. That materially changes the right architecture and backlog shape for the project.

Evidence:
- The planning artifacts still describe the project as Claude-centric with Gemini fallback.
- The codebase now contains an adapter foundation in [model_adapters.py](/Users/paul/github/strands-agents-demo/model_adapters.py:1) and a runtime adapter boundary in [deploy/app.py](/Users/paul/github/strands-agents-demo/deploy/app.py:1).
- The technical research in [`technical-multi-provider-model-support-research-2026-05-07.md`](/Users/paul/github/strands-agents-demo/_bmad-output/planning-artifacts/research/technical-multi-provider-model-support-research-2026-05-07.md:1) recommends a Bedrock-first, capability-driven architecture with staged provider expansion.

## 2. Impact Analysis

### Epic Impact

- **Epic 1** is affected directly.
  - It currently frames local model support as Bedrock primary with Gemini fallback.
  - It must now define the adapter/gateway foundation explicitly.
- **Epic 2** remains valid, but its deployment story must be reframed around a Bedrock-first runtime adapter path rather than generic model symmetry.
- **Epic 3** remains valid, but its documentation scope must explain the new adapter architecture and the narrower deployed-runtime support boundary.
- A **new follow-on epic** is recommended for broader multi-provider expansion beyond the initial adapter foundation.

### Story Impact

- Story 1.2 needs updated acceptance criteria to validate adapter-based local model construction.
- Deployment and documentation stories need wording updates to align with Bedrock-first runtime support.
- Additional backlog entries are needed for capability registry expansion and staged model-family support.

### Artifact Conflicts

- **PRD** conflicts:
  - still states Claude primary and Gemini fallback
  - overstates model switching as a simple env-var change across the board
- **Architecture** conflicts:
  - still encodes direct `bedrock|gemini` branching as the core design
  - does not describe adapters, capability metadata, or staged provider expansion
- **Epics** conflicts:
  - no explicit epic for broader provider expansion
  - provider support assumptions are too narrow
- **README / `.env.example` / deployment comments** conflict:
  - still communicate the older provider model

### Technical Impact

- Code:
  - adapter foundation is already introduced and needs planning alignment
- Infrastructure:
  - no fundamental rewrite required; Bedrock-first deployment remains valid
- Deployment:
  - deployed runtime support should remain Bedrock-first for MVP
- Testing:
  - tests must increasingly validate capability boundaries, not just provider names
- Documentation:
  - must clearly distinguish local adapter support from deployed runtime support

## 3. Recommended Approach

### Selected Path

**Hybrid: Direct Adjustment + PRD MVP Review**

- Use **Direct Adjustment** to revise PRD, architecture, epics, stories, and secondary artifacts.
- Use **PRD MVP Review** only to correct wording and scope assumptions, not to reduce the MVP.

### Why This Path

- **Implementation effort and timeline impact**
  - Moderate and controlled. The architecture direction has already been validated in code.
- **Technical risk and complexity**
  - Lower than rollback and lower than jumping immediately to five direct-provider integrations.
- **Momentum**
  - Preserved. The current refactor becomes the foundation rather than rework.
- **Sustainability**
  - Stronger with a capability-driven model interface and staged provider expansion.
- **Business value**
  - Higher. The project becomes a more credible modern multi-model reference implementation.

### Options Evaluated

- **Option 1: Direct Adjustment**
  - Viable
  - Effort: Medium
  - Risk: Medium
- **Option 2: Potential Rollback**
  - Not viable
  - Effort: Medium
  - Risk: High
- **Option 3: PRD MVP Review**
  - Viable as wording/scope correction only
  - Effort: Low to Medium
  - Risk: Low

## 4. Detailed Change Proposals

### 4.1 PRD Changes

Artifact: [`_bmad-output/planning-artifacts/prd.md`](/Users/paul/github/strands-agents-demo/_bmad-output/planning-artifacts/prd.md:1)

**OLD**
- Model Selection: Claude via Amazon Bedrock as primary LLM; Gemini free tier as documented fallback. Switching requires only an environment variable change.
- Integration Requirements:
  - Amazon Bedrock (Claude) or Google Gemini API as the LLM backend
- MVP Feature Set:
  - Claude (Bedrock) primary; Gemini free tier documented fallback

**NEW**
- Model Selection: The project uses a capability-driven model abstraction. Amazon Bedrock is the primary model access plane for MVP, with model selection controlled via environment variables and adapter-based model wiring. Initial local adapters support Bedrock and Gemini; the architecture is designed to expand toward Gemma, Moonshot AI, Llama, Qwen, and DeepSeek in staged increments.
- Integration Requirements:
  - Amazon Bedrock as the primary LLM backend and deployment-aligned inference plane for MVP
  - Strands model adapters for local model construction
  - Optional future direct-provider or LiteLLM-based integrations where Bedrock capability gaps justify them
- MVP Feature Set:
  - Capability-driven model abstraction for local model selection
  - Bedrock-first model support for MVP
  - Gemini retained as an initial local adapter path
  - Planned staged expansion path toward Gemma, Moonshot AI, Llama, Qwen, and DeepSeek

**Rationale**
- Aligns the PRD with the approved architecture direction and existing refactor.
- Preserves MVP while removing outdated provider assumptions.

### 4.2 Architecture Changes

Artifact: [`_bmad-output/planning-artifacts/architecture.md`](/Users/paul/github/strands-agents-demo/_bmad-output/planning-artifacts/architecture.md:1)

**OLD**
- LLM: Amazon Bedrock (Claude 3 Sonnet/Nova Micro) primary; Google Gemini free tier fallback
- Decision: Two-variable env var pattern (`MODEL_PROVIDER` + `MODEL_ID`)
- Agent code pattern:

```python
if os.environ["MODEL_PROVIDER"] == "gemini":
    model = GeminiModel(model_id=os.environ["MODEL_ID"], ...)
else:
    model = BedrockModel(model_id=os.environ["MODEL_ID"], ...)
```

- Code Organization: Single `agent.py` for all agent logic; `deploy/` directory isolated for infrastructure concerns

**NEW**
- LLM / Model Access Strategy: Capability-driven model abstraction with Amazon Bedrock as the primary inference and deployment-aligned control plane for MVP. Initial local adapters support Bedrock and Gemini; the architecture is designed for staged expansion toward Gemma, Moonshot AI, Llama, Qwen, and DeepSeek.
- Decision: Environment-variable-driven provider and model selection remains, but provider choice is routed through adapters behind a `Model` interface with explicit capability metadata rather than direct vendor branching in app logic.
- Agent code pattern:

```python
adapter = create_local_model_adapter(os.environ["MODEL_PROVIDER"], os.environ)
model = adapter.build()
agent = Agent(model=model, tools=[get_today_date], ...)
```

- Runtime architecture pattern:
  - local path uses Strands-backed model adapters
  - deployed AgentCore path uses a runtime adapter contract
  - provider/model differences are normalized behind adapter boundaries
  - capability checks determine whether a given model/runtime combination is supported
- Code Organization:
  - `agent.py` remains lean and delegates model construction
  - `model_adapters.py` owns local adapter selection and capabilities
  - `deploy/app.py` owns runtime adapter behavior for deployed inference
  - `deploy/` remains isolated for infrastructure concerns

**Rationale**
- Replaces outdated provider branching with the approved adapter/gateway architecture.
- Formalizes the Bedrock-first, staged-expansion strategy.

### 4.3 Epic and Story Changes

Artifact: [`_bmad-output/planning-artifacts/epics.md`](/Users/paul/github/strands-agents-demo/_bmad-output/planning-artifacts/epics.md:1)

**OLD**
- Epic 1 is framed as “multi-provider model configuration (Bedrock primary, Gemini fallback)”
- FR12 and NFR8/NFR9/NFR10 are Claude/Gemini-specific
- Story 1.2 treats Gemini as the alternate model strategy
- No explicit epic exists for staged provider expansion

**NEW**
- Revise Epic 1 framing to:
  - “capability-driven local model configuration with adapter-based provider selection, Bedrock-first support, and initial Gemini local adapter support”
- Revise FR12 to:
  - “A developer configures the model provider and model identifier via environment variables and adapter-based model selection without modifying application logic”
- Revise NFR8 / NFR9 / NFR10 to:
  - NFR8: The agent functions correctly with Bedrock-backed model support for MVP
  - NFR9: Initial non-Bedrock local adapter support may be provided where documented
  - NFR10: Model switching requires configuration changes only when the selected model/runtime combination is supported by the configured adapter path
- Revise Story 1.2 to validate adapter-based local model construction and keep Bedrock as the primary validated path
- Add a new follow-on epic:
  - **Epic 4: Multi-Provider Model Expansion**
  - Focus:
    - capability registry expansion
    - provider/model compatibility validation
    - Bedrock-first model-family rollout
    - optional LiteLLM or direct-provider paths where justified
    - documentation and test expansion for each supported family

**Rationale**
- Gives the new architecture a proper backlog home.
- Separates adapter foundation work from broader provider expansion.

### 4.4 Secondary Artifact Changes

Artifacts:
- [README.md](/Users/paul/github/strands-agents-demo/README.md:1)
- [`.env.example`](/Users/paul/github/strands-agents-demo/.env.example:1)
- [deploy/deploy.py](/Users/paul/github/strands-agents-demo/deploy/deploy.py:1)
- [`_bmad-output/implementation-artifacts/sprint-status.yaml`](/Users/paul/github/strands-agents-demo/_bmad-output/implementation-artifacts/sprint-status.yaml:1)

**OLD**
- README explains model switching as Bedrock ↔ Gemini
- `.env.example` documents provider selection as only `bedrock` or `gemini`
- deployment commentary assumes Gemini as the main alternate path
- sprint status/backlog does not reflect adapter-foundation or staged provider expansion work

**NEW**
- README:
  - describe adapter-based local model construction
  - describe runtime adapter boundary in deployed path
  - explain Bedrock-first support for MVP
  - explain staged provider expansion
- `.env.example`:
  - keep current working provider examples
  - clarify current supported local adapters
  - clarify deployed runtime support is narrower than local support
- `deploy/deploy.py`:
  - revise comments to reflect Bedrock-first deployed support and future runtime adapter expansion
- `sprint-status.yaml`:
  - update epic/story structure after approval to reflect the new plan

**Rationale**
- Prevents documentation and execution artifacts from drifting behind approved planning changes.

## 5. PRD MVP Impact and High-Level Action Plan

### MVP Impact

- **MVP is still achievable**
- **MVP scope does not need reduction**
- **MVP wording and model assumptions do need correction**

### High-Level Action Plan

1. Update PRD to remove the old Claude/Gemini-only model story.
2. Update architecture to formalize the adapter/gateway design.
3. Update epics and stories to:
   - make adapter-foundation work explicit
   - keep Bedrock-first deployment explicit
   - introduce a staged provider-expansion epic
4. Update README, `.env.example`, deployment comments, and sprint status.
5. Route implementation according to scope and begin backlog reorganization.

### Dependencies and Sequencing

- PRD and architecture should be updated before final backlog reorganization.
- Epic/story changes should be reflected in sprint status after proposal approval.
- Broader provider rollout should follow the adapter foundation, not precede it.

## 6. Implementation Handoff

### Scope Classification

**Moderate**

This is not a direct one-story implementation task. It requires backlog reorganization and planning artifact updates, but it does not require a full strategic reset.

### Handoff Recipients

- **Product Owner / Developer**
  - update epics, stories, and sprint status
  - translate the approved architecture changes into actionable backlog items
- **Developer**
  - continue implementation along the adapter/gateway path
  - align README, `.env.example`, deployment comments, and tests with the approved artifact changes
- **Architect**
  - validate final architecture wording if additional direct-provider runtime support is introduced later

### Success Criteria

- PRD, architecture, and epics no longer contradict the approved adapter-based direction
- Sprint status reflects the revised epic/story structure
- README and `.env.example` communicate current support boundaries accurately
- Future provider expansion work is explicitly staged rather than implied

## 7. Checklist Summary

- Trigger/context analysis: complete
- Epic impact assessment: complete
- Artifact conflict analysis: complete
- Path forward evaluation: complete
- Incremental edit proposals: approved

## 8. Recommended Next Step

Approve this Sprint Change Proposal, then route to backlog/documentation update work before further provider-expansion implementation.
