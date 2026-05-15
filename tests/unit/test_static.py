"""Static file contract tests — verifies scaffold files satisfy their Story ACs.

AC #2 (Story 1.1): requirements.txt contains pinned/minimum deps.
AC #3 (Story 1.1): .env.example contains required section headers, variables, and
descriptive comments for the scaffold contract.
AC #5 (Story 1.1): .gitignore excludes .env, __pycache__/, .venv/, *.pyc.
AC #1 (Story 1.4): .vscode/launch.json has type=debugpy, console=integratedTerminal, envFile.
AC #1 (Story 1.4): .vscode/extensions.json recommends ms-python.python and vscode-pylance.
AC #6 (Story 1.2): agent.py is under 150 lines.

AC references: Story 3.3 AC #6.
"""

import json
import pathlib
import ast

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
assert (
    PROJECT_ROOT / "agent.py"
).exists(), f"PROJECT_ROOT resolved incorrectly: {PROJECT_ROOT}"


# ── requirements.txt ─────────────────────────────────────────────────────────


class TestRequirementsTxt:
    def _content(self) -> str:
        return (PROJECT_ROOT / "requirements.txt").read_text()

    def test_strands_agents_is_pinned(self):
        """AC #2 (Story 1.1): strands-agents must be pinned to exact version."""
        assert "strands-agents==1.26.0" in self._content()

    def test_contains_strands_agents_tools(self):
        """AC #2 (Story 1.1): strands-agents-tools must be present."""
        assert "strands-agents-tools" in self._content()

    def test_contains_python_dotenv(self):
        """AC #2 (Story 1.1): python-dotenv must be present."""
        assert "python-dotenv" in self._content()

    def test_contains_boto3(self):
        """AC #2 (Story 1.1): boto3 must be present."""
        assert "boto3" in self._content()

    def test_contains_bedrock_agentcore(self):
        """AC #2 (Story 1.1): bedrock-agentcore (deploy dependency) must be present."""
        assert "bedrock-agentcore" in self._content()


# ── .env.example ─────────────────────────────────────────────────────────────


class TestEnvExample:
    def _content(self) -> str:
        return (PROJECT_ROOT / ".env.example").read_text()

    def _lines(self) -> list[str]:
        return (PROJECT_ROOT / ".env.example").read_text().splitlines()

    def _line_index(self, expected: str) -> int:
        lines = self._lines()
        assert expected in lines, f"Missing line in .env.example: {expected}"
        return lines.index(expected)

    def test_has_llm_configuration_section(self):
        """AC #3 (Story 1.1): LLM Configuration section header must be present."""
        assert "# --- LLM Configuration ---" in self._content()

    def test_has_aws_configuration_section(self):
        """AC #3 (Story 1.1): AWS Configuration section header must be present."""
        assert "# --- AWS Configuration" in self._content()

    def test_has_agentcore_deployment_section(self):
        """AC #3 (Story 1.1): AgentCore Deployment section header must be present."""
        assert "# --- AgentCore Deployment ---" in self._content()

    def test_has_google_gemini_section(self):
        """AC #3 (Story 1.1): Optional Google Gemini section header must be present."""
        assert "# --- Optional: Google Gemini" in self._content()

    def test_has_model_provider_variable(self):
        assert "MODEL_PROVIDER" in self._content()

    def test_has_model_id_variable(self):
        assert "MODEL_ID" in self._content()

    def test_has_aws_region_variable(self):
        assert "AWS_REGION" in self._content()

    def test_has_agent_name_variable(self):
        assert "AGENT_NAME" in self._content()

    def test_has_google_api_key_variable(self):
        assert "GOOGLE_API_KEY" in self._content()

    def test_aws_region_has_description_comment_directly_above(self):
        """AC #3 (Story 1.1): AWS_REGION must have a direct description comment."""
        lines = self._lines()
        index = self._line_index("AWS_REGION=us-east-1")
        assert lines[index - 1] == (
            "# AWS region for Bedrock API calls and AgentCore deployment"
        )

    def test_google_api_key_has_description_comment_directly_above(self):
        """AC #3 (Story 1.1): GOOGLE_API_KEY must have a direct description comment."""
        lines = self._lines()
        index = self._line_index("# GOOGLE_API_KEY=your-gemini-api-key-here")
        assert lines[index - 1] == (
            "# Your Google AI Studio API key (required when MODEL_PROVIDER=gemini)"
        )

    def test_model_provider_comment_mentions_supported_providers(self):
        """AC #3 (Story 1.1): MODEL_PROVIDER comment must document provider choices."""
        lines = self._lines()
        index = self._line_index("MODEL_PROVIDER=bedrock")
        assert lines[index - 1] == (
            '# Provider: "bedrock" (Amazon Bedrock), "gemini" (Google Gemini), or "llama" (Meta Llama via Bedrock)'
        )

    def test_model_id_comment_mentions_bedrock_and_gemini(self):
        """AC #3 (Story 1.1): MODEL_ID comment must cover both local model paths."""
        content = self._content()
        assert '# Model ID — Bedrock: "us.amazon.nova-micro-v1:0"' in content
        assert '#           — Gemini: "gemini-2.0-flash"' in content

    def test_planned_provider_comment_marks_future_expansion(self):
        """AC #2 (Story 4.1): planned model families must not read as enabled providers."""
        content = self._content()
        assert "Planned additions (not yet enabled)" in content
        for family in ("Gemma", "Moonshot/Kimi", "Qwen", "DeepSeek"):
            assert family in content
        assert "will fail explicitly" in content
        assert "local adapter selection raises ValueError" in content

    def test_agent_name_comment_mentions_idempotency(self):
        """AC #3 (Story 1.1): AGENT_NAME comment must describe deployment naming intent."""
        lines = self._lines()
        index = self._line_index("AGENT_NAME=age-in-days-demo")
        assert lines[index - 1] == (
            "# Name for your agent in AgentCore (used for idempotency check)"
        )

    def test_no_real_aws_key_id(self):
        """AC #3 (Story 1.1): .env.example must not contain real AWS access key IDs."""
        content = self._content()
        # Real AWS key IDs start with AKIA, ASIA, or AROA followed by 16 uppercase chars
        import re

        assert not re.search(
            r"\b(AKIA|ASIA|AROA)[A-Z0-9]{16}\b", content
        ), ".env.example appears to contain a real AWS access key ID"


