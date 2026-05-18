"""Static tests for manual red-team CI infrastructure."""

from pathlib import Path

import yaml

from compliance.prepare_promptfoo_config import prepare_promptfoo_config

PROJECT_ROOT = Path(__file__).parent.parent.parent
REDTEAM_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "redteam.yml"
GITHUB_ACTIONS_STACK = PROJECT_ROOT / "infra" / "github_actions_stack.py"
PROMPTFOO_CONFIG = PROJECT_ROOT / "compliance" / "promptfoo-redteam.yaml"
GUARDRAIL_TEMPLATE = PROJECT_ROOT / "deploy" / "guardrail.yaml"
MAKEFILE = PROJECT_ROOT / "Makefile"


class CfnYamlLoader(yaml.SafeLoader):
    pass


def _construct_cfn_tag(loader, tag_suffix, node):
    return loader.construct_scalar(node)


CfnYamlLoader.add_multi_constructor("!", _construct_cfn_tag)


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

    def test_workflow_is_manual_dispatch_only(self):
        workflow = self._workflow()
        triggers = workflow[True]
        assert "workflow_dispatch" in triggers
        assert "schedule" not in triggers
        assert "push" not in triggers
        assert "pull_request" not in triggers

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
        assert target_ids == ["bedrock:amazon.nova-micro-v1:0"]
        content = PROMPTFOO_CONFIG.read_text().lower()
        assert "bedrock-agentcore" not in content
        assert "runtimes/" not in content

    def test_promptfoo_config_does_not_use_shell_default_expansion(self):
        content = PROMPTFOO_CONFIG.read_text()
        assert ":-" not in content

    def test_promptfoo_bedrock_region_is_concrete(self):
        with PROMPTFOO_CONFIG.open() as f:
            config = yaml.safe_load(f)

        target = config["targets"][0]
        assert target["config"]["region"] == "us-east-1"

    def test_workflow_prepares_runtime_promptfoo_config(self):
        workflow = self._workflow()
        steps = workflow["jobs"]["redteam"]["steps"]
        prepare_step = next(
            step
            for step in steps
            if step.get("name") == "Prepare promptfoo configuration"
        )
        run_step = next(
            step for step in steps if step.get("name") == "Run promptfoo red-team scan"
        )

        assert prepare_step["run"] == "python compliance/prepare_promptfoo_config.py"
        assert "--config compliance/promptfoo-redteam.ci.yaml" in run_step["run"]

    def test_make_redteam_prepares_runtime_promptfoo_config(self):
        content = MAKEFILE.read_text()
        assert "$(PYTHON) compliance/prepare_promptfoo_config.py" in content
        assert "--config compliance/promptfoo-redteam.ci.yaml" in content

    def test_prepare_promptfoo_config_removes_guardrail_when_unset(self, tmp_path):
        source = tmp_path / "promptfoo.yaml"
        destination = tmp_path / "promptfoo.ci.yaml"
        source.write_text(PROMPTFOO_CONFIG.read_text())

        guardrails_enabled = prepare_promptfoo_config(
            source, destination, guardrail_id=""
        )
        content = destination.read_text()

        assert guardrails_enabled is False
        assert "guardrailIdentifier:" not in content
        assert "guardrailVersion:" not in content
        assert "region: us-east-1" in content

    def test_prepare_promptfoo_config_keeps_guardrail_when_set(self, tmp_path):
        source = tmp_path / "promptfoo.yaml"
        destination = tmp_path / "promptfoo.ci.yaml"
        source.write_text(PROMPTFOO_CONFIG.read_text())

        guardrails_enabled = prepare_promptfoo_config(
            source, destination, guardrail_id="abc123", guardrail_version="DRAFT"
        )
        content = destination.read_text()

        assert guardrails_enabled is True
        assert "guardrailIdentifier: abc123" in content
        assert "guardrailVersion: DRAFT" in content
        assert "${GUARDRAIL_ID}" not in content
        assert "${GUARDRAIL_VERSION}" not in content


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


class TestGuardrailTemplate:
    def _template(self) -> dict:
        with GUARDRAIL_TEMPLATE.open() as f:
            return yaml.load(f, Loader=CfnYamlLoader)

    def test_prompt_attack_filter_uses_cloudformation_enum(self):
        template = self._template()

        filters = template["Resources"]["StrandsDemoGuardrail"]["Properties"][
            "ContentPolicyConfig"
        ]["FiltersConfig"]
        filter_types = {filter_config["Type"] for filter_config in filters}

        assert "PROMPT_ATTACK" in filter_types
        assert "PROMPT_ATTACKS" not in filter_types

    def test_guardrail_description_fits_cloudformation_limit(self):
        template = self._template()

        description = template["Resources"]["StrandsDemoGuardrail"]["Properties"][
            "Description"
        ]

        assert len(description) <= 200
