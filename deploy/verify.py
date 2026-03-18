"""AgentCore verification script — invokes the deployed agent and prints the response."""

import json
import os
import re
import sys
import time

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ReadTimeoutError
from dotenv import load_dotenv

# load_dotenv() must be called before any os.environ access
load_dotenv()

TEST_PROMPT = "I was born on 14th March 1990"


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


def _decode_body(raw: str) -> str:
    """Unwrap JSON-encoded response strings returned by AgentCore.

    The runtime wraps the agent's reply in a JSON string, so the raw body
    looks like: '"Hello\\nWorld"'. json.loads() decodes the escapes and
    strips the outer quotes. Falls back to the raw string if not valid JSON.
    """
    try:
        decoded = json.loads(raw)
        if isinstance(decoded, str):
            return decoded
    except (json.JSONDecodeError, ValueError):
        pass
    return raw


def main() -> None:
    """Invoke the deployed AgentCore agent and verify it responds correctly."""
    try:
        aws_region = os.environ["AWS_REGION"]
        agent_name_raw = os.environ["AGENT_NAME"]
    except KeyError as e:
        print(f"\nMissing required environment variable: {e}")
        print("  Hint: Copy .env.example to .env and fill in all required values.")
        sys.exit(1)

    # AgentCore runtime names forbid hyphens — apply same sanitization as deploy.py
    agent_name = agent_name_raw.replace("-", "_")

    print(f"\nVerifying deployed agent '{agent_name}' in {aws_region}...\n")

    # Control-plane client: look up the runtime ARN by name
    agentcore_ctrl = boto3.client("bedrock-agentcore-control", region_name=aws_region)
    try:
        _, agent_arn = _find_existing_runtime(agentcore_ctrl, agent_name)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        print(f"Could not list runtimes ({code}): {msg}")
        print("  Hint: Check AWS credentials and that AWS_REGION is correct.")
        sys.exit(1)

    if agent_arn is None:
        print(f"Agent runtime '{agent_name}' not found in {aws_region}.")
        print("  Hint: Run 'make deploy' first to deploy the agent.")
        sys.exit(1)

    print(f"  Runtime ARN: {agent_arn}")
    print(f'  Test prompt: "{TEST_PROMPT}"\n')

    timeout_seconds = int(os.environ.get("VERIFY_TIMEOUT_SECONDS", "30"))

    # Data-plane client: invoke the runtime (different service from control-plane)
    agentcore_data = boto3.client(
        "bedrock-agentcore",
        region_name=aws_region,
        config=Config(connect_timeout=10, read_timeout=timeout_seconds),
    )
    start = time.monotonic()
    try:
        response = agentcore_data.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            payload=json.dumps({"prompt": TEST_PROMPT}),
        )
    except ReadTimeoutError:
        print(f"Agent did not respond within {timeout_seconds} seconds.")
        print("  Hint: Set VERIFY_TIMEOUT_SECONDS to increase the limit.")
        sys.exit(1)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        print(f"Invocation failed ({code}): {msg}")
        if code in ("AccessDeniedException", "UnauthorizedException"):
            print("  Hint: Your IAM user/role needs bedrock-agentcore:InvokeAgentRuntime.")
        elif code == "ResourceNotFoundException":
            print("  Hint: Runtime not found — check AGENT_NAME and AWS_REGION.")
        else:
            print("  Hint: Check AWS_REGION and that the runtime is in READY status.")
        sys.exit(1)

    # Parse response — body key may vary; handle StreamingBody and raw bytes
    body = response.get("response") or response.get("body") or response.get("payload")
    if body is None:
        print(f"Unexpected response shape — keys: {list(response.keys())}")
        print("  Update verify.py to use the correct response key above.")
        sys.exit(1)

    if hasattr(body, "read"):
        raw = body.read().decode("utf-8")
    elif isinstance(body, (bytes, bytearray)):
        raw = body.decode("utf-8")
    else:
        raw = str(body)

    result = _decode_body(raw)

    elapsed = time.monotonic() - start
    if elapsed > timeout_seconds:
        print(f"Response took {elapsed:.1f}s — exceeded {timeout_seconds}s limit.")
        print("  Hint: Set VERIFY_TIMEOUT_SECONDS to increase the limit.")
        sys.exit(1)

    if not re.search(r"\d+", result):
        print("Response does not contain an age-in-days value.")
        print(f"  Got: {result}")
        sys.exit(1)

    print(f"Agent responded (in {elapsed:.1f}s):\n")
    print(result)
    print("\nVerification complete.")
    print("Next: open the AgentCore console to confirm get_today_date tool traces are visible.")
    print("  https://console.aws.amazon.com/bedrock-agentcore/")


if __name__ == "__main__":
    main()
