---
name: AgentCore deployment hard-won learnings
description: Critical technical discoveries from deploying to AgentCore PYTHON_3_12 runtime — use as checklist when modifying deploy/deploy.py or deploy/app.py
type: project
---

The AgentCore PYTHON_3_12 runtime has these non-obvious requirements discovered through debugging story 2-2:

1. **Bundle ALL dependencies** — do NOT assume boto3/botocore are pre-installed. Bundle everything with `pip install --target pkg_dir --platform manylinux2014_aarch64 --python-version 312 --only-binary :all:` to get Linux ARM64-compatible wheels.
2. **ARM64, not x86_64** — the runtime runs on Linux ARM64 (aarch64). Using x86_64 wheels causes UPDATE_FAILED.
3. **Exclude .pyc/__pycache__** — Python bytecache compiled on a different Python version is incompatible. AgentCore rejects the zip with "Python cache files incompatible" error.
4. **host="0.0.0.0" required** — `BedrockAgentCoreApp.run()` defaults to `127.0.0.1` unless it detects Docker (`/.dockerenv` or `DOCKER_CONTAINER` env var). AgentCore's container runtime is NOT Docker, so pass `host="0.0.0.0"` explicitly or the health check (`/ping`) is unreachable and every invocation times out with "Runtime initialization time exceeded".
5. **Use Python 3.12 locally** — recreate venv with Python 3.12 to match the runtime exactly and avoid .pyc incompatibilities.
6. **No CloudWatch logs by default** — AgentCore doesn't create a log group automatically; debug 500 errors by testing the Bedrock call locally first.

**Why:** Discovered through multiple failed deploy iterations on 2026-03-18.
**How to apply:** Use as a checklist when modifying deploy/deploy.py or deploy/app.py for this project.