# ── .gitignore ────────────────────────────────────────────────────────────────


class TestGitignore:
    def _content(self) -> str:
        return (PROJECT_ROOT / ".gitignore").read_text()

    def test_excludes_dotenv(self):
        """AC #5 (Story 1.1): .env must be in .gitignore."""
        assert ".env" in self._content()

    def test_excludes_pycache(self):
        """AC #5 (Story 1.1): __pycache__/ must be in .gitignore."""
        assert "__pycache__/" in self._content()

    def test_excludes_venv(self):
        """AC #5 (Story 1.1): .venv/ must be in .gitignore."""
        assert ".venv/" in self._content()

    def test_excludes_pyc(self):
        """AC #5 (Story 1.1): *.pyc (or broader *.py[cod]) must be in .gitignore."""
        content = self._content()
        # Accept either exact *.pyc or the broader glob *.py[cod] which covers pyc/pyo/pyd
        assert "*.pyc" in content or "*.py[cod]" in content


# ── .vscode/launch.json ───────────────────────────────────────────────────────


class TestVSCodeLaunchJson:
    def _config(self) -> dict:
        path = PROJECT_ROOT / ".vscode" / "launch.json"
        return json.loads(path.read_text())

    def _first_config(self) -> dict:
        configs = self._config().get("configurations", [])
        assert configs, ".vscode/launch.json has no configurations"
        return configs[0]

    def test_type_is_debugpy(self):
        """AC #1 (Story 1.4): debugger type must be debugpy."""
        assert self._first_config()["type"] == "debugpy"

    def test_request_is_launch(self):
        """AC #1 (Story 1.4): debugger request must launch agent.py."""
        assert self._first_config()["request"] == "launch"

    def test_console_is_integrated_terminal(self):
        """AC #2 (Story 1.4): console must be integratedTerminal (required for input() REPL)."""
        assert self._first_config()["console"] == "integratedTerminal"

    def test_env_file_references_dotenv(self):
        """AC #1 (Story 1.4): envFile must reference .env."""
        env_file = self._first_config().get("envFile", "")
        assert env_file == "${workspaceFolder}/.env"

    def test_program_points_to_agent_py(self):
        """AC #1 (Story 1.4): program must launch agent.py."""
        program = self._first_config().get("program", "")
        assert program == "${workspaceFolder}/agent.py"


# ── .vscode/extensions.json ───────────────────────────────────────────────────


class TestVSCodeExtensionsJson:
    def _recommendations(self) -> list:
        path = PROJECT_ROOT / ".vscode" / "extensions.json"
        return json.loads(path.read_text()).get("recommendations", [])

    def test_recommends_python_extension(self):
        """AC #1 (Story 1.4): ms-python.python must be recommended."""
        assert "ms-python.python" in self._recommendations()

    def test_recommends_pylance(self):
        """AC #1 (Story 1.4): ms-python.vscode-pylance must be recommended."""
        assert "ms-python.vscode-pylance" in self._recommendations()


# ── agent.py line count ───────────────────────────────────────────────────────


class TestAgentPyConstraints:
    def test_under_150_lines(self):
        """AC #6 (Story 1.2): agent.py must stay under 150 lines."""
        lines = (PROJECT_ROOT / "agent.py").read_text().splitlines()
        assert len(lines) < 150, (
            f"agent.py has {len(lines)} lines — exceeds 150-line architectural limit. "
            "Extract tools to tools.py if the file grows beyond this."
        )


# ── deploy/app.py import isolation ───────────────────────────────────────────


