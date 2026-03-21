import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from deploy.create_dashboard import _build_dashboard_body, main, NIST_RMF_DASHBOARD_NAME

ENV = {"AWS_REGION": "us-east-1", "AGENT_NAME": "test-agent"}


class TestCreateDashboard:

    def test_put_dashboard_called_once(self):
        with (
            patch.dict(os.environ, {**ENV}, clear=True),
            patch("deploy.create_dashboard.boto3.client") as mock_boto3,
        ):
            mock_cw = MagicMock()
            mock_boto3.return_value = mock_cw
            main()
            mock_cw.put_dashboard.assert_called_once()
            call_kwargs = mock_cw.put_dashboard.call_args.kwargs
            assert call_kwargs["DashboardName"] == NIST_RMF_DASHBOARD_NAME

    def test_dashboard_body_contains_log_widget(self):
        body = json.loads(_build_dashboard_body("us-east-1", None, "/aws/logs/test"))
        log_widgets = [w for w in body["widgets"] if w["type"] == "log"]
        assert len(log_widgets) == 1
        assert "tool_call_start" in log_widgets[0]["properties"]["query"]

    def test_guardrail_widget_included_when_guardrail_id_set(self):
        body = json.loads(
            _build_dashboard_body("us-east-1", "abc-123", "/aws/logs/test")
        )
        metric_widgets = [w for w in body["widgets"] if w["type"] == "metric"]
        assert len(metric_widgets) == 1
        widget_str = str(metric_widgets[0])
        assert "AWS/Bedrock/Guardrails" in widget_str
        assert "Invocations" in widget_str
        assert "InvocationsIntervened" in widget_str
        assert "GuardrailArn" in widget_str

    def test_guardrail_widget_omitted_when_guardrail_id_absent(self):
        body = json.loads(_build_dashboard_body("us-east-1", None, "/aws/logs/test"))
        metric_widgets = [w for w in body["widgets"] if w["type"] == "metric"]
        assert len(metric_widgets) == 0

    def test_missing_aws_region_exits_1(self):
        with (
            patch.dict(os.environ, {"AGENT_NAME": "test"}, clear=True),
            patch("deploy.create_dashboard.boto3.client"),
            pytest.raises(SystemExit) as exc,
        ):
            main()
        assert exc.value.code == 1
