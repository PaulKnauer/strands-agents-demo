#!/usr/bin/env python3
"""CDK app for repository CI/security infrastructure."""

import os

import aws_cdk as cdk
from dotenv import load_dotenv

from agentcore_runtime_role_stack import AgentCoreRuntimeRoleStack
from github_actions_stack import GithubActionsStack
from transaction_search_stack import TransactionSearchStack

load_dotenv()

app = cdk.App()
agent_name = os.environ.get("AGENT_NAME")
model_id = os.environ.get("MODEL_ID")

GithubActionsStack(
    app,
    "StrandsDemoGithubActionsStack",
    description="GitHub Actions OIDC role for strands-agents-demo red-team CI",
    synthesizer=cdk.LegacyStackSynthesizer(),
)

TransactionSearchStack(
    app,
    "StrandsDemoTransactionSearchStack",
    description="Enable CloudWatch Transaction Search for strands-agents-demo observability",
    synthesizer=cdk.LegacyStackSynthesizer(),
)

if agent_name and model_id:
    AgentCoreRuntimeRoleStack(
        app,
        "StrandsDemoAgentCoreRuntimeRoleStack",
        agent_name=agent_name,
        model_id=model_id,
        description="AgentCore runtime IAM role for strands-agents-demo",
        synthesizer=cdk.LegacyStackSynthesizer(),
    )

app.synth()
