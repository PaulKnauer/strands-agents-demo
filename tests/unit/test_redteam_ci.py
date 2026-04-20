"""Static tests for scheduled red-team CI infrastructure."""

from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).parent.parent.parent
REDTEAM_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "redteam.yml"
GITHUB_ACTIONS_STACK = PROJECT_ROOT / "infra" / "github_actions_stack.py"
PROMPTFOO_CONFIG = PROJECT_ROOT / "compliance" / "promptfoo-redteam.yaml"


class TestRedteamWorkflowCredentials:
    def _workflow(self) -> dict:
        with REDTEAM_WORKFLOW.open() as f:
            return yaml.safe_load(f)

    def _content(self) -> str:
        return REDTEAM_WORKFLOW.read_text()

    def test_workflow_requests_oidc_token_permission(self):
        workflow = self._workflow()
        assert workflow["permissions"]["contents"] == "read"
        assert workflow["permissions"]["id-token"] == "write"

    def test_workflow_uses_configure_aws_credentials(self):
        content = self._content()
        assert "aws-actions/configure-aws-credentials@v4" in content
        assert "role-to-assume: ${{ secrets.AWS_ROLE_TO_ASSUME }}" in content

    def test_workflow_does_not_require_static_aws_key_secrets(self):
        content = self._content()
        legacy_key_secret = "secrets." + "AWS_" + "ACCESS_KEY_ID"
        legacy_secret_key_secret = "secrets." + "AWS_" + "SECRET_ACCESS_KEY"
        assert legacy_key_secret not in content
        assert legacy_secret_key_secret not in content

    def test_workflow_does_not_deploy_or_invoke_agentcore(self):
        content = self._content().lower()
        assert "make deploy" not in content
        assert "deploy/deploy.py" not in content
        assert "deploy/verify.py" not in content
        assert "bedrock-agentcore" not in content

    def test_missing_role_secret_still_uploads_evidence_artifact(self):
        content = self._content()
        assert "Missing AWS_ROLE_TO_ASSUME secret" in content
        assert "compliance/redteam-report.json" in content

    def test_promptfoo_targets_bedrock_directly_not_agentcore(self):
        with PROMPTFOO_CONFIG.open() as f:
            config = yaml.safe_load(f)

        target_ids = [target["id"] for target in config["targets"]]
        assert target_ids == ["bedrock:anthropic.claude-3-haiku-20240307-v1:0"]
        content = PROMPTFOO_CONFIG.read_text().lower()
        assert "bedrock-agentcore" not in content
        assert "runtimes/" not in content


class TestGithubActionsCdkStack:
    def _content(self) -> str:
        return GITHUB_ACTIONS_STACK.read_text()

    def test_stack_scopes_trust_to_this_repo_main_branch(self):
        content = self._content()
        assert "repo:{owner}/{repo}:ref:{github_ref}" in content
        assert '"refs/heads/main"' in content
        assert "sts.amazonaws.com" in content

    def test_stack_uses_web_identity_principal(self):
        assert "iam.WebIdentityPrincipal" in self._content()

    def test_stack_grants_bedrock_runtime_permissions_only(self):
        content = self._content()
        assert "bedrock:InvokeModel" in content
        assert "bedrock:InvokeModelWithResponseStream" in content
        assert "bedrock:ApplyGuardrail" in content
        assert "bedrock:*" not in content
