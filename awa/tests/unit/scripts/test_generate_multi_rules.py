# ruff: noqa: ANN401
"""Unit tests for the AI Documentation Generator script."""

import importlib.util
import shutil
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from tests.utils.platform_test_utils import normalize_path_for_comparison

# Calculate project root correctly from tests/unit/scripts/test_generate_multi_rules.py
test_file_path = Path(__file__).resolve()
# Go up 3 levels: tests/unit/scripts/test_generate_multi_rules.py -> project_root
project_root = test_file_path.parents[3]

# Import the script as a module
script_path = project_root / "scripts" / "ai-documentation-generator" / "tools" / "generate_multi_rules.py"
spec = importlib.util.spec_from_file_location(
    "generate_multi_rules",
    script_path,
)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load spec for {script_path}")
generate_multi_rules_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_multi_rules_module)

# Import the classes and functions we need to test
DocumentationReferenceProcessor = generate_multi_rules_module.DocumentationReferenceProcessor
MetadataRuleGenerator = generate_multi_rules_module.MetadataRuleGenerator
main = generate_multi_rules_module.main
logger = generate_multi_rules_module.logger


@pytest.fixture
def temp_project() -> Any:
    """Create a temporary project structure for testing."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create directory structure
    docs_dir = temp_dir / "docs"
    ai_dir = docs_dir / "ai"
    ai_dir.mkdir(parents=True)

    # Create sample source files
    core_instructions = ai_dir / "core-instructions.md"
    core_instructions.write_text("""# Core Instructions

This is the main rule file.

## Configuration

```yaml
claude:
  base_rule: true
  description: "Core instructions for all development"
  command_name: "core-instructions"
cursor:
  description: "Core development rules"
  globs: ["**/*"]
  alwaysApply: true
copilot:
  base_rule: true
  description: "Core development instructions"
  output_type: "instructions"
```

Some content here.
""")

    baml_dev = ai_dir / "baml-development.md"
    baml_dev.write_text("""# BAML Development

Rules for BAML development.

## Configuration

```yaml
claude:
  description: "BAML development context"
  command_name: "baml-dev"
  include_in_index: true
cursor:
  description: "BAML development rules"
  globs: ["**/*.baml", "**/*.py"]
copilot:
  description: "BAML development instructions"
  output_type: "instructions"
  applyTo: ["**/*.baml"]
```

BAML specific content.
""")

    # Create include file for testing references
    include_file = docs_dir / "includes" / "sample.md"
    include_file.parent.mkdir(parents=True)
    include_file.write_text(
        "# Sample Include\n\nThis is included content.\n\n## Additional Section\n\nThis content should remain.",
    )

    # Create a README for testing includes
    readme = temp_dir / "README.md"
    readme.write_text("# Project README\n\nProject description.")

    yield {
        "temp_dir": temp_dir,
        "docs_dir": docs_dir,
        "ai_dir": ai_dir,
        "core_instructions": core_instructions,
        "baml_dev": baml_dev,
        "include_file": include_file,
        "readme": readme,
    }

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestDocumentationReferenceProcessor:
    """Test DocumentationReferenceProcessor class."""

    def test_init(self, temp_project: dict[str, Any]) -> None:
        """Test processor initialization."""
        processor = DocumentationReferenceProcessor(temp_project["temp_dir"])
        assert processor.project_root == temp_project["temp_dir"]

    def test_process_references_no_includes(self, temp_project: dict[str, Any]) -> None:
        """Test processing content with no includes."""
        processor = DocumentationReferenceProcessor(temp_project["temp_dir"])
        content = "# Test\n\nNo includes here."
        result = processor.process_references(content)
        assert result == content

    def test_process_references_with_include(self, temp_project: dict[str, Any]) -> None:
        """Test processing content with VitePress include."""
        processor = DocumentationReferenceProcessor(temp_project["temp_dir"])
        content = "# Test\n\n<!--@include: ../includes/sample.md -->\n\nAfter include."
        result = processor.process_references(content)
        # H1 header and intro paragraph are removed to avoid duplication
        assert "# Sample Include" not in result
        assert "This is included content." not in result
        # But remaining content should be preserved
        assert "## Additional Section" in result
        assert "This content should remain." in result
        assert "After include." in result

    def test_process_references_with_comment(self, temp_project: dict[str, Any]) -> None:
        """Test processing include with comment."""
        processor = DocumentationReferenceProcessor(temp_project["temp_dir"])
        content = "<!--@include: ../includes/sample.md --> <!-- This is a comment -->"
        result = processor.process_references(content)
        assert "<!-- This is a comment -->" in result
        # H1 header is removed to avoid duplication
        assert "# Sample Include" not in result
        # But remaining content should be preserved
        assert "## Additional Section" in result

    def test_resolve_vitepress_include_relative_path(self, temp_project: dict[str, Any]) -> None:
        """Test resolving relative include path."""
        processor = DocumentationReferenceProcessor(temp_project["temp_dir"])
        result = processor._resolve_vitepress_include("../includes/sample.md", "")
        # H1 header and intro paragraph are removed to avoid duplication
        assert "# Sample Include" not in result
        assert "This is included content." not in result
        # But remaining content should be preserved
        assert "## Additional Section" in result
        assert "This content should remain." in result

    def test_resolve_vitepress_include_project_root_path(self, temp_project: dict[str, Any]) -> None:
        """Test resolving project root include path."""
        processor = DocumentationReferenceProcessor(temp_project["temp_dir"])
        result = processor._resolve_vitepress_include("../../README.md", "")
        # H1 header and intro paragraph are removed to avoid duplication
        assert "# Project README" not in result
        assert "Project description." not in result
        # Since the README only has header and description, result should be empty
        assert result.strip() == ""

    def test_resolve_vitepress_include_file_not_found(self, temp_project: dict[str, Any]) -> None:
        """Test resolving non-existent include file."""
        processor = DocumentationReferenceProcessor(temp_project["temp_dir"])
        result = processor._resolve_vitepress_include("../nonexistent.md", "")
        assert "Include file not found" in result

    def test_extract_section(self, temp_project: dict[str, Any]) -> None:
        """Test extracting specific section from markdown."""
        processor = DocumentationReferenceProcessor(temp_project["temp_dir"])
        content = """# Main Title

