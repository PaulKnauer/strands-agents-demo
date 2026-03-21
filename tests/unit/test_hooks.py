"""Unit tests for compliance/hooks.py — AuditLoggingHook."""

import json
import logging
from unittest.mock import MagicMock

import pytest

from compliance.hooks import AuditLoggingHook
from strands.hooks import HookRegistry
from strands.hooks.events import (
    AfterInvocationEvent,
    AfterToolCallEvent,
    BeforeInvocationEvent,
    BeforeToolCallEvent,
    MessageAddedEvent,
)
from strands.types.tools import ToolUse


def get_audit_records(caplog_records):
    """Parse DEBUG log records from strands_agent.audit logger into dicts."""
    return [
        json.loads(r.message)
        for r in caplog_records
        if r.name == "strands_agent.audit" and r.levelno == logging.DEBUG
    ]


def make_tool_use(name="get_today_date", tool_input=None, tool_use_id="t-001") -> ToolUse:
    return {"name": name, "input": tool_input or {}, "toolUseId": tool_use_id}


class TestAuditLoggingHookRegistration:
    def test_hook_registers_all_five_event_types(self):
        """All five Strands hook events must have registered callbacks."""
        registry = HookRegistry()
        hook = AuditLoggingHook()
        hook.register_hooks(registry)

        expected_events = [
            BeforeInvocationEvent,
            AfterInvocationEvent,
            BeforeToolCallEvent,
            AfterToolCallEvent,
            MessageAddedEvent,
        ]
        for event_type in expected_events:
            callbacks = registry._registered_callbacks.get(event_type, [])
            assert len(callbacks) >= 1, f"No callback registered for {event_type.__name__}"


class TestInvocationStartRecord:
    def test_invocation_start_record_structure(self, caplog):
        """invocation_start record must contain event, invocation_id, session_id, timestamp."""
        with caplog.at_level(logging.DEBUG, logger="strands_agent.audit"):
            hook = AuditLoggingHook(session_id="test-session-abc")
            event = BeforeInvocationEvent(agent=MagicMock(), messages=None)
            hook._on_before_invocation(event)

        records = get_audit_records(caplog.records)
        assert len(records) == 1
        r = records[0]
        assert r["event"] == "invocation_start"
        assert "invocation_id" in r
        assert r["session_id"] == "test-session-abc"
        assert "timestamp" in r

    def test_invocation_start_sets_invocation_id(self, caplog):
        """_on_before_invocation must set self._invocation_id to a non-empty string."""
        with caplog.at_level(logging.DEBUG, logger="strands_agent.audit"):
            hook = AuditLoggingHook()
            hook._on_before_invocation(BeforeInvocationEvent(agent=MagicMock(), messages=None))
        assert hook._invocation_id is not None
        assert len(hook._invocation_id) > 0


class TestToolCallRecords:
    def test_tool_call_start_record_structure(self, caplog):
        """tool_call_start record must contain tool_name and tool_input."""
        with caplog.at_level(logging.DEBUG, logger="strands_agent.audit"):
            hook = AuditLoggingHook(session_id="s1")
            tool_use = make_tool_use(name="get_today_date", tool_input={"arg": "val"})
            event = BeforeToolCallEvent(
                agent=MagicMock(),
                selected_tool=None,
                tool_use=tool_use,
                invocation_state={},
            )
            hook._on_before_tool_call(event)

        records = get_audit_records(caplog.records)
        assert len(records) == 1
        r = records[0]
        assert r["event"] == "tool_call_start"
        assert r["tool_name"] == "get_today_date"
        assert r["tool_input"] == {"arg": "val"}

    def test_tool_call_end_result_truncated_to_200_chars(self, caplog):
        """result_snippet in tool_call_end must be truncated to 200 characters."""
        long_result = "x" * 300
        with caplog.at_level(logging.DEBUG, logger="strands_agent.audit"):
            hook = AuditLoggingHook(session_id="s1")
            tool_use = make_tool_use()
            event = AfterToolCallEvent(
                agent=MagicMock(),
                selected_tool=None,
                tool_use=tool_use,
                invocation_state={},
                result=long_result,
            )
            hook._on_after_tool_call(event)

        records = get_audit_records(caplog.records)
        assert len(records) == 1
        r = records[0]
        assert r["event"] == "tool_call_end"
        assert r["tool_name"] == "get_today_date"
        assert len(r["result_snippet"]) == 200

    def test_tool_call_end_short_result_not_truncated(self, caplog):
        """Short results must be preserved in full (not padded)."""
        with caplog.at_level(logging.DEBUG, logger="strands_agent.audit"):
            hook = AuditLoggingHook()
            tool_use = make_tool_use()
            event = AfterToolCallEvent(
                agent=MagicMock(),
                selected_tool=None,
                tool_use=tool_use,
                invocation_state={},
                result="2026-03-20",
            )
            hook._on_after_tool_call(event)

        records = get_audit_records(caplog.records)
        assert records[0]["result_snippet"] == "2026-03-20"


