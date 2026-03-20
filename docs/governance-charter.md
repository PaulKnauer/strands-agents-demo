# Governance Charter — Age-in-Days Agent

_NIST AI RMF Function: GOVERN_

This document establishes the governance structure for the Age-in-Days Agent reference implementation. It defines accountability roles, risk tolerance, and the conditions under which the governance documentation must be reviewed.

---

## Purpose

This charter exists to ensure that the AI system deployed in this project has clearly defined accountability, documented risk boundaries, and a review process — regardless of the size or informality of the development team. For a single-developer demo project, the same individual may hold all three roles defined below. That is explicitly acceptable; the purpose is to establish the accountability structure so it can scale when needed.

This charter supports NIST AI RMF GOVERN function subcategories 1.1 (legal and regulatory compliance), 1.3 (risk tolerance), 1.4 (transparent risk management process), and 1.7 (roles and responsibilities).

---

## Accountability Roles

### Agent Owner

**Definition:** The Agent Owner is the person accountable for the agent's outcomes, risk decisions, and overall alignment with its intended purpose. The Agent Owner has authority to approve changes to the agent's capability surface (new tools, new model providers), risk tolerance, and deployment configuration.

**Responsibilities:**
- Approving changes to the system card, risk register, and governance charter
- Making risk acceptance decisions for open risks in the risk register
- Ensuring the agent is decommissioned or updated when it no longer meets the risk tolerance defined in this charter
- Authorising the addition of new tools or changes to the system prompt

**Current assignment:** The developer and maintainer of the strands-agents-demo repository.

---

### Agent Operator

**Definition:** The Agent Operator is the person responsible for the day-to-day runtime health of the agent — monitoring its operational status, responding to incidents, and executing operational procedures (deployment, restart, decommissioning).

**Responsibilities:**
- Monitoring the agent's operational status when deployed to AWS AgentCore
- Executing deployment and redeployment procedures via `deploy/deploy.py`
- Responding to unexpected agent behaviour or runtime errors
- Escalating incidents that may represent new risks to the Agent Owner
- Executing the decommissioning procedure if the agent exceeds risk tolerance thresholds

**Current assignment:** Same as Agent Owner (single-developer project).

---

### Agent Auditor

**Definition:** The Agent Auditor is the person (or function) responsible for reviewing agent behaviour against documented policy — verifying that the agent operates within its defined scope, that risks are accurately documented, and that mitigations are effective.

**Responsibilities:**
- Reviewing the risk register at each defined review trigger
- Verifying that automated red-team CI tests (introduced in Story 4.4) are passing and accurately reflect risk coverage
- Raising compliance concerns when observed agent behaviour diverges from the system card's documented scope
- Reviewing pull requests that modify `agent.py`, `deploy/`, or any file in `docs/` for compliance implications

**Current assignment:** Same as Agent Owner (single-developer project). Any external contributor who raises a compliance concern via a GitHub issue or pull request comment is treated as a de facto auditor for that concern.

---

## Risk Tolerance

_NIST AI RMF GOVERN-1.3._

This project is a developer reference implementation. Its deployment context is demonstration and education. Its user base is technically proficient developers who understand they are interacting with an AI agent.

**Acceptable risk level:** LOW to MEDIUM. Risks rated MEDIUM are acceptable provided:
1. A mitigation is documented in the risk register, and
2. The mitigation is either already implemented or scheduled for implementation in an identified story.

**Not acceptable:** Any risk rated HIGH without an immediate remediation plan. Any risk involving exposure of real user credentials or secrets. Any risk that could cause the agent to take autonomous actions beyond returning a text response.

**Scope limitation:** This risk tolerance applies to the agent as a reference implementation. Organisations forking this project for production deployment in regulated industries (healthcare, finance, legal, government) must conduct their own risk assessment. The Agent Owner of a production fork is responsible for establishing an appropriate risk tolerance for that deployment context.

---

## Review Trigger Conditions

_NIST AI RMF GOVERN-1.4._

The system card (`docs/ai-system-card.md`), risk register (`docs/risk-register.md`), and this governance charter must be reviewed and updated when any of the following conditions occur:

1. **Dependency change:** A new dependency is added to `requirements.txt`, or an existing dependency is upgraded to a major or security-relevant version.
2. **Model change:** The agent's `MODEL_ID` or `MODEL_PROVIDER` is changed in `.env.example` or the architecture documentation.
3. **Tool surface change:** A new `@tool` function is added to `agent.py` or any tool is removed. Each new tool expands the agent's capability and risk surface.
4. **Security incident:** Any unexpected agent behaviour, suspected prompt injection, or unintended data disclosure is observed during testing or operation.
5. **Epic or story with compliance implications:** A story materially changes the agent's data flows, deployment configuration, or risk controls (e.g., adding Bedrock Guardrails in Story 4.3 closes open risks in the register).
6. **Annual review:** Regardless of changes, the documentation is reviewed at least once per calendar year to confirm it accurately reflects the current system.

---

## Escalation and Incident Response

If an incident is observed that suggests the agent is operating outside its documented scope or risk tolerance:

1. **Immediately** stop the agent (type `exit` in the REPL, or pause/decommission the AgentCore runtime via the AWS console or CLI).
2. **Document** the incident: what was observed, when, what input triggered it.
3. **Assess** whether the incident represents a new risk not in the register, or a failure of an existing mitigation.
4. **Update** the risk register with the new finding.
5. **Notify** the Agent Owner (in a single-developer project, this is self-notification; in a multi-contributor project, open a GitHub issue tagged `compliance`).
6. **Resolve** before redeploying: implement a mitigation, update the risk register, and confirm the incident is not reproducible.

---

## Decommissioning

The agent should be decommissioned (AgentCore runtime deleted, deployment artifacts removed) when:

- The project is no longer actively maintained and the AgentCore runtime continues to incur cost
- A HIGH-rated risk is identified that cannot be mitigated within an acceptable timeframe
- The underlying Strands SDK or AgentCore service reaches end-of-life and cannot be updated

Decommissioning procedure: run `aws bedrock-agentcore delete-agent-runtime --agent-runtime-id <id>` or use the AgentCore console. Remove the endpoint URL from any documentation or shared configuration.

---

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-20 | Initial governance charter created as part of Epic 4, Story 4.1 | Paul |

---

_This document supports NIST AI RMF function **GOVERN** (subcategories 1.1, 1.3, 1.4, 1.7, 6.1)._

_Reference: NIST AI 100-1 (AI RMF 1.0)._
