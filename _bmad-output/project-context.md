---
project_name: 'strands-agents-demo'
user_name: 'Paul'
date: '2026-05-14'
sections_completed:
  [
    'technology_stack',
    'language_rules',
    'framework_rules',
    'testing_rules',
    'quality_rules',
    'workflow_rules',
    'anti_patterns',
  ]
existing_patterns_found: 10
status: 'complete'
rule_count: 22
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- Python local runtime: 3.11+
- AgentCore runtime: `PYTHON_3_12`
- Local agent framework: `strands-agents==1.26.0`
- Tool helpers: `strands-agents-tools`
- Env loading: `python-dotenv~=1.0.1`
- AWS SDK: `boto3~=1.34.0`
- Cloud runtime SDK: `bedrock-agentcore`
- Test/config parsing: `pyyaml~=6.0`
- Test runner: `pytest`
- Formatting: `black`

## Critical Implementation Rules

### Language-Specific Rules

- Call `load_dotenv()` before any `os.environ` access in local/deploy entrypoints. This is a deliberate fail-fast config pattern.
- Prefer `os.environ[...]` when the variable is required and misconfiguration should hard-fail immediately.
- Keep `agent.py` lean; static tests enforce it stays under 150 lines.
- Return error strings rather than raising from tool helpers such as date retrieval paths.
- Use small, purposeful comments only where runtime behavior is non-obvious.

### Framework-Specific Rules

- Treat `agent.py` and `deploy/app.py` as separate runtime paths with different constraints.
- `agent.py` is the local REPL path and uses Strands abstractions.
- `deploy/app.py` is the AgentCore cloud path and uses direct Bedrock Converse API calls via `boto3`, not Strands.
- Do not import `strands-agents` into `deploy/app.py`; the deployment bundle is intentionally built around `bedrock-agentcore` and bundled wheels.
- Keep the local and cloud system prompts behaviorally aligned unless there is an explicit reason to diverge.
- In AgentCore, `app.run(host="0.0.0.0")` must remain unconditional; guarding it behind `__main__` breaks startup health checks.

### Provider And Model Rules

- Current provider abstraction is explicit: `MODEL_PROVIDER` plus `MODEL_ID`.
- Local adapter code supports `bedrock`, `gemini`, `llama`, and `litellm` (exploratory local-only evaluation boundary); all other local provider values raise `ValueError`.
- Deployed AgentCore code supports `bedrock` and `llama` (both Bedrock-backed via Converse); other deployed provider values return an explicit unsupported-provider error before Bedrock invocation.
- `llama` is a Bedrock-backed family alias (Meta Llama 3.1 70B Instruct via Amazon Bedrock); it is not a direct Meta API integration. Enabled as of Story 4.3.
- `litellm` is an exploratory local-only evaluation boundary (Story 4.4). It is not deployable through AgentCore. It requires `pip install 'strands-agents[litellm]'` and provider-specific credentials. Do not treat it as a production-aligned default or as parity with the Bedrock-first path.
- Future post-Story-4.5 expansion targets Gemma, Moonshot/Kimi, Qwen, and DeepSeek through Amazon Bedrock; these are future work, not currently configured providers.
- Adding any new provider requires extending the abstraction, tests, docs, deployment assumptions, and verification strategy together — never a one-file edit. Specifically: update `model_adapters.py` registry, `README.md` support matrix and verification table, `.env.example` provider labels, deployed runtime provider check, IAM/model ARN handling, and the relevant unit + static tests in a single coordinated change.
- Do not assume a model change is local-only. Bedrock/AgentCore deployment, IAM scopes, `.env.example`, README, and tests are coupled to provider choices.
- Bedrock guardrails are optional and must only be wired when `GUARDRAIL_ID` is set.
- If provider support differs between local and deployed runtimes, document that boundary explicitly rather than hiding it behind silent fallbacks.

### Local Adapter Registry Convention (Story 4.2+)

- `model_adapters.py` owns a `ModelCapabilities` frozen dataclass registry (`_REGISTRY`) that is the single source of truth for provider/family capability metadata.
- `supported_local_providers()` returns provider keys where `enabled=True` and `"local"` is in `runtimes`; a provider enabled only for a deployed runtime will not appear.
- `planned_model_families()` returns provider keys that are planned but not yet enabled.
- `get_model_capabilities(provider)` returns the `ModelCapabilities` entry or `None` for unknown keys.
- Planned family metadata (`enabled=False`) must not imply runnable provider support; `create_local_model_adapter()` raises `ValueError` with "planned candidate" language for these entries.
- The deployed runtime (`deploy/app.py`) must not import or use the local registry; it uses its own explicit provider check for Bedrock-backed providers (`bedrock` and `llama`).

### Testing Rules

- Preserve the contract-test mindset: scaffold files and repo conventions are enforced by static tests, not just behavioral tests.
- Unit tests mock cloud SDKs; do not relabel mock-only tests as integration tests.
- `tests/conftest.py` stubs `bedrock_agentcore` before imports. Keep that pattern intact when changing cloud entrypoints.
- Keep deterministic evals separate from live evals; live LLM tests must remain opt-in via pytest markers.
- When changing provider logic, add or update tests in both local agent and deployed runtime paths if both are affected.

### Code Quality & Style Rules

- Follow existing file naming and module layout: top-level app entrypoints, `deploy/` for cloud runtime/deployment code, `infra/` for CDK support, `tests/unit` and `tests/evals` for test split.
- Preserve simple procedural structure over premature abstraction unless complexity clearly justifies extraction.
- Use ASCII unless the file already relies on Unicode; this repo mostly uses ASCII source with occasional README symbols.
- Maintain `.env.example` as documentation-only scaffolding with no real secrets.
- Keep developer setup copy-pasteable through `Makefile` targets and README examples.

### Deployment Workflow Rules

- AgentCore deployment packaging is intentional: bundle `deploy/app.py` and Linux wheels, not `agent.py`.
- Do not remove the manylinux/cp312 wheel install logic from `deploy/deploy.py`; it exists to avoid runtime import failures.
- Preserve least-privilege IAM scoping where model ARNs and AgentCore resources are targeted explicitly.
- Respect AWS region special cases already encoded in deploy logic, especially `us-east-1` S3 bucket creation.
- Re-deploy behavior must remain idempotent; update existing resources rather than duplicating them.

### Critical Don't-Miss Rules

- Do not collapse local Strands execution and deployed Bedrock Converse execution into one path unless you can prove AgentCore startup/runtime constraints still hold.
- Do not add silent provider defaults that hide missing env vars or unsupported model/runtime combinations.
- Do not break system-prompt parity, tool protocol ordering, or guardrail propagation across Converse turns; tests assert these details.
- Do not commit `.env`, generated secrets, promptfoo outputs, or deployment artifacts already covered by `.gitignore`.
- Do not change `.env.example`, `Makefile`, or deployment scripts without checking the corresponding static/unit tests.

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code.
- Treat provider/model changes as cross-cutting architecture work, not a one-file edit.
- When in doubt, preserve runtime separation and the existing test contracts.
- Update this file when new provider/runtime rules become stable project conventions.

**For Humans:**

- Keep this file focused on non-obvious implementation constraints.
- Update it when provider support, deployment model, or testing contracts change.
- Remove rules that become obsolete after the multi-provider refactor lands.

Last Updated: 2026-05-15