Some intro content.

## Section A

Content of section A.

### Subsection A1

Subsection content.

## Section B

Content of section B.
"""
        result = processor._extract_section(content, "Section A")
        assert "## Section A" in result
        assert "Content of section A." in result
        assert "### Subsection A1" in result
        assert "Subsection content." in result
        assert "Section B" not in result

    def test_extract_section_not_found(self, temp_project: dict[str, Any]) -> None:
        """Test extracting non-existent section."""
        processor = DocumentationReferenceProcessor(temp_project["temp_dir"])
        content = "# Main Title\n\nNo matching section."
        result = processor._extract_section(content, "Missing Section")
        assert "Section 'Missing Section' not found" in result

    def test_extract_lines_range(self, temp_project: dict[str, Any]) -> None:
        """Test extracting line range."""
        processor = DocumentationReferenceProcessor(temp_project["temp_dir"])
        content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        result = processor._extract_lines(content, "2-4")
        assert result == "Line 2\nLine 3\nLine 4"

    def test_extract_lines_single_line(self, temp_project: dict[str, Any]) -> None:
        """Test extracting single line."""
        processor = DocumentationReferenceProcessor(temp_project["temp_dir"])
        content = "Line 1\nLine 2\nLine 3"
        result = processor._extract_lines(content, "2")
        assert result == "Line 2"

    def test_extract_lines_invalid_range(self, temp_project: dict[str, Any]) -> None:
        """Test extracting invalid line range."""
        processor = DocumentationReferenceProcessor(temp_project["temp_dir"])
        content = "Line 1\nLine 2\nLine 3"
        result = processor._extract_lines(content, "invalid")
        assert "Invalid line range" in result


class TestMetadataRuleGenerator:
    """Test MetadataRuleGenerator class."""

    def test_init(self, temp_project: dict[str, Any]) -> None:
        """Test generator initialization."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])
        assert generator.project_root == temp_project["temp_dir"]
        assert generator.source_dir == temp_project["ai_dir"]
        assert isinstance(generator.reference_processor, DocumentationReferenceProcessor)

    def test_read_source_file(self, temp_project: dict[str, Any]) -> None:
        """Test reading source file content."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])
        content = generator._read_source_file("core-instructions.md")
        assert "# Core Instructions" in content
        assert "This is the main rule file." in content
        assert "Some content here." in content
        # Configuration section should be removed
        assert "## Configuration" not in content
        assert "base_rule: true" not in content

    def test_read_source_file_nonexistent(self, temp_project: dict[str, Any]) -> None:
        """Test reading non-existent source file."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])
        content = generator._read_source_file("nonexistent.md")
        assert content == ""

    def test_read_metadata_file(self, temp_project: dict[str, Any]) -> None:
        """Test reading metadata from source file."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])
        metadata = generator._read_metadata_file("core-instructions.md")
        assert "claude" in metadata
        assert "cursor" in metadata
        assert "copilot" in metadata
        assert metadata["claude"]["base_rule"] is True
        assert metadata["claude"]["command_name"] == "core-instructions"

    def test_read_metadata_file_nonexistent(self, temp_project: dict[str, Any]) -> None:
        """Test reading metadata from non-existent file."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])
        metadata = generator._read_metadata_file("nonexistent.md")
        assert metadata == {}

    def test_discover_source_files(self, temp_project: dict[str, Any]) -> None:
        """Test discovering source files."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])
        files = generator._discover_source_files()
        assert "core-instructions.md" in files
        assert "baml-development.md" in files
        assert "index.md" not in files  # Should be excluded
        assert len(files) == 2

    def test_generate_cursor_file(self, temp_project: dict[str, Any]) -> None:
        """Test generating Cursor .mdc file."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])
        metadata = generator._read_metadata_file("core-instructions.md")
        result = generator._generate_cursor_file("core-instructions.md", metadata)

        assert result.startswith("---\n")
        assert "alwaysApply: true" in result
        assert "globs: **/*" in result
        assert 'description: "Core development rules"' in result
        assert "---\n\n# Core Instructions" in result
        assert "Some content here." in result

    def test_generate_copilot_file_instructions(self, temp_project: dict[str, Any]) -> None:
        """Test generating Copilot instructions file."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])
        metadata = generator._read_metadata_file("baml-development.md")
        result = generator._generate_copilot_file("baml-development.md", metadata)

        assert result.startswith("---\n")
        assert 'applyTo: "**/*.baml"' in result
        assert "description:" not in result  # Description should not be included
        assert "---\n\n# BAML Development" in result
        assert "BAML specific content." in result

    def test_generate_copilot_file_prompts(self, temp_project: dict[str, Any]) -> None:
        """Test generating Copilot prompts file."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])
        # Modify metadata to use prompts type
        metadata = {
            "copilot": {
                "description": "Test prompt",
                "output_type": "prompts",
            },
        }
        result = generator._generate_copilot_file("baml-development.md", metadata)

        # Prompts should not have any frontmatter according to GitHub docs
        assert not result.startswith("---\n")
        assert "description:" not in result
        assert "applyTo:" not in result
        assert result.startswith("# BAML Development")
        assert "BAML specific content." in result

    def test_generate_copilot_file_instructions_multiple_apply_to(self, temp_project: dict[str, Any]) -> None:
        """Test generating Copilot instructions file with multiple applyTo patterns."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])
        metadata = {
            "copilot": {
                "description": "Multi-pattern instructions",
                "output_type": "instructions",
                "applyTo": ["**/*.baml", "**/*.py", "**/*.ts"],
            },
        }
        result = generator._generate_copilot_file("test.md", metadata)

        assert result.startswith("---\n")
        assert "applyTo: \n" in result
        assert '  - "**/*.baml"' in result
        assert '  - "**/*.py"' in result
        assert '  - "**/*.ts"' in result
        assert "description:" not in result

    def test_generate_claude_file(self, temp_project: dict[str, Any]) -> None:
        """Test generating Claude command file."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])
        metadata = generator._read_metadata_file("baml-development.md")
        result = generator._generate_claude_file("baml-development.md", metadata)

        assert result.startswith("# BAML development context\n\n")
        assert "BAML specific content." in result

    def test_validate_base_rules_valid(self, temp_project: dict[str, Any]) -> None:
        """Test validating base rules with valid configuration."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])
        # Should not raise any exception
        generator._validate_base_rules()

    def test_validate_base_rules_multiple_claude(self, temp_project: dict[str, Any]) -> None:
        """Test validating base rules with multiple Claude base rules."""
        # Create another file with Claude base rule
        duplicate_file = temp_project["ai_dir"] / "duplicate.md"
        duplicate_file.write_text("""# Duplicate

