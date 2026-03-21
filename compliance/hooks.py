"""Compliance hooks for NIST AI RMF runtime monitoring.

This module provides HookProvider implementations that attach to the Strands
Agent SDK hook registry and produce structured audit records without modifying
any agent business logic.

NIST AI RMF functions addressed:
- MEASURE-2.5: Runtime monitoring via structured invocation and tool call logs.
- MANAGE-2.4: Incident tracking via a complete JSONL audit trail.

JSONL output contract:
    Each call to ``_emit()`` writes exactly one JSON object as the log message.
    To produce valid JSONL at the sink, the handler attached to the
    ``strands_agent.audit`` logger MUST use a formatter whose format string is
    ``'%(message)s'`` (message only — no level prefix or logger name).

    Example configuration for local runs::

        import logging
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logging.getLogger("strands_agent.audit").addHandler(handler)
        logging.getLogger("strands_agent.audit").setLevel(logging.DEBUG)

    In production (AgentCore / CloudWatch), configure the log handler via the
    deployment environment so no code changes are needed here.

    Using ``logging.basicConfig(level=logging.DEBUG)`` will NOT produce valid
    JSONL because ``basicConfig`` prepends ``LEVEL:logger_name:`` to every line.
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import (
    AfterInvocationEvent,
    AfterToolCallEvent,
    BeforeInvocationEvent,
    BeforeToolCallEvent,
    MessageAddedEvent,
)

logger = logging.getLogger("strands_agent.audit")


class AuditLoggingHook(HookProvider):
    """Writes a structured JSONL audit trail for every agent invocation and tool call.

    Each audit record is emitted via the ``strands_agent.audit`` logger at DEBUG
    level so the output destination (stdout, file, CloudWatch) is configurable by
    the caller without modifying this class.

    A single ``session_id`` (UUID) is shared across all records produced by this
    hook instance, enabling correlation of multi-turn conversations.

    Usage::

        agent = Agent(model=model, tools=[...], hooks=[AuditLoggingHook()])
    """

    def __init__(self, session_id: Optional[str] = None) -> None:
        self.session_id: str = session_id or str(uuid.uuid4())
        self._invocation_id: Optional[str] = None
        self._start_time: Optional[float] = None

    def register_hooks(self, registry: HookRegistry) -> None:
        """Register callbacks on all five Strands hook events.

        Supports NIST AI RMF MEASURE-2.5 (runtime monitoring) by capturing
        the full invocation lifecycle: start, tool calls, messages, and end.
        """
        registry.add_callback(BeforeInvocationEvent, self._on_before_invocation)
        registry.add_callback(AfterInvocationEvent, self._on_after_invocation)
        registry.add_callback(BeforeToolCallEvent, self._on_before_tool_call)
        registry.add_callback(AfterToolCallEvent, self._on_after_tool_call)
        registry.add_callback(MessageAddedEvent, self._on_message_added)

    def _emit(self, record: dict) -> None:
        """Attach common fields and emit the record via the audit logger."""
        record["timestamp"] = datetime.now(timezone.utc).isoformat()
        record["session_id"] = self.session_id
        logger.debug(json.dumps(record))

    def _on_before_invocation(self, event: BeforeInvocationEvent) -> None:
        """Emit invocation_start record.

        NIST AI RMF MEASURE-2.5: marks the start of a monitored invocation.
        """
        self._invocation_id = str(uuid.uuid4())
        self._start_time = time.monotonic()
        self._emit(
            {
                "event": "invocation_start",
                "invocation_id": self._invocation_id,
            }
        )

    def _on_after_invocation(self, event: AfterInvocationEvent) -> None:
        """Emit invocation_end record with elapsed duration.

        NIST AI RMF MANAGE-2.4: provides timing data for incident analysis.
        """
        duration = (
            time.monotonic() - self._start_time if self._start_time is not None else 0.0
        )
        self._emit(
            {
                "event": "invocation_end",
                "invocation_id": self._invocation_id,
                "duration_seconds": duration,
            }
        )

    def _on_before_tool_call(self, event: BeforeToolCallEvent) -> None:
        """Emit tool_call_start record with tool name and input.

        NIST AI RMF MEASURE-2.5: records what tool was called and with what
        arguments, enabling auditors to verify tool use is within scope.
        """
        self._emit(
            {
                "event": "tool_call_start",
                "invocation_id": self._invocation_id,
                "tool_name": event.tool_use["name"],
                "tool_input": event.tool_use["input"],
            }
        )

    def _on_after_tool_call(self, event: AfterToolCallEvent) -> None:
        """Emit tool_call_end record with truncated result.

        Result is truncated to 200 characters to prevent unbounded log growth.
        NIST AI RMF MANAGE-2.4: records tool outputs for forensic analysis.
        """
        self._emit(
            {
                "event": "tool_call_end",
                "invocation_id": self._invocation_id,
                "tool_name": event.tool_use["name"],
                "result_snippet": str(event.result)[:200],
            }
        )

    def _on_message_added(self, event: MessageAddedEvent) -> None:
        """Emit message_added record with role and content length only.

        Raw content is deliberately omitted to avoid inadvertently logging PII
        in the audit trail (NIST AI 600-1 data privacy risk category).
        NIST AI RMF MEASURE-2.5: tracks conversation structure without storing
        user-supplied data.
        """
        msg = event.message
        role = (
            msg.get("role", "unknown")
            if isinstance(msg, dict)
            else getattr(msg, "role", "unknown")
        )
        content = (
            msg.get("content", "")
            if isinstance(msg, dict)
            else getattr(msg, "content", "")
        )
        self._emit(
            {
                "event": "message_added",
                "invocation_id": self._invocation_id,
                "role": role,
                "content_length": len(str(content)),
                # raw content deliberately omitted — avoids logging PII
            }
        )
