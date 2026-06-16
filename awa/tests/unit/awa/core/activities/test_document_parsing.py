"""Unit tests for document parsing activity."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from temporalio.testing import ActivityEnvironment

from awa.core.activities.read_file_and_parse_activity import read_file_and_parse_activity
from awa.sdk.models.exceptions.fatal_application_error import FatalApplicationError
from awa.sdk.models.exceptions.file_extension_not_supported_error import FileExtensionNotSupportedApplicationError
from awa.sdk.models.read_file_and_parse_input import ReadFileAndParseInput
from tests.utils.platform_test_utils import normalize_line_endings


class TestDocumentParsingActivity:
    @pytest.mark.asyncio
    async def test_plain_text_passthrough(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that plain text files are returned without parsing."""
        # Test various plain text extensions
        test_cases = [
            ("test.txt", "Plain text content"),
            ("readme.md", "# Markdown content\n\nThis is markdown"),
            ("notes.markdown", "Another markdown file"),
            ("app.log", "2025-01-01 INFO: Log entry"),
        ]

        for filename, content in test_cases:
            # Arrange
            file_path = tmp_path / filename
            file_path.write_text(content)

            # Act
            inp = ReadFileAndParseInput(file_path=str(file_path))
            result = await activity_env.run(read_file_and_parse_activity, inp)

            # Assert - normalize line endings for cross-platform comparison
            normalized_result = normalize_line_endings(result)
            normalized_content = normalize_line_endings(content)
            assert normalized_result == normalized_content, f"Failed for {filename}"

    @pytest.mark.asyncio
    async def test_file_not_found_returns_default(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that non-existent files return the default value."""
        # Act
        nonexistent_path = tmp_path / "nonexistent.txt"
        inp = ReadFileAndParseInput(
            file_path=str(nonexistent_path),
            default_content="default content",
        )
        result = await activity_env.run(read_file_and_parse_activity, inp)

        # Assert
        assert result == "default content"

    @pytest.mark.asyncio
    async def test_file_not_found_returns_empty_string(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that non-existent files return empty string when no default."""
        # Act
        nonexistent_path = tmp_path / "nonexistent.txt"
        inp = ReadFileAndParseInput(file_path=str(nonexistent_path))
        result = await activity_env.run(read_file_and_parse_activity, inp)

        # Assert
        assert result == ""

    @pytest.mark.asyncio
    async def test_markitdown_parsing(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that supported document formats are parsed with MarkItDown."""
        # Arrange
        # Create mock binary content representing a document
        mock_content = b"Mock document content"
        file_path = tmp_path / "document.docx"
        file_path.write_bytes(mock_content)

        # Mock MarkItDown to verify it's called
        mock_result = MagicMock()
        mock_result.text_content = "# Parsed Document\n\nThis is the parsed content."

        with patch("awa.core.activities.read_file_and_parse_activity.MarkItDown") as mock_markitdown:
            mock_instance = MagicMock()
            mock_instance.convert.return_value = mock_result
            mock_markitdown.return_value = mock_instance

            # Act
            inp = ReadFileAndParseInput(file_path=str(file_path))
            result = await activity_env.run(read_file_and_parse_activity, inp)

            # Assert
            assert result == "# Parsed Document\n\nThis is the parsed content."
            mock_markitdown.assert_called_once()
            mock_instance.convert.assert_called_once()

            # Verify that convert was called with a file path
            call_args = mock_instance.convert.call_args[0]
            assert isinstance(call_args[0], str)  # Should be a file path
            assert call_args[0].endswith(".docx")  # Should have the correct extension

    @pytest.mark.asyncio
    async def test_markitdown_parsing_error_raises_fatal_error(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that parsing errors raise FatalApplicationError."""
        # Arrange
        file_path = tmp_path / "problematic.pdf"
        content = b"Mock PDF content that causes parsing error"
        file_path.write_bytes(content)

        with patch("awa.core.activities.read_file_and_parse_activity.MarkItDown") as mock_markitdown:
            mock_instance = MagicMock()
            mock_instance.convert.side_effect = Exception("Parsing failed")
            mock_markitdown.return_value = mock_instance

            # Act & Assert
            inp = ReadFileAndParseInput(file_path=str(file_path))
            with pytest.raises(FatalApplicationError) as exc_info:
                await activity_env.run(read_file_and_parse_activity, inp)

            # Verify the error message contains the original exception message
            assert "Error parsing file: Parsing failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_various_file_extensions(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that various document extensions trigger MarkItDown parsing."""
        # Extensions that should trigger parsing
        parsing_extensions = [
            ".pdf",
            ".docx",
            ".pptx",
            ".xlsx",
            ".xls",
            ".html",
            ".csv",
            ".epub",
            ".msg",  # Outlook message files
        ]

        with patch("awa.core.activities.read_file_and_parse_activity.MarkItDown") as mock_markitdown:
            mock_result = MagicMock()
            mock_result.text_content = "Parsed content"
            mock_instance = MagicMock()
            mock_instance.convert.return_value = mock_result
            mock_markitdown.return_value = mock_instance

            for ext in parsing_extensions:
                # Reset mock
                mock_markitdown.reset_mock()
                mock_instance.reset_mock()

                # Arrange
                file_path = tmp_path / f"test{ext}"
                file_path.write_bytes(b"Mock content")

                # Act
                inp = ReadFileAndParseInput(file_path=str(file_path))
                result = await activity_env.run(read_file_and_parse_activity, inp)

                # Assert
                assert result == "Parsed content", f"Failed for extension {ext}"
                mock_markitdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_case_insensitive_extensions(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that file extensions are case-insensitive."""
        # Test upper case plain text extension
        file_upper = tmp_path / "README.MD"
        content_upper = "# Upper case markdown"
        file_upper.write_text(content_upper)

        inp = ReadFileAndParseInput(file_path=str(file_upper))
        result = await activity_env.run(read_file_and_parse_activity, inp)
        assert result == content_upper

        # Test mixed case document extension
        file_mixed = tmp_path / "Document.DocX"
        file_mixed.write_bytes(b"Mock Word content")

        with patch("awa.core.activities.read_file_and_parse_activity.MarkItDown") as mock_markitdown:
            mock_result = MagicMock()
            mock_result.text_content = "Parsed Word doc"
            mock_instance = MagicMock()
            mock_instance.convert.return_value = mock_result
            mock_markitdown.return_value = mock_instance

            inp = ReadFileAndParseInput(file_path=str(file_mixed))
            result = await activity_env.run(read_file_and_parse_activity, inp)
            assert result == "Parsed Word doc"
            mock_markitdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_unsupported_extensions_passthrough(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that unsupported file extensions are returned without parsing."""
        # Test various unsupported extensions
        test_cases = [
            ("binary.bin", b"Binary content"),
            ("config.ini", b"[section]\nkey=value"),
            ("script.py", b"print('Hello, World!')"),
            ("image.jpg", b"\xff\xd8\xff\xe0"),  # JPEG header
            ("archive.zip", b"PK\x03\x04"),  # ZIP header
            ("data.json", b'{"key": "value"}'),  # JSON is now passthrough
            ("data.xml", b"<root><item>value</item></root>"),  # XML is now passthrough
        ]

        for filename, content in test_cases:
            # Arrange
            file_path = tmp_path / filename
            file_path.write_bytes(content)

            # Act
            inp = ReadFileAndParseInput(file_path=str(file_path))
            result = await activity_env.run(read_file_and_parse_activity, inp)

            # Assert - should return decoded content without parsing
            expected = content.decode("utf-8", errors="ignore")
            assert result == expected, f"Failed for {filename}"

        # Verify MarkItDown is never called for unsupported types
        with patch("awa.core.activities.read_file_and_parse_activity.MarkItDown") as mock_markitdown:
            unknown_file = tmp_path / "test.xyz"
            unknown_file.write_bytes(b"Unknown format")
            inp = ReadFileAndParseInput(file_path=str(unknown_file))
            result = await activity_env.run(read_file_and_parse_activity, inp)
            assert result == "Unknown format"
            mock_markitdown.assert_not_called()

    @pytest.mark.asyncio
    async def test_strict_mode_raises_for_unsupported_types(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that strict mode raises exception for unsupported file types."""
        # Test various unsupported extensions that should raise in strict mode
        test_cases = [
            "test.txt",
            "script.py",
            "config.ini",
            "data.json",  # JSON is not in SUPPORTED_EXTENSIONS
            "data.xml",  # XML is not in SUPPORTED_EXTENSIONS
        ]

        for filename in test_cases:
            # Arrange
            file_path = tmp_path / filename
            file_path.write_text("Test content")
            inp = ReadFileAndParseInput(
                file_path=str(file_path),
                strict=True,
            )

            # Act & Assert
            with pytest.raises(FileExtensionNotSupportedApplicationError) as exc_info:
                await activity_env.run(read_file_and_parse_activity, inp)

            # Verify the error message contains the extension
            assert Path(filename).suffix in str(exc_info.value)
            assert "not supported for parsing" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_strict_mode_false_returns_raw_content(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that strict=False returns raw content for unsupported types."""
        # Arrange
        file_path = tmp_path / "test.txt"
        content = "Plain text content"
        file_path.write_text(content)
        inp = ReadFileAndParseInput(
            file_path=str(file_path),
            strict=False,  # Explicitly set to False
        )

        # Act
        result = await activity_env.run(read_file_and_parse_activity, inp)

        # Assert
        assert result == content

    @pytest.mark.asyncio
    async def test_strict_mode_true_parses_supported_types(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that strict mode still parses supported file types."""
        # Arrange
        file_path = tmp_path / "document.pdf"
        file_path.write_bytes(b"Mock PDF content")
        inp = ReadFileAndParseInput(
            file_path=str(file_path),
            strict=True,
        )

        with patch("awa.core.activities.read_file_and_parse_activity.MarkItDown") as mock_markitdown:
            mock_result = MagicMock()
            mock_result.text_content = "Parsed PDF content"
            mock_instance = MagicMock()
            mock_instance.convert.return_value = mock_result
            mock_markitdown.return_value = mock_instance

            # Act
            result = await activity_env.run(read_file_and_parse_activity, inp)

            # Assert
            assert result == "Parsed PDF content"
            mock_markitdown.assert_called_once()
