# Use venv binaries when available (local dev); fall back to PATH (CI / no venv)
PYTHON  := $(shell test -f venv/bin/python && echo venv/bin/python || echo python)
PIP     := $(shell test -f venv/bin/pip && echo venv/bin/pip || echo pip)
BLACK   := $(shell test -f venv/bin/black && echo venv/bin/black || echo black)

# ── Help ─────────────────────────────────────────────────────────────────────

.PHONY: help
help:
	@echo ""
	@echo "  strands-agents-demo"
	@echo ""
	@echo "  Setup"
	@echo "    make install      Create venv and install dependencies"
	@echo "    make env          Copy .env.example → .env (skips if .env exists)"
	@echo ""
	@echo "  Development"
	@echo "    make run          Run the age-in-days agent (local REPL)"
	@echo "    make format       Auto-format Python files with black"
	@echo "    make lint         Check formatting with black (no changes)"
	@echo "    make test         Run unit + eval tests"
	@echo "    make test-unit    Run unit tests only"
	@echo "    make test-evals   Run deterministic evals (no AWS required)"
	@echo "    make test-evals-live  Run all evals including live LLM"
	@echo ""
	@echo "  Deployment"
	@echo "    make guardrail    Create/update Bedrock Guardrail stack and print outputs"
	@echo "    make redteam-role Deploy GitHub Actions OIDC role for scheduled red-team CI"
	@echo "    make transaction-search Enable CloudWatch Transaction Search for AgentCore observability"
	@echo "    make create-role  Deploy AgentCore runtime IAM role via CDK"
	@echo "    make deploy       Deploy agent to AWS AgentCore"
	@echo "    make verify       Invoke deployed agent and verify response"
	@echo "    make teardown     Remove all AWS resources created by deploy"
	@echo "    make teardown-role Remove AgentCore runtime IAM role stack"
	@echo "    make teardown-redteam-role  Remove GitHub Actions OIDC role stack"
	@echo "    make teardown-transaction-search  Disable Transaction Search CDK stack resources"
	@echo "    make redteam      Run promptfoo red-team scan (requires Node.js + AWS auth)"
	@echo "    make dashboard    Create/update CloudWatch NIST-RMF compliance dashboard"
	@echo ""
	@echo "  Housekeeping"
	@echo "    make clean        Remove venv and compiled Python files"
	@echo ""

# ── Setup ────────────────────────────────────────────────────────────────────

.PHONY: install
install:
	python3 -m venv venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo ""
	@echo "  ✅ Dependencies installed. Run 'make env' if you haven't set up .env yet."

.PHONY: env
env:
	@if [ -f .env ]; then \
		echo "  .env already exists — skipping. Edit it directly if needed."; \
	else \
		cp .env.example .env; \
		echo "  ✅ .env created from .env.example — fill in your values before running."; \
	fi

# ── Development ──────────────────────────────────────────────────────────────

.PHONY: run
run:
	$(PYTHON) agent.py

.PHONY: format
format:
	$(BLACK) agent.py deploy/deploy.py deploy/app.py deploy/teardown.py deploy/verify.py deploy/create_dashboard.py infra/app.py infra/agentcore_runtime_role_stack.py infra/github_actions_stack.py infra/transaction_search_stack.py

.PHONY: lint
lint:
	$(BLACK) --check agent.py deploy/deploy.py deploy/app.py deploy/verify.py deploy/create_dashboard.py infra/app.py infra/agentcore_runtime_role_stack.py infra/github_actions_stack.py infra/transaction_search_stack.py

.PHONY: test-unit
test-unit:
	$(PYTHON) -m pytest tests/unit/ -v

.PHONY: test-evals
test-evals:
	$(PYTHON) -m pytest tests/evals/ -v -m "not eval"

.PHONY: test-evals-live
test-evals-live:
	$(PYTHON) -m pytest tests/evals/ -v

.PHONY: test
test: test-unit test-evals

# ── Deployment ───────────────────────────────────────────────────────────────

.PHONY: guardrail
guardrail:
	aws cloudformation deploy --template-file deploy/guardrail.yaml --stack-name strands-demo-guardrail --region $${AWS_REGION:-us-east-1}
	aws cloudformation describe-stacks --stack-name strands-demo-guardrail --region $${AWS_REGION:-us-east-1} --query 'Stacks[0].Outputs[].[OutputKey,OutputValue]' --output table

.PHONY: redteam-role
redteam-role:
	$(PIP) install -r infra/requirements.txt
	npx --yes aws-cdk@2 deploy StrandsDemoGithubActionsStack --app "$(PYTHON) infra/app.py" --require-approval never

.PHONY: transaction-search
transaction-search:
	$(PIP) install -r infra/requirements.txt
	npx --yes aws-cdk@2 deploy StrandsDemoTransactionSearchStack --app "$(PYTHON) infra/app.py" --require-approval never

.PHONY: teardown-redteam-role
teardown-redteam-role:
	$(PIP) install -r infra/requirements.txt
	npx --yes aws-cdk@2 destroy StrandsDemoGithubActionsStack --app "$(PYTHON) infra/app.py" --force

.PHONY: teardown-transaction-search
teardown-transaction-search:
	$(PIP) install -r infra/requirements.txt
	npx --yes aws-cdk@2 destroy StrandsDemoTransactionSearchStack --app "$(PYTHON) infra/app.py" --force

.PHONY: create-role
create-role:
	$(PIP) install -r infra/requirements.txt
	npx --yes aws-cdk@2 deploy StrandsDemoAgentCoreRuntimeRoleStack --app "$(PYTHON) infra/app.py" --require-approval never

.PHONY: teardown-role
teardown-role:
	$(PIP) install -r infra/requirements.txt
	npx --yes aws-cdk@2 destroy StrandsDemoAgentCoreRuntimeRoleStack --app "$(PYTHON) infra/app.py" --force

.PHONY: deploy
deploy: create-role
	$(PYTHON) deploy/deploy.py

.PHONY: verify
verify:
	$(PYTHON) deploy/verify.py

.PHONY: teardown
teardown:
	$(PYTHON) deploy/teardown.py

.PHONY: redteam
redteam:
	GUARDRAIL_VERSION=$${GUARDRAIL_VERSION:-DRAFT} $(PYTHON) compliance/prepare_promptfoo_config.py
	GUARDRAIL_VERSION=$${GUARDRAIL_VERSION:-DRAFT} npx promptfoo@0.121.2 redteam run --config compliance/promptfoo-redteam.ci.yaml --output compliance/redteam-report.json

.PHONY: dashboard
dashboard:
	$(PYTHON) deploy/create_dashboard.py

# ── Housekeeping ─────────────────────────────────────────────────────────────

.PHONY: clean
clean:
	rm -rf venv
	rm -rf cdk.out
	find . -type d -name __pycache__ -not -path './_bmad/*' -not -path './.claude/*' -exec rm -rf {} +
	find . -name '*.pyc' -not -path './_bmad/*' -not -path './.claude/*' -delete
	@echo "  ✅ Cleaned venv and compiled Python files."
