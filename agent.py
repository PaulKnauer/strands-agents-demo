"""Age-in-Days Agent — Strands Agents SDK demo."""

import os
import datetime

from compliance.hooks import AuditLoggingHook
from dotenv import load_dotenv
from model_adapters import create_local_model_adapter
from strands import Agent, tool

# load_dotenv() must be called before any os.environ access;
# it populates the environment from the .env file silently if not found
load_dotenv()

SYSTEM_PROMPT = """You are a helpful assistant that calculates a person's age in days.
When given a date of birth, you MUST call the get_today_date tool to retrieve today's
date — never use your training knowledge for the current date.
When a date is given in DD/MM/YYYY format (e.g. 14/03/1990), interpret the first number
as the day and the second as the month.
Then calculate and return the age in days in a friendly, conversational response.
If the date format is ambiguous (e.g. 3/4/1990 could be March 4 or April 3), ask for
clarification before calculating. If the input cannot be parsed as a date at all,
return a helpful error message."""


@tool
def get_today_date() -> str:
    """Returns today's date in ISO 8601 format (YYYY-MM-DD)."""
    try:
        return datetime.date.today().isoformat()
    except Exception as e:
        return f"Error retrieving today's date: {str(e)}"


def create_agent():
    """Construct and return the agent. Deferred so import has no side effects."""
    adapter = create_local_model_adapter(os.environ["MODEL_PROVIDER"], os.environ)
    model = adapter.build()
    return Agent(
        model=model,
        tools=[get_today_date],
        system_prompt=SYSTEM_PROMPT,
        hooks=[AuditLoggingHook()],
    )


def run_repl(agent) -> None:
    """Run the interactive REPL loop until the user exits."""
    print("Age-in-Days Agent (type 'exit' to quit)")
    while True:
        user_input = input("\nYou: ").strip()
        # Accept common exit variations — users naturally type any of these
        if user_input.lower() in ("exit", "quit", "q"):
            break
        # Skip empty input silently — forwarding a blank string to the LLM wastes an API call
        if not user_input:
            continue
        response = agent(user_input)
        print(f"\nAgent: {response}")


if __name__ == "__main__":
    run_repl(create_agent())