## Configuration

```yaml
claude:
  base_rule: true
  description: "Duplicate base rule"
```
""")

        generator = MetadataRuleGenerator(temp_project["temp_dir"])
        with pytest.raises(ValueError) as excinfo:
            generator._validate_base_rules()

        assert "Multiple files have base_rule: true for claude" in str(excinfo.value)
        assert "core-instructions.md" in str(excinfo.value)
        assert "duplicate.md" in str(excinfo.value)

    def test_generate_rule_index(self, temp_project: dict[str, Any]) -> None:
        """Test generating rule index."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])
        result = generator._generate_agent_rule_index("claude")

        assert "## Available AI Rules" in result
        assert "**/baml-dev**: BAML development context" in result
        # core-instructions should be excluded from index
        assert "core-instructions" not in result

    def test_generate_rule_index_empty(self, temp_project: dict[str, Any]) -> None:
        """Test generating rule index with no commands."""
        # Remove all files except core-instructions
        temp_project["baml_dev"].unlink()

        generator = MetadataRuleGenerator(temp_project["temp_dir"])
        result = generator._generate_agent_rule_index("claude")

        assert result == ""

    def test_generate_agent_rules_cursor(self, temp_project: dict[str, Any]) -> None:
        """Test generating rules for Cursor agent."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])

        with patch.object(Path, "mkdir") as mock_mkdir, patch.object(Path, "write_text") as mock_write:
            files = generator.generate_agent_rules("cursor")

            # Normalize file paths for cross-platform comparison
            normalized_files = [normalize_path_for_comparison(f) for f in files]

            assert len(files) == 2
            assert ".cursor/rules/core-instructions.mdc" in normalized_files
            assert ".cursor/rules/baml-development.mdc" in normalized_files

            # Verify directories were created
            mock_mkdir.assert_called()
            # Verify files were written
            assert mock_write.call_count == 2

    def test_generate_agent_rules_copilot_base_rule(self, temp_project: dict[str, Any]) -> None:
        """Test generating Copilot base rule."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])

        with patch.object(Path, "mkdir"), patch.object(Path, "write_text"):
            files = generator.generate_agent_rules("copilot")

            # Normalize file paths for cross-platform comparison
            normalized_files = [normalize_path_for_comparison(f) for f in files]

            # Should have base rule and regular rule
            assert len(files) >= 2
            assert ".github/copilot-instructions.md" in normalized_files
            assert ".github/instructions/baml-development.instructions.md" in normalized_files

    def test_generate_agent_rules_claude_base_rule(self, temp_project: dict[str, Any]) -> None:
        """Test generating Claude base rule."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])

        with patch.object(Path, "mkdir"), patch.object(Path, "write_text"):
            files = generator.generate_agent_rules("claude")

            # Normalize file paths for cross-platform comparison
            normalized_files = [normalize_path_for_comparison(f) for f in files]

            # Should have base rule and regular rule
            assert len(files) >= 2
            assert "CLAUDE.md" in normalized_files
            assert ".claude/commands/baml-dev.md" in normalized_files

    def test_generate_agent_rules_invalid_agent(self, temp_project: dict[str, Any]) -> None:
        """Test generating rules for invalid agent."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])

        with pytest.raises(ValueError) as excinfo:
            generator.generate_agent_rules("invalid")

        assert "Unknown agent: invalid" in str(excinfo.value)

    def test_generate_all_rules(self, temp_project: dict[str, Any]) -> None:
        """Test generating rules for all agents."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])

        with (
            patch.object(Path, "mkdir"),
            patch.object(Path, "write_text"),
            patch.object(logger, "info") as mock_logger_info,
        ):
            results = generator.generate_all_rules()

            assert "cursor" in results
            assert "copilot" in results
            assert "claude" in results
            assert len(results["cursor"]) >= 2
            assert len(results["copilot"]) >= 2
            assert len(results["claude"]) >= 2

            # Should log success messages
            mock_logger_info.assert_called()

    def test_clean_generated_files(self, temp_project: dict[str, Any]) -> None:
        """Test cleaning generated files."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])

        # Create some fake generated files
        cursor_dir = temp_project["temp_dir"] / ".cursor" / "rules"
        cursor_dir.mkdir(parents=True)
        cursor_file = cursor_dir / "core-instructions.mdc"
        cursor_file.write_text("fake content")

        github_dir = temp_project["temp_dir"] / ".github"
        github_dir.mkdir(parents=True)
        copilot_file = github_dir / "copilot-instructions.md"
        copilot_file.write_text("fake content")

        claude_file = temp_project["temp_dir"] / "CLAUDE.md"
        claude_file.write_text("fake content")

        with patch.object(logger, "info") as mock_logger_info:
            generator.clean_generated_files()

        # Files should be deleted
        assert not cursor_file.exists()
        assert not copilot_file.exists()
        assert not claude_file.exists()

        # Should log removal messages
        mock_logger_info.assert_called()

    def test_validate_source_files(self, temp_project: dict[str, Any]) -> None:
        """Test validating source files."""
        generator = MetadataRuleGenerator(temp_project["temp_dir"])

        with patch.object(logger, "info") as mock_logger_info:
            result = generator.validate_source_files()

        assert result is True
        mock_logger_info.assert_called()
        # Should log file information
        info_calls = [call[0][0] for call in mock_logger_info.call_args_list]
        assert any("Found %d source files:" in call for call in info_calls)
        assert any("core-instructions.md" in str(call) for call in mock_logger_info.call_args_list)
        assert any("baml-development.md" in str(call) for call in mock_logger_info.call_args_list)


