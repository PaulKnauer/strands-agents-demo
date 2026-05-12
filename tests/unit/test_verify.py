"""Unit tests for deploy/verify.py — runtime lookup, invocation, response validation."""

import os
import pytest
from datetime import date
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError, ReadTimeoutError

from deploy.verify import (
    _build_runtime_session_id,
    _find_existing_runtime,
    _decode_body,
    _expected_days,
    _contains_expected_age,
    _positive_int_env,
)

AGENT_ARN = "arn:aws:bedrock-agentcore:us-east-1:123456:agent-runtime/test_agent"
ENV = {"AWS_REGION": "us-east-1", "AGENT_NAME": "test-agent"}


def _client_error(code: str, message: str = "error") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": message}}, "operation")


def _make_ctrl(found: bool = True) -> MagicMock:
    mock = MagicMock()
    runtimes = (
        [
            {
                "agentRuntimeName": "test_agent",
                "agentRuntimeId": "id-1",
                "agentRuntimeArn": AGENT_ARN,
            }
        ]
        if found
        else []
    )
    mock.list_agent_runtimes.return_value = {"agentRuntimes": runtimes}
    mock.get_agent_runtime.return_value = {"status": "READY"}
    return mock


def _make_data(body: str = '"You are 13149 days old."') -> MagicMock:
    """Return a mock data-plane client whose invoke_agent_runtime returns a JSON-encoded body.

    AC #7 (Story 3.3): body is a JSON-encoded string (e.g. '"text"') so _decode_body
    unwrapping is exercised on the happy path, not bypassed by a plain string.
    """
    mock = MagicMock()
    mock.invoke_agent_runtime.return_value = {"response": body}
    return mock


def _boto3_factory(ctrl, data):
    def factory(service_name, **kwargs):
        return ctrl if service_name == "bedrock-agentcore-control" else data

    return factory


# ── _decode_body ─────────────────────────────────────────────────────────────


class TestDecodeBody:
    def test_unwraps_json_string(self):
        assert _decode_body('"Hello World"') == "Hello World"

    def test_decodes_escaped_newlines(self):
        assert _decode_body('"line1\\nline2"') == "line1\nline2"

    def test_falls_back_on_plain_string(self):
        assert _decode_body("plain text") == "plain text"

    def test_falls_back_on_invalid_json(self):
        assert _decode_body("{not valid}") == "{not valid}"

    def test_falls_back_when_json_is_not_string(self):
        # If the body is a JSON number or object, return raw
        assert _decode_body("42") == "42"


class TestBuildRuntimeSessionId:
    def test_prefix_and_length_are_stable(self):
        value = _build_runtime_session_id()
        assert value.startswith("verify-session-")
        assert len(value) == len("verify-session-") + 32


# ── _expected_days ────────────────────────────────────────────────────────────


