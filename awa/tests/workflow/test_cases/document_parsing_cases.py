"""Test cases for document parsing functionality."""

from pathlib import Path

# Get the base path for test documents
TEST_DATA_DIR = Path(__file__).parent.parent / "test-data" / "documents"

# Test cases for document parsing
TEST_CASES = [
    {
        "name": "Plain text file passthrough",
        "file_path": str(TEST_DATA_DIR / "sample.txt"),
        "expected_contains": [
            "This is a sample plain text file.",
            "It contains multiple lines and paragraphs",
            "Plain text files should be returned as-is",
        ],
        "should_not_contain": ["#", "```", "**"],  # No markdown formatting
    },
    {
        "name": "Markdown file passthrough",
        "file_path": str(TEST_DATA_DIR / "sample.md"),
        "expected_contains": [
            "# Sample Markdown Document",
            "**sample markdown**",
            "```python",
            "def hello_world():",
        ],
        "should_not_contain": [],  # Markdown should be preserved
    },
    {
        "name": "CSV file parsing",
        "file_path": str(TEST_DATA_DIR / "sample.csv"),
        "expected_contains": [
            "Name",
            "Age",
            "City",
            "Occupation",
            "John Doe",
            "Software Engineer",
            "Jane Smith",
            "Data Scientist",
        ],
        "should_not_contain": [],
    },
    {
        "name": "JSON file parsing",
        "file_path": str(TEST_DATA_DIR / "sample.json"),
        "expected_contains": [
            "Sample JSON Document",
            "version",
            "1.0",
            "Item One",
            "Item Two",
            "debug",
            "timeout",
        ],
        "should_not_contain": [],
    },
    {
        "name": "HTML file parsing",
        "file_path": str(TEST_DATA_DIR / "sample.html"),
        "expected_contains": [
            "# Sample HTML Page",  # Should be converted to markdown heading
            "**sample HTML document**",  # Bold text should be in markdown
            "## Features",  # H2 should be converted
            "### Example Table",  # H3 should be converted
            "| Test 1 | Pass |",  # Table should be in markdown format
            "[our website]",  # Link should be in markdown format
        ],
        "should_not_contain": ["<h1>", "</body>", "<table>", "<strong>"],  # HTML tags should be converted
    },
    {
        "name": "Non-existent file with default",
        "file_path": str(TEST_DATA_DIR / "nonexistent.pdf"),
        "default": "This is the default content",
        "expected_exact": "This is the default content",
    },
]
