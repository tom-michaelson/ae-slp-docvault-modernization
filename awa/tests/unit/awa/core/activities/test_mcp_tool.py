import subprocess
from unittest.mock import AsyncMock, patch

import pytest
from temporalio.testing import ActivityEnvironment

from awa.core.activities.mcp_tool import _diagnose_mcp_server_startup, invoke_mcp_tool


class TestInvokeMCPTool:
    @pytest.mark.asyncio
    async def test_invoke_mcp_tool_http_server(self, activity_env: ActivityEnvironment) -> None:
        # Arrange
        tool_name = "add"
        parameters = {"a": 5, "b": 3}
        mcp_config = {
            "mcpServers": {
                "calculator": {
                    "url": "http://127.0.0.1:9000/mcp",
                    "transport": "streamable-http",
                },
            },
        }
        expected_result = 8

        mock_client = AsyncMock()
        mock_client.call_tool.return_value = expected_result

        with patch("awa.core.activities.mcp_tool.Client", return_value=mock_client):
            # Act
            result = await activity_env.run(
                invoke_mcp_tool,
                mcp_config=mcp_config,
                tool_name=tool_name,
                parameters=parameters,
            )

            # Assert
            assert result == expected_result
            mock_client.__aenter__.assert_called_once()
            mock_client.__aexit__.assert_called_once()
            mock_client.call_tool.assert_called_once_with(tool_name, parameters)

    @pytest.mark.asyncio
    async def test_invoke_mcp_tool_local_server(self, activity_env: ActivityEnvironment) -> None:
        # Arrange
        tool_name = "multiply"
        parameters = {"a": 4, "b": 6}
        mcp_config = {
            "mcpServers": {
                "calculator": {
                    "command": "python",
                    "args": ["/path/to/local/server.py"],
                    "transport": "stdio",
                },
            },
        }
        expected_result = 24

        mock_client = AsyncMock()
        mock_client.call_tool.return_value = expected_result

        with patch("awa.core.activities.mcp_tool.Client", return_value=mock_client):
            # Act
            result = await activity_env.run(
                invoke_mcp_tool,
                mcp_config=mcp_config,
                tool_name=tool_name,
                parameters=parameters,
            )

            # Assert
            assert result == expected_result
            mock_client.__aenter__.assert_called_once()
            mock_client.__aexit__.assert_called_once()
            mock_client.call_tool.assert_called_once_with(tool_name, parameters)

    @pytest.mark.asyncio
    async def test_invoke_mcp_tool_handles_client_exception(self, activity_env: ActivityEnvironment) -> None:
        # Arrange
        tool_name = "failing_tool"
        parameters = {"param": "value"}
        mcp_config = {
            "mcpServers": {
                "calculator": {
                    "url": "http://127.0.0.1:9000/mcp",
                    "transport": "streamable-http",
                },
            },
        }

        mock_client = AsyncMock()
        mock_client.call_tool.side_effect = Exception("MCP server error")

        with patch("awa.core.activities.mcp_tool.Client", return_value=mock_client):
            # Act
            result = await activity_env.run(
                invoke_mcp_tool,
                mcp_config=mcp_config,
                tool_name=tool_name,
                parameters=parameters,
            )

            # Assert - error is returned as dict instead of raised
            assert isinstance(result, dict)
            assert "error" in result
            assert "MCP server error" in result["error"]
            assert result["tool"] == tool_name
            assert result["parameters"] == parameters

            # Verify client context manager is called for each retry attempt (2 times)
            assert mock_client.__aenter__.call_count == 2
            assert mock_client.__aexit__.call_count == 2
            # Verify tool is called for each retry attempt (2 times)
            assert mock_client.call_tool.call_count == 2

    @pytest.mark.asyncio
    async def test_invoke_mcp_tool_string_url_config(self, activity_env: ActivityEnvironment) -> None:
        """Test invoke_mcp_tool with string URL configuration."""
        # Arrange
        tool_name = "test_tool"
        parameters = {"param": "value"}
        mcp_config = "http://127.0.0.1:9000/mcp"
        expected_result = "success"

        mock_client = AsyncMock()
        mock_client.call_tool.return_value = expected_result

        with (
            patch("awa.core.activities.mcp_tool.Client", return_value=mock_client),
            patch("awa.core.activities.mcp_tool.SSETransport") as mock_transport,
        ):
            # Act
            result = await activity_env.run(
                invoke_mcp_tool,
                mcp_config=mcp_config,
                tool_name=tool_name,
                parameters=parameters,
            )

            # Assert
            assert result == expected_result
            mock_transport.assert_called_once_with(url=mcp_config)
            mock_client.__aenter__.assert_called_once()
            mock_client.__aexit__.assert_called_once()
            mock_client.call_tool.assert_called_once_with(tool_name, parameters)