class TestExpectedDays:
    def test_returns_positive_integer(self):
        result = _expected_days()
        assert isinstance(result, int)
        assert result > 0

    def test_increases_over_time(self):
        from datetime import UTC, datetime

        with patch("deploy.verify.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 3, 14, tzinfo=UTC)
            day1 = _expected_days()
            mock_datetime.now.return_value = datetime(2026, 3, 15, tzinfo=UTC)
            day2 = _expected_days()
        assert day2 - day1 == 1

    def test_uses_utc_date(self):
        from datetime import UTC, datetime

        with patch("deploy.verify.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 3, 14, 23, 30, tzinfo=UTC)
            assert _expected_days() == 13149
            mock_datetime.now.assert_called_once_with(UTC)


# ── _contains_expected_age ────────────────────────────────────────────────────


class TestContainsExpectedAge:
    def test_plain_number_matches(self):
        assert _contains_expected_age("You are 13149 days old.", 13149)

    def test_comma_formatted_matches(self):
        assert _contains_expected_age("You were born 13,149 days ago.", 13149)

    def test_wrong_number_does_not_match(self):
        assert not _contains_expected_age("You are 999 days old.", 13149)

    def test_empty_response_does_not_match(self):
        assert not _contains_expected_age("", 13149)

    def test_partial_number_does_not_match(self):
        assert not _contains_expected_age("131490", 13149)

    def test_fractional_number_does_not_match(self):
        assert not _contains_expected_age("You are 13,149.5 days old.", 13149)
        assert not _contains_expected_age("You are 13149.0 days old.", 13149)

    def test_negative_number_does_not_match(self):
        assert not _contains_expected_age("You are -13,149 days old.", 13149)

    def test_number_without_day_context_does_not_match(self):
        assert not _contains_expected_age(
            "I could not verify that 13,149 is correct.", 13149
        )

    def test_large_numeric_token_does_not_crash(self):
        huge_number = "9" * 5000
        assert not _contains_expected_age(f"{huge_number} days old", 13149)


# ── _positive_int_env ─────────────────────────────────────────────────────────


class TestPositiveIntEnv:
    def test_default_when_unset(self):
        with patch.dict(os.environ, {}, clear=True):
            assert _positive_int_env("VERIFY_PERF_BUDGET_SECONDS", 5) == 5

    def test_reads_positive_integer(self):
        with patch.dict(os.environ, {"VERIFY_PERF_BUDGET_SECONDS": "10"}):
            assert _positive_int_env("VERIFY_PERF_BUDGET_SECONDS", 5) == 10

    @pytest.mark.parametrize("value", ["", "5.5", "0", "-1", "abc"])
    def test_invalid_value_exits_with_message(self, value, capsys):
        with (
            patch.dict(os.environ, {"VERIFY_PERF_BUDGET_SECONDS": value}),
            pytest.raises(SystemExit) as exc,
        ):
            _positive_int_env("VERIFY_PERF_BUDGET_SECONDS", 5)
        assert exc.value.code == 1
        assert "positive integer" in capsys.readouterr().out


# ── _find_existing_runtime ────────────────────────────────────────────────────


class TestFindExistingRuntime:
    def test_found_returns_id_and_arn(self):
        ctrl = MagicMock()
        ctrl.list_agent_runtimes.return_value = {
            "agentRuntimes": [
                {
                    "agentRuntimeName": "other",
                    "agentRuntimeId": "id-0",
                    "agentRuntimeArn": "arn-0",
                },
                {
                    "agentRuntimeName": "my_agent",
                    "agentRuntimeId": "id-1",
                    "agentRuntimeArn": "arn-1",
                },
            ]
        }
        runtime_id, runtime_arn = _find_existing_runtime(ctrl, "my_agent")
        assert runtime_id == "id-1"
        assert runtime_arn == "arn-1"

    def test_not_found_returns_none_pair(self):
        ctrl = MagicMock()
        ctrl.list_agent_runtimes.return_value = {"agentRuntimes": []}
        runtime_id, runtime_arn = _find_existing_runtime(ctrl, "missing")
        assert runtime_id is None
        assert runtime_arn is None

    def test_pagination_follows_next_token(self):
        ctrl = MagicMock()
        ctrl.list_agent_runtimes.side_effect = [
            {
                "agentRuntimes": [
                    {
                        "agentRuntimeName": "other",
                        "agentRuntimeId": "id-0",
                        "agentRuntimeArn": "arn-0",
                    }
                ],
                "nextToken": "tok-1",
            },
            {
                "agentRuntimes": [
                    {
                        "agentRuntimeName": "my_agent",
                        "agentRuntimeId": "id-2",
                        "agentRuntimeArn": "arn-2",
                    }
                ],
            },
        ]
        runtime_id, runtime_arn = _find_existing_runtime(ctrl, "my_agent")
        assert runtime_id == "id-2"
        assert ctrl.list_agent_runtimes.call_count == 2
        # Second call must pass the nextToken
        second_call_kwargs = ctrl.list_agent_runtimes.call_args_list[1][1]
        assert second_call_kwargs["nextToken"] == "tok-1"


# ── main() ────────────────────────────────────────────────────────────────────


class TestMain:
    def _run_main(
        self, ctrl, data, env=None, monotonic_values=None, expected_days=13149
    ):
        """Helper: run main() with patched boto3, env, timing, and expected-age calculation."""
        from deploy.verify import main

        timing = monotonic_values or [
            0.0,
            1.0,
        ]  # default: 1s elapsed (within 5s budget)
        env = env or ENV

        with (
            patch("deploy.verify.load_dotenv"),
            patch.dict(os.environ, env, clear=False),
            patch("deploy.verify.boto3.client", side_effect=_boto3_factory(ctrl, data)),
            patch("deploy.verify.time.monotonic", side_effect=timing),
            patch("deploy.verify._expected_days", return_value=expected_days),
        ):
            main()

    def test_happy_path_exits_cleanly(self, capsys):
        ctrl = _make_ctrl(found=True)
        data = _make_data(
            '"You are 13149 days old."'
        )  # JSON-encoded: exercises _decode_body
        self._run_main(ctrl, data)  # must not raise
        captured = capsys.readouterr()
        assert "13,149" in captured.out
        assert "Verification complete." in captured.out
        assert "Result: PASS" in captured.out
        assert "Runtime session ID:" in captured.out
        assert data.invoke_agent_runtime.call_args.kwargs[
            "runtimeSessionId"
        ].startswith("verify-session-")

    def test_missing_env_var_exits_1(self):
        from deploy.verify import main

        with (
            patch("deploy.verify.load_dotenv"),
            patch.dict(os.environ, {}, clear=True),
            pytest.raises(SystemExit) as exc,
        ):
            main()
        assert exc.value.code == 1

    def test_agent_not_found_exits_1(self):
        ctrl = _make_ctrl(found=False)
        data = _make_data()
        with pytest.raises(SystemExit) as exc:
            self._run_main(ctrl, data)
        assert exc.value.code == 1

    def test_runtime_not_found_hint_mentions_deploy(self, capsys):
        ctrl = _make_ctrl(found=False)
        data = _make_data()
        with pytest.raises(SystemExit):
            self._run_main(ctrl, data)
        assert "deploy.py" in capsys.readouterr().out

    def test_runtime_not_ready_exits_before_invocation(self, capsys):
        ctrl = _make_ctrl(found=True)
        ctrl.get_agent_runtime.return_value = {
            "status": "CREATE_FAILED",
            "failureReason": "binary files are incompatible with Linux ARM64",
        }
        data = _make_data()

        with pytest.raises(SystemExit) as exc:
            self._run_main(ctrl, data)

        assert exc.value.code == 1
        data.invoke_agent_runtime.assert_not_called()
        out = capsys.readouterr().out
        assert "CREATE_FAILED" in out
        assert "Linux ARM64" in out
        assert "ARM64-compatible" in out

    @patch("deploy.verify.time.sleep")
    def test_transient_runtime_status_waits_before_invocation(self, mock_sleep, capsys):
        ctrl = _make_ctrl(found=True)
        ctrl.get_agent_runtime.side_effect = [
            {"status": "CREATING"},
            {"status": "READY"},
        ]
        data = _make_data('"You are 13149 days old."')

        self._run_main(ctrl, data, monotonic_values=[0.0, 1.0, 2.0, 3.0])

        mock_sleep.assert_called_once_with(5)
        data.invoke_agent_runtime.assert_called_once()
        assert "CREATING" in capsys.readouterr().out

    def test_runtime_status_lookup_client_error_exits_1(self, capsys):
        ctrl = _make_ctrl(found=True)
        ctrl.get_agent_runtime.side_effect = _client_error(
            "AccessDeniedException", "denied"
        )
        data = _make_data()

        with pytest.raises(SystemExit) as exc:
            self._run_main(ctrl, data)

        assert exc.value.code == 1
        assert "inspect runtime status" in capsys.readouterr().out

    def test_read_timeout_exits_1(self, capsys):
        from deploy.verify import main

        ctrl = _make_ctrl(found=True)
        data = MagicMock()
        data.invoke_agent_runtime.side_effect = ReadTimeoutError(
            endpoint_url="https://test"
        )

        with (
            patch("deploy.verify.load_dotenv"),
            patch.dict(
                os.environ, {**ENV, "VERIFY_TIMEOUT_SECONDS": "30"}, clear=False
            ),
            patch("deploy.verify.boto3.client", side_effect=_boto3_factory(ctrl, data)),
            patch("deploy.verify.time.monotonic", side_effect=[0.0]),
            patch("deploy.verify._expected_days", return_value=13149),
            pytest.raises(SystemExit) as exc,
        ):
            main()

        assert exc.value.code == 1
        assert "30 seconds" in capsys.readouterr().out

    def test_elapsed_over_perf_budget_exits_1(self, capsys):
        ctrl = _make_ctrl(found=True)
        data = _make_data("You are 13149 days old.")
        with pytest.raises(SystemExit) as exc:
            self._run_main(ctrl, data, monotonic_values=[0.0, 31.0])
        assert exc.value.code == 1
        assert "exceeded" in capsys.readouterr().out

    def test_perf_budget_env_override(self, capsys):
        ctrl = _make_ctrl(found=True)
        data = _make_data('"You are 13149 days old."')
        # elapsed 8s is above default 5s budget but below the 10s override — should pass
        self._run_main(
            ctrl,
            data,
            env={**ENV, "VERIFY_PERF_BUDGET_SECONDS": "10"},
            monotonic_values=[0.0, 8.0],
        )
        assert "Result: PASS" in capsys.readouterr().out

    def test_wrong_age_exits_1(self, capsys):
        ctrl = _make_ctrl(found=True)
        data = _make_data('"You are 999 days old."')
        with pytest.raises(SystemExit) as exc:
            self._run_main(ctrl, data, expected_days=13149)
        assert exc.value.code == 1
        out = capsys.readouterr().out
        assert "age-in-days" in out
        assert "13,149" in out

    def test_wrong_age_mentions_model_provider(self, capsys):
        ctrl = _make_ctrl(found=True)
        data = _make_data('"Error: MODEL_PROVIDER is required"')
        with pytest.raises(SystemExit):
            self._run_main(ctrl, data, expected_days=13149)
        assert "MODEL_PROVIDER" in capsys.readouterr().out

    def test_comma_formatted_age_passes(self, capsys):
        ctrl = _make_ctrl(found=True)
        data = _make_data('"You were born 13,149 days ago."')
        self._run_main(ctrl, data, expected_days=13149)
        assert "Result: PASS" in capsys.readouterr().out

    def test_accepts_expected_age_when_utc_date_changes_during_invocation(self, capsys):
        from deploy.verify import main

        ctrl = _make_ctrl(found=True)
        data = _make_data('"You are 13150 days old."')

        with (
            patch("deploy.verify.load_dotenv"),
            patch.dict(os.environ, ENV, clear=False),
            patch("deploy.verify.boto3.client", side_effect=_boto3_factory(ctrl, data)),
            patch("deploy.verify.time.monotonic", side_effect=[0.0, 1.0]),
            patch(
                "deploy.verify._today_utc",
                side_effect=[date(2026, 3, 14), date(2026, 3, 15)],
            ),
        ):
            main()

        assert "Result: PASS" in capsys.readouterr().out

    def test_response_with_no_digits_exits_1(self, capsys):
        ctrl = _make_ctrl(found=True)
        data = _make_data("Sorry, I could not calculate that.")
        with pytest.raises(SystemExit) as exc:
            self._run_main(ctrl, data)
        assert exc.value.code == 1
        assert "age-in-days" in capsys.readouterr().out

    def test_ctrl_client_error_exits_1(self):
        from deploy.verify import main

        ctrl = MagicMock()
        ctrl.list_agent_runtimes.side_effect = _client_error("AccessDeniedException")
        data = _make_data()

        with (
            patch("deploy.verify.load_dotenv"),
            patch.dict(os.environ, ENV, clear=False),
            patch("deploy.verify.boto3.client", side_effect=_boto3_factory(ctrl, data)),
            patch("deploy.verify._expected_days", return_value=13149),
            pytest.raises(SystemExit) as exc,
        ):
            main()
        assert exc.value.code == 1

    def test_ctrl_client_error_hint_mentions_deploy(self, capsys):
        from deploy.verify import main

        ctrl = MagicMock()
        ctrl.list_agent_runtimes.side_effect = _client_error(
            "SomeError", "something broke"
        )
        data = _make_data()

        with (
            patch("deploy.verify.load_dotenv"),
            patch.dict(os.environ, ENV, clear=False),
            patch("deploy.verify.boto3.client", side_effect=_boto3_factory(ctrl, data)),
            patch("deploy.verify._expected_days", return_value=13149),
            pytest.raises(SystemExit),
        ):
            main()
        out = capsys.readouterr().out
        assert "deploy.py" in out
        assert "credentials/IAM" in out

    def test_invalid_timeout_env_exits_1(self, capsys):
        ctrl = _make_ctrl(found=True)
        data = _make_data('"You are 13149 days old."')

        with pytest.raises(SystemExit) as exc:
            self._run_main(ctrl, data, env={**ENV, "VERIFY_TIMEOUT_SECONDS": "bad"})

        assert exc.value.code == 1
        assert "VERIFY_TIMEOUT_SECONDS" in capsys.readouterr().out

    def test_invalid_perf_budget_env_exits_1(self, capsys):
        ctrl = _make_ctrl(found=True)
        data = _make_data('"You are 13149 days old."')

        with pytest.raises(SystemExit) as exc:
            self._run_main(ctrl, data, env={**ENV, "VERIFY_PERF_BUDGET_SECONDS": "0"})

        assert exc.value.code == 1
        assert "VERIFY_PERF_BUDGET_SECONDS" in capsys.readouterr().out

    def test_invoke_client_error_access_denied_exits_1(self, capsys):
        from deploy.verify import main

        ctrl = _make_ctrl(found=True)
        data = MagicMock()
        data.invoke_agent_runtime.side_effect = _client_error(
            "AccessDeniedException", "Access denied"
        )

        with (
            patch("deploy.verify.load_dotenv"),
            patch.dict(os.environ, ENV, clear=False),
            patch("deploy.verify.boto3.client", side_effect=_boto3_factory(ctrl, data)),
            patch("deploy.verify.time.monotonic", side_effect=[0.0]),
            patch("deploy.verify._expected_days", return_value=13149),
            pytest.raises(SystemExit) as exc,
        ):
            main()

        assert exc.value.code == 1
        assert "InvokeAgentRuntime" in capsys.readouterr().out

    def test_invoke_client_error_resource_not_found_exits_1(self, capsys):
        from deploy.verify import main

        ctrl = _make_ctrl(found=True)
        data = MagicMock()
        data.invoke_agent_runtime.side_effect = _client_error(
            "ResourceNotFoundException", "Runtime not found"
        )

        with (
            patch("deploy.verify.load_dotenv"),
            patch.dict(os.environ, ENV, clear=False),
            patch("deploy.verify.boto3.client", side_effect=_boto3_factory(ctrl, data)),
            patch("deploy.verify.time.monotonic", side_effect=[0.0]),
            patch("deploy.verify._expected_days", return_value=13149),
            pytest.raises(SystemExit) as exc,
        ):
            main()

        assert exc.value.code == 1
        out = capsys.readouterr().out
        assert "AGENT_NAME" in out
        assert "InvokeAgentRuntime" in out
