"""AgentCore verification script — invokes the deployed agent and verifies the response."""

import json
import os
import re
import sys
import time
import uuid
from datetime import UTC, date, datetime

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ReadTimeoutError
from dotenv import load_dotenv

# load_dotenv() must be called before any os.environ access
load_dotenv()

TEST_PROMPT = "I was born on 14th March 1990"
_DOB = date(1990, 3, 14)
_TERMINAL_NOT_READY_STATUSES = {"FAILED", "DELETING", "CREATE_FAILED", "UPDATE_FAILED"}


def _today_utc() -> date:
    """Return today's date in UTC."""
    return datetime.now(UTC).date()


def _expected_days(today: date | None = None) -> int:
    """Return the expected age in days from the fixed DOB to a UTC date."""
    return ((today or _today_utc()) - _DOB).days


def _contains_expected_age(text: str, expected: int) -> bool:
    """Return True if text contains expected as a whole number.

    Accepts comma-grouped formatting such as "13,149" without allowing a
    larger, fractional, or signed number to satisfy expected=13149.
    """
    for match in re.finditer(r"(?<![\d+.\-])(?:\d{1,3}(?:,\d{3})+|\d+)(?![\d.])", text):
        token = match.group(0).replace(",", "")
        try:
            value = int(token)
        except ValueError:
            continue
        if value != expected:
            continue
        context = text[max(0, match.start() - 40) : match.end() + 40].lower()
        if "day" in context:
            return True
    return False


