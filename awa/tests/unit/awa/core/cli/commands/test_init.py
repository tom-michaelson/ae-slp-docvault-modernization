"""Unit tests for the init CLI command."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from typer.testing import CliRunner

from awa.core.cli.commands.init import (
    LLMProviderSetup,
    _init,
    app,
    create_global_config_files,
    validate_configuration_requirements,
)
from awa.core.models.config.llm_providers_config import LlmProviderEnum


class TestInitCommand:
    """Test cases for init CLI command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_init_command_help(self) -> None:
        """Test init command help."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Initialize AWA global configuration" in result.stdout

    @patch("awa.core.cli.commands.init.asyncio.run")
    @patch("awa.core.cli.commands.init.init_logging")
    def test_init_command_invocation(self, mock_init_logging: MagicMock, mock_asyncio_run: MagicMock) -> None:
        """Test init command invocation."""
        mock_init_logging.return_value = None

        def close_coroutine(coro: object) -> None:
            coro.close()

        mock_asyncio_run.side_effect = close_coroutine

        result = self.runner.invoke(app, [])
        assert result.exit_code == 0

        mock_init_logging.assert_called_once()
        mock_asyncio_run.assert_called_once()

    @patch("awa.core.cli.commands.init.asyncio.run")
    @patch("awa.core.cli.commands.init.init_logging")
    def test_init_command_with_force_flag(self, mock_init_logging: MagicMock, mock_asyncio_run: MagicMock) -> None:
        """Test init command with force flag."""
        mock_init_logging.return_value = None

        def close_coroutine(coro: object) -> None:
            coro.close()

        mock_asyncio_run.side_effect = close_coroutine

        result = self.runner.invoke(app, ["--force"])
        assert result.exit_code == 0

        mock_init_logging.assert_called_once()
        mock_asyncio_run.assert_called_once()


class TestLLMProviderSetup:
    """Test cases for LLMProviderSetup class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.setup = LLMProviderSetup()

    def test_get_provider_requirements_openai(self) -> None:
        """Test getting OpenAI provider requirements."""
        requirements = self.setup.get_provider_requirements(LlmProviderEnum.OPEN_AI)

        assert requirements["env_vars"] == ["OPENAI_API_KEY"]
        assert requirements["config_class"] is None
        assert "OPENAI_API_KEY" in requirements["prompts"]

    def test_get_provider_requirements_azure_openai(self) -> None:
        """Test getting Azure OpenAI provider requirements."""
        requirements = self.setup.get_provider_requirements(LlmProviderEnum.AZURE_OPEN_AI)

        assert "AZURE_OPENAI_API_KEY" in requirements["env_vars"]
        assert requirements["config_class"] is not None
        assert "resource_name" in requirements["prompts"]
        assert "api_version" in requirements["defaults"]

    def test_get_provider_requirements_aws_bedrock(self) -> None:
        """Test getting AWS Bedrock provider requirements."""
        requirements = self.setup.get_provider_requirements(LlmProviderEnum.AWS_BEDROCK)

        assert "AWS_REGION" in requirements["env_vars"]
        assert "AWS_PROFILE" in requirements["env_vars"]
        assert "AWS_REGION" in requirements["defaults"]

    def test_get_provider_requirements_lite_llm(self) -> None:
        """Test getting LiteLLM provider requirements."""
        requirements = self.setup.get_provider_requirements(LlmProviderEnum.LITE_LLM)

        assert "LITE_LLM_API_KEY" in requirements["env_vars"]
        assert requirements["config_class"] is not None
        assert "base_url" in requirements["prompts"]

    def test_get_provider_requirements_github_copilot(self) -> None:
        """Test getting GitHub Copilot provider requirements."""
        requirements = self.setup.get_provider_requirements(LlmProviderEnum.GITHUB_COPILOT)

        assert "GITHUB_COPILOT_API_KEY" in requirements["env_vars"]
        assert requirements["config_class"] is not None
        assert "base_url" in requirements["defaults"]

    def test_create_provider_config_openai(self) -> None:
        """Test creating OpenAI provider config."""
        user_inputs = {"OPENAI_API_KEY": "test-key"}
        config = self.setup.create_provider_config(LlmProviderEnum.OPEN_AI, user_inputs)

        assert config == {}  # OpenAI doesn't need additional config

    def test_create_provider_config_azure_openai(self) -> None:
        """Test creating Azure OpenAI provider config."""
        user_inputs = {
            "AZURE_OPENAI_API_KEY": "test-key",
            "resource_name": "test-resource",
            "api_version": "2024-10-21",
        }
        config = self.setup.create_provider_config(LlmProviderEnum.AZURE_OPEN_AI, user_inputs)

        assert "azure_openai" in config
        assert config["azure_openai"]["resource_name"] == "test-resource"
        assert config["azure_openai"]["api_version"] == "2024-10-21"

    def test_create_provider_config_lite_llm(self) -> None:
        """Test creating LiteLLM provider config."""
        user_inputs = {
            "LITE_LLM_API_KEY": "test-key",
            "base_url": "https://api.litellm.com",
        }
        config = self.setup.create_provider_config(LlmProviderEnum.LITE_LLM, user_inputs)

        assert "lite_llm" in config
        assert config["lite_llm"]["base_url"] == "https://api.litellm.com"

    def test_create_provider_config_github_copilot(self) -> None:
        """Test creating GitHub Copilot provider config."""
        user_inputs = {
            "GITHUB_COPILOT_API_KEY": "test-key",
            "base_url": "https://api.githubcopilot.com",
        }
        config = self.setup.create_provider_config(LlmProviderEnum.GITHUB_COPILOT, user_inputs)

        assert "github_copilot" in config
        assert config["github_copilot"]["base_url"] == "https://api.githubcopilot.com"

    def test_create_env_vars(self) -> None:
        """Test creating environment variables."""
        user_inputs = {
            "OPENAI_API_KEY": "test-key",
            "extra_field": "extra_value",
        }
        env_vars = self.setup.create_env_vars(LlmProviderEnum.OPEN_AI, user_inputs)

        assert env_vars["OPENAI_API_KEY"] == "test-key"
        assert "extra_field" not in env_vars  # Should only include defined env vars


