"""AgentCore Runtime entrypoint — age-in-days agent via Bedrock Converse API.

Uses boto3 directly rather than strands-agents, which cannot be pip-installed within
AgentCore's 30-second HTTP-server startup window. boto3 is bundled in the deployment
ZIP via bedrock-agentcore's transitive dependency — it is NOT reliably pre-installed
in the AgentCore PYTHON_3_12 runtime despite documentation suggesting otherwise.
agent.py (local REPL) still uses strands-agents.
The deployed runtime is started through bootstrap.py so ADOT auto-instrumentation
is active before boto3 imports and Bedrock calls occur.
"""

import datetime
import os
import re
from contextlib import contextmanager

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from bedrock_agentcore import BedrockAgentCoreApp

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
except ImportError:  # pragma: no cover - deployment zip always bundles ADOT
    Status = None
    StatusCode = None
    trace = None

app = BedrockAgentCoreApp()

MAX_TURNS = 10  # prevent runaway tool-calling loops
MAX_PROMPT_CHARS = 4000  # guard against token-cost amplification attacks
DEFAULT_MODEL_ID = "us.amazon.nova-micro-v1:0"

# Identical system prompt to agent.py — same agent behaviour in cloud as locally.
SYSTEM_PROMPT = """You are a helpful assistant that calculates a person's age in days.
When given a date of birth, you MUST call the get_today_date tool to retrieve today's
date — never use your training knowledge for the current date.
When a date is given in DD/MM/YYYY format (e.g. 14/03/1990), interpret the first number
as the day and the second as the month.
Then calculate and return the age in days in a friendly, conversational response.
If the date format is ambiguous (e.g. 3/4/1990 could be March 4 or April 3), ask for
clarification before calculating. If the input cannot be parsed as a date at all,
return a helpful error message."""

# Tool definition for the Converse API — mirrors the @tool in agent.py.
TOOLS = [
    {
        "toolSpec": {
            "name": "get_today_date",
            "description": "Returns today's date in ISO 8601 format (YYYY-MM-DD).",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                }
            },
        }
    }
]

_MONTHS = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}


def _tracer():
    """Return the OpenTelemetry tracer when ADOT is available."""
    if trace is None:
        return None
    return trace.get_tracer("age_in_days_demo")


@contextmanager
def _span(name: str, attributes: dict[str, str | int] | None = None):
    """Yield an OTEL span when instrumentation is available, else a no-op."""
    tracer = _tracer()
    if tracer is None:
        yield None
        return

    with tracer.start_as_current_span(name) as span:
        for key, value in (attributes or {}).items():
            span.set_attribute(key, value)
        yield span


def _record_exception(span, error: Exception) -> None:
    """Attach exception details to a span when OTEL is available."""
    if span is None:
        return
    span.record_exception(error)
    if Status and StatusCode:
        span.set_status(Status(StatusCode.ERROR, str(error)))


def _set_span_attribute(span, key: str, value) -> None:
    """Set a span attribute when OTEL is available and the value is not None."""
    if span is None or value is None:
        return
    span.set_attribute(key, value)


def _get_today_date() -> str:
    """Return today's UTC ISO date; return error string on failure (never raise)."""
    try:
        return datetime.datetime.now(datetime.UTC).date().isoformat()
    except Exception as e:
        return f"Error retrieving today's date: {str(e)}"


def _parse_date_of_birth(prompt: str) -> datetime.date | None:
    """Parse supported DOB formats from a user prompt."""
    numeric_match = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", prompt)
    if numeric_match:
        day = int(numeric_match.group(1))
        month = int(numeric_match.group(2))
        year = int(numeric_match.group(3))
        try:
            return datetime.date(year, month, day)
        except ValueError:
            return None

    month_names = "|".join(sorted(_MONTHS, key=len, reverse=True))
    named_match = re.search(
        rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({month_names})\s+(\d{{4}})\b",
        prompt,
        re.IGNORECASE,
    )
    if not named_match:
        return None
    day = int(named_match.group(1))
    month = _MONTHS[named_match.group(2).lower()]
    year = int(named_match.group(3))
    try:
        return datetime.date(year, month, day)
    except ValueError:
        return None


def _format_age_response(dob: datetime.date, today: datetime.date) -> str:
    """Return a deterministic age-in-days response."""
    age_days = (today - dob).days
    return (
        f"You were born on {dob.isoformat()}. As of {today.isoformat()}, "
        f"you are {age_days:,} days old."
    )


