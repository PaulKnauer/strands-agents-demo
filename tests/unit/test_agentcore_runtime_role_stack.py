"""Unit tests for the AgentCore runtime role CDK stack."""

from pathlib import Path

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from infra.agentcore_runtime_role_stack import AgentCoreRuntimeRoleStack

PROJECT_ROOT = Path(__file__).parent.parent.parent


def _template() -> Template:
    app = cdk.App()
    stack = AgentCoreRuntimeRoleStack(
        app,
        "TestAgentCoreRuntimeRoleStack",
        agent_name="age-in-days-demo",
        model_id="us.amazon.nova-micro-v1:0",
    )
    return Template.from_stack(stack)


class TestAgentCoreRuntimeRoleStack:
    def test_creates_named_role_and_outputs(self):
        template = _template()
        template.has_resource_properties(
            "AWS::IAM::Role",
            {"RoleName": "AmazonBedrockAgentCoreRuntime_age_in_days_demo"},
        )
        template.has_output("AgentCoreRuntimeRoleArn", {})
        template.has_output("AgentCoreRuntimeRoleName", {})

    def test_includes_observability_permissions(self):
        template = _template()
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": Match.object_like(
                    {
                        "Statement": Match.array_with(
                            [
                                Match.object_like(
                                    {
                                        "Action": Match.array_with(
                                            ["xray:PutTraceSegments"]
                                        )
                                    }
                                ),
                                Match.object_like(
                                    {"Action": "cloudwatch:PutMetricData"}
                                ),
                            ]
                        )
                    }
                )
            },
        )


class TestAgentCoreRuntimeRoleMakeTargets:
    def test_cdk_app_loads_dotenv(self):
        content = (PROJECT_ROOT / "infra" / "app.py").read_text()
        assert "load_dotenv()" in content

    def test_makefile_has_create_role_target(self):
        content = (PROJECT_ROOT / "Makefile").read_text()
        assert "deploy StrandsDemoAgentCoreRuntimeRoleStack" in content

    def test_makefile_has_teardown_role_target(self):
        content = (PROJECT_ROOT / "Makefile").read_text()
        assert ".PHONY: teardown-role" in content
        assert "destroy StrandsDemoAgentCoreRuntimeRoleStack" in content