class TestConfigurationValidation:
    """Test cases for configuration validation."""

    @pytest.mark.asyncio
    async def test_validate_configuration_requirements_missing_files(self) -> None:
        """Test validation when config files don't exist."""
        with patch("awa.core.cli.commands.init.ConfigPaths") as mock_config_paths:
            mock_paths = MagicMock()
            mock_paths.get_global_config_dir.return_value = Path("/nonexistent")
            mock_config_paths.return_value = mock_paths

            result = await validate_configuration_requirements()
            assert result is False

    @pytest.mark.asyncio
    async def test_validate_configuration_requirements_invalid_config(self) -> None:
        """Test validation with invalid config content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            config_file = config_dir / "config.yaml"
            env_file = config_dir / ".env"

            # Create files with invalid content
            config_file.write_text("invalid: yaml: content:")
            env_file.write_text("TEST=value")

            with patch("awa.core.cli.commands.init.ConfigPaths") as mock_config_paths:
                mock_paths = MagicMock()
                mock_paths.get_global_config_dir.return_value = config_dir
                mock_config_paths.return_value = mock_paths

                result = await validate_configuration_requirements()
                assert result is False

    @pytest.mark.asyncio
    async def test_validate_configuration_requirements_valid_config(self) -> None:
        """Test validation with valid config content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            config_file = config_dir / "config.yaml"
            env_file = config_dir / ".env"

            # Create files with valid content
            config_data = {
                "llm": {
                    "default_model": "test-model",
                    "models": [{"name": "test-model", "provider": "OpenAI"}],
                },
            }

            with config_file.open("w") as f:
                yaml.safe_dump(config_data, f)
            env_file.write_text("OPENAI_API_KEY=test-key")

            with patch("awa.core.cli.commands.init.ConfigPaths") as mock_config_paths:
                mock_paths = MagicMock()
                mock_paths.get_global_config_dir.return_value = config_dir
                mock_config_paths.return_value = mock_paths

                result = await validate_configuration_requirements()
                assert result is True


class TestConfigFileCreation:
    """Test cases for config file creation."""

    @pytest.mark.asyncio
    async def test_create_global_config_files(self) -> None:
        """Test creating global config files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            with patch("awa.core.cli.commands.init.ConfigPaths") as mock_config_paths:
                mock_paths = MagicMock()
                mock_paths.get_global_config_dir.return_value = config_dir
                mock_config_paths.return_value = mock_paths

                user_inputs = {
                    "OPENAI_API_KEY": "test-key",
                }

                await create_global_config_files(
                    LlmProviderEnum.OPEN_AI,
                    user_inputs,
                    "gpt-4",
                    "my-openai-model",
                )

                # Check that files were created
                config_file = config_dir / "config.yaml"
                env_file = config_dir / ".env"

                assert config_file.exists()
                assert env_file.exists()

                # Check config content
                with config_file.open() as f:
                    config_data = yaml.safe_load(f)

                assert config_data["llm"]["default_model"] == "my-openai-model"
                assert config_data["llm"]["models"][0]["name"] == "my-openai-model"
                assert config_data["llm"]["models"][0]["provider"] == "OpenAI"
                assert config_data["llm"]["models"][0]["model"] == "gpt-4"

                # Check env content
                env_content = env_file.read_text()
                assert "OPENAI_API_KEY=test-key" in env_content


class TestInitAsyncFunction:
    """Test cases for the async _init function."""

    @pytest.mark.asyncio
    async def test_init_with_existing_config_no_force(self) -> None:
        """Test _init with existing config and no force flag."""
        with patch("awa.core.cli.commands.init.validate_configuration_requirements") as mock_validate:
            mock_validate.return_value = True

            with patch("awa.core.cli.commands.init.logger") as mock_logger:
                await _init(force=False)

                mock_logger.info.assert_any_call("✅ Global configuration already exists and is valid")
                mock_logger.info.assert_any_call("Use 'awa init --force' to reconfigure")

    @pytest.mark.asyncio
    async def test_init_with_force_flag(self) -> None:
        """Test _init with force flag bypasses existing config check."""
        with (
            patch("awa.core.cli.commands.init.validate_configuration_requirements") as mock_validate,
            patch("awa.core.cli.commands.init.create_global_config_files") as mock_create,
            patch("awa.core.cli.commands.init.typer.prompt") as mock_prompt,
        ):
            # Mock user inputs
            mock_prompt.side_effect = [
                1,  # Provider selection (OpenAI)
                "test-key",  # API key
                "gpt-4",  # Model name
                "my-model",  # Model alias
                8001,  # API port
                8000,  # UI port
                8002,  # Temporal UI port
            ]

            mock_create.return_value = None

            await _init(force=True)

            # Validate that config creation was called
            mock_create.assert_called_once()

            # Validate that the existing config check was skipped
            mock_validate.assert_not_called()