def _run_agent(prompt: str) -> str:
    """Run the agentic tool-calling loop via the Bedrock Converse API."""
    # MODEL_ID is always injected by deploy.py's environmentVariables; the default
    # only fires in misconfigured test scenarios. Use Amazon Nova Micro so the
    # deployed path does not depend on Anthropic model access.
    model_id = os.environ.get("MODEL_ID", DEFAULT_MODEL_ID)
    region = os.environ.get("AWS_REGION", "us-east-1")
    # Bedrock Guardrails are optional — only wired when GUARDRAIL_ID is configured.
    # Mirrors the conditional kwargs pattern in agent.py.
    # NIST MANAGE-2.2 / MANAGE-1.3: guardrails enforce content safety and PII
    # anonymisation at the model layer for the deployed AgentCore runtime path.
    guardrail_id = os.environ.get("GUARDRAIL_ID")
    guardrail_version = os.environ.get("GUARDRAIL_VERSION", "DRAFT")
    guardrail_config = (
        {"guardrailIdentifier": guardrail_id, "guardrailVersion": guardrail_version}
        if guardrail_id
        else None
    )

    bedrock = boto3.client("bedrock-runtime", region_name=region)
    messages = [{"role": "user", "content": [{"text": prompt}]}]
    dob = _parse_date_of_birth(prompt)

    with _span(
        "agent.run",
        {
            "agent.name": os.environ.get("AGENT_NAME", "age_in_days_demo"),
            "bedrock.model_id": model_id,
            "app.prompt_length": len(prompt),
        },
    ) as run_span:
        # Agentic loop — continues until the model issues end_turn (no more tool calls).
        # MAX_TURNS prevents infinite loops if the model misbehaves or a bad prompt
        # causes repeated tool calls without converging to end_turn.
        for turn_number in range(1, MAX_TURNS + 1):
            with _span("bedrock.converse", {"agent.turn": turn_number}) as model_span:
                converse_kwargs = dict(
                    modelId=model_id,
                    system=[{"text": SYSTEM_PROMPT}],
                    messages=messages,
                    toolConfig={"tools": TOOLS},
                )
                if guardrail_config:
                    converse_kwargs["guardrailConfig"] = guardrail_config
                response = bedrock.converse(**converse_kwargs)
                _set_span_attribute(
                    model_span, "bedrock.stop_reason", response["stopReason"]
                )

            output_message = response["output"]["message"]
            messages.append(output_message)

            if response["stopReason"] == "tool_use":
                # Collect results for every tool call the model issued this turn.
                tool_results = []
                today = None
                for block in output_message["content"]:
                    tool_use = block.get("toolUse")
                    if tool_use and tool_use["name"] == "get_today_date":
                        with _span(
                            "tool.get_today_date",
                            {"tool.name": "get_today_date"},
                        ) as tool_span:
                            _set_span_attribute(tool_span, "tool.input", "{}")
                            today_text = _get_today_date()
                            _set_span_attribute(tool_span, "tool.output", today_text)
                        try:
                            today = datetime.date.fromisoformat(today_text)
                        except ValueError:
                            today = None
                        tool_results.append(
                            {
                                "toolResult": {
                                    "toolUseId": tool_use["toolUseId"],
                                    "content": [{"text": today_text}],
                                }
                            }
                        )
                if dob and today:
                    if run_span is not None:
                        run_span.set_attribute("tool.get_today_date.used", True)
                    final_response = _format_age_response(dob, today)
                    _set_span_attribute(
                        run_span, "agent.final_response", final_response
                    )
                    return final_response
                messages.append({"role": "user", "content": tool_results})
            else:
                # end_turn — return the model's final text response.
                for block in output_message["content"]:
                    if "text" in block:
                        _set_span_attribute(
                            run_span, "agent.final_response", block["text"]
                        )
                        return block["text"]
                return "No response generated."
    raise RuntimeError(f"Agent did not reach end_turn within {MAX_TURNS} turns.")


@app.entrypoint
def handle_invocation(payload: dict) -> str:
    """Process an AgentCore runtime invocation and return the agent response."""
    with _span("agent.handle_invocation") as invocation_span:
        model_provider = os.environ.get("MODEL_PROVIDER")
        if invocation_span is not None:
            invocation_span.set_attribute(
                "agent.payload_keys", ",".join(sorted(payload.keys()))
            )
        if not model_provider:
            return "Error: MODEL_PROVIDER is required by the deployed runtime. Set MODEL_PROVIDER=bedrock."
        if model_provider != "bedrock":
            return (
                f"Error: MODEL_PROVIDER='{model_provider}' is not supported by the deployed"
                " runtime. Only 'bedrock' is supported."
            )
        prompt = payload.get("prompt", "")
        if not prompt.strip():
            return "Error: empty prompt."
        if len(prompt) > MAX_PROMPT_CHARS:
            return f"Error: prompt exceeds {MAX_PROMPT_CHARS} character limit."
        try:
            return _run_agent(prompt)
        except (ClientError, BotoCoreError) as e:
            _record_exception(invocation_span, e)
            return (
                "Error invoking Bedrock model from AgentCore runtime. Check MODEL_ID,"
                " Bedrock model access, inference profile support, and the runtime IAM"
                f" role's bedrock:InvokeModel permissions. Details: {e}"
            )


# app.run() must be called unconditionally — not guarded by __name__ == "__main__".
# AgentCore's PYTHON_3_12 runtime does not execute app.py as __main__, so a guarded
# call would silently skip app.run() and the HTTP server would never start.
# host="0.0.0.0" is required: AgentCore's container runtime is not Docker, so the SDK
# defaults to 127.0.0.1 (loopback), which makes the /ping health check unreachable
# from outside the container and causes the 30s initialization timeout.
# Local testing uses agent.py directly; app.py is cloud-only.
app.run(host="0.0.0.0")
