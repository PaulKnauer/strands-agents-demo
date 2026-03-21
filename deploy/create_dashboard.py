"""CloudWatch compliance dashboard — NIST AI RMF MEASURE-2.4/2.5 and MANAGE-2.4/4.1."""

import json
import os
import sys

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

NIST_RMF_DASHBOARD_NAME = "NIST-RMF-AgentCompliance"


def _build_dashboard_body(region: str, guardrail_id: str | None, log_group: str) -> str:
    """Build the CloudWatch dashboard JSON body.

    Returns a JSON string (not dict) — CloudWatch put_dashboard requires a string.
    Widget 1 (Guardrail Block Rate) is omitted when guardrail_id is None.
    """
    widgets = []

    if guardrail_id:
        # Widget 1: Guardrail Block Rate — NIST MEASURE-2.4 (safety monitoring).
        # Shows Invocations vs InvocationsIntervened (blocks) over time.
        # Namespace: AWS/Bedrock/Guardrails — dimensions GuardrailArn + GuardrailVersion.
        # Source: https://docs.aws.amazon.com/bedrock/latest/userguide/monitoring-guardrails-cw-metrics.html
        widgets.append(
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "title": "Guardrail Block Rate (NIST MEASURE-2.4)",
                    "metrics": [
                        [
                            "AWS/Bedrock/Guardrails",
                            "Invocations",
                            "GuardrailArn",
                            guardrail_id,
                            "GuardrailVersion",
                            "DRAFT",
                            {"label": "Invocations"},
                        ],
                        [
                            "AWS/Bedrock/Guardrails",
                            "InvocationsIntervened",
                            "GuardrailArn",
                            guardrail_id,
                            "GuardrailVersion",
                            "DRAFT",
                            {"label": "Interventions (Blocks)", "color": "#ff6b6b"},
                        ],
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                },
            }
        )

    # Widget 2: Tool Invocation Audit Trail — NIST MEASURE-2.5 (runtime monitoring).
    # Queries the JSONL audit log produced by AuditLoggingHook in compliance/hooks.py.
    # Filters for tool_call_start events to show when and what tools were invoked.
    log_widget_y = 6 if guardrail_id else 0
    widgets.append(
        {
            "type": "log",
            "x": 0,
            "y": log_widget_y,
            "width": 24,
            "height": 6,
            "properties": {
                "title": "Tool Invocation Audit Trail (NIST MEASURE-2.5)",
                "query": (
                    f"SOURCE '{log_group}'\n"
                    "| fields @timestamp, event, tool_name, invocation_id\n"
                    "| filter event = 'tool_call_start'\n"
                    "| sort @timestamp desc\n"
                    "| limit 50"
                ),
                "region": region,
                "view": "table",
            },
        }
    )

    return json.dumps({"widgets": widgets})


def main() -> None:
    """Create or update the NIST-RMF-AgentCompliance CloudWatch dashboard."""
    try:
        region = os.environ["AWS_REGION"]
        agent_name = os.environ["AGENT_NAME"].replace("-", "_")
    except KeyError as e:
        print(f"\n❌ Missing required environment variable: {e}")
        print("   Hint: Copy .env.example to .env and fill in all required values.")
        sys.exit(1)

    guardrail_id = os.environ.get("GUARDRAIL_ID")
    # Default log group matches AgentCore's auto-provisioned log group name pattern.
    # Override with LOG_GROUP_NAME env var if your deployment uses a different name.
    log_group = os.environ.get(
        "LOG_GROUP_NAME", f"/aws/bedrock-agentcore/runtimes/{agent_name}"
    )

    print(f"\n📊 Creating CloudWatch dashboard: {NIST_RMF_DASHBOARD_NAME}")
    if not guardrail_id:
        print(
            "   ℹ️  GUARDRAIL_ID not set — Guardrail Block Rate widget will be omitted."
        )

    cw = boto3.client("cloudwatch", region_name=region)
    body = _build_dashboard_body(region, guardrail_id, log_group)

    try:
        cw.put_dashboard(DashboardName=NIST_RMF_DASHBOARD_NAME, DashboardBody=body)
    except ClientError as e:
        print(f"\n❌ Failed to create dashboard: {e}")
        print(
            "   Hint: Verify AWS credentials and that CloudWatch is accessible in the region."
        )
        sys.exit(1)

    console_url = (
        f"https://{region}.console.aws.amazon.com/cloudwatch/home"
        f"?region={region}#dashboards/dashboard/{NIST_RMF_DASHBOARD_NAME}"
    )
    print(f"  ✅ Dashboard created: {NIST_RMF_DASHBOARD_NAME}")
    print(f"  🔗 {console_url}")


if __name__ == "__main__":
    main()
