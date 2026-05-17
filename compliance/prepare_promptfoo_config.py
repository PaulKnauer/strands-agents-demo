"""Prepare a promptfoo config for the current red-team environment."""

from __future__ import annotations

import os
from pathlib import Path

SOURCE = Path("compliance/promptfoo-redteam.yaml")
DESTINATION = Path("compliance/promptfoo-redteam.ci.yaml")
GUARDRAIL_KEYS = ("guardrailIdentifier:", "guardrailVersion:")


def prepare_promptfoo_config(
    source: Path = SOURCE,
    destination: Path = DESTINATION,
    guardrail_id: str | None = None,
    guardrail_version: str | None = None,
) -> bool:
    """Write a promptfoo config and return whether guardrails were kept."""
    guardrail_id = (
        guardrail_id if guardrail_id is not None else os.environ.get("GUARDRAIL_ID", "")
    )
    guardrail_version = (
        guardrail_version
        if guardrail_version is not None
        else os.environ.get("GUARDRAIL_VERSION", "DRAFT")
    )
    lines = source.read_text().splitlines()

    if not guardrail_id:
        lines = [
            line for line in lines if not any(key in line for key in GUARDRAIL_KEYS)
        ]
    else:
        # promptfoo 0.121.2 does not expand ${VAR} in target config sections;
        # substitute directly so Bedrock receives the concrete guardrail identifier.
        lines = [
            line.replace("${GUARDRAIL_ID}", guardrail_id).replace(
                "${GUARDRAIL_VERSION}", guardrail_version
            )
            for line in lines
        ]

    destination.write_text("\n".join(lines) + "\n")
    return bool(guardrail_id)


if __name__ == "__main__":
    guardrails_enabled = prepare_promptfoo_config()
    if not guardrails_enabled:
        print(
            "GUARDRAIL_ID is not set; running red-team scan without Bedrock Guardrails."
        )
