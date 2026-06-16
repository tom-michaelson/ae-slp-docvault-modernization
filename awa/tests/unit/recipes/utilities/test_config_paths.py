"""Unit tests for config_paths utilities."""

from pathlib import Path
from unittest.mock import patch

import pytest

from cookbook.recipes.utilities.config_paths import ConfigPaths


class TestConfigPaths:
    """Test suite for ConfigPaths utility class."""

    def test_get_global_config_dir_basic(self) -> None:
        """Test getting global config directory with default home."""
        with patch.object(Path, "home") as mock_home:
            mock_home.return_value = Path("/home/user")

            result = ConfigPaths.get_global_config_dir()

            assert isinstance(result, Path)
            assert result == Path("/home/user") / ".awa"
            mock_home.assert_called_once()

    def test_get_global_config_dir_different_home_paths(self) -> None:
        """Test global config directory with various home path scenarios."""
        test_cases = [
            ("/Users/john", "/Users/john/.awa"),
            ("/home/jane", "/home/jane/.awa"),
            ("C:/Users/Bob", "C:/Users/Bob/.awa"),  # Use forward slashes for cross-platform consistency
            ("/", "/.awa"),
        ]

        for home_path, expected_str in test_cases:
            with patch.object(Path, "home") as mock_home:
                mock_home.return_value = Path(home_path)

                result = ConfigPaths.get_global_config_dir()

                assert str(result) == expected_str
                assert isinstance(result, Path)
                mock_home.assert_called_once()

    def test_get_global_config_dir_path_properties(self) -> None:
        """Test that returned path has correct properties."""
        with patch.object(Path, "home") as mock_home:
            mock_home.return_value = Path("/home/testuser")

            result = ConfigPaths.get_global_config_dir()

            # Verify path construction
            assert result.name == ".awa"
            assert result.parent == Path("/home/testuser")
            assert str(result) == "/home/testuser/.awa"

    def test_get_config_file_paths_basic(self) -> None:
        """Test getting config file paths with mocked directories."""
        with patch.object(Path, "cwd") as mock_cwd, patch.object(Path, "home") as mock_home:
            mock_cwd.return_value = Path("/current/project")
            mock_home.return_value = Path("/home/user")

            result = ConfigPaths.get_config_file_paths()

            # Verify structure and types
            assert isinstance(result, dict)
            assert "env_files" in result
            assert "yaml_files" in result
            assert isinstance(result["env_files"], list)
            assert isinstance(result["yaml_files"], list)

            # Verify env files order (highest to lowest precedence)
            expected_env = [
                Path("/current/project/.env"),
                Path("/home/user/.awa/.env"),
            ]
            assert result["env_files"] == expected_env

            # Verify yaml files order (highest to lowest precedence)
            expected_yaml = [
                Path("/current/project/config.yaml"),
                Path("/home/user/.awa/config.yaml"),
            ]
            assert result["yaml_files"] == expected_yaml

            # Verify method calls (cwd called twice: once for env, once for yaml)
            assert mock_cwd.call_count == 2
            assert mock_home.call_count == 1

    def test_get_config_file_paths_different_directories(self) -> None:
        """Test config file paths with different current and home directories."""
        test_scenarios = [
            {
                "cwd": "/var/www/app",
                "home": "/home/deploy",
                "expected_env": [
                    "/var/www/app/.env",
                    "/home/deploy/.awa/.env",
                ],
                "expected_yaml": [
                    "/var/www/app/config.yaml",
                    "/home/deploy/.awa/config.yaml",
                ],
            },
            {
                "cwd": "C:/Projects/MyApp",  # Use forward slashes
                "home": "C:/Users/Developer",  # Use forward slashes
                "expected_env": [
                    "C:/Projects/MyApp/.env",
                    "C:/Users/Developer/.awa/.env",
                ],
                "expected_yaml": [
                    "C:/Projects/MyApp/config.yaml",
                    "C:/Users/Developer/.awa/config.yaml",
                ],
            },
            {
                "cwd": "/temp",  # Use /temp instead of /tmp to avoid security warning
                "home": "/root",
                "expected_env": [
                    "/temp/.env",
                    "/root/.awa/.env",
                ],
                "expected_yaml": [
                    "/temp/config.yaml",
                    "/root/.awa/config.yaml",
                ],
            },
        ]

        for scenario in test_scenarios:
            with patch.object(Path, "cwd") as mock_cwd, patch.object(Path, "home") as mock_home:
                mock_cwd.return_value = Path(scenario["cwd"])
                mock_home.return_value = Path(scenario["home"])

                result = ConfigPaths.get_config_file_paths()

                # Compare string representations for cross-platform consistency
                env_strs = [str(p) for p in result["env_files"]]
                yaml_strs = [str(p) for p in result["yaml_files"]]

                assert env_strs == scenario["expected_env"]
                assert yaml_strs == scenario["expected_yaml"]

    def test_get_config_file_paths_precedence_order(self) -> None:
        """Test that config file paths maintain correct precedence order."""
        with patch.object(Path, "cwd") as mock_cwd, patch.object(Path, "home") as mock_home:
            mock_cwd.return_value = Path("/project")
            mock_home.return_value = Path("/user")

            result = ConfigPaths.get_config_file_paths()

            # Current directory should come first (highest precedence)
            assert result["env_files"][0] == Path("/project/.env")
            assert result["yaml_files"][0] == Path("/project/config.yaml")

            # Global directory should come second (lower precedence)
            assert result["env_files"][1] == Path("/user/.awa/.env")
            assert result["yaml_files"][1] == Path("/user/.awa/config.yaml")

            # Verify exactly 2 paths for each type
            assert len(result["env_files"]) == 2
            assert len(result["yaml_files"]) == 2

    def test_get_config_file_paths_uses_global_config_dir_method(self) -> None:
        """Test that get_config_file_paths properly uses get_global_config_dir method."""
        with (
            patch.object(ConfigPaths, "get_global_config_dir") as mock_global_dir,
            patch.object(Path, "cwd") as mock_cwd,
        ):
            mock_global_dir.return_value = Path("/custom/awa/dir")
            mock_cwd.return_value = Path("/current")

            result = ConfigPaths.get_config_file_paths()

            # Verify the mocked global directory was used
            assert result["env_files"][1] == Path("/custom/awa/dir/.env")
            assert result["yaml_files"][1] == Path("/custom/awa/dir/config.yaml")

            # Verify the method was called
            mock_global_dir.assert_called_once()

    def test_get_global_state_file_basic(self) -> None:
        """Test getting global state file path."""
        with patch.object(Path, "home") as mock_home:
            mock_home.return_value = Path("/home/user")

            result = ConfigPaths.get_global_state_file()

            assert isinstance(result, Path)
            assert result == Path("/home/user/.awa/services.json")
            assert result.name == "services.json"
            assert result.parent.name == ".awa"

    def test_get_global_state_file_different_homes(self) -> None:
        """Test global state file with various home directories."""
        test_cases = [
            ("/Users/alice", "/Users/alice/.awa/services.json"),
            ("/home/bob", "/home/bob/.awa/services.json"),
            ("C:/Users/Charlie", "C:/Users/Charlie/.awa/services.json"),  # Use forward slashes
            ("/", "/.awa/services.json"),
        ]

        for home_path, expected_str in test_cases:
            with patch.object(Path, "home") as mock_home:
                mock_home.return_value = Path(home_path)

                result = ConfigPaths.get_global_state_file()

                assert str(result) == expected_str
                assert isinstance(result, Path)
                mock_home.assert_called_once()

    def test_get_global_state_file_uses_global_config_dir(self) -> None:
        """Test that get_global_state_file uses get_global_config_dir method."""
        with patch.object(ConfigPaths, "get_global_config_dir") as mock_global_dir:
            mock_global_dir.return_value = Path("/custom/config/path")

            result = ConfigPaths.get_global_state_file()

            assert result == Path("/custom/config/path/services.json")
            mock_global_dir.assert_called_once()

    def test_all_methods_return_path_objects(self) -> None:
        """Test that all methods return proper Path objects."""
        with patch.object(Path, "home") as mock_home, patch.object(Path, "cwd") as mock_cwd:
            mock_home.return_value = Path("/home/test")
            mock_cwd.return_value = Path("/current/test")

            # Test get_global_config_dir
            global_dir = ConfigPaths.get_global_config_dir()
            assert isinstance(global_dir, Path)

            # Test get_global_state_file
            state_file = ConfigPaths.get_global_state_file()
            assert isinstance(state_file, Path)

            # Test get_config_file_paths
            config_paths = ConfigPaths.get_config_file_paths()
            assert isinstance(config_paths, dict)

            for file_list in config_paths.values():
                assert isinstance(file_list, list)
                for path in file_list:
                    assert isinstance(path, Path)

    def test_path_construction_consistency(self) -> None:
        """Test that path construction is consistent across methods."""
        with patch.object(Path, "home") as mock_home, patch.object(Path, "cwd") as mock_cwd:
            mock_home.return_value = Path("/home/consistent")
            mock_cwd.return_value = Path("/current/consistent")

            # Get paths from different methods
            global_dir = ConfigPaths.get_global_config_dir()
            state_file = ConfigPaths.get_global_state_file()
            config_paths = ConfigPaths.get_config_file_paths()

            # Verify consistency in global directory usage
            assert state_file.parent == global_dir
            assert config_paths["env_files"][1].parent == global_dir
            assert config_paths["yaml_files"][1].parent == global_dir

            # Verify all global paths use same base directory
            global_env = config_paths["env_files"][1]
            global_yaml = config_paths["yaml_files"][1]

            assert global_env.parent == global_yaml.parent == state_file.parent

    def test_static_methods_no_instance_required(self) -> None:
        """Test that all methods are properly static and don't require instance."""
        # Should be able to call methods directly on class without instantiation
        with patch.object(Path, "home") as mock_home, patch.object(Path, "cwd") as mock_cwd:
            mock_home.return_value = Path("/test")
            mock_cwd.return_value = Path("/test")

            # These should work without creating an instance
            result1 = ConfigPaths.get_global_config_dir()
            result2 = ConfigPaths.get_global_state_file()
            result3 = ConfigPaths.get_config_file_paths()

            assert isinstance(result1, Path)
            assert isinstance(result2, Path)
            assert isinstance(result3, dict)

    def test_path_immutability_and_safety(self) -> None:
        """Test that returned paths are safe and don't affect internal state."""
        with patch.object(Path, "home") as mock_home, patch.object(Path, "cwd") as mock_cwd:
            mock_home.return_value = Path("/home/safe")
            mock_cwd.return_value = Path("/current/safe")

            # Get paths multiple times
            dir1 = ConfigPaths.get_global_config_dir()
            dir2 = ConfigPaths.get_global_config_dir()

            paths1 = ConfigPaths.get_config_file_paths()
            paths2 = ConfigPaths.get_config_file_paths()

            # Results should be equivalent but independent
            assert dir1 == dir2
            assert paths1 == paths2

            # Modifying one shouldn't affect the other (they should be independent objects)
            # Note: Path objects are immutable, but lists can be modified
            paths1["env_files"].append(Path("/fake"))
            assert len(paths2["env_files"]) == 2  # Original should be unchanged

    @pytest.mark.parametrize(
        ("home_path", "expected_suffix"),
        [
            ("/home/user", ".awa"),
            ("/Users/developer", ".awa"),
            ("C:/Users/Admin", ".awa"),  # Use forward slashes for consistency
            ("/", ".awa"),
        ],
    )
    def test_global_config_dir_suffix_consistency(self, home_path: str, expected_suffix: str) -> None:
        """Test that global config directory always uses correct suffix."""
        with patch.object(Path, "home") as mock_home:
            mock_home.return_value = Path(home_path)

            result = ConfigPaths.get_global_config_dir()

            assert result.name == expected_suffix
            assert str(result).endswith(expected_suffix)

    @pytest.mark.parametrize(
        ("file_type", "expected_names"),
        [
            ("env_files", [".env", ".env"]),
            ("yaml_files", ["config.yaml", "config.yaml"]),
        ],
    )
    def test_config_file_names_consistency(self, file_type: str, expected_names: list[str]) -> None:
        """Test that config file names are consistent."""
        with patch.object(Path, "home") as mock_home, patch.object(Path, "cwd") as mock_cwd:
            mock_home.return_value = Path("/home/test")
            mock_cwd.return_value = Path("/current/test")

            result = ConfigPaths.get_config_file_paths()

            file_paths = result[file_type]
            actual_names = [path.name for path in file_paths]

            assert actual_names == expected_names

    def test_state_file_name_consistency(self) -> None:
        """Test that state file name is consistent."""
        with patch.object(Path, "home") as mock_home:
            mock_home.return_value = Path("/home/test")

            result = ConfigPaths.get_global_state_file()

            assert result.name == "services.json"
            assert result.suffix == ".json"

    def test_edge_case_empty_path_components(self) -> None:
        """Test behavior with edge case path scenarios."""
        with patch.object(Path, "home") as mock_home, patch.object(Path, "cwd") as mock_cwd:
            # Test with minimal paths
            mock_home.return_value = Path()
            mock_cwd.return_value = Path()

            # Methods should still work and return valid Path objects
            global_dir = ConfigPaths.get_global_config_dir()
            state_file = ConfigPaths.get_global_state_file()
            config_paths = ConfigPaths.get_config_file_paths()

            assert isinstance(global_dir, Path)
            assert isinstance(state_file, Path)
            assert isinstance(config_paths, dict)

            # Paths should still have expected components
            assert global_dir.name == ".awa"
            assert state_file.name == "services.json"

    def test_method_isolation(self) -> None:
        """Test that methods don't interfere with each other."""
        with patch.object(Path, "home") as mock_home, patch.object(Path, "cwd") as mock_cwd:
            mock_home.return_value = Path("/isolation/test")
            mock_cwd.return_value = Path("/current/test")

            # Call methods in different orders to ensure no state interference
            order1 = [
                ConfigPaths.get_global_config_dir(),
                ConfigPaths.get_config_file_paths(),
                ConfigPaths.get_global_state_file(),
            ]

            # Reset mocks
            mock_home.reset_mock()
            mock_cwd.reset_mock()
            mock_home.return_value = Path("/isolation/test")
            mock_cwd.return_value = Path("/current/test")

            order2 = [
                ConfigPaths.get_global_state_file(),
                ConfigPaths.get_global_config_dir(),
                ConfigPaths.get_config_file_paths(),
            ]

            # Results should be consistent regardless of call order
            assert order1[0] == order2[1]  # get_global_config_dir
            assert order1[1] == order2[2]  # get_config_file_paths
            assert order1[2] == order2[0]  # get_global_state_file
