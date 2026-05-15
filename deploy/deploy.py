"""AgentCore deployment script — provisions AWS infrastructure and deploys the agent."""

import io
import json
import os
import subprocess
import sys
import tempfile
import time
import zipfile
from urllib.parse import quote

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# load_dotenv() must be called before any os.environ access;
# it populates the environment from the .env file silently if not found
load_dotenv()

DEFAULT_MODEL_ID = "us.amazon.nova-micro-v1:0"
_US_INFERENCE_PROFILE_REGIONS = ("us-east-1", "us-east-2", "us-west-2")
_RUNTIME_ROLE_STACK_NAME = "StrandsDemoAgentCoreRuntimeRoleStack"

# Providers that are Bedrock-backed and permitted for AgentCore deployment.
# "llama" routes through Bedrock Converse — no direct Meta API involved.
_BEDROCK_BACKED_PROVIDERS = frozenset({"bedrock", "llama"})


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


def _ensure_s3_bucket(s3, bucket_name: str, region: str, account_id: str) -> None:
    """Create the S3 bucket if it does not already exist."""
    try:
        s3.head_bucket(Bucket=bucket_name, ExpectedBucketOwner=account_id)
        print(f"  S3 bucket exists: {bucket_name}")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("404", "NoSuchBucket"):
            # us-east-1 must NOT pass CreateBucketConfiguration — AWS raises
            # InvalidLocationConstraint if you do (other regions require it)
            if region == "us-east-1":
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": region},
                )
            print(f"  Created S3 bucket: {bucket_name}")
        else:
            raise
    # Enforce SSE-S3 encryption — idempotent, safe to apply on existing buckets
    s3.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
            "Rules": [
                {"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}
            ]
        },
    )


def _build_deployment_zip(project_root: str) -> bytes:
    """Create an in-memory ZIP with app.py and pre-bundled dependencies.

    agent.py is intentionally excluded — it imports strands-agents (not present in
    the runtime) and is local-REPL only. app.py is the cloud entrypoint.
    bootstrap.py is bundled as the AgentCore entrypoint so ADOT auto-instrumentation
    starts before app.py imports boto3 or the BedrockAgentCore SDK.

    Dependencies (including boto3 via bedrock-agentcore's transitive deps) are
    resolved and downloaded for the Linux ARM64 (manylinux2014_aarch64) platform at
    deploy-time using pip's cross-platform wheel support, then bundled into the zip.
    boto3 must be bundled — it is NOT reliably pre-installed in PYTHON_3_12 despite
    documentation suggesting otherwise (confirmed during deployment testing).

    The PYTHON_3_12 runtime extracts the zip to /var/task/ (in sys.path), so
    root-level packages are importable without sys.path changes.

    Using Linux wheels at build-time means Rust/C extensions (e.g. pydantic-core)
    are compatible with the runtime — macOS dylibs would crash on startup.
    """
    buf = io.BytesIO()
    with tempfile.TemporaryDirectory() as pkg_dir:
        print(
            "  Pre-installing bedrock-agentcore (Linux ARM64 wheels) into deployment package..."
        )
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "bedrock-agentcore",
                "aws-opentelemetry-distro>=0.10.0",
                "--target",
                pkg_dir,
                "--platform",
                "manylinux2014_aarch64",
                "--python-version",
                "312",
                "--only-binary",
                ":all:",
                "--implementation",
                "cp",
                "--quiet",
            ],
            check=True,
        )

        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # app.py is the cloud entrypoint — agent.py is local-REPL only and must not be bundled
            # (it imports strands-agents which is not present in the runtime, causing ImportError)
            zf.write(os.path.join(project_root, "deploy", "app.py"), arcname="app.py")
            zf.write(
                os.path.join(project_root, "deploy", "bootstrap.py"),
                arcname="bootstrap.py",
            )
            # Bundle all installed packages at zip root.
            # Skip __pycache__ dirs and .pyc/.pyo files — bytecode is Python
            # version-specific and compiled for the local interpreter, not the
            # runtime's Python 3.12.
            for dirpath, dirnames, filenames in os.walk(pkg_dir):
                dirnames[:] = [d for d in dirnames if d != "__pycache__"]
                for filename in filenames:
                    if filename.endswith((".pyc", ".pyo")):
                        continue
                    full_path = os.path.join(dirpath, filename)
                    arcname = os.path.relpath(full_path, pkg_dir)
                    zf.write(full_path, arcname=arcname)

    return buf.getvalue()


