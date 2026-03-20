# Story 4.1: NIST AI RMF Governance Foundation Documentation

Status: done

## Story

As a developer reviewing this project,
I want NIST AI RMF GOVERN and MAP documentation in the `docs/` directory,
So that the project has a documented risk boundary, accountability chain, and system inventory that serve as the foundation for all subsequent compliance controls in Epic 4.

## Context

This story is the first story of **Epic 4: NIST AI RMF Compliance Layer**, which adds responsible-AI governance infrastructure to the strands-agents-demo reference implementation.

The purpose of Epic 4 is to demonstrate that the Strands Agents SDK + AWS AgentCore stack is not just capable of building agents — it is capable of building *trustworthy* agents that meet NIST AI RMF standards. This makes the demo credible for enterprise and regulated-industry developers evaluating the stack.

**This story is documentation-only.** No `agent.py`, `deploy/`, or test files are modified. All deliverables are Markdown files in the `docs/` directory.

## Background: NIST AI RMF Relevant to This Story

The NIST AI Risk Management Framework (AI RMF 1.0) has four functions. This story addresses the first two:

- **GOVERN** — Establish policies, roles, accountability, and risk tolerance. Requires: documented intended use, out-of-scope uses, third-party component inventory, risk tolerance statement, accountability assignments, and review cadence.
- **MAP** — Identify and document risks across all system components. Requires: a risk register enumerating potential harms with likelihood/impact/mitigation, data flow documentation, and system boundary definition.

The most directly applicable NIST sub-categories for this story:
- GOVERN-1.1: Legal/regulatory compliance documentation
- GOVERN-1.3: Organisational risk tolerance documented
- GOVERN-1.4: Transparent, documented risk management process
- GOVERN-6.1: Third-party/supply-chain risk management (Bedrock, Strands SDK, AgentCore)
- MAP-1.1: Intended use, deployment context, and user populations documented
- MAP-2.2: Risks documented across all system components

**Key source:** NIST AI 100-1 (AI RMF 1.0), NIST AI 600-1 (Generative AI Profile — 12 risk categories for LLM-based agents including confabulation, prompt injection, data poisoning, harmful content, PII exposure).

## Acceptance Criteria

1. **Given** the `docs/` directory exists in the project root,
   **When** I list its contents,
   **Then** it contains exactly three files: `ai-system-card.md`, `risk-register.md`, and `governance-charter.md`.

2. **Given** `docs/ai-system-card.md` exists,
   **When** I read it,
   **Then** it contains all of the following sections with non-placeholder content:
   - System Purpose (what the agent does)
   - Intended Users (audience and use cases)
   - Out-of-Scope Uses (explicit exclusions)
   - Third-Party Components (Strands SDK version, Bedrock, AgentCore with versions where known)
   - Data Flows (what enters and exits the agent; whether any data is persisted)
   - Harm Categories Considered (at minimum: prompt injection, hallucination/confabulation, PII exposure, harmful content — each with likelihood and impact rating)
   - Risk Tolerance Statement (demo/reference scope; not for production PII handling)
   - Human Oversight Mechanism (how a user can verify and correct agent output)
   - Review Cadence (when this document should be updated)

3. **Given** `docs/risk-register.md` exists,
   **When** I read it,
   **Then** it contains a Markdown table with columns: `ID`, `Risk`, `Likelihood`, `Impact`, `Mitigation`, `Owner`, `Status` — and at minimum five rows covering:
   - R-1: Prompt injection
   - R-2: Incorrect date calculation (tool error)
   - R-3: Model provider outage
   - R-4: PII in user prompt
   - R-5: Hallucinated "today" date (model bypasses tool)
   And each row has non-placeholder content in all columns.

4. **Given** `docs/governance-charter.md` exists,
   **When** I read it,
   **Then** it contains:
   - A statement of who is responsible for the agent (Agent Owner role)
   - A statement of who is responsible for runtime operations (Agent Operator role)
   - A statement of who is responsible for compliance review (Agent Auditor role; may be the same person as Agent Owner for a demo)
   - The project's risk tolerance (explicit statement that this is a reference implementation, not for production regulated use without further controls)
   - The review trigger conditions (dependency update, model change, new tool added, security incident)

5. **Given** all three documents exist,
   **When** I read each one,
   **Then** none contains the literal string `TODO`, `PLACEHOLDER`, `TBD`, or `[to be completed]` (case-insensitive).

6. **Given** all three documents exist,
   **When** I read each one,
   **Then** each references the NIST AI RMF function it supports (GOVERN or MAP) either in its introduction or a footnote.

7. **Given** `docs/ai-system-card.md` references third-party components,
   **When** I cross-reference with `requirements.txt`,
   **Then** the Strands Agents SDK version listed in `ai-system-card.md` matches the pinned version in `requirements.txt` (`strands-agents==1.26.0`).

## Tasks / Subtasks

