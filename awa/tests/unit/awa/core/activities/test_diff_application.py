"""Test cases for diff application activities."""

from unittest.mock import patch

import pytest

from awa.core.activities.apply_diff import apply_diff_activity, open_file, remove_file, write_file
from awa.core.models.apply_diff_result import ApplyDiffResult
from awa.core.utils.diff_utilities import DiffError


@pytest.mark.asyncio
async def test_apply_diff_success() -> None:
    """Test applying a diff that succeeds."""
    # Mock the process_patch function from diff_utilities module
    with patch("awa.core.activities.apply_diff.process_patch") as mock_process:
        mock_process.return_value = "Done!"

        diff_text = """*** Begin Patch
*** Update File: example.py
 def hello():
     print("Hello, world!")

-def main():
-    hello()
+def main():
+    hello()
+    goodbye()

 if __name__ == "__main__":
     main()
*** End Patch"""

        # Call the activity
        result = await apply_diff_activity(diff_text)

        # Verify the result
        assert isinstance(result, ApplyDiffResult)
        assert result.success is True

        # Verify process_patch was called with the diff text
        # The other parameters would be the actual function objects
        mock_process.assert_called_once()
        args, _ = mock_process.call_args
        assert args[0] == diff_text


@pytest.mark.asyncio
async def test_apply_diff_failure() -> None:
    """Test applying a diff that fails."""
    # Mock the process_patch function to raise an exception
    with patch("awa.core.activities.apply_diff.process_patch") as mock_process:
        mock_process.side_effect = DiffError("Invalid diff")

        diff_text = "*** Begin Patch\n*** Invalid Patch"

        # Call the activity
        result = await apply_diff_activity(diff_text)

        # Verify the result
        assert isinstance(result, ApplyDiffResult)
        assert result.success is False
        assert result.message == "Invalid diff"


@pytest.mark.asyncio
async def test_apply_diff_file_not_found() -> None:
    """Test applying a diff when file is not found."""
    # Mock the process_patch function to raise FileNotFoundError
    with patch("awa.core.activities.apply_diff.process_patch") as mock_process:
        mock_process.side_effect = FileNotFoundError("File not found: example.py")

        diff_text = "*** Begin Patch\n*** Update File: example.py\n*** End Patch"

        # Call the activity
        result = await apply_diff_activity(diff_text)

        # Verify the result
        assert isinstance(result, ApplyDiffResult)
        assert result.success is False
        assert result.message == "File not found: example.py"


@pytest.mark.asyncio
async def test_apply_diff_os_error() -> None:
    """Test applying a diff when OS error occurs."""
    # Mock the process_patch function to raise OSError
    with patch("awa.core.activities.apply_diff.process_patch") as mock_process:
        mock_process.side_effect = OSError("Permission denied")

        diff_text = "*** Begin Patch\n*** Update File: example.py\n*** End Patch"

        # Call the activity
        result = await apply_diff_activity(diff_text)

        # Verify the result
        assert isinstance(result, ApplyDiffResult)
        assert result.success is False
        assert result.message == "Permission denied"


@pytest.mark.asyncio
async def test_file_operations() -> None:
    """Test file operations used by apply_diff."""
    # Test open_file
    with patch("awa.core.activities.apply_diff.FileSystemUtils.read_async") as mock_read:
        mock_read.return_value = "file content"
        content = await open_file("test_file.txt")
        assert content == "file content"
        mock_read.assert_called_once_with("test_file.txt")

    # Test write_file
    with patch("awa.core.activities.apply_diff.FileSystemUtils.write_async") as mock_write:
        await write_file("test/dir/file.txt", "new content")
        mock_write.assert_called_once_with("test/dir/file.txt", "new content")

    # Test remove_file
    with patch("awa.core.activities.apply_diff.FileSystemUtils.remove_async") as mock_remove:
        await remove_file("existing_file.txt")
        mock_remove.assert_called_once_with("existing_file.txt")