def _positive_int_env(name: str, default: int) -> int:
    """Read a positive integer env var or exit with an actionable message."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        print(f"{name} must be a positive integer; got {raw!r}.")
        sys.exit(1)
    if value < 1:
        print(f"{name} must be a positive integer; got {raw!r}.")
        sys.exit(1)
    return value


def _print_invoke_failure_hint() -> None:
    """Print the full invoke troubleshooting checklist required by the story."""
    print(
        "  Hint: Check AWS credentials, bedrock-agentcore:InvokeAgentRuntime"
        " permission, runtime READY status, AGENT_NAME, and AWS_REGION. A region"
        " mismatch between .env and the deployed runtime is a common cause."
    )


def _wait_for_runtime_ready(
    agentcore_ctrl, agent_runtime_id: str, agent_name: str, timeout_seconds: int = 60
):
    """Return runtime details when READY, waiting briefly through transient states."""
    start = None
    while True:
        runtime = agentcore_ctrl.get_agent_runtime(agentRuntimeId=agent_runtime_id)
        status = runtime.get("status")
        if status == "READY":
            return runtime
        if status in _TERMINAL_NOT_READY_STATUSES or status.endswith("_FAILED"):
            return runtime
        if start is None:
            start = time.monotonic()
        if time.monotonic() - start >= timeout_seconds:
            return runtime
        print(f"Agent runtime '{agent_name}' is {status}; waiting for READY...")
        time.sleep(5)


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


def _build_runtime_session_id() -> str:
    """Return a verifier-owned runtime session identifier."""
    return f"verify-session-{uuid.uuid4().hex}"


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
    verification_date = _today_utc()
    expected = _expected_days(verification_date)

    print(f"\nVerifying deployed agent '{agent_name}' in {aws_region}...")
    print(f"  Expected age: {expected:,} days  (DOB: 1990-03-14 → today, UTC)\n")

    # Control-plane client: look up the runtime ARN by name
    agentcore_ctrl = boto3.client("bedrock-agentcore-control", region_name=aws_region)
    try:
        agent_runtime_id, agent_arn = _find_existing_runtime(agentcore_ctrl, agent_name)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        print(f"Could not list runtimes ({code}): {msg}")
        print(
            "  Hint: Check AWS credentials/IAM permissions, AWS_REGION, and"
            " AGENT_NAME are correct, and that 'python deploy/deploy.py' has"
            " completed successfully."
        )
        sys.exit(1)

    if agent_arn is None:
        print(f"Agent runtime '{agent_name}' not found in {aws_region}.")
        print(
            "  Hint: Check AWS_REGION and AGENT_NAME, then run"
            " 'python deploy/deploy.py' to deploy the agent."
        )
        sys.exit(1)

    try:
        runtime = _wait_for_runtime_ready(agentcore_ctrl, agent_runtime_id, agent_name)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        print(f"Could not inspect runtime status ({code}): {msg}")
        print(
            "  Hint: Check AWS credentials/IAM permissions and confirm the runtime"
            " still exists in this region."
        )
        sys.exit(1)

    status = runtime.get("status")
    if status != "READY":
        print(f"Agent runtime '{agent_name}' is not READY (status: {status}).")
        failure_reason = runtime.get("failureReason")
        if failure_reason:
            print(f"  Failure reason: {failure_reason}")
            if "ARM64" in failure_reason or "binary files" in failure_reason:
                print(
                    "  Hint: Rebuild and redeploy the AgentCore artifact with"
                    " ARM64-compatible Linux wheels before running verification."
                )
        else:
            print("  Hint: Re-run 'python deploy/deploy.py' and wait for READY status.")
        sys.exit(1)

    print(f"  Runtime: {agent_name}")
    print(f"  Runtime ARN: {agent_arn}")
    print(f'  Test prompt: "{TEST_PROMPT}"\n')

    # VERIFY_TIMEOUT_SECONDS controls the boto3 transport read-timeout only.
    # VERIFY_PERF_BUDGET_SECONDS controls the correctness performance check (default 5s).
    timeout_seconds = _positive_int_env("VERIFY_TIMEOUT_SECONDS", 30)
    perf_budget = _positive_int_env("VERIFY_PERF_BUDGET_SECONDS", 5)
    runtime_session_id = _build_runtime_session_id()

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
            runtimeSessionId=runtime_session_id,
            payload=json.dumps({"prompt": TEST_PROMPT}),
        )
    except ReadTimeoutError:
        print(f"Agent did not respond within {timeout_seconds} seconds.")
        print("  Hint: Set VERIFY_TIMEOUT_SECONDS to increase the transport limit.")
        sys.exit(1)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        print(f"Invocation failed ({code}): {msg}")
        if code in ("AccessDeniedException", "UnauthorizedException"):
            print("  Access denied while invoking the AgentCore runtime.")
        elif code == "ResourceNotFoundException":
            print("  Runtime not found during invocation.")
        else:
            print(
                "  Invocation reached AgentCore but failed before a response returned."
            )
        _print_invoke_failure_hint()
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
    completion_date = _today_utc()
    expected_values = {expected}
    if completion_date != verification_date:
        expected_values.add(_expected_days(completion_date))

    print(f"Agent responded (in {elapsed:.1f}s):\n")
    print(result)
    print()
    print(
        f"  Runtime session ID: {response.get('runtimeSessionId', runtime_session_id)}"
    )
    print()

    passed = True

    if not any(_contains_expected_age(result, value) for value in expected_values):
        expected_display = " or ".join(
            f"{value:,}" for value in sorted(expected_values)
        )
        print(
            f"FAIL — response does not contain the expected age-in-days"
            f" value ({expected_display})."
        )
        print(f"  Got: {result}")
        print(
            "  If the response indicates a model or provider error, check:"
            " MODEL_PROVIDER=bedrock (only 'bedrock' is supported in the deployed runtime),"
            " MODEL_ID, and Bedrock model access in your region."
        )
        passed = False

    if elapsed > perf_budget:
        print(
            f"FAIL — elapsed time {elapsed:.1f}s exceeded {perf_budget}s performance"
            " budget."
        )
        print(
            "  Hint: Set VERIFY_PERF_BUDGET_SECONDS to override the budget (default 5s)."
            " Use VERIFY_TIMEOUT_SECONDS to extend the transport limit (default 30s)."
        )
        passed = False

    if not passed:
        sys.exit(1)

    print(
        f"  Expected: {expected:,} days  |  Elapsed: {elapsed:.1f}s"
        f" (within {perf_budget}s budget)  |  Result: PASS"
    )
    print("\nVerification complete.")
    print(
        "Next: open the AgentCore console to confirm get_today_date tool traces are visible."
    )
    print("  https://console.aws.amazon.com/bedrock-agentcore/")


if __name__ == "__main__":
    main()