- [x] Task 1: Create `docs/ai-system-card.md` (AC: #1, #2, #5, #6, #7)
  - [x] Write System Purpose section: single-purpose agent calculating age in days from a date of birth
  - [x] Write Intended Users section: developers and solutions architects evaluating Strands Agents SDK + AWS AgentCore
  - [x] Write Out-of-Scope Uses: medical/legal age determination, identity verification, production PII handling without additional controls
  - [x] Write Third-Party Components: `strands-agents==1.26.0`, Amazon Bedrock (model inference), AWS AgentCore (deployment/serving), `python-dotenv>=1.0.0`, `boto3>=1.34.0`
  - [x] Write Data Flows: user prompt → BedrockModel → `get_today_date` tool (local stdlib call) → response. No user data persisted. No PII collected or stored.
  - [x] Write Harm Categories Considered table (minimum 5 rows from NIST AI 600-1 categories)
  - [x] Write Risk Tolerance Statement
  - [x] Write Human Oversight Mechanism
  - [x] Write Review Cadence
  - [x] Add NIST AI RMF reference (GOVERN + MAP functions)

- [x] Task 2: Create `docs/risk-register.md` (AC: #1, #3, #5, #6)
  - [x] Create Markdown table with required columns
  - [x] Add R-1 through R-5 rows as specified in AC #3
  - [x] Verify all cells are non-placeholder
  - [x] Add NIST AI RMF reference (MAP function)
  - [x] Add a brief introduction explaining what this document is and how to maintain it

- [x] Task 3: Create `docs/governance-charter.md` (AC: #1, #4, #5, #6)
  - [x] Write Agent Owner role definition and assignment
  - [x] Write Agent Operator role definition and assignment
  - [x] Write Agent Auditor role definition and assignment
  - [x] Write risk tolerance statement
  - [x] Write review trigger conditions
  - [x] Add NIST AI RMF reference (GOVERN function)

- [x] Task 4: Cross-reference verification (AC: #7)
  - [x] Confirm Strands SDK version in `ai-system-card.md` matches `requirements.txt`
  - [x] Confirm no TODO/PLACEHOLDER/TBD strings in any of the three files

## Dev Notes

### File Locations

All three deliverables go in the **existing** `docs/` directory at the project root:

```
strands-agents-demo/
  docs/
    ai-system-card.md         ← NEW (Task 1)
    risk-register.md          ← NEW (Task 2)
    governance-charter.md     ← NEW (Task 3)
```

The `docs/` directory currently exists and is empty. Do not create any subdirectories.

### Content Guidance for ai-system-card.md

The system card is the primary GOVERN + MAP artifact. It tells any developer, compliance reviewer, or stakeholder what this agent does, who it is for, what it will not do, and what risks have been considered.

**Harm categories to include** (drawn from NIST AI 600-1 twelve risk categories, scoped to this agent's actual risk surface):

| Harm Category | NIST AI 600-1 Risk | Likelihood for this agent | Impact |
|---|---|---|---|
| Prompt injection | Prompt injection | LOW — narrow tool surface | LOW |
| Hallucination | Confabulation | LOW — forced tool call | LOW |
| Harmful content | Harmful content generation | LOW — date calculator | LOW |
| PII exposure | Data privacy | LOW — no PII stored | MEDIUM |
| Incorrect date output | Output quality | LOW — verifiable | LOW |

Likelihood and Impact ratings should be LOW/MEDIUM/HIGH. For this agent, most are LOW because it has a single, deterministic tool and does not handle sensitive data.

**Risk Tolerance Statement wording example:**
> This agent is a developer reference implementation. It is designed for demonstration and educational use. It has not been assessed for regulated industry use cases (healthcare, finance, legal) or for deployment contexts where incorrect date calculations could cause harm. Organisations deploying a fork of this agent in production must conduct their own risk assessment.

### Content Guidance for risk-register.md

The risk register is the MAP artifact. Keep the table concise — this is a demo, not an enterprise deployment.

Recommended row content:

| ID | Risk | Likelihood | Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|
| R-1 | Prompt injection overrides system prompt | LOW | LOW | Narrow tool surface; Bedrock Guardrails (Epic 4, Story 4.3) | Dev | Open |
| R-2 | Tool error causes incorrect date calculation | LOW | LOW | `get_today_date` has try/except; unit tested | Dev | Mitigated |
| R-3 | Model provider outage | MEDIUM | MEDIUM | Multi-provider env var switching (Bedrock → Gemini) | Dev | Open |
| R-4 | PII inadvertently included in user prompt | LOW | MEDIUM | Bedrock Guardrails PII redaction (Epic 4, Story 4.3) | Dev | Open |
| R-5 | Agent hallucinates today's date instead of calling tool | LOW | LOW | System prompt explicitly instructs tool use; tested | Dev | Mitigated |

Note the forward references to Story 4.3 (Bedrock Guardrails) — these are intentional, showing that the risk register is a living document.

### Content Guidance for governance-charter.md

Keep this short — one to two pages. For a single-developer demo project, the same person may hold all three roles. That is explicitly acceptable; the point is to establish the accountability structure.

**Role definitions:**
- **Agent Owner** — the person accountable for the agent's outcomes and risk decisions. For this project: the developer/maintainer of the repository.
- **Agent Operator** — the person responsible for runtime health, monitoring, and incident response. For this project: same as Agent Owner.
- **Agent Auditor** — the person responsible for reviewing agent behaviour against documented policy. For this project: same as Agent Owner, with the expectation that any external contributor raising a compliance concern will be treated as a de facto auditor.

**Review triggers (when to update all three docs):**
1. A new dependency is added or an existing one is upgraded
2. The agent's model ID or model provider changes
3. A new `@tool` function is added (expands the capability and risk surface)
4. A security incident or unexpected agent behaviour is observed
5. Annually, regardless of changes

### Relationship to Subsequent Stories

- **Story 4.2** (Audit Hooks) will reference the risk register — specifically R-1 through R-5 — to explain which risks the audit log addresses.
- **Story 4.3** (Bedrock Guardrails) will close R-1 (prompt injection) and R-4 (PII) from open to mitigated.
- **Story 4.4** (Red-Team CI) will close or further mitigate R-1 and R-5.
- The system card's Third-Party Components section will need updating when `GUARDRAIL_ID` / `GUARDRAIL_VERSION` env vars are added in Story 4.3.

### Style Requirements

- All files: Markdown, consistent with the project's existing documentation style
- No emojis (consistent with existing project files)
- Clear section headings (##, ###)
- Tables use Markdown pipe syntax
- Writing tone: technical and factual — these are compliance artifacts, not marketing copy
- Length: `ai-system-card.md` ~150–250 lines, `risk-register.md` ~60–80 lines, `governance-charter.md` ~80–120 lines

### What NOT To Do

- Do not modify `agent.py`, `requirements.txt`, `.env.example`, or any implementation file outside `docs/` (BMAD tracking files such as `sprint-status.yaml` and the story file itself are exempt from this restriction)
- Do not run `black` or any formatter (these are Markdown files)
- Do not add a `docs/index.md` or any file not specified in the ACs
- Do not use placeholder content — every cell and section must contain real, project-specific information

## Architecture Compliance Notes

The existing architecture document (`_bmad-output/planning-artifacts/architecture.md`) defines the project structure. This story adds `docs/` files that are not referenced in the original architecture because NIST AI RMF compliance was out of scope at MVP. No architectural boundaries are violated — `docs/` is a documentation directory with no code dependencies.

The research document at `_bmad-output/planning-artifacts/research/technical-nist-ai-rmf-agents-research-2026-03-19.md` contains the full NIST AI RMF research and is the authoritative source for content guidance. The Phase 1 section ("Foundation Documentation") provides the detailed content specification this story implements.

## Definition of Done

- [x] `docs/ai-system-card.md` created with all required sections and non-placeholder content
- [x] `docs/risk-register.md` created with Markdown table and minimum 5 risk rows
- [x] `docs/governance-charter.md` created with role definitions, risk tolerance, and review triggers
- [x] All three files reference the NIST AI RMF function they support
- [x] No TODO/PLACEHOLDER/TBD strings in any file
- [x] Strands SDK version in `ai-system-card.md` matches `requirements.txt` (`strands-agents==1.26.0`)
- [x] No implementation files outside `docs/` have been modified (BMAD tracking files exempt)

## Dev Agent Record

### Completion Notes

Implemented 2026-03-20. Documentation-only story — three Markdown files created in `docs/`.

- `docs/ai-system-card.md`: 7 harm categories (H-1 through H-7) drawn from NIST AI 600-1, full data flow diagram, third-party component table with 7 entries including version pins matching `requirements.txt`, risk tolerance statement, human oversight mechanisms, and review cadence.
- `docs/risk-register.md`: 5 risks (R-1 through R-5) in a Markdown table with all required columns; R-2 and R-5 marked Mitigated (existing controls); R-1, R-3, R-4 marked Open with forward references to Story 4.3.
- `docs/governance-charter.md`: Three roles defined (Agent Owner, Agent Operator, Agent Auditor), risk tolerance statement (LOW–MEDIUM acceptable), 6 review trigger conditions, escalation/incident response procedure, and decommissioning procedure.

All AC verification checks passed:
- AC#1: `docs/` contains exactly 3 files
- AC#2: All 9 required sections present in `ai-system-card.md`
- AC#3: R-1 through R-5 present with non-placeholder content
- AC#4: All 3 governance charter elements present
- AC#5: No TODO/PLACEHOLDER/TBD strings found
- AC#6: All 3 files reference NIST AI RMF functions
- AC#7: `strands-agents==1.26.0` matches in both `ai-system-card.md` and `requirements.txt`

No implementation files outside `docs/` were modified. BMAD tracking files (`sprint-status.yaml`, story file) were updated as standard workflow bookkeeping.

## File List

- `docs/ai-system-card.md` (new)
- `docs/risk-register.md` (new)
- `docs/governance-charter.md` (new)

## Change Log

| Date | Change |
|---|---|
| 2026-03-20 | Story 4.1 implemented — created `docs/ai-system-card.md`, `docs/risk-register.md`, `docs/governance-charter.md` |
