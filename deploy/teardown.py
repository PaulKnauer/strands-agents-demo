"""AgentCore teardown script — removes all AWS resources created by deploy.py."""

import os
import sys

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

try:
    from deploy.create_dashboard import NIST_RMF_DASHBOARD_NAME
except ModuleNotFoundError as e:
    if e.name != "deploy.create_dashboard":
        raise

    # Direct execution (`python deploy/teardown.py`) puts deploy/ on sys.path,
    # so the package import above resolves deploy.py instead of the deploy dir.
    from create_dashboard import NIST_RMF_DASHBOARD_NAME

load_dotenv()


def main() -> None:
    """Delete AgentCore runtime, S3 deployment artefacts, and dashboard."""
    try:
        aws_region = os.environ["AWS_REGION"]
        agent_name_raw = os.environ["AGENT_NAME"]
        os.environ["MODEL_ID"]
    except KeyError as e:
        print(f"\n❌ Missing required environment variable: {e}")
        print("   Hint: Copy .env.example to .env and fill in all required values.")
        sys.exit(1)

    agent_name = agent_name_raw.replace("-", "_")

    print(
        f"\n🗑️  Tearing down AgentCore resources for '{agent_name}' in {aws_region}..."
    )
    print(
        "   This will delete: AgentCore runtime, S3 deployment object, CloudWatch dashboard.\n"
    )

    sts = boto3.client("sts", region_name=aws_region)
    try:
        account_id = sts.get_caller_identity()["Account"]
    except ClientError as e:
        print(f"❌ Could not determine AWS account ID: {e}")
        sys.exit(1)

    s3_bucket = f"bedrock-agentcore-code-{account_id}-{aws_region}"
    s3_key = f"{agent_name}/deployment.zip"

    agentcore_ctrl = boto3.client("bedrock-agentcore-control", region_name=aws_region)
    s3 = boto3.client("s3", region_name=aws_region)

    # ── Step 1: Delete AgentCore runtime ─────────────────────────────────────
    print("Step 1/4: Deleting AgentCore runtime...")
    try:
        # Find the runtime ID by name (no server-side name filter — must scan)
        runtime_id = None
        next_token = None
        while True:
            kwargs = {"maxResults": 100}
            if next_token:
                kwargs["nextToken"] = next_token
            response = agentcore_ctrl.list_agent_runtimes(**kwargs)
            for rt in response.get("agentRuntimes", []):
                if rt.get("agentRuntimeName") == agent_name:
                    runtime_id = rt["agentRuntimeId"]
                    break
            if runtime_id or not response.get("nextToken"):
                break
            next_token = response["nextToken"]

        if runtime_id:
            agentcore_ctrl.delete_agent_runtime(agentRuntimeId=runtime_id)
            print(f"  ✅ Deleted AgentCore runtime: {runtime_id}")
        else:
            print(f"  ℹ️  AgentCore runtime '{agent_name}' not found — skipping.")
    except ClientError as e:
        print(f"  ⚠️  Could not delete AgentCore runtime: {e}")

    # ── Step 2: Delete S3 deployment artefact ────────────────────────────────
    # The bucket (bedrock-agentcore-code-*) is shared across AgentCore deployments
    # so we only remove this agent's object, not the bucket itself.
    print("\nStep 2/3: Deleting S3 deployment object...")
    try:
        s3.delete_object(Bucket=s3_bucket, Key=s3_key)
        print(f"  ✅ Deleted s3://{s3_bucket}/{s3_key}")
        print(f"  ℹ️  Bucket '{s3_bucket}' retained (shared AgentCore bucket).")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("NoSuchBucket", "NoSuchKey"):
            print(f"  ℹ️  S3 object not found — skipping.")
        else:
            print(f"  ⚠️  Could not delete S3 object: {e}")

    # ── Step 3: Delete CloudWatch compliance dashboard ───────────────────────
    print("\nStep 3/3: Deleting CloudWatch compliance dashboard...")
    cw = boto3.client("cloudwatch", region_name=aws_region)
    try:
        cw.delete_dashboards(DashboardNames=[NIST_RMF_DASHBOARD_NAME])
        print(f"  ✅ Deleted CloudWatch dashboard: {NIST_RMF_DASHBOARD_NAME}")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "ResourceNotFound":
            print(
                f"  ℹ️  CloudWatch dashboard '{NIST_RMF_DASHBOARD_NAME}' not found — skipping."
            )
        else:
            print(f"  ⚠️  Could not delete CloudWatch dashboard: {e}")

    print("\n✅ Teardown complete.")
    print(
        "   ℹ️  The AgentCore runtime IAM role is CDK-managed. Use 'make teardown-role' to remove it."
    )


if __name__ == "__main__":
    main()