def _get_runtime_role_arn(cloudformation, stack_name: str) -> str:
    """Return the runtime role ARN from the CDK stack outputs."""
    try:
        response = cloudformation.describe_stacks(StackName=stack_name)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "ValidationError":
            print(f"\n❌ Required IAM role stack not found: {stack_name}")
            print(
                "   Hint: Provision the runtime role through CDK first with 'make create-role'."
            )
            sys.exit(1)
        raise

    outputs = {
        item["OutputKey"]: item["OutputValue"]
        for item in response["Stacks"][0].get("Outputs", [])
    }
    role_arn = outputs.get("AgentCoreRuntimeRoleArn")
    role_name = outputs.get("AgentCoreRuntimeRoleName")
    if role_arn:
        label = role_name or role_arn
        print(f"  IAM role exists (CDK-managed): {label}")
        return role_arn

    print(f"\n❌ Required IAM role output not found in stack: {stack_name}")
    print(
        "   Hint: Re-run 'make create-role' so the CDK stack publishes AgentCoreRuntimeRoleArn."
    )
    sys.exit(1)


def _find_existing_runtime(agentcore_ctrl, agent_name: str):
    """Return (agentRuntimeId, agentRuntimeArn) if runtime exists, else (None, None).

    list_agent_runtimes() has no server-side name filter — must filter client-side.
    Paginates through all results so accounts with >100 runtimes are handled correctly.
    """
    next_token = None
    while True:
        kwargs = {"maxResults": 100}
        if next_token:
            kwargs["nextToken"] = next_token
        response = agentcore_ctrl.list_agent_runtimes(**kwargs)
        for runtime in response.get("agentRuntimes", []):
            if runtime.get("agentRuntimeName") == agent_name:
                return runtime["agentRuntimeId"], runtime["agentRuntimeArn"]
        next_token = response.get("nextToken")
        if not next_token:
            break
    return None, None


def _build_artifact(s3_bucket: str, s3_key: str) -> dict:
    """Build the agentRuntimeArtifact structure for create/update calls."""
    return {
        "codeConfiguration": {
            "code": {"s3": {"bucket": s3_bucket, "prefix": s3_key}},
            # PYTHON_3_12 is the latest stable runtime available in AgentCore
            "runtime": "PYTHON_3_12",
            # Single-element list — AgentCore expects a Python script path here,
            # not ["python", "app.py"]. bootstrap.py enables ADOT before app.py loads.
            "entryPoint": ["bootstrap.py"],
        }
    }


def _wait_for_ready(
    agentcore_ctrl, agent_runtime_id: str, timeout_seconds: int = 300
) -> None:
    """Poll until runtime status is READY or raise on failure/timeout."""
    elapsed = 0
    print("  Waiting for agent to be ready", end="", flush=True)
    while elapsed < timeout_seconds:
        response = agentcore_ctrl.get_agent_runtime(agentRuntimeId=agent_runtime_id)
        status = response["status"]
        if status == "READY":
            print(" ✅")
            return
        if status.endswith("_FAILED") or status in ("FAILED", "DELETING"):
            print(f" ❌")
            reason = response.get("failureReason")
            detail = f": {reason}" if reason else ""
            raise RuntimeError(
                f"Agent runtime entered unexpected status: {status}{detail}"
            )
        print(".", end="", flush=True)
        time.sleep(10)
        elapsed += 10
    raise TimeoutError("Agent did not become READY within 5 minutes")


def _handle_client_error(e: ClientError, context: str) -> None:
    """Print a descriptive troubleshooting hint for common AWS errors."""
    code = e.response["Error"]["Code"]
    msg = e.response["Error"]["Message"]
    print(f"\n❌ AWS error during {context} ({code}): {msg}")
    if code in ("AccessDeniedException", "UnauthorizedException"):
        print("   Hint: Your AWS user/role is missing required permissions.")
        print(
            "   For deployment, you need: bedrock-agentcore-control:*, s3:*, iam:CreateRole,"
        )
        print("   iam:PutRolePolicy, sts:GetCallerIdentity. See:")
        print(
            "   https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html"
        )
    elif code == "ResourceNotFoundException":
        print(
            "   Hint: Check that AWS_REGION is correct and AgentCore is available there."
        )
        print(
            "   AgentCore is currently available in select regions (e.g. us-east-1, us-west-2)."
        )
    elif code in ("InvalidClientTokenId", "ExpiredTokenException"):
        print("   Hint: AWS credentials are invalid or expired.")
        print(
            "   Refresh your AWS CLI, IAM Identity Center, or other standard AWS SDK credentials."
        )
    elif code == "InvalidParameterException":
        print(
            "   Hint: A parameter value is invalid. Check AGENT_NAME (letters/digits/underscores"
        )
        print("   only, must start with a letter) and MODEL_ID format.")
    else:
        print("   Hint: Check AWS_REGION, AGENT_NAME, and MODEL_ID in your .env file.")
        print(f"   Full error: {e}")
    sys.exit(1)