class TestDeployAppImports:
    """Verify deploy/app.py does not import local Strands runtime modules.

    AC #1 (Story 2.2): the deployed runtime must be isolated from agent.py,
    model_adapters.py, and strands-agents. Those packages are absent in the
    AgentCore PYTHON_3_12 runtime, so importing them would cause an ImportError
    at startup and violates the local/cloud boundary established by this project.
    """

    def _source(self) -> str:
        return (PROJECT_ROOT / "deploy" / "app.py").read_text()

    def _imported_modules(self) -> set[str]:
        tree = ast.parse(self._source())
        modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module)
        return modules

    def test_does_not_import_strands(self):
        """deploy/app.py must not import strands — the Strands SDK is not available in AgentCore."""
        imports = self._imported_modules()
        assert "strands" not in imports and not any(
            module.startswith("strands.") for module in imports
        ), (
            "deploy/app.py must not import strands. "
            "The deployed runtime uses boto3 Converse directly."
        )

    def test_does_not_import_agent(self):
        """deploy/app.py must not import agent — agent.py is local-REPL only."""
        assert "agent" not in self._imported_modules(), (
            "deploy/app.py must not import agent. "
            "agent.py is local-REPL only and must not be bundled in the deployment ZIP."
        )

    def test_does_not_import_model_adapters(self):
        """deploy/app.py must not import model_adapters — the local adapter factory must not reach AgentCore."""
        assert "model_adapters" not in self._imported_modules(), (
            "deploy/app.py must not import model_adapters. "
            "The local adapter factory must not be used in the deployed runtime."
        )

    def test_uses_bedrock_agentcore_and_boto3(self):
        """deploy/app.py must import bedrock_agentcore and boto3 — these are the deployed runtime dependencies."""
        source = self._source()
        assert (
            "bedrock_agentcore" in source
        ), "deploy/app.py must import bedrock_agentcore (the AgentCore SDK)."
        assert (
            "import boto3" in source
        ), "deploy/app.py must import boto3 (for Bedrock Converse API calls)."


# ── README provider roadmap contract ─────────────────────────────────────────


class TestReadmeProviderRoadmap:
    def _content(self) -> str:
        return (PROJECT_ROOT / "README.md").read_text()

    def test_nist_section_no_longer_claims_current_epic_4(self):
        """AC #1 (Story 4.1): current Epic 4 must not also describe NIST compliance."""
        content = self._content()
        introduction = content.split("## What This Demonstrates", 1)[0]
        assert "Epic 4 is the NIST" not in introduction
        assert "NIST AI RMF compliance layer** (Epic 4)" not in introduction
        nist_section = content.split("## NIST AI RMF Compliance", 1)[1].split(
            "## Project Structure", 1
        )[0]
        assert "Epic 4 of this project implements" not in nist_section
        assert "earlier work" in nist_section

    def test_model_expansion_roadmap_preserves_runtime_boundary(self):
        """AC #2 (Story 4.1/4.3): README must distinguish supported and planned provider paths."""
        content = self._content()
        assert "### Model expansion roadmap" in content
        assert "`bedrock` (local + deployed), `gemini` (local only)" in content
        assert "`llama` (local + deployed, Bedrock-backed)" in content
        assert "Planned" in content and "Gemma" in content and "DeepSeek" in content
        assert "Local adapter selection raises `ValueError`" in content
        assert "deployment preflight rejects non-Bedrock-backed providers" in content
        assert "deployed runtime returns an unsupported-provider error" in content


# ── project-context provider boundary contract ───────────────────────────────


class TestProjectContextProviderRules:
    def _content(self) -> str:
        return (PROJECT_ROOT / "_bmad-output" / "project-context.md").read_text()

    def test_provider_rules_distinguish_local_and_deployed_support(self):
        """AC #2 (Story 4.1/4.3): project context must preserve local/cloud provider boundaries."""
        content = self._content()
        assert "Local adapter code supports `bedrock`, `gemini`, and `llama`" in content
        assert "all other local provider values raise `ValueError`" in content
        assert "Deployed AgentCore code supports `bedrock` and `llama`" in content
        assert "unsupported-provider error before Bedrock invocation" in content

    def test_provider_rules_mark_expansion_targets_as_future_work(self):
        """AC #1 (Story 4.1/4.3): project context must not imply still-planned families are enabled."""
        content = self._content()
        assert "future work, not currently configured providers" in content
        for family in ("Gemma", "Moonshot/Kimi", "Qwen", "DeepSeek"):
            assert family in content

    def test_local_adapter_registry_convention_is_documented(self):
        """AC #3 (Story 4.2): project context must preserve registry convention."""
        content = self._content()
        assert "### Local Adapter Registry Convention (Story 4.2+)" in content
        assert "ModelCapabilities" in content
        assert "`_REGISTRY`" in content
        assert "supported_local_providers()" in content
        assert "planned_model_families()" in content
        assert "get_model_capabilities(provider)" in content
        assert "must not import or use the local registry" in content
