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
	@echo "    make deploy       Deploy agent to AWS AgentCore"
	@echo "    make verify       Invoke deployed agent and verify response"
	@echo "    make teardown     Remove all AWS resources created by deploy"
	@echo "    make redteam      Run promptfoo red-team scan (requires Node.js + AWS creds)"
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
	$(BLACK) agent.py deploy/deploy.py deploy/app.py deploy/teardown.py deploy/verify.py

.PHONY: lint
lint:
	$(BLACK) --check agent.py deploy/deploy.py deploy/app.py deploy/verify.py

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

.PHONY: deploy
deploy:
	$(PYTHON) deploy/deploy.py

.PHONY: verify
verify:
	$(PYTHON) deploy/verify.py

.PHONY: teardown
teardown:
	$(PYTHON) deploy/teardown.py

.PHONY: redteam
redteam:
	npx promptfoo@0.121.2 redteam run --config compliance/promptfoo-redteam.yaml --output compliance/redteam-report.json

# ── Housekeeping ─────────────────────────────────────────────────────────────

.PHONY: clean
clean:
	rm -rf venv
	find . -type d -name __pycache__ -not -path './_bmad/*' -not -path './.claude/*' -exec rm -rf {} +
	find . -name '*.pyc' -not -path './_bmad/*' -not -path './.claude/*' -delete
	@echo "  ✅ Cleaned venv and compiled Python files."