class TestMain:
    """Test main function."""

    @patch("sys.argv", ["generate_multi_rules.py", "generate"])
    def test_main_generate_all(self) -> None:
        """Test main function with generate command for all agents."""
        with (
            patch.object(MetadataRuleGenerator, "__init__", return_value=None) as mock_init,
            patch.object(MetadataRuleGenerator, "generate_all_rules") as mock_generate,
            patch.object(logger, "info") as mock_logger_info,
            patch("logging.basicConfig"),
        ):
            mock_generate.return_value = {
                "cursor": ["file1.mdc", "file2.mdc"],
                "copilot": ["file3.md"],
                "claude": ["file4.md"],
            }

            main()

            mock_init.assert_called_once()
            mock_generate.assert_called_once()
            mock_logger_info.assert_called()

    @patch("sys.argv", ["generate_multi_rules.py", "generate", "--agent", "cursor"])
    def test_main_generate_specific_agent(self) -> None:
        """Test main function with generate command for specific agent."""
        with (
            patch.object(MetadataRuleGenerator, "__init__", return_value=None) as mock_init,
            patch.object(MetadataRuleGenerator, "generate_agent_rules") as mock_generate,
            patch.object(logger, "info") as mock_logger_info,
            patch("logging.basicConfig"),
        ):
            mock_generate.return_value = ["file1.mdc", "file2.mdc"]

            main()

            mock_init.assert_called_once()
            mock_generate.assert_called_once_with("cursor")
            mock_logger_info.assert_called()

    @patch("sys.argv", ["generate_multi_rules.py", "clean"])
    def test_main_clean(self) -> None:
        """Test main function with clean command."""
        with (
            patch.object(MetadataRuleGenerator, "__init__", return_value=None) as mock_init,
            patch.object(MetadataRuleGenerator, "clean_generated_files") as mock_clean,
            patch.object(logger, "info") as mock_logger_info,
            patch("logging.basicConfig"),
        ):
            main()

            mock_init.assert_called_once()
            mock_clean.assert_called_once()
            mock_logger_info.assert_called_with("🧹 Cleaning generated rule files...")

    @patch("sys.argv", ["generate_multi_rules.py", "validate"])
    def test_main_validate(self) -> None:
        """Test main function with validate command."""
        with (
            patch.object(MetadataRuleGenerator, "__init__", return_value=None) as mock_init,
            patch.object(MetadataRuleGenerator, "validate_source_files") as mock_validate,
            patch.object(logger, "info") as mock_logger_info,
            patch("logging.basicConfig"),
        ):
            main()

            mock_init.assert_called_once()
            mock_validate.assert_called_once()
            mock_logger_info.assert_called_with("🔍 Validating source files and metadata...")

    @patch("sys.argv", ["generate_multi_rules.py", "list"])
    def test_main_list(self) -> None:
        """Test main function with list command."""
        with (
            patch.object(MetadataRuleGenerator, "__init__", return_value=None) as mock_init,
            patch.object(MetadataRuleGenerator, "_discover_source_files") as mock_discover,
            patch.object(MetadataRuleGenerator, "_read_metadata_file") as mock_read_meta,
            patch.object(logger, "info") as mock_logger_info,
            patch("logging.basicConfig"),
        ):
            mock_discover.return_value = ["core-instructions.md", "baml-development.md"]
            mock_read_meta.return_value = {"cursor": {}, "copilot": {}, "claude": {}}

            main()

            mock_init.assert_called_once()
            mock_discover.assert_called_once()
            mock_logger_info.assert_called()
