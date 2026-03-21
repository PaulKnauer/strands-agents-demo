"""AgentCore Runtime entrypoint — age-in-days agent via Bedrock Converse API.

Uses boto3 directly rather than strands-agents, which cannot be pip-installed within
AgentCore's 30-second HTTP-server startup window. boto3 is bundled in the deployment
ZIP via bedrock-agentcore's transitive dependency — it is NOT reliably pre-installed
in the AgentCore PYTHON_3_12 runtime despite documentation suggesting otherwise.
agent.py (local REPL) still uses strands-agents.
AgentCore traces every tool call automatically — no custom logging code required.
"""

import datetime
import os

import boto3
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

MAX_TURNS = 10  # prevent runaway tool-calling loops
MAX_PROMPT_CHARS = 4000  # guard against token-cost amplification attacks

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


def _get_today_date() -> str:
    """Return today's ISO date; return error string on failure (never raise)."""
    try:
        return datetime.date.today().isoformat()
    except Exception as e:
        return f"Error retrieving today's date: {str(e)}"


def _run_agent(prompt: str) -> str:
    """Run the agentic tool-calling loop via the Bedrock Converse API."""
    # MODEL_ID is always injected by deploy.py's environmentVariables — the default
    # only fires in misconfigured test scenarios. Use haiku: confirmed available on
    # standard accounts without Marketplace subscription (sonnet requires it).
    model_id = os.environ.get("MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
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

    # Agentic loop — continues until the model issues end_turn (no more tool calls).
    # MAX_TURNS prevents infinite loops if the model misbehaves or a bad prompt
    # causes repeated tool calls without converging to end_turn.
    for _ in range(MAX_TURNS):
        converse_kwargs = dict(
            modelId=model_id,
            system=[{"text": SYSTEM_PROMPT}],
            messages=messages,
            toolConfig={"tools": TOOLS},
        )
        if guardrail_config:
            converse_kwargs["guardrailConfig"] = guardrail_config
        response = bedrock.converse(**converse_kwargs)

        output_message = response["output"]["message"]
        messages.append(output_message)

        if response["stopReason"] == "tool_use":
            # Collect results for every tool call the model issued this turn.
            tool_results = []
            for block in output_message["content"]:
                tool_use = block.get("toolUse")
                if tool_use and tool_use["name"] == "get_today_date":
                    tool_results.append(
                        {
                            "toolResult": {
                                "toolUseId": tool_use["toolUseId"],
                                "content": [{"text": _get_today_date()}],
                            }
                        }
                    )
            messages.append({"role": "user", "content": tool_results})
        else:
            # end_turn — return the model's final text response.
            for block in output_message["content"]:
                if "text" in block:
                    return block["text"]
            return "No response generated."
    raise RuntimeError(f"Agent did not reach end_turn within {MAX_TURNS} turns.")


@app.entrypoint
def handle_invocation(payload: dict) -> str:
    """Process an AgentCore runtime invocation and return the agent response."""
    prompt = payload.get("prompt", "")
    if not prompt.strip():
        return "Error: empty prompt."
    if len(prompt) > MAX_PROMPT_CHARS:
        return f"Error: prompt exceeds {MAX_PROMPT_CHARS} character limit."
    return _run_agent(prompt)


# app.run() must be called unconditionally — not guarded by __name__ == "__main__".
# AgentCore's PYTHON_3_12 runtime does not execute app.py as __main__, so a guarded
# call would silently skip app.run() and the HTTP server would never start.
# host="0.0.0.0" is required: AgentCore's container runtime is not Docker, so the SDK
# defaults to 127.0.0.1 (loopback), which makes the /ping health check unreachable
# from outside the container and causes the 30s initialization timeout.
# Local testing uses agent.py directly; app.py is cloud-only.
app.run(host="0.0.0.0")
