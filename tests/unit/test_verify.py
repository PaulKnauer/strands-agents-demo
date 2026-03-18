"""Unit tests for deploy/verify.py — runtime lookup, invocation, response validation."""

import os
import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError, ReadTimeoutError

from deploy.verify import _find_existing_runtime, _decode_body

AGENT_ARN = "arn:aws:bedrock-agentcore:us-east-1:123456:agent-runtime/test_agent"
ENV = {"AWS_REGION": "us-east-1", "AGENT_NAME": "test-agent"}


def _client_error(code: str, message: str = "error") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": message}}, "operation")


def _make_ctrl(found: bool = True) -> MagicMock:
    mock = MagicMock()
    runtimes = (
        [{"agentRuntimeName": "test_agent", "agentRuntimeId": "id-1", "agentRuntimeArn": AGENT_ARN}]
        if found
        else []
    )
    mock.list_agent_runtimes.return_value = {"agentRuntimes": runtimes}
    return mock


def _make_data(body: str = "You are 13149 days old.") -> MagicMock:
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


# ── _find_existing_runtime ────────────────────────────────────────────────────

class TestFindExistingRuntime:
    def test_found_returns_id_and_arn(self):
        ctrl = MagicMock()
        ctrl.list_agent_runtimes.return_value = {
            "agentRuntimes": [
                {"agentRuntimeName": "other", "agentRuntimeId": "id-0", "agentRuntimeArn": "arn-0"},
                {"agentRuntimeName": "my_agent", "agentRuntimeId": "id-1", "agentRuntimeArn": "arn-1"},
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
                "agentRuntimes": [{"agentRuntimeName": "other", "agentRuntimeId": "id-0", "agentRuntimeArn": "arn-0"}],
                "nextToken": "tok-1",
            },
            {
                "agentRuntimes": [{"agentRuntimeName": "my_agent", "agentRuntimeId": "id-2", "agentRuntimeArn": "arn-2"}],
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
    def _run_main(self, ctrl, data, env=None, monotonic_values=None):
        """Helper: run main() with patched boto3, env, and timing."""
        from deploy.verify import main

        timing = monotonic_values or [0.0, 1.0]  # default: 1s elapsed (within limit)
        env = env or ENV

        with (
            patch("deploy.verify.load_dotenv"),
            patch.dict(os.environ, env, clear=False),
            patch("deploy.verify.boto3.client", side_effect=_boto3_factory(ctrl, data)),
            patch("deploy.verify.time.monotonic", side_effect=timing),
        ):
            main()

    def test_happy_path_exits_cleanly(self, capsys):
        ctrl = _make_ctrl(found=True)
        data = _make_data("You are 13149 days old.")
        self._run_main(ctrl, data)  # must not raise
        captured = capsys.readouterr()
        assert "13149" in captured.out
        assert "Verification complete." in captured.out

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

    def test_read_timeout_exits_1(self, capsys):
        from deploy.verify import main

        ctrl = _make_ctrl(found=True)
        data = MagicMock()
        data.invoke_agent_runtime.side_effect = ReadTimeoutError(endpoint_url="https://test")

        with (
            patch("deploy.verify.load_dotenv"),
            patch.dict(os.environ, {**ENV, "VERIFY_TIMEOUT_SECONDS": "30"}, clear=False),
            patch("deploy.verify.boto3.client", side_effect=_boto3_factory(ctrl, data)),
            patch("deploy.verify.time.monotonic", side_effect=[0.0]),
            pytest.raises(SystemExit) as exc,
        ):
            main()

        assert exc.value.code == 1
        assert "30 seconds" in capsys.readouterr().out

    def test_elapsed_over_limit_exits_1(self, capsys):
        ctrl = _make_ctrl(found=True)
        data = _make_data("You are 13149 days old.")
        with pytest.raises(SystemExit) as exc:
            self._run_main(ctrl, data, monotonic_values=[0.0, 31.0])
        assert exc.value.code == 1
        assert "exceeded" in capsys.readouterr().out

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
            pytest.raises(SystemExit) as exc,
        ):
            main()
        assert exc.value.code == 1

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
            pytest.raises(SystemExit) as exc,
        ):
            main()

        assert exc.value.code == 1
        assert "InvokeAgentRuntime" in capsys.readouterr().out
