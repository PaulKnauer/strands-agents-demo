"""Tests for the CloudWatch dashboard deletion step in teardown.py."""

import os
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

ENV = {
    "AWS_REGION": "us-east-1",
    "AGENT_NAME": "test-agent",
    "MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0",
}


def _make_client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "DeleteDashboards")


class TestTeardownDashboard:

    def _run_main_with_mocks(self, cw_side_effect=None):
        """Run teardown.main() with all AWS clients mocked."""
        mock_cw = MagicMock()
        if cw_side_effect:
            mock_cw.delete_dashboards.side_effect = cw_side_effect

        mock_sts = MagicMock()
        mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}

        mock_agentcore = MagicMock()
        mock_agentcore.list_agent_runtimes.return_value = {"agentRuntimes": []}

        mock_iam = MagicMock()
        mock_s3 = MagicMock()

        def client_factory(service, **kwargs):
            return {
                "sts": mock_sts,
                "bedrock-agentcore-control": mock_agentcore,
                "iam": mock_iam,
                "s3": mock_s3,
                "cloudwatch": mock_cw,
            }[service]

        with (
            patch.dict(os.environ, ENV, clear=True),
            patch("deploy.teardown.boto3.client", side_effect=client_factory),
        ):
            from deploy import teardown

            teardown.main()

        return mock_cw

    def test_dashboard_deleted_successfully(self):
        mock_cw = self._run_main_with_mocks()
        mock_cw.delete_dashboards.assert_called_once()

    def test_dashboard_resource_not_found_continues(self, capsys):
        mock_cw = self._run_main_with_mocks(
            cw_side_effect=_make_client_error("ResourceNotFound")
        )
        captured = capsys.readouterr()
        assert "not found" in captured.out
        assert "⚠️" not in captured.out.split("Step 4")[1]

    def test_dashboard_other_client_error_prints_warning(self, capsys):
        mock_cw = self._run_main_with_mocks(
            cw_side_effect=_make_client_error("AccessDeniedException")
        )
        captured = capsys.readouterr()
        assert "⚠️" in captured.out