def main() -> None:
    """Provision AWS infrastructure and deploy the agent to AgentCore."""
    # Validate required env vars — os.environ[] raises KeyError on missing (fail-fast)
    try:
        aws_region = os.environ["AWS_REGION"]
        agent_name_raw = os.environ["AGENT_NAME"]
        model_id = os.environ["MODEL_ID"]
        model_provider = os.environ["MODEL_PROVIDER"]
    except KeyError as e:
        print(f"\n❌ Missing required environment variable: {e}")
        print("   Hint: Copy .env.example to .env and fill in all required values.")
        sys.exit(1)

    if model_provider not in _BEDROCK_BACKED_PROVIDERS:
        print(
            f"\n❌ Unsupported MODEL_PROVIDER for AgentCore deployment: '{model_provider}'"
        )
        print(
            "   The AgentCore deployed runtime (deploy/app.py) uses Bedrock Converse"
            " directly and only supports Bedrock-backed providers: bedrock, llama."
        )
        print(
            "   Set MODEL_PROVIDER=bedrock or MODEL_PROVIDER=llama in your .env before deploying."
        )
        sys.exit(1)

    # AgentCore runtime names must match [a-zA-Z][a-zA-Z0-9_]{0,47} — hyphens not allowed
    agent_name = agent_name_raw.replace("-", "_")
    if agent_name != agent_name_raw:
        print(
            f"  Note: AGENT_NAME sanitized from '{agent_name_raw}' to '{agent_name}' (hyphens → underscores)"
        )

    print(f"\n🚀 Deploying agent '{agent_name}' to AgentCore in {aws_region}...\n")

    # Get AWS account ID — needed for constructing ARNs and the S3 bucket name
    try:
        sts = boto3.client("sts", region_name=aws_region)
        account_id = sts.get_caller_identity()["Account"]
    except ClientError as e:
        _handle_client_error(e, "STS GetCallerIdentity")

    s3_bucket = f"bedrock-agentcore-code-{account_id}-{aws_region}"
    s3_key = f"{agent_name}/deployment.zip"
    s3 = boto3.client("s3", region_name=aws_region)
    cloudformation = boto3.client("cloudformation", region_name=aws_region)
    agentcore_ctrl = boto3.client("bedrock-agentcore-control", region_name=aws_region)

    # ── Step 1: Ensure S3 bucket exists ──────────────────────────────────────
    print("Step 1/5: Ensuring S3 bucket...")
    try:
        _ensure_s3_bucket(s3, s3_bucket, aws_region, account_id)
    except ClientError as e:
        _handle_client_error(e, "S3 bucket creation")

    # ── Step 2: Package and upload agent code ─────────────────────────────────
    print("\nStep 2/5: Packaging and uploading agent code...")
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    zip_bytes = _build_deployment_zip(project_root)
    try:
        s3.put_object(Bucket=s3_bucket, Key=s3_key, Body=zip_bytes)
        print(f"  Uploaded {len(zip_bytes)} bytes → s3://{s3_bucket}/{s3_key}")
    except ClientError as e:
        _handle_client_error(e, "S3 upload")

    # ── Step 3: Resolve IAM execution role (CDK-managed) ─────────────────────
    print("\nStep 3/5: Ensuring IAM execution role...")
    try:
        role_arn = _get_runtime_role_arn(cloudformation, _RUNTIME_ROLE_STACK_NAME)
    except ClientError as e:
        _handle_client_error(e, "IAM role lookup")

    # ── Step 4: Create or update AgentCore runtime (idempotent) ──────────────
    print("\nStep 4/5: Deploying AgentCore runtime (idempotent)...")
    artifact = _build_artifact(s3_bucket, s3_key)
    env_vars = {
        "AGENT_NAME": agent_name,
        "AGENT_OBSERVABILITY_ENABLED": "true",
        "AWS_AGENTIC_OBSERVABILITY_OPT_IN": "true",
        "MODEL_PROVIDER": model_provider,
        "MODEL_ID": model_id,
        "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT": f"https://xray.{aws_region}.amazonaws.com/v1/traces",
        "OTEL_RESOURCE_ATTRIBUTES": f"service.name={agent_name}",
        "OTEL_TRACES_EXPORTER": "otlp",
        "AWS_REGION": aws_region,
    }
    # GOOGLE_API_KEY passthrough is preserved for completeness but is not used by the
    # deployed runtime. The provider check above ensures only Bedrock-backed providers
    # (bedrock, llama) reach this point — Gemini is local-only.
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    if google_api_key:
        env_vars["GOOGLE_API_KEY"] = google_api_key
    network_config = {"networkMode": "PUBLIC"}

    # IAM roles are eventually consistent — the trust policy may not be assumable immediately
    # after creation. Retry on InvalidParameterException or ValidationException with a "role"
    # message. ValidationException is what AgentCore actually raises for new roles.
    _MAX_IAM_RETRIES = 8
    _IAM_RETRY_WAIT_S = 15

    try:
        existing_id, existing_arn = _find_existing_runtime(agentcore_ctrl, agent_name)

        if existing_id is None:
            print(f"  Creating new AgentCore runtime '{agent_name}'...")
            for attempt in range(_MAX_IAM_RETRIES):
                try:
                    response = agentcore_ctrl.create_agent_runtime(
                        agentRuntimeName=agent_name,
                        agentRuntimeArtifact=artifact,
                        networkConfiguration=network_config,
                        roleArn=role_arn,
                        environmentVariables=env_vars,
                        description="Age-in-days demo agent — Strands Agents SDK showcase",
                    )
                    break
                except ClientError as e:
                    code = e.response["Error"]["Code"]
                    msg = e.response["Error"]["Message"]
                    if (
                        code in ("InvalidParameterException", "ValidationException")
                        and "role" in msg.lower()
                        and attempt < _MAX_IAM_RETRIES - 1
                    ):
                        print(
                            f"  IAM role not yet assumable — retrying in {_IAM_RETRY_WAIT_S}s"
                            f" ({attempt + 1}/{_MAX_IAM_RETRIES - 1})..."
                        )
                        time.sleep(_IAM_RETRY_WAIT_S)
                    else:
                        raise
            agent_runtime_id = response["agentRuntimeId"]
            agent_arn = response["agentRuntimeArn"]
            print(f"  Runtime created: {agent_runtime_id}")
        else:
            # Runtime already exists — update to avoid duplicates (idempotency)
            print(f"  Runtime already exists (ID: {existing_id}) — updating...")
            agentcore_ctrl.update_agent_runtime(
                agentRuntimeId=existing_id,
                agentRuntimeArtifact=artifact,
                networkConfiguration=network_config,
                roleArn=role_arn,
                environmentVariables=env_vars,
            )
            agent_runtime_id = existing_id
            agent_arn = existing_arn
            print(f"  Runtime updated: {agent_runtime_id}")

    except ClientError as e:
        _handle_client_error(e, "AgentCore runtime create/update")

    # ── Step 5: Wait for READY status ────────────────────────────────────────
    print("\nStep 5/5: Waiting for runtime to be ready...")
    try:
        _wait_for_ready(agentcore_ctrl, agent_runtime_id)
    except (RuntimeError, TimeoutError) as e:
        print(f"\n❌ Deployment did not complete: {e}")
        print("   Hint: Check the AgentCore console for detailed error logs.")
        print(f"   https://console.aws.amazon.com/bedrock-agentcore/")
        sys.exit(1)

    # ── Done: Print endpoint information ─────────────────────────────────────
    # URL-encode the ARN (colons and slashes must be percent-encoded in the path segment)
    endpoint_url = (
        f"https://bedrock-agentcore.{aws_region}.amazonaws.com"
        f"/runtimes/{quote(agent_arn, safe='')}/invocations"
    )
    print(f"\n🎉 Agent deployed successfully!")
    print(f"   Agent Name  : {agent_name}")
    print(f"   Runtime ID  : {agent_runtime_id}")
    print(f"   Runtime ARN : {agent_arn}")
    print(f"\n   Endpoint URL (copy for verification):")
    print(f"   {endpoint_url}")
    print(f"\n   Or view the agent in the AWS console:")
    print(f"   https://console.aws.amazon.com/bedrock-agentcore/")


if __name__ == "__main__":
    main()
