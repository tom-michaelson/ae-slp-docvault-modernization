"""Unit tests for PlatformUtils class."""

import sys
from unittest.mock import patch

from awa.core.utils.platform_utils import PlatformUtils


class TestPlatformUtils:
    """Test cases for PlatformUtils class."""

    @patch.object(sys, "platform", "win32")
    def test_is_windows_true(self) -> None:
        """Test is_windows returns True on Windows platform."""
        assert PlatformUtils.is_windows() is True

    @patch.object(sys, "platform", "linux")
    def test_is_windows_false_linux(self) -> None:
        """Test is_windows returns False on Linux platform."""
        assert PlatformUtils.is_windows() is False

    @patch.object(sys, "platform", "darwin")
    def test_is_windows_false_darwin(self) -> None:
        """Test is_windows returns False on macOS platform."""
        assert PlatformUtils.is_windows() is False

    @patch.object(sys, "platform", "win32")
    def test_is_unix_false(self) -> None:
        """Test is_unix returns False on Windows platform."""
        assert PlatformUtils.is_unix() is False

    @patch.object(sys, "platform", "linux")
    def test_is_unix_true_linux(self) -> None:
        """Test is_unix returns True on Linux platform."""
        assert PlatformUtils.is_unix() is True

    @patch.object(sys, "platform", "darwin")
    def test_is_unix_true_darwin(self) -> None:
        """Test is_unix returns True on macOS platform."""
        assert PlatformUtils.is_unix() is True

    @patch.object(sys, "platform", "win32")
    def test_get_platform_type_windows(self) -> None:
        """Test get_platform_type returns 'windows' on Windows platform."""
        assert PlatformUtils.get_platform_type() == "windows"

    @patch.object(sys, "platform", "linux")
    def test_get_platform_type_unix_linux(self) -> None:
        """Test get_platform_type returns 'unix' on Linux platform."""
        assert PlatformUtils.get_platform_type() == "unix"

    @patch.object(sys, "platform", "darwin")
    def test_get_platform_type_unix_darwin(self) -> None:
        """Test get_platform_type returns 'unix' on macOS platform."""
        assert PlatformUtils.get_platform_type() == "unix"

    @patch.object(sys, "platform", "win32")
    def test_get_platform_name_windows(self) -> None:
        """Test get_platform_name returns sys.platform value on Windows."""
        assert PlatformUtils.get_platform_name() == "win32"

    @patch.object(sys, "platform", "linux")
    def test_get_platform_name_linux(self) -> None:
        """Test get_platform_name returns sys.platform value on Linux."""
        assert PlatformUtils.get_platform_name() == "linux"

    @patch.object(sys, "platform", "darwin")
    def test_get_platform_name_darwin(self) -> None:
        """Test get_platform_name returns sys.platform value on macOS."""
        assert PlatformUtils.get_platform_name() == "darwin"
