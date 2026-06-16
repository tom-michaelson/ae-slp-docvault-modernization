from unittest.mock import MagicMock, call, patch

import pytest

from awa.core.cli.options import handle_options


@pytest.mark.asyncio
@patch("awa.core.cli.options.EnvConfig.update_env_config")
@patch("awa.core.cli.options.ConfigLoader.load_config")
@patch("awa.core.cli.options.Path")
async def test_handle_options_overrides_paths(
    mock_path: MagicMock,
    mock_config_loader: MagicMock,
    mock_env_loader: MagicMock,
) -> None:
    # Arrange
    mock_env = ".test_env"
    mock_config = "test_config.yaml"
    file_exists = True
    mock_path.file_exists.return_value(file_exists)

    # Act
    handle_options(mock_env, mock_config)

    # Assert
    assert mock_config_loader.call_args == call(mock_config)
    assert mock_env_loader.call_args == call(mock_env)


@pytest.mark.asyncio
@patch("awa.core.cli.options.EnvConfig.update_env_config")
@patch("awa.core.cli.options.ConfigLoader.load_config")
@patch("awa.core.cli.options.Path")
async def test_handle_missing_options_does_not_override(
    mock_path: MagicMock,
    mock_config_loader: MagicMock,
    mock_env_loader: MagicMock,
) -> None:
    # Arrange
    file_exists = True
    mock_path.file_exists.return_value(file_exists)

    # Act
    handle_options(None, None)

    # Assert
    assert mock_config_loader.call_args is None
    assert mock_env_loader.call_args is None
