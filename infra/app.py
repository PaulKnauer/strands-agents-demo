#!/usr/bin/env python3
"""CDK app for repository CI/security infrastructure."""

import aws_cdk as cdk

from github_actions_stack import GithubActionsStack

app = cdk.App()

GithubActionsStack(
    app,
    "StrandsDemoGithubActionsStack",
    description="GitHub Actions OIDC role for strands-agents-demo red-team CI",
    synthesizer=cdk.LegacyStackSynthesizer(),
)

app.synth()
