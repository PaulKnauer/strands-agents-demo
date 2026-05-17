"""GitHub Actions OIDC infrastructure for scheduled red-team scans."""

from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_iam as iam
from constructs import Construct


class GithubActionsStack(Stack):
    """Provision a least-privilege role for GitHub Actions red-team scans."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        owner = self.node.try_get_context("githubOwner") or "PaulKnauer"
        repo = self.node.try_get_context("githubRepo") or "strands-agents-demo"
        github_ref = self.node.try_get_context("githubRef") or "refs/heads/main"
        oidc_provider_arn = self.node.try_get_context("githubOidcProviderArn")
        if not oidc_provider_arn:
            oidc_provider = iam.CfnOIDCProvider(
                self,
                "GitHubOidcProvider",
                url="https://token.actions.githubusercontent.com",
                client_id_list=["sts.amazonaws.com"],
                thumbprint_list=["6938fd4d98bab03faadb97b34396831e3780aea1"],
            )
            oidc_provider_arn = oidc_provider.attr_arn

        role = iam.Role(
            self,
            "RedteamGithubActionsRole",
            role_name="strands-demo-redteam-github-actions",
            assumed_by=iam.WebIdentityPrincipal(
                oidc_provider_arn,
                conditions={
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                    },
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": (
                            f"repo:{owner}/{repo}:ref:{github_ref}"
                        )
                    },
                },
            ),
            description=(
                "Short-lived GitHub Actions role for strands-agents-demo "
                "promptfoo red-team scans"
            ),
        )

        role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                # Wildcard covers any Anthropic foundation model so that upgrading
                # the red-team target model does not require a CDK redeploy.
                resources=[
                    f"arn:{self.partition}:bedrock:{self.region}::foundation-model/anthropic.*"
                ],
            )
        )
        role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:ApplyGuardrail"],
                resources=[
                    f"arn:{self.partition}:bedrock:{self.region}:{self.account}:guardrail/*"
                ],
            )
        )

        CfnOutput(
            self,
            "GitHubActionsRoleArn",
            value=role.role_arn,
            description="Store this value as the GitHub secret AWS_ROLE_TO_ASSUME.",
        )
        CfnOutput(
            self,
            "GitHubActionsSecretCommand",
            value=(
                "gh secret set AWS_ROLE_TO_ASSUME "
                f"--repo {owner}/{repo} --body {role.role_arn}"
            ),
            description="Command to configure the repository secret used by Redteam CI.",
        )
