"""Unit tests for deploy/deploy.py — env validation, error hints, idempotency, polling.

AC #3 (Story 3.3): deploy.py error-handling, idempotency, and polling logic.
AC #4 (Story 2.1): troubleshooting hints for common AWS errors.
AC #3 (Story 2.1): idempotency — update, not duplicate, on re-deploy.
"""

import json
import io
import os
import sys
import zipfile
import pytest
from unittest.mock import MagicMock, patch, call
from botocore.exceptions import ClientError

from deploy.deploy import (
    _bedrock_model_resources,
    _build_artifact,
    _build_deployment_zip,
    _get_runtime_role_arn,
    _find_existing_runtime,
    _handle_client_error,
    _wait_for_ready,
    _ensure_s3_bucket,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _client_error(code: str, message: str = "error") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": message}}, "operation")


ENV = {
    "AWS_REGION": "us-east-1",
    "AGENT_NAME": "test-agent",
    "MODEL_ID": "us.amazon.nova-micro-v1:0",
    "MODEL_PROVIDER": "bedrock",
}


# ── _handle_client_error ─────────────────────────────────────────────────────


class TestHandleClientError:
    def test_access_denied_prints_iam_hint(self, capsys):
        with pytest.raises(SystemExit) as exc:
            _handle_client_error(_client_error("AccessDeniedException"), "test")
        assert exc.value.code == 1
        out = capsys.readouterr().out
        assert "permissions" in out.lower()

    def test_unauthorized_prints_iam_hint(self, capsys):
        with pytest.raises(SystemExit) as exc:
            _handle_client_error(_client_error("UnauthorizedException"), "test")
        assert exc.value.code == 1
        out = capsys.readouterr().out
        assert "permissions" in out.lower()

    def test_resource_not_found_prints_region_hint(self, capsys):
        with pytest.raises(SystemExit) as exc:
            _handle_client_error(_client_error("ResourceNotFoundException"), "test")
        assert exc.value.code == 1
        out = capsys.readouterr().out
        assert "region" in out.lower()

    def test_invalid_token_prints_credentials_hint(self, capsys):
        with pytest.raises(SystemExit) as exc:
            _handle_client_error(_client_error("InvalidClientTokenId"), "test")
        assert exc.value.code == 1
        out = capsys.readouterr().out
        assert "credential" in out.lower()

    def test_expired_token_prints_credentials_hint(self, capsys):
        with pytest.raises(SystemExit) as exc:
            _handle_client_error(_client_error("ExpiredTokenException"), "test")
        assert exc.value.code == 1
        out = capsys.readouterr().out
        assert "credential" in out.lower()

    def test_invalid_parameter_prints_agent_name_hint(self, capsys):
        with pytest.raises(SystemExit) as exc:
            _handle_client_error(_client_error("InvalidParameterException"), "test")
        assert exc.value.code == 1
        out = capsys.readouterr().out
        assert "AGENT_NAME" in out or "parameter" in out.lower()

    def test_unknown_code_prints_generic_hint(self, capsys):
        with pytest.raises(SystemExit) as exc:
            _handle_client_error(_client_error("SomeUnknownError"), "test")
        assert exc.value.code == 1
        out = capsys.readouterr().out
        assert "AWS_REGION" in out or "hint" in out.lower() or "error" in out.lower()


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
        second_kwargs = ctrl.list_agent_runtimes.call_args_list[1][1]
        assert second_kwargs["nextToken"] == "tok-1"


# ── _wait_for_ready ───────────────────────────────────────────────────────────


class TestWaitForReady:
    @patch("deploy.deploy.time.sleep")
    def test_ready_status_returns_immediately(self, mock_sleep):
        ctrl = MagicMock()
        ctrl.get_agent_runtime.return_value = {"status": "READY"}
        _wait_for_ready(ctrl, "runtime-id-1", timeout_seconds=60)
        assert mock_sleep.call_count == 0

    @patch("deploy.deploy.time.sleep")
    def test_failed_status_raises_runtime_error(self, mock_sleep):
        ctrl = MagicMock()
        ctrl.get_agent_runtime.return_value = {"status": "FAILED"}
        with pytest.raises(RuntimeError, match="unexpected status"):
            _wait_for_ready(ctrl, "runtime-id-1", timeout_seconds=60)

    @patch("deploy.deploy.time.sleep")
    def test_create_failed_status_includes_failure_reason(self, mock_sleep):
        ctrl = MagicMock()
        ctrl.get_agent_runtime.return_value = {
            "status": "CREATE_FAILED",
            "failureReason": "binary files are incompatible with Linux ARM64",
        }
        with pytest.raises(RuntimeError, match="Linux ARM64"):
            _wait_for_ready(ctrl, "runtime-id-1", timeout_seconds=60)
        mock_sleep.assert_not_called()

    @patch("deploy.deploy.time.sleep")
    def test_timeout_raises_timeout_error(self, mock_sleep):
        ctrl = MagicMock()
        # Always returns CREATING — never becomes READY
        ctrl.get_agent_runtime.return_value = {"status": "CREATING"}
        with pytest.raises(TimeoutError, match="READY"):
            _wait_for_ready(ctrl, "runtime-id-1", timeout_seconds=20)
        # Should have polled twice (0s, 10s, 20s → timeout at elapsed=20)
        assert ctrl.get_agent_runtime.call_count >= 2

    @patch("deploy.deploy.time.sleep")
    def test_ready_after_one_poll_returns(self, mock_sleep):
        ctrl = MagicMock()
        ctrl.get_agent_runtime.side_effect = [
            {"status": "CREATING"},
            {"status": "READY"},
        ]
        _wait_for_ready(ctrl, "runtime-id-1", timeout_seconds=60)
        assert ctrl.get_agent_runtime.call_count == 2
        assert mock_sleep.call_count == 1


# ── _ensure_s3_bucket ─────────────────────────────────────────────────────────


class TestEnsureS3Bucket:
    def test_us_east_1_creates_without_location_constraint(self):
        s3 = MagicMock()
        s3.head_bucket.side_effect = _client_error("404")
        _ensure_s3_bucket(s3, "my-bucket", "us-east-1", "123456789012")
        s3.create_bucket.assert_called_once_with(Bucket="my-bucket")

    def test_other_region_creates_with_location_constraint(self):
        s3 = MagicMock()
        s3.head_bucket.side_effect = _client_error("404")
        _ensure_s3_bucket(s3, "my-bucket", "eu-west-1", "123456789012")
        s3.create_bucket.assert_called_once_with(
            Bucket="my-bucket",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
        )

    def test_existing_bucket_skips_create(self):
        s3 = MagicMock()
        s3.head_bucket.return_value = {}  # bucket exists
        _ensure_s3_bucket(s3, "my-bucket", "us-east-1", "123456789012")
        s3.create_bucket.assert_not_called()

    def test_always_applies_sse_encryption(self):
        s3 = MagicMock()
        s3.head_bucket.return_value = {}
        _ensure_s3_bucket(s3, "my-bucket", "us-east-1", "123456789012")
        s3.put_bucket_encryption.assert_called_once()
        call_kwargs = s3.put_bucket_encryption.call_args[1]
        assert call_kwargs["Bucket"] == "my-bucket"


# ── main() — env var validation ───────────────────────────────────────────────


class TestMainEnvValidation:
    def _run_main_no_env(self, env: dict):
        from deploy.deploy import main

        with (
            patch("deploy.deploy.load_dotenv"),
            patch.dict(os.environ, env, clear=True),
            pytest.raises(SystemExit) as exc,
        ):
            main()
        return exc.value.code

    def test_missing_aws_region_exits_1(self, capsys):
        code = self._run_main_no_env(
            {
                "AGENT_NAME": "test-agent",
                "MODEL_ID": "some-model",
                "MODEL_PROVIDER": "bedrock",
            }
        )
        assert code == 1
        assert "AWS_REGION" in capsys.readouterr().out

    def test_missing_agent_name_exits_1(self, capsys):
        code = self._run_main_no_env(
            {
                "AWS_REGION": "us-east-1",
                "MODEL_ID": "some-model",
                "MODEL_PROVIDER": "bedrock",
            }
        )
        assert code == 1
        assert "AGENT_NAME" in capsys.readouterr().out

    def test_missing_model_id_exits_1(self, capsys):
        code = self._run_main_no_env(
            {
                "AWS_REGION": "us-east-1",
                "AGENT_NAME": "test-agent",
                "MODEL_PROVIDER": "bedrock",
            }
        )
        assert code == 1
        assert "MODEL_ID" in capsys.readouterr().out

    def test_missing_model_provider_exits_1(self, capsys):
        code = self._run_main_no_env(
            {
                "AWS_REGION": "us-east-1",
                "AGENT_NAME": "test-agent",
                "MODEL_ID": "some-model",
            }
        )
        assert code == 1
        assert "MODEL_PROVIDER" in capsys.readouterr().out

    def test_hint_message_references_env_example(self, capsys):
        """Missing env var message must reference .env.example."""
        self._run_main_no_env({})
        out = capsys.readouterr().out
        assert ".env" in out

    def test_non_bedrock_model_provider_exits_1(self, capsys):
        """AC #2 (Story 2.2): MODEL_PROVIDER != 'bedrock' must fail deployment with a clear error."""
        code = self._run_main_no_env(
            {
                "AWS_REGION": "us-east-1",
                "AGENT_NAME": "test-agent",
                "MODEL_ID": "some-model",
                "MODEL_PROVIDER": "gemini",
            }
        )
        assert code == 1
        out = capsys.readouterr().out
        assert (
            "gemini" in out.lower()
            or "MODEL_PROVIDER" in out
            or "bedrock" in out.lower()
        )


# ── main() — idempotency (create vs update) ───────────────────────────────────


class TestMainIdempotency:
    def _make_boto3_factory(self, sts, s3, cloudformation, ctrl):
        def factory(service_name, **kwargs):
            if service_name == "sts":
                return sts
            if service_name == "s3":
                return s3
            if service_name == "cloudformation":
                return cloudformation
            if service_name == "bedrock-agentcore-control":
                return ctrl
            return MagicMock()

        return factory

    def _base_mocks(self):
        sts = MagicMock()
        sts.get_caller_identity.return_value = {"Account": "123456789012"}

        s3 = MagicMock()
        s3.head_bucket.return_value = {}  # bucket exists

        cloudformation = MagicMock()
        cloudformation.describe_stacks.return_value = {
            "Stacks": [
                {
                    "Outputs": [
                        {
                            "OutputKey": "AgentCoreRuntimeRoleArn",
                            "OutputValue": "arn:aws:iam::123456789012:role/test-role",
                        },
                        {
                            "OutputKey": "AgentCoreRuntimeRoleName",
                            "OutputValue": "generated-role-name",
                        },
                    ]
                }
            ]
        }

        return sts, s3, cloudformation

    @patch("deploy.deploy.load_dotenv")
    @patch("deploy.deploy._build_deployment_zip", return_value=b"zipbytes")
    def test_new_runtime_calls_create(self, mock_zip, mock_dotenv):
        sts, s3, cloudformation = self._base_mocks()
        ctrl = MagicMock()
        ctrl.list_agent_runtimes.return_value = {"agentRuntimes": []}
        ctrl.create_agent_runtime.return_value = {
            "agentRuntimeId": "rt-123",
            "agentRuntimeArn": "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/rt-123",
        }
        ctrl.get_agent_runtime.return_value = {"status": "READY"}

        with (
            patch.dict(os.environ, ENV, clear=True),
            patch(
                "deploy.deploy.boto3.client",
                side_effect=self._make_boto3_factory(sts, s3, cloudformation, ctrl),
            ),
            patch("deploy.deploy.time.sleep"),
        ):
            from deploy.deploy import main

            main()

        ctrl.create_agent_runtime.assert_called_once()
        ctrl.update_agent_runtime.assert_not_called()
        env_vars = ctrl.create_agent_runtime.call_args.kwargs["environmentVariables"]
        assert env_vars["AGENT_OBSERVABILITY_ENABLED"] == "true"
        assert env_vars["AWS_AGENTIC_OBSERVABILITY_OPT_IN"] == "true"
        assert env_vars["OTEL_TRACES_EXPORTER"] == "otlp"
        assert (
            env_vars["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"]
            == "https://xray.us-east-1.amazonaws.com/v1/traces"
        )
        assert env_vars["OTEL_RESOURCE_ATTRIBUTES"] == "service.name=test_agent"

    @patch("deploy.deploy.load_dotenv")
    @patch("deploy.deploy._build_deployment_zip", return_value=b"zipbytes")
    def test_existing_runtime_calls_update(self, mock_zip, mock_dotenv):
        sts, s3, cloudformation = self._base_mocks()
        ctrl = MagicMock()
        ctrl.list_agent_runtimes.return_value = {
            "agentRuntimes": [
                {
                    "agentRuntimeName": "test_agent",
                    "agentRuntimeId": "rt-existing",
                    "agentRuntimeArn": "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/rt-existing",
                }
            ]
        }
        ctrl.get_agent_runtime.return_value = {"status": "READY"}

        with (
            patch.dict(os.environ, ENV, clear=True),
            patch(
                "deploy.deploy.boto3.client",
                side_effect=self._make_boto3_factory(sts, s3, cloudformation, ctrl),
            ),
            patch("deploy.deploy.time.sleep"),
        ):
            from deploy.deploy import main

            main()

        ctrl.update_agent_runtime.assert_called_once()
        ctrl.create_agent_runtime.assert_not_called()
        env_vars = ctrl.update_agent_runtime.call_args.kwargs["environmentVariables"]
        assert env_vars["AGENT_OBSERVABILITY_ENABLED"] == "true"
        assert env_vars["AWS_AGENTIC_OBSERVABILITY_OPT_IN"] == "true"
        assert env_vars["OTEL_TRACES_EXPORTER"] == "otlp"
        assert (
            env_vars["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"]
            == "https://xray.us-east-1.amazonaws.com/v1/traces"
        )
        assert env_vars["OTEL_RESOURCE_ATTRIBUTES"] == "service.name=test_agent"


# ── _build_artifact ───────────────────────────────────────────────────────────


class TestBuildArtifact:
    def test_runtime_is_python_312(self):
        artifact = _build_artifact("my-bucket", "my-key/deployment.zip")
        assert artifact["codeConfiguration"]["runtime"] == "PYTHON_3_12"

    def test_entry_point_is_single_element_bootstrap_py(self):
        """Entry point must stay a single Python file for AgentCore validation."""
        artifact = _build_artifact("my-bucket", "my-key/deployment.zip")
        assert artifact["codeConfiguration"]["entryPoint"] == ["bootstrap.py"]

    def test_uses_s3_source_with_correct_bucket_and_key(self):
        artifact = _build_artifact("test-bucket", "agent/deployment.zip")
        s3 = artifact["codeConfiguration"]["code"]["s3"]
        assert s3["bucket"] == "test-bucket"
        assert s3["prefix"] == "agent/deployment.zip"


# ── _build_deployment_zip ────────────────────────────────────────────────────


class TestBuildDeploymentZip:
    @patch("deploy.deploy.subprocess.run")
    def test_dependency_install_targets_agentcore_arm64(self, mock_run, tmp_path):
        project_root = tmp_path
        deploy_dir = project_root / "deploy"
        deploy_dir.mkdir()
        (deploy_dir / "app.py").write_text("app = object()\n")
        (deploy_dir / "bootstrap.py").write_text("import app\n")

        zip_bytes = _build_deployment_zip(str(project_root))

        assert zip_bytes
        cmd = mock_run.call_args.args[0]
        platform_index = cmd.index("--platform") + 1
        python_version_index = cmd.index("--python-version") + 1
        binary_index = cmd.index("--only-binary") + 1
        assert cmd[platform_index] == "manylinux2014_aarch64"
        assert cmd[python_version_index] == "312"
        assert cmd[binary_index] == ":all:"
        assert "aws-opentelemetry-distro>=0.10.0" in cmd

    @patch("deploy.deploy.subprocess.run")
    def test_bundle_contains_bootstrap_and_app(self, mock_run, tmp_path):
        project_root = tmp_path
        deploy_dir = project_root / "deploy"
        deploy_dir.mkdir()
        (deploy_dir / "app.py").write_text("app = object()\n")
        (deploy_dir / "bootstrap.py").write_text("import app\n")

        zip_bytes = _build_deployment_zip(str(project_root))

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = set(zf.namelist())
        assert "app.py" in names
        assert "bootstrap.py" in names


# ── _ensure_iam_role ──────────────────────────────────────────────────────────


class TestGetRuntimeRoleArn:
    def test_inference_profile_resources_include_profile_and_routed_models(self):
        resources = _bedrock_model_resources(
            "us-east-1",
            "123456789012",
            "us.amazon.nova-micro-v1:0",
        )

        assert (
            "arn:aws:bedrock:us-east-1:123456789012:inference-profile/"
            "us.amazon.nova-micro-v1:0"
        ) in resources
        assert (
            "arn:aws:bedrock:us-east-1::foundation-model/" "amazon.nova-micro-v1:0"
        ) in resources
        assert (
            "arn:aws:bedrock:us-east-2::foundation-model/" "amazon.nova-micro-v1:0"
        ) in resources
        assert (
            "arn:aws:bedrock:us-west-2::foundation-model/" "amazon.nova-micro-v1:0"
        ) in resources

    def test_stack_output_role_arn_returned(self):
        cloudformation = MagicMock()
        cloudformation.describe_stacks.return_value = {
            "Stacks": [
                {
                    "Outputs": [
                        {
                            "OutputKey": "AgentCoreRuntimeRoleArn",
                            "OutputValue": "arn:aws:iam::123456789012:role/generated",
                        },
                        {
                            "OutputKey": "AgentCoreRuntimeRoleName",
                            "OutputValue": "generated-role-name",
                        },
                    ]
                }
            ]
        }
        assert (
            _get_runtime_role_arn(
                cloudformation, "StrandsDemoAgentCoreRuntimeRoleStack"
            )
            == "arn:aws:iam::123456789012:role/generated"
        )

    def test_missing_stack_exits_with_cdk_hint(self, capsys):
        cloudformation = MagicMock()
        cloudformation.describe_stacks.side_effect = _client_error("ValidationError")
        with pytest.raises(SystemExit) as exc:
            _get_runtime_role_arn(
                cloudformation, "StrandsDemoAgentCoreRuntimeRoleStack"
            )
        assert exc.value.code == 1
        out = capsys.readouterr().out
        assert "make create-role" in out
        assert "CDK" in out

    def test_missing_output_exits_with_cdk_hint(self, capsys):
        cloudformation = MagicMock()
        cloudformation.describe_stacks.return_value = {"Stacks": [{"Outputs": []}]}
        with pytest.raises(SystemExit) as exc:
            _get_runtime_role_arn(
                cloudformation, "StrandsDemoAgentCoreRuntimeRoleStack"
            )
        assert exc.value.code == 1
        assert "AgentCoreRuntimeRoleArn" in capsys.readouterr().out


# ── main() — endpoint output ──────────────────────────────────────────────────


class TestEndpointOutput:
    """Verify main() prints required deployment details on successful deployment."""

    def _make_boto3_factory(self, sts, s3, cloudformation, ctrl):
        def factory(service_name, **kwargs):
            if service_name == "sts":
                return sts
            if service_name == "s3":
                return s3
            if service_name == "cloudformation":
                return cloudformation
            if service_name == "bedrock-agentcore-control":
                return ctrl
            return MagicMock()

        return factory

    @patch("deploy.deploy.load_dotenv")
    @patch("deploy.deploy._build_deployment_zip", return_value=b"zipbytes")
    def test_endpoint_url_url_encodes_arn(self, mock_zip, mock_dotenv, capsys):
        sts = MagicMock()
        sts.get_caller_identity.return_value = {"Account": "123456789012"}
        s3 = MagicMock()
        s3.head_bucket.return_value = {}
        cloudformation = MagicMock()
        cloudformation.describe_stacks.return_value = {
            "Stacks": [
                {
                    "Outputs": [
                        {
                            "OutputKey": "AgentCoreRuntimeRoleArn",
                            "OutputValue": "arn:aws:iam::123456789012:role/generated",
                        }
                    ]
                }
            ]
        }
        ctrl = MagicMock()
        agent_arn = "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/rt-abc"
        ctrl.list_agent_runtimes.return_value = {"agentRuntimes": []}
        ctrl.create_agent_runtime.return_value = {
            "agentRuntimeId": "rt-abc",
            "agentRuntimeArn": agent_arn,
        }
        ctrl.get_agent_runtime.return_value = {"status": "READY"}

        with (
            patch.dict(os.environ, ENV, clear=True),
            patch(
                "deploy.deploy.boto3.client",
                side_effect=self._make_boto3_factory(
                    sts, s3, cloudformation, ctrl
                ),
            ),
            patch("deploy.deploy.time.sleep"),
        ):
            from deploy.deploy import main

            main()

        out = capsys.readouterr().out
        # Colons and slashes in ARN must be percent-encoded in the URL path segment
        assert (
            "arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3A123456789012%3Aruntime%2Frt-abc"
            in out
        )
        assert "Agent Name" in out
        assert "Runtime ID" in out
        assert "Runtime ARN" in out
