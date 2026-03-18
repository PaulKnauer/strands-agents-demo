"""Root conftest — stubs out cloud SDKs that cannot be imported in unit/integration tests."""

import sys
from unittest.mock import MagicMock

# bedrock_agentcore is only pre-installed in the AgentCore cloud runtime, not locally.
# Stub it before any test file imports deploy.app so the import chain doesn't fail.
# Use an identity function for .entrypoint so @app.entrypoint preserves the real function.
_mock_app = MagicMock()
_mock_app.entrypoint = lambda fn: fn   # identity: decorated function survives unchanged
_mock_app.run = MagicMock()            # no-op: prevents HTTP server from starting on import

_mock_agentcore = MagicMock()
_mock_agentcore.BedrockAgentCoreApp.return_value = _mock_app

sys.modules.setdefault("bedrock_agentcore", _mock_agentcore)
