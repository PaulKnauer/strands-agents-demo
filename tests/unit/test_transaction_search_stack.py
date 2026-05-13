"""Unit tests for CloudWatch Transaction Search CDK infrastructure."""

from pathlib import Path

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from infra.transaction_search_stack import TransactionSearchStack

PROJECT_ROOT = Path(__file__).parent.parent.parent


def _template() -> Template:
    app = cdk.App()
    stack = TransactionSearchStack(app, "TestTransactionSearchStack")
    return Template.from_stack(stack)


class TestTransactionSearchStack:
    def test_creates_logs_resource_policy(self):
        template = _template()

        template.has_resource_properties(
            "AWS::Logs::ResourcePolicy",
            {
                "PolicyName": "TransactionSearchAccess",
                "PolicyDocument": Match.object_like(
                    {
                        "Fn::Sub": Match.string_like_regexp(
                            '"Service": "xray.amazonaws.com"'
                        )
                    }
                ),
            },
        )

    def test_creates_transaction_search_config(self):
        template = _template()

        template.has_resource_properties(
            "AWS::XRay::TransactionSearchConfig",
            {"IndexingPercentage": 100},
        )

    def test_outputs_console_and_manual_drift_guidance(self):
        template = _template()

        template.has_output("TransactionSearchConsoleUrl", {})
        template.has_output(
            "TransactionSearchManualEnablementWarning",
            {
                "Value": Match.string_like_regexp(
                    "disable it before the first CDK deploy"
                )
            },
        )

    def test_dependency_orders_config_after_resource_policy(self):
        template = _template().to_json()
        config_resource = template["Resources"]["TransactionSearchConfig"]

        assert "DependsOn" in config_resource

    def test_context_can_override_indexing_percentage(self):
        app = cdk.App(context={"transactionSearchIndexingPercentage": "10"})
        stack = TransactionSearchStack(app, "ContextTransactionSearchStack")
        template = Template.from_stack(stack)

        template.has_resource_properties(
            "AWS::XRay::TransactionSearchConfig",
            {"IndexingPercentage": 10},
        )


class TestTransactionSearchMakeTargets:
    def test_makefile_has_transaction_search_deploy_target(self):
        content = (PROJECT_ROOT / "Makefile").read_text()
        assert ".PHONY: transaction-search" in content
        assert "deploy StrandsDemoTransactionSearchStack" in content

    def test_makefile_has_transaction_search_teardown_target(self):
        content = (PROJECT_ROOT / "Makefile").read_text()
        assert ".PHONY: teardown-transaction-search" in content
        assert "destroy StrandsDemoTransactionSearchStack" in content
