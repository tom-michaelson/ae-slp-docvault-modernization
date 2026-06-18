import runpy
from unittest.mock import MagicMock, patch


class TestMain:
    """Test cases for __main__ script."""

    @patch("awa.core.api.api.start_api_server")
    def test_main_calls_start_api_server(self, mock_start_api_server: MagicMock) -> None:
        """Test that running __main__ calls start_api_server."""
        runpy.run_module("awa.core.api.__main__", run_name="__main__")
        mock_start_api_server.assert_called_once()
