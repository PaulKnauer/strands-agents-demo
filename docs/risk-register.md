# Risk Register — Age-in-Days Agent

_NIST AI RMF Function: MAP_

This document is the risk register for the Age-in-Days Agent reference implementation. It enumerates identified risks across all system components, their likelihood and impact ratings, current mitigations, and open/mitigated status.

This register is a living document. It must be updated whenever:
- A new risk is identified
- A risk's mitigation status changes (e.g., a Story in Epic 4 delivers a control that closes an open risk)
- The system's capability or deployment context changes

**Likelihood and Impact ratings:** LOW / MEDIUM / HIGH, assessed relative to a developer demonstration context.

**Status values:**
- `Open` — risk identified, mitigation not yet implemented
- `Mitigated` — a control is in place that sufficiently reduces the risk
- `Accepted` — risk acknowledged and accepted without mitigation (with rationale)

---

## Risk Register

| ID | Risk | Likelihood | Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|
| R-1 | Prompt injection overrides the system prompt or causes the agent to behave outside its intended purpose | LOW | LOW | Narrow tool surface (one deterministic tool with no write access or external network calls); Bedrock Guardrails PROMPT_ATTACKS filter at HIGH strength (deployed in Epic 4, Story 4.3); automated red-team CI tests delivered in Story 4.4 (see `tests/unit/test_safety_boundaries.py` and `compliance/promptfoo-redteam.yaml`) | Dev | Mitigated |
| R-2 | Tool error in `get_today_date` causes the agent to return an incorrect or missing age calculation | LOW | LOW | `get_today_date` wraps `datetime.date.today()` in a try/except and returns a descriptive error string on failure; unit tested in `tests/unit/test_agent_tool.py` | Dev | Mitigated |
| R-3 | Amazon Bedrock model provider outage causes the agent to be unavailable | MEDIUM | MEDIUM | Multi-provider fallback: switching to Google Gemini requires only a change to `MODEL_PROVIDER` and `MODEL_ID` environment variables and `pip install strands-agents[gemini]`; no code modification required | Dev | Open |
| R-4 | User inadvertently includes personally identifiable information (date of birth or other PII) in their prompt, which is transmitted to Amazon Bedrock | LOW | MEDIUM | No PII is stored or logged by the agent code; Bedrock Guardrails PII anonymisation (EMAIL, PHONE — ANONYMIZE action) deployed in Epic 4, Story 4.3; users are informed in README that prompts are sent to Bedrock | Dev | Mitigated |
| R-5 | The language model hallucinates today's date instead of invoking `get_today_date`, producing an incorrect age calculation | LOW | LOW | System prompt explicitly instructs the agent to call the `get_today_date` tool before calculating age; behavioral contract tests in `tests/evals/test_behavioral_contracts.py` validate tool invocation on valid date input | Dev | Mitigated |

---

## Notes on Open Risks

**R-3 (Provider outage):** Assessed as MEDIUM likelihood over the lifetime of a deployed agent; the fallback path to Gemini is documented and tested but not automated. An operational runbook for switching providers would close this risk further.

## Notes on Mitigated Risks

**R-1 (Prompt injection):** Mitigated by Bedrock Guardrails PROMPT_ATTACKS filter at HIGH strength (deployed in Story 4.3 via `deploy/guardrail.yaml`). Automated red-team CI tests delivered in Story 4.4: deterministic safety boundary tests run on every push (`tests/unit/test_safety_boundaries.py`); adversarial promptfoo probe suite runs weekly and on demand (`compliance/promptfoo-redteam.yaml`, `make redteam`).

**R-4 (PII transmission):** Mitigated by Bedrock Guardrails PII anonymisation (EMAIL and PHONE entities set to ANONYMIZE action, deployed in Story 4.3). The anonymisation action redacts sensitive values before they reach the model or the audit trail while allowing the agent to respond helpfully.

---

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-20 | Initial risk register created as part of Epic 4, Story 4.1 | Paul |
| 2026-03-20 | R-1 and R-4 updated to Mitigated — Bedrock Guardrails deployed in Story 4.3 | Paul |
| 2026-03-21 | R-1 mitigation note updated — red-team CI delivered in Story 4.4 | Paul |

---

_This document supports NIST AI RMF function **MAP** (subcategories 1.1, 2.2, 5.1)._

_Reference: NIST AI 100-1 (AI RMF 1.0), NIST AI 600-1 (Generative AI Profile, July 2024)._
