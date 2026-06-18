"""Test suite for MCPConfigLoader class.

Comprehensive tests covering configuration loading, variable substitution,
environment file handling, caching, and error scenarios.
"""

import json
import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock, mock_open, patch

import pytest

from awa.core.utils.mcp_config_loader import MCPConfigLoader


class TestMCPConfigLoader:
    """Test suite for the MCPConfigLoader class."""

    def setup_method(self) -> None:
        """Set up test environment before each test method."""
        # Clear cache before each test to ensure isolation
        MCPConfigLoader.clear_cache()

    def teardown_method(self) -> None:
        """Clean up after each test method."""
        # Clear cache after each test
        MCPConfigLoader.clear_cache()

    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def sample_config(self) -> dict[str, Any]:
        """Return a sample MCP configuration for testing."""
        return {
            "inputs": {
                "api_key": {
                    "type": "password",
                    "id": "api_key",
                    "description": "API Key for service",
                },
                "model_name": {
                    "type": "text",
                    "id": "model_name",
                    "description": "Model to use",
                },
            },
            "servers": {
                "test_server": {
                    "type": "stdio",
                    "command": "python",
                    "args": ["-m", "test_module"],
                    "env": {
                        "API_KEY": "${input:api_key}",
                        "MODEL": "${input:model_name}",
                        "WORKSPACE": "${workspaceFolder}",
                        "HOME_DIR": "${env:HOME}",
                    },
                },
                "http_server": {
                    "type": "http",
                    "url": "https://api.example.com",
                    "headers": {
                        "Authorization": "Bearer ${input:api_key}",
                    },
                },
                "sse_server": {
                    "type": "sse",
                    "url": "https://stream.example.com/events",
                },
            },
        }

    @pytest.fixture
    def sample_inputs(self) -> dict[str, str]:
        """Return sample inputs for variable substitution."""
        return {
            "api_key": "test_api_key_123",
            "model_name": "gpt-4",
        }

    def test_load_mcp_config_from_multiple_locations(self, temp_dir: Path, sample_config: dict[str, Any]) -> None:
        """Test loading configuration from mcp.json (primary location)."""
        # Create config file with unique content
        config = sample_config.copy()
        # Add a unique server for identification
        config["servers"]["test_marker"] = {
            "type": "stdio",
            "command": "echo",
            "args": ["test"],
        }

        # Write mcp.json (primary location)
        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(config, f)

        # Load config should find mcp.json
        loaded_config = MCPConfigLoader.load_mcp_config(
            working_dir=temp_dir,
            inputs={"api_key": "test", "model_name": "test"},
        )

        assert loaded_config is not None
        # Check that config was loaded by looking for the unique marker server
        assert "test_marker" in loaded_config.servers
        assert len(loaded_config.servers) == 4  # 3 original + 1 marker

    def test_load_mcp_config_from_root_directory(self, temp_dir: Path, sample_config: dict[str, Any]) -> None:
        """Test loading configuration from mcp.json when .vscode/mcp.json doesn't exist."""
        # Create only root config file
        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(sample_config, f)

        config = MCPConfigLoader.load_mcp_config(
            working_dir=temp_dir,
            inputs={"api_key": "test", "model_name": "test"},
        )

        assert config is not None
        assert len(config.servers) == 3
        assert "test_server" in config.servers
        assert "http_server" in config.servers
        assert "sse_server" in config.servers

    def test_load_mcp_config_returns_none_when_no_config_found(self, temp_dir: Path) -> None:
        """Test that None is returned when no configuration file exists."""
        config = MCPConfigLoader.load_mcp_config(working_dir=temp_dir)
        assert config is None

    def test_load_mcp_config_uses_cwd_when_no_working_dir(self, sample_config: dict[str, Any]) -> None:
        """Test that current working directory is used when working_dir is None."""
        with (
            patch("pathlib.Path.cwd") as mock_cwd,
            patch("pathlib.Path.exists") as mock_exists,
            patch("pathlib.Path.open", mock_open(read_data=json.dumps(sample_config))),
            patch("pathlib.Path.stat") as mock_stat,
        ):
            mock_cwd.return_value = Path("/fake/cwd")
            mock_exists.return_value = True
            mock_stat.return_value = Mock(st_mtime=1234567890)

            config = MCPConfigLoader.load_mcp_config(
                inputs={"api_key": "test", "model_name": "test"},
            )

            assert config is not None
            mock_cwd.assert_called_once()

    def test_variable_substitution_input_variables(
        self,
        temp_dir: Path,
        sample_config: dict[str, Any],
        sample_inputs: dict[str, str],
    ) -> None:
        """Test ${input:id} variable substitution."""
        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(sample_config, f)

        with patch.dict(os.environ, {"HOME": "/home/user"}):
            config = MCPConfigLoader.load_mcp_config(
                working_dir=temp_dir,
                inputs=sample_inputs,
            )

        assert config is not None
        test_server = config.servers["test_server"]

        # Check input variable substitution
        assert test_server.env["API_KEY"] == "test_api_key_123"
        assert test_server.env["MODEL"] == "gpt-4"

        # Check HTTP server header substitution
        http_server = config.servers["http_server"]
        assert http_server.headers["Authorization"] == "Bearer test_api_key_123"

    def test_variable_substitution_workspace_folder(
        self,
        temp_dir: Path,
        sample_config: dict[str, Any],
        sample_inputs: dict[str, str],
    ) -> None:
        """Test ${workspaceFolder} variable substitution."""
        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(sample_config, f)

        with patch.dict(os.environ, {"HOME": "/home/user"}):
            config = MCPConfigLoader.load_mcp_config(
                working_dir=temp_dir,
                inputs=sample_inputs,
            )

        assert config is not None
        test_server = config.servers["test_server"]
        assert test_server.env["WORKSPACE"] == str(temp_dir)

    def test_variable_substitution_environment_variables(
        self,
        temp_dir: Path,
        sample_config: dict[str, Any],
        sample_inputs: dict[str, str],
    ) -> None:
        """Test ${env:VAR_NAME} variable substitution."""
        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(sample_config, f)

        with patch.dict(os.environ, {"HOME": "/home/user"}):
            config = MCPConfigLoader.load_mcp_config(
                working_dir=temp_dir,
                inputs=sample_inputs,
            )

        assert config is not None
        test_server = config.servers["test_server"]
        assert test_server.env["HOME_DIR"] == "/home/user"

    def test_variable_substitution_missing_input_raises_error(
        self,
        temp_dir: Path,
        sample_config: dict[str, Any],
    ) -> None:
        """Test that missing input variables raise ValueError."""
        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(sample_config, f)

        with pytest.raises(ValueError, match=r"Missing input value for '.*api_key.*'"):
            MCPConfigLoader.load_mcp_config(
                working_dir=temp_dir,
                inputs={"model_name": "gpt-4"},  # Missing api_key
            )

    def test_variable_substitution_missing_env_var_raises_error(
        self,
        temp_dir: Path,
        sample_config: dict[str, Any],
        sample_inputs: dict[str, str],
    ) -> None:
        """Test that missing environment variables raise ValueError."""
        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(sample_config, f)

        # Ensure HOME is not set
        with (
            patch.dict(os.environ, {}, clear=True),
            pytest.raises(ValueError, match="Environment variable 'HOME' not found"),
        ):
            MCPConfigLoader.load_mcp_config(
                working_dir=temp_dir,
                inputs=sample_inputs,
            )

    def test_variable_substitution_unsupported_variable_raises_error(
        self,
        temp_dir: Path,
        sample_inputs: dict[str, str],
    ) -> None:
        """Test that unsupported variable types raise ValueError."""
        config_with_bad_var = {
            "servers": {
                "test_server": {
                    "type": "stdio",
                    "command": "${unsupported:variable}",
                    "args": [],
                },
            },
        }

        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(config_with_bad_var, f)

        with pytest.raises(ValueError, match="Unsupported variable type"):
            MCPConfigLoader.load_mcp_config(
                working_dir=temp_dir,
                inputs=sample_inputs,
            )

    def test_environment_file_loading_absolute_path(
        self,
        temp_dir: Path,
        sample_inputs: dict[str, str],
    ) -> None:
        """Test loading environment file with absolute path."""
        # Create environment file
        env_file = temp_dir / "test.env"
        env_content = """
# Test environment file
API_KEY=from_env_file
DATABASE_URL=postgresql://localhost/test
DEBUG=true
QUOTED_VAR="quoted value"
SINGLE_QUOTED='single quoted'
"""
        env_file.write_text(env_content.strip())

        config = {
            "servers": {
                "test_server": {
                    "type": "stdio",
                    "command": "python",
                    "args": ["-m", "test"],
                    "envFile": str(env_file),
                    "env": {
                        "OVERRIDE_VAR": "override_value",
                    },
                },
            },
        }

        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(config, f)

        loaded_config = MCPConfigLoader.load_mcp_config(
            working_dir=temp_dir,
            inputs=sample_inputs,
        )

        assert loaded_config is not None
        server = loaded_config.servers["test_server"]

        # Check that env file variables are loaded
        assert server.env["API_KEY"] == "from_env_file"
        assert server.env["DATABASE_URL"] == "postgresql://localhost/test"
        assert server.env["DEBUG"] == "true"
        assert server.env["QUOTED_VAR"] == "quoted value"
        assert server.env["SINGLE_QUOTED"] == "single quoted"

        # Check that existing env variables take precedence
        assert server.env["OVERRIDE_VAR"] == "override_value"

    def test_environment_file_loading_relative_path(
        self,
        temp_dir: Path,
        sample_inputs: dict[str, str],
    ) -> None:
        """Test loading environment file with relative path."""
        # Create environment file
        env_file = temp_dir / "config" / "test.env"
        env_file.parent.mkdir(parents=True)
        env_file.write_text("RELATIVE_VAR=relative_value")

        config = {
            "servers": {
                "test_server": {
                    "type": "stdio",
                    "command": "python",
                    "args": ["-m", "test"],
                    "envFile": "config/test.env",  # Relative path
                },
            },
        }

        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(config, f)

        loaded_config = MCPConfigLoader.load_mcp_config(
            working_dir=temp_dir,
            inputs=sample_inputs,
        )

        assert loaded_config is not None
        server = loaded_config.servers["test_server"]
        assert server.env["RELATIVE_VAR"] == "relative_value"

    def test_environment_file_not_found_raises_error(
        self,
        temp_dir: Path,
        sample_inputs: dict[str, str],
    ) -> None:
        """Test that missing environment file raises FileNotFoundError."""
        config = {
            "servers": {
                "test_server": {
                    "type": "stdio",
                    "command": "python",
                    "args": ["-m", "test"],
                    "envFile": "nonexistent.env",
                },
            },
        }

        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(config, f)

        with pytest.raises(FileNotFoundError, match="Environment file not found"):
            MCPConfigLoader.load_mcp_config(
                working_dir=temp_dir,
                inputs=sample_inputs,
            )

    def test_environment_file_invalid_format_raises_error(
        self,
        temp_dir: Path,
        sample_inputs: dict[str, str],
    ) -> None:
        """Test that malformed environment file raises ValueError."""
        # Create malformed environment file
        env_file = temp_dir / "bad.env"
        env_file.write_text("INVALID_LINE_WITHOUT_EQUALS")

        config = {
            "servers": {
                "test_server": {
                    "type": "stdio",
                    "command": "python",
                    "args": ["-m", "test"],
                    "envFile": str(env_file),
                },
            },
        }

        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(config, f)

        with pytest.raises(ValueError, match="Invalid format on line"):
            MCPConfigLoader.load_mcp_config(
                working_dir=temp_dir,
                inputs=sample_inputs,
            )

    def test_server_config_validation_stdio(self, temp_dir: Path) -> None:
        """Test server configuration validation for stdio transport."""
        # Valid stdio configuration
        valid_config = {
            "servers": {
                "stdio_server": {
                    "type": "stdio",
                    "command": "python",
                    "args": ["-m", "test"],
                },
            },
        }

        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(valid_config, f)

        # Clear cache to ensure we load from temp_dir, not from any cached or parent directory configs
        MCPConfigLoader.clear_cache()
        config = MCPConfigLoader.load_mcp_config(working_dir=temp_dir)
        assert config is not None

        # Invalid stdio configuration (missing command)
        invalid_config = {
            "servers": {
                "stdio_server": {
                    "type": "stdio",
                    "args": ["-m", "test"],
                },
            },
        }

        with (temp_dir / "mcp_invalid.json").open("w") as f:
            json.dump(invalid_config, f)

        # Remove the valid config to test the invalid one
        (temp_dir / "mcp.json").unlink()
        (temp_dir / "mcp_invalid.json").rename(temp_dir / "mcp.json")

        # Clear cache again to ensure we load the new invalid config
        MCPConfigLoader.clear_cache()
        with pytest.raises(ValueError, match="stdio transport requires a command"):
            MCPConfigLoader.load_mcp_config(working_dir=temp_dir)

    def test_server_config_validation_http(self, temp_dir: Path) -> None:
        """Test server configuration validation for HTTP transport."""
        # Valid HTTP configuration
        valid_config = {
            "servers": {
                "http_server": {
                    "type": "http",
                    "url": "https://api.example.com",
                },
            },
        }

        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(valid_config, f)

        # Clear cache to ensure we load from temp_dir, not from any cached or parent directory configs
        MCPConfigLoader.clear_cache()
        config = MCPConfigLoader.load_mcp_config(working_dir=temp_dir)
        assert config is not None

        # Invalid HTTP configuration (missing URL)
        invalid_config = {
            "servers": {
                "http_server": {
                    "type": "http",
                    "headers": {"Authorization": "Bearer token"},
                },
            },
        }

        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(invalid_config, f)

        # Clear cache again to ensure we load the new invalid config
        MCPConfigLoader.clear_cache()
        with pytest.raises(ValueError, match="http transport requires a url"):
            MCPConfigLoader.load_mcp_config(working_dir=temp_dir)

    def test_server_config_validation_sse(self, temp_dir: Path) -> None:
        """Test server configuration validation for SSE transport."""
        # Valid SSE configuration
        valid_config = {
            "servers": {
                "sse_server": {
                    "type": "sse",
                    "url": "https://stream.example.com/events",
                },
            },
        }

        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(valid_config, f)

        # Clear cache to ensure we load from temp_dir, not from any cached or parent directory configs
        MCPConfigLoader.clear_cache()
        config = MCPConfigLoader.load_mcp_config(working_dir=temp_dir)
        assert config is not None

        # Invalid SSE configuration (missing URL)
        invalid_config = {
            "servers": {
                "sse_server": {
                    "type": "sse",
                },
            },
        }

        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(invalid_config, f)

        # Clear cache again to ensure we load the new invalid config
        MCPConfigLoader.clear_cache()
        with pytest.raises(ValueError, match="sse transport requires a url"):
            MCPConfigLoader.load_mcp_config(working_dir=temp_dir)

    def test_server_config_validation_unsupported_transport(self, temp_dir: Path) -> None:
        """Test server configuration validation for unsupported transport types."""
        invalid_config = {
            "servers": {
                "invalid_server": {
                    "type": "websocket",  # Unsupported transport
                    "url": "ws://example.com",
                },
            },
        }

        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(invalid_config, f)

        # Clear cache to ensure we load from temp_dir, not from any cached or parent directory configs
        MCPConfigLoader.clear_cache()
        # Pydantic will raise a validation error for invalid literal values
        with pytest.raises(ValueError):
            MCPConfigLoader.load_mcp_config(working_dir=temp_dir)

    def test_caching_functionality(
        self,
        temp_dir: Path,
        sample_config: dict[str, Any],
        sample_inputs: dict[str, str],
    ) -> None:
        """Test that configuration caching works correctly."""
        config_file = temp_dir / "mcp.json"

        with config_file.open("w") as f:
            json.dump(sample_config, f)

        # Load config first time
        config1 = MCPConfigLoader.load_mcp_config(
            working_dir=temp_dir,
            inputs=sample_inputs,
        )

        # Load config second time - should use cache
        with patch("pathlib.Path.open", mock_open()) as mock_file:
            config2 = MCPConfigLoader.load_mcp_config(
                working_dir=temp_dir,
                inputs=sample_inputs,
            )

            # File should not be opened because cache is used
            mock_file.assert_not_called()

        # Configs should be the same object from cache
        assert config1 is config2

    def test_cache_invalidation_on_file_modification(
        self,
        temp_dir: Path,
        sample_config: dict[str, Any],
        sample_inputs: dict[str, str],
    ) -> None:
        """Test that cache is invalidated when file is modified."""
        config_file = temp_dir / "mcp.json"

        with config_file.open("w") as f:
            json.dump(sample_config, f)

        # Load config first time
        config1 = MCPConfigLoader.load_mcp_config(
            working_dir=temp_dir,
            inputs=sample_inputs,
        )

        # Simulate file modification by mocking different mtime
        with patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value = Mock(st_mtime=9999999999)  # Different mtime

            # This should reload from file, not cache
            with patch("pathlib.Path.open", mock_open(read_data=json.dumps(sample_config))):
                config2 = MCPConfigLoader.load_mcp_config(
                    working_dir=temp_dir,
                    inputs=sample_inputs,
                )

        # Should be different objects due to cache invalidation
        assert config1 is not config2

    def test_clear_cache(self, temp_dir: Path, sample_config: dict[str, Any], sample_inputs: dict[str, str]) -> None:
        """Test cache clearing functionality."""
        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(sample_config, f)

        # Load config to populate cache
        MCPConfigLoader.load_mcp_config(
            working_dir=temp_dir,
            inputs=sample_inputs,
        )

        # Verify cache has entries
        assert len(MCPConfigLoader._config_cache) > 0
        assert len(MCPConfigLoader._config_hash_cache) > 0

        # Clear cache
        MCPConfigLoader.clear_cache()

        # Verify cache is empty
        assert len(MCPConfigLoader._config_cache) == 0
        assert len(MCPConfigLoader._config_hash_cache) == 0

    def test_invalid_json_raises_error(self, temp_dir: Path) -> None:
        """Test that invalid JSON raises ValueError."""
        config_file = temp_dir / "mcp.json"
        config_file.write_text("{ invalid json }")

        # Clear cache to ensure we load from temp_dir, not from any cached or parent directory configs
        MCPConfigLoader.clear_cache()
        with pytest.raises(ValueError, match="Invalid JSON"):
            MCPConfigLoader.load_mcp_config(working_dir=temp_dir)

    def test_invalid_config_structure_raises_error(self, temp_dir: Path) -> None:
        """Test that invalid configuration structure raises an error."""
        invalid_config = {
            "servers": "not_a_dict",  # Should be a dict
        }

        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(invalid_config, f)

        # Clear cache to ensure we load from temp_dir, not from any cached or parent directory configs
        MCPConfigLoader.clear_cache()
        # The error can happen either during processing or validation
        with pytest.raises((ValueError, TypeError, AttributeError)):
            MCPConfigLoader.load_mcp_config(working_dir=temp_dir)

    def test_nested_variable_substitution(self, temp_dir: Path, sample_inputs: dict[str, str]) -> None:
        """Test variable substitution in nested structures."""
        config = {
            "servers": {
                "nested_server": {
                    "type": "stdio",
                    "command": "${env:PYTHON_PATH}",
                    "args": ["--api-key", "${input:api_key}", "--model", "${input:model_name}"],
                    "env": {
                        "NESTED_VAR": "${workspaceFolder}/data",
                    },
                },
            },
        }

        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(config, f)

        with patch.dict(os.environ, {"PYTHON_PATH": "/usr/bin/python3"}):
            loaded_config = MCPConfigLoader.load_mcp_config(
                working_dir=temp_dir,
                inputs=sample_inputs,
            )

        assert loaded_config is not None
        server = loaded_config.servers["nested_server"]

        assert server.command == "/usr/bin/python3"
        assert server.args == ["--api-key", "test_api_key_123", "--model", "gpt-4"]
        assert server.env["NESTED_VAR"] == f"{temp_dir}/data"

    def test_environment_file_with_comments_and_empty_lines(
        self,
        temp_dir: Path,
        sample_inputs: dict[str, str],
    ) -> None:
        """Test environment file parsing handles comments and empty lines correctly."""
        env_file = temp_dir / "test.env"
        env_content = """
# This is a comment
API_KEY=test_key

# Another comment
DATABASE_URL=postgresql://localhost/db

# Empty line above and below

DEBUG=true
"""
        env_file.write_text(env_content)

        config = {
            "servers": {
                "test_server": {
                    "type": "stdio",
                    "command": "python",
                    "args": ["-m", "test"],
                    "envFile": str(env_file),
                },
            },
        }

        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(config, f)

        loaded_config = MCPConfigLoader.load_mcp_config(
            working_dir=temp_dir,
            inputs=sample_inputs,
        )

        assert loaded_config is not None
        server = loaded_config.servers["test_server"]

        assert server.env["API_KEY"] == "test_key"
        assert server.env["DATABASE_URL"] == "postgresql://localhost/db"
        assert server.env["DEBUG"] == "true"
        assert len(server.env) == 3  # Only actual variables, no comments

    def test_hash_string_method(self) -> None:
        """Test the internal hash string method."""
        test_string = "test_string"
        hash_result = MCPConfigLoader._hash_string(test_string)

        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA-256 produces 64-character hex string

        # Same input should produce same hash
        assert MCPConfigLoader._hash_string(test_string) == hash_result

        # Different input should produce different hash
        assert MCPConfigLoader._hash_string("different_string") != hash_result

    def test_empty_servers_config(self, temp_dir: Path) -> None:
        """Test handling of configuration with empty servers dictionary."""
        config = {"servers": {}}

        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(config, f)

        loaded_config = MCPConfigLoader.load_mcp_config(working_dir=temp_dir)

        assert loaded_config is not None
        assert loaded_config.servers == {}

    def test_inputs_are_optional(self, temp_dir: Path) -> None:
        """Test that inputs section is optional in configuration."""
        config = {
            "servers": {
                "simple_server": {
                    "type": "stdio",
                    "command": "python",
                    "args": ["-m", "simple"],
                },
            },
        }

        with (temp_dir / "mcp.json").open("w") as f:
            json.dump(config, f)

        loaded_config = MCPConfigLoader.load_mcp_config(working_dir=temp_dir)

        assert loaded_config is not None
        assert loaded_config.inputs is None
        assert len(loaded_config.servers) == 1
