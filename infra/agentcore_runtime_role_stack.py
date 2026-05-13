"""CDK stack for the AgentCore runtime execution role."""

from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_iam as iam
from constructs import Construct

_US_INFERENCE_PROFILE_REGIONS = ("us-east-1", "us-east-2", "us-west-2")


def _sanitized_agent_name(raw: str) -> str:
    return raw.replace("-", "_")


def _bedrock_model_resources(
    aws_region: str, account_id: str, model_id: str
) -> list[str]:
    """Return Bedrock InvokeModel resources for a model or inference profile."""
    if model_id.startswith("us."):
        base_model_id = model_id.removeprefix("us.")
        return [
            f"arn:aws:bedrock:{aws_region}:{account_id}:inference-profile/{model_id}",
            *[
                f"arn:aws:bedrock:{region}::foundation-model/{base_model_id}"
                for region in _US_INFERENCE_PROFILE_REGIONS
            ],
        ]
    if model_id.startswith("global."):
        base_model_id = model_id.removeprefix("global.")
        return [
            f"arn:aws:bedrock:{aws_region}:{account_id}:inference-profile/{model_id}",
            f"arn:aws:bedrock:*::foundation-model/{base_model_id}",
        ]
    return [f"arn:aws:bedrock:{aws_region}::foundation-model/{model_id}"]


class AgentCoreRuntimeRoleStack(Stack):
    """Provision the runtime execution role used by deploy.py."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        agent_name: str,
        model_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        sanitized_name = _sanitized_agent_name(agent_name)
        role_name = f"AmazonBedrockAgentCoreRuntime_{sanitized_name}"
        region = Stack.of(self).region
        account = Stack.of(self).account

        model_resources = _bedrock_model_resources(region, account, model_id)
        agent_resource = (
            f"arn:aws:bedrock-agentcore:{region}:{account}:runtime/{sanitized_name}*"
        )
        runtime_logs_group = f"arn:aws:logs:{region}:{account}:log-group:/aws/bedrock-agentcore/runtimes/*"
        runtime_logs_streams = f"{runtime_logs_group}:log-stream:*"

        role = iam.Role(
            self,
            "AgentCoreRuntimeRole",
            role_name=role_name,
            description="Least-privilege execution role for AgentCore runtime",
            assumed_by=iam.ServicePrincipal(
                "bedrock-agentcore.amazonaws.com",
                conditions={
                    "StringEquals": {"aws:SourceAccount": account},
                    "ArnLike": {
                        "aws:SourceArn": (
                            f"arn:aws:bedrock-agentcore:{region}:{account}:*"
                        )
                    },
                },
            ),
        )

        role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=model_resources,
            )
        )
        role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock-agentcore:*"],
                resources=[agent_resource],
            )
        )
        role.add_to_policy(
            iam.PolicyStatement(
                actions=["logs:DescribeLogStreams", "logs:CreateLogGroup"],
                resources=[runtime_logs_group],
            )
        )
        role.add_to_policy(
            iam.PolicyStatement(
                actions=["logs:DescribeLogGroups"],
                resources=[f"arn:aws:logs:{region}:{account}:log-group:*"],
            )
        )
        role.add_to_policy(
            iam.PolicyStatement(
                actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                resources=[runtime_logs_streams],
            )
        )
        role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "xray:GetSamplingRules",
                    "xray:GetSamplingTargets",
                ],
                resources=["*"],
            )
        )
        role.add_to_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
                conditions={
                    "StringEquals": {"cloudwatch:namespace": "bedrock-agentcore"}
                },
            )
        )

        CfnOutput(self, "AgentCoreRuntimeRoleArn", value=role.role_arn)
        CfnOutput(self, "AgentCoreRuntimeRoleName", value=role.role_name)
        CfnOutput(
            self,
            "AgentCoreObservabilityPermissions",
            value=(
                "CloudWatch Logs, X-Ray telemetry, and bedrock-agentcore metrics "
                "permissions are attached to the runtime role."
            ),
        )