class TestMessageAddedRecord:
    def test_message_added_contains_role_and_content_length(self, caplog):
        """message_added record must include role and content_length."""
        with caplog.at_level(logging.DEBUG, logger="strands_agent.audit"):
            hook = AuditLoggingHook(session_id="s1")
            event = MessageAddedEvent(
                agent=MagicMock(),
                message={"role": "user", "content": "I was born on 14th March 1990"},
            )
            hook._on_message_added(event)

        records = get_audit_records(caplog.records)
        assert len(records) == 1
        r = records[0]
        assert r["event"] == "message_added"
        assert r["role"] == "user"
        assert r["content_length"] == len("I was born on 14th March 1990")

    def test_message_added_no_raw_content(self, caplog):
        """message_added record must NOT include raw content (PII protection)."""
        with caplog.at_level(logging.DEBUG, logger="strands_agent.audit"):
            hook = AuditLoggingHook()
            event = MessageAddedEvent(
                agent=MagicMock(),
                message={"role": "user", "content": "sensitive personal data"},
            )
            hook._on_message_added(event)

        records = get_audit_records(caplog.records)
        r = records[0]
        assert "content" not in r
        assert "text" not in r
        assert "sensitive personal data" not in json.dumps(r)


class TestInvocationEndRecord:
    def test_invocation_end_has_duration(self, caplog):
        """invocation_end record must contain duration_seconds as a float >= 0."""
        with caplog.at_level(logging.DEBUG, logger="strands_agent.audit"):
            hook = AuditLoggingHook(session_id="s1")
            hook._on_before_invocation(BeforeInvocationEvent(agent=MagicMock(), messages=None))
            hook._on_after_invocation(AfterInvocationEvent(agent=MagicMock()))

        records = get_audit_records(caplog.records)
        end_records = [r for r in records if r["event"] == "invocation_end"]
        assert len(end_records) == 1
        assert isinstance(end_records[0]["duration_seconds"], float)
        assert end_records[0]["duration_seconds"] >= 0.0


class TestCommonFields:
    def test_all_records_have_timestamp_and_session_id(self, caplog):
        """Every emitted record must include timestamp (ISO 8601) and session_id."""
        session = "fixed-session-id"
        with caplog.at_level(logging.DEBUG, logger="strands_agent.audit"):
            hook = AuditLoggingHook(session_id=session)
            # Fire several events
            hook._on_before_invocation(BeforeInvocationEvent(agent=MagicMock(), messages=None))
            tool_use = make_tool_use()
            hook._on_before_tool_call(
                BeforeToolCallEvent(
                    agent=MagicMock(),
                    selected_tool=None,
                    tool_use=tool_use,
                    invocation_state={},
                )
            )
            hook._on_after_tool_call(
                AfterToolCallEvent(
                    agent=MagicMock(),
                    selected_tool=None,
                    tool_use=tool_use,
                    invocation_state={},
                    result="2026-03-20",
                )
            )
            hook._on_message_added(
                MessageAddedEvent(
                    agent=MagicMock(),
                    message={"role": "assistant", "content": "Your age is 13159 days."},
                )
            )
            hook._on_after_invocation(AfterInvocationEvent(agent=MagicMock()))

        records = get_audit_records(caplog.records)
        assert len(records) == 5, f"Expected 5 records, got {len(records)}"
        for r in records:
            assert "timestamp" in r, f"Record missing timestamp: {r}"
            assert r["session_id"] == session, f"Record has wrong session_id: {r}"
            # Validate ISO 8601 format (contains T and +00:00 or Z)
            ts = r["timestamp"]
            assert "T" in ts, f"Timestamp not in ISO 8601 format: {ts}"


class TestJSONLContract:
    def test_message_only_formatter_produces_valid_jsonl(self):
        """With %(message)s formatter, each emitted line is a standalone JSON object (JSONL).

        Validates AC #3: one JSON object per line. Uses a real StreamHandler configured
        with the %(message)s format — the format required at every JSONL sink.
        """
        import io

        audit_logger = logging.getLogger("strands_agent.audit")
        buf = io.StringIO()
        handler = logging.StreamHandler(buf)
        handler.setFormatter(logging.Formatter("%(message)s"))
        handler.setLevel(logging.DEBUG)
        audit_logger.addHandler(handler)
        audit_logger.setLevel(logging.DEBUG)
        try:
            hook = AuditLoggingHook(session_id="jsonl-test")
            hook._on_before_invocation(BeforeInvocationEvent(agent=MagicMock(), messages=None))
            hook._on_after_invocation(AfterInvocationEvent(agent=MagicMock()))
        finally:
            audit_logger.removeHandler(handler)

        lines = [l for l in buf.getvalue().splitlines() if l.strip()]
        assert len(lines) >= 2, f"Expected at least 2 lines, got: {buf.getvalue()!r}"
        for line in lines:
            parsed = json.loads(line)  # raises json.JSONDecodeError if line is not valid JSON
            assert isinstance(parsed, dict), f"Expected JSON object per line, got: {line!r}"