class TestDiagnoseMCPServerStartup:
    """Test cases for _diagnose_mcp_server_startup function."""

    @pytest.mark.asyncio
    async def test_diagnose_invalid_config_not_dict(self) -> None:
        """Test diagnostic function with invalid config (not a dict)."""
        # Act & Assert - Should return early without error
        result = await _diagnose_mcp_server_startup("not_a_dict")
        assert result is None

    @pytest.mark.asyncio
    async def test_diagnose_missing_mcp_servers(self) -> None:
        """Test diagnostic function with config missing mcpServers."""
        # Arrange
        config = {"someOtherKey": "value"}

        # Act & Assert - Should return early without error
        result = await _diagnose_mcp_server_startup(config)
        assert result is None

    @pytest.mark.asyncio
    async def test_diagnose_npx_server_found(self) -> None:
        """Test diagnostic function with npx command when npx is found."""
        # Arrange
        config = {
            "mcpServers": {
                "test_server": {
                    "command": "npx",
                    "args": ["some-package"],
                },
            },
        }

        with patch("awa.core.activities.mcp_tool.subprocess.run") as mock_run:
            # Mock successful npx check and package test
            mock_run.side_effect = [
                # First call: sys.executable with shutil.which (successful)
                subprocess.CompletedProcess(
                    args=[subprocess.sys.executable, "-c", "..."],
                    returncode=0,
                    stdout="/usr/local/bin/npx\n",
                ),
                # Second call: npx package test (successful)
                subprocess.CompletedProcess(
                    args=["/usr/local/bin/npx", "-y", "some-package", "--help"],
                    returncode=0,
                    stdout="help output",
                ),
            ]

            # Act & Assert - Should complete without error
            result = await _diagnose_mcp_server_startup(config)
            assert result is None

            # Verify both subprocess calls were made
            assert mock_run.call_count == 2

    @pytest.mark.asyncio
    async def test_diagnose_npx_server_not_found(self) -> None:
        """Test diagnostic function with npx command when npx is not found."""
        # Arrange
        config = {
            "mcpServers": {
                "test_server": {
                    "command": "npx",
                    "args": ["some-package"],
                },
            },
        }

        with patch("awa.core.activities.mcp_tool.subprocess.run") as mock_run:
            # Mock failed npx check (not found)
            mock_run.return_value = subprocess.CompletedProcess(
                args=[subprocess.sys.executable, "-c", "..."],
                returncode=0,
                stdout="",
            )

            # Act & Assert - Should return early and not test package
            result = await _diagnose_mcp_server_startup(config)
            assert result is None

            # Verify only the npx check was called (no package test)
            assert mock_run.call_count == 1

    @pytest.mark.asyncio
    async def test_diagnose_npx_server_os_error(self) -> None:
        """Test diagnostic function with npx command when subprocess throws exception."""
        # Arrange
        config = {
            "mcpServers": {
                "test_server": {
                    "command": "npx",
                    "args": ["some-package"],
                },
            },
        }

        with patch("awa.core.activities.mcp_tool.subprocess.run", side_effect=OSError("Test error")):
            # Act & Assert - Should handle exception and return early
            result = await _diagnose_mcp_server_startup(config)
            assert result is None

    @pytest.mark.asyncio
    async def test_diagnose_npx_package_test_failed(self) -> None:
        """Test diagnostic function when package test fails."""
        # Arrange
        config = {
            "mcpServers": {
                "test_server": {
                    "command": "npx",
                    "args": ["-y", "some-package"],
                },
            },
        }

        with patch("awa.core.activities.mcp_tool.subprocess.run") as mock_run:
            # Mock successful npx check but failed package test
            mock_run.side_effect = [
                # First call: sys.executable with shutil.which (successful)
                subprocess.CompletedProcess(
                    args=[subprocess.sys.executable, "-c", "..."],
                    returncode=0,
                    stdout="/usr/local/bin/npx\n",
                ),
                # Second call: npx package test (failed)
                subprocess.CompletedProcess(
                    args=["/usr/local/bin/npx", "-y", "some-package", "--help"],
                    returncode=1,
                    stderr="Package not found",
                ),
            ]

            # Act & Assert - Should complete despite package test failure
            result = await _diagnose_mcp_server_startup(config)
            assert result is None

            # Verify both subprocess calls were made
            assert mock_run.call_count == 2

    @pytest.mark.asyncio
    async def test_diagnose_npx_package_test_timeout(self) -> None:
        """Test diagnostic function when package test times out."""
        # Arrange
        config = {
            "mcpServers": {
                "test_server": {
                    "command": "npx",
                    "args": ["some-package"],
                },
            },
        }

        with patch("awa.core.activities.mcp_tool.subprocess.run") as mock_run:
            # Mock successful npx check but timeout on package test
            mock_run.side_effect = [
                # First call: sys.executable with shutil.which (successful)
                subprocess.CompletedProcess(
                    args=[subprocess.sys.executable, "-c", "..."],
                    returncode=0,
                    stdout="/usr/local/bin/npx\n",
                ),
                # Second call: npx package test (timeout)
                subprocess.TimeoutExpired(cmd=["/usr/local/bin/npx", "-y", "some-package", "--help"], timeout=30),
            ]

            # Act & Assert - Should handle timeout gracefully
            result = await _diagnose_mcp_server_startup(config)
            assert result is None

    @pytest.mark.asyncio
    async def test_diagnose_npx_with_env_variables(self) -> None:
        """Test diagnostic function with environment variables."""
        # Arrange
        config = {
            "mcpServers": {
                "test_server": {
                    "command": "npx",
                    "args": ["some-package"],
                    "env": {"NODE_ENV": "test", "DEBUG": "true"},
                },
            },
        }

        with patch("awa.core.activities.mcp_tool.subprocess.run") as mock_run:
            # Mock successful calls
            mock_run.side_effect = [
                # First call: sys.executable with shutil.which (successful)
                subprocess.CompletedProcess(
                    args=[subprocess.sys.executable, "-c", "..."],
                    returncode=0,
                    stdout="/usr/local/bin/npx\n",
                ),
                # Second call: npx package test (successful)
                subprocess.CompletedProcess(
                    args=["/usr/local/bin/npx", "-y", "some-package", "--help"],
                    returncode=0,
                    stdout="help output",
                ),
            ]

            # Act
            result = await _diagnose_mcp_server_startup(config)
            assert result is None

            # Verify environment variables were passed to second call
            second_call = mock_run.call_args_list[1]
            assert "env" in second_call.kwargs
            env = second_call.kwargs["env"]
            assert "NODE_ENV" in env
            assert env["NODE_ENV"] == "test"

    @pytest.mark.asyncio
    async def test_diagnose_non_npx_server(self) -> None:
        """Test diagnostic function with non-npx command."""
        # Arrange
        config = {
            "mcpServers": {
                "test_server": {
                    "command": "python",
                    "args": ["script.py"],
                },
            },
        }

        # Act & Assert - Should complete without error (no special handling for non-npx)
        result = await _diagnose_mcp_server_startup(config)
        assert result is None
