import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from temporalio.testing import ActivityEnvironment

from awa.core.activities.jira import (
    _add_comment,
    _build_request_body,
    _determine_issue_type,
    _execute_issue_request,
    add_jira_comment,
    read_jira_issue,
    upsert_jira_issue,
)
from awa.core.utils.markdown_to_jira_converter import convert_markdown_to_jira_wiki_format
from awa.sdk.models.exceptions.fatal_application_error import FatalApplicationError
from awa.sdk.models.exceptions.retryable_application_error import RetryableApplicationError
from awa.sdk.models.jira_issue_request import JiraIssueRequest
from awa.sdk.models.jira_issue_response import JiraIssueResponse


class TestJiraActivities:
    """Test cases for Jira activity functions."""

    @pytest.mark.asyncio
    async def test_read_jira_issue_success(self, activity_env: ActivityEnvironment) -> None:
        """Test successful reading of a Jira issue."""
        # Arrange
        request = JiraIssueRequest(
            project_id="TEST",
            key="TEST-123",
            summary="Test issue",
            description="Test description",
        )
        expected_response = JiraIssueResponse(
            key="TEST-123",
            summary="Test issue",
            description="Test description",
            issue_type="Story",
        )

        with patch("awa.core.activities.jira._execute_issue_request", return_value=expected_response) as mock_execute:
            # Act
            result = await activity_env.run(read_jira_issue, request)

            # Assert
            assert result == expected_response
            mock_execute.assert_called_once_with(
                method="GET",
                url_suffix="/TEST-123?fields=issuetype,components,key,summary,description,labels",
                query_params={"expand": "renderedFields"},
            )

    @pytest.mark.asyncio
    async def test_read_jira_issue_missing_key(self, activity_env: ActivityEnvironment) -> None:
        """Test reading a Jira issue without a key raises FatalApplicationError."""
        # Arrange
        request = JiraIssueRequest(
            project_id="TEST",
            key=None,
            summary="Test issue",
            description="Test description",
        )

        # Act & Assert
        with pytest.raises(FatalApplicationError, match="Jira issue key is required to read a Jira issue"):
            await activity_env.run(read_jira_issue, request)

    @pytest.mark.asyncio
    async def test_upsert_jira_issue_create_success(self, activity_env: ActivityEnvironment) -> None:
        """Test successful creation of a Jira issue."""
        # Arrange
        request = JiraIssueRequest(
            project_id="TEST",
            key=None,  # No key means create
            summary="New issue",
            description="New description",
        )
        expected_response = JiraIssueResponse(key="TEST-124")

        with patch("awa.core.activities.jira._execute_issue_request", return_value=expected_response) as mock_execute:
            # Act
            result = await activity_env.run(upsert_jira_issue, request)

            # Assert
            assert result == "TEST-124"
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert call_args[1]["method"] == "POST"
            assert call_args[1]["url_suffix"] is None
            assert call_args[1]["body_json"] is not None

    @pytest.mark.asyncio
    async def test_upsert_jira_issue_update_success(self, activity_env: ActivityEnvironment) -> None:
        """Test successful update of a Jira issue."""
        # Arrange
        request = JiraIssueRequest(
            project_id="TEST",
            key="TEST-123",
            summary="Updated issue",
            description="Updated description",
        )
        expected_response = JiraIssueResponse(key="TEST-123")

        with patch("awa.core.activities.jira._execute_issue_request", return_value=expected_response) as mock_execute:
            # Act
            result = await activity_env.run(upsert_jira_issue, request)

            # Assert
            assert result == "TEST-123"
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert call_args[1]["method"] == "PUT"
            assert call_args[1]["url_suffix"] == "/TEST-123"
            assert call_args[1]["body_json"] is not None

    @pytest.mark.asyncio
    async def test_upsert_jira_issue_with_comments(self, activity_env: ActivityEnvironment) -> None:
        """Test upserting a Jira issue with comments."""
        # Arrange
        request = JiraIssueRequest(
            project_id="TEST",
            key="TEST-123",
            summary="Issue with comments",
            description="Description",
            comments=["Comment 1", "Comment 2"],
        )
        expected_response = JiraIssueResponse(key="TEST-123")

        with (
            patch("awa.core.activities.jira._execute_issue_request", return_value=expected_response) as mock_execute,
            patch("awa.core.activities.jira._add_comment") as mock_add_comment,
        ):
            # Act
            result = await activity_env.run(upsert_jira_issue, request)

            # Assert
            assert result == "TEST-123"
            mock_execute.assert_called_once()
            assert mock_add_comment.call_count == 2
            mock_add_comment.assert_any_call("TEST-123", "Comment 1")
            mock_add_comment.assert_any_call("TEST-123", "Comment 2")

    @pytest.mark.asyncio
    async def test_add_jira_comment_success(self, activity_env: ActivityEnvironment) -> None:
        """Test successful addition of comments to a Jira issue."""
        # Arrange
        request = JiraIssueRequest(
            project_id="TEST",
            key="TEST-123",
            comments=["Comment 1", "Comment 2"],
        )

        with patch("awa.core.activities.jira._add_comment") as mock_add_comment:
            # Act
            await activity_env.run(add_jira_comment, request)

            # Assert
            assert mock_add_comment.call_count == 2
            mock_add_comment.assert_any_call("TEST-123", "Comment 1")
            mock_add_comment.assert_any_call("TEST-123", "Comment 2")

    @pytest.mark.asyncio
    async def test_add_jira_comment_missing_key(self, activity_env: ActivityEnvironment) -> None:
        """Test adding comments without a key raises FatalApplicationError."""
        # Arrange
        request = JiraIssueRequest(
            project_id="TEST",
            key=None,
            comments=["Comment 1"],
        )

        # Act & Assert
        with pytest.raises(FatalApplicationError, match="Jira issue key is required to add a comment"):
            await activity_env.run(add_jira_comment, request)


class TestJiraHelperFunctions:
    """Test cases for Jira helper functions."""

    @pytest.mark.asyncio
    async def test_add_comment_success(self) -> None:
        """Test successful comment addition."""
        # Arrange
        key = "TEST-123"
        comment = "This is a test comment"
        expected_response = JiraIssueResponse(key=key)

        with patch("awa.core.activities.jira._execute_issue_request", return_value=expected_response) as mock_execute:
            # Act
            await _add_comment(key, comment)

            # Assert
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert call_args[1]["method"] == "POST"
            assert call_args[1]["url_suffix"] == "/TEST-123/comment"

            # Verify the request body structure
            body_json = call_args[1]["body_json"]
            body = json.loads(body_json)
            assert "body" in body

    @pytest.mark.asyncio
    async def test_execute_issue_request_success(self) -> None:
        """Test successful HTTP request execution."""
        # Arrange
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "key": "TEST-123",
            "fields": {
                "summary": "Test issue",
                "issuetype": {"name": "Story"},
            },
            "renderedFields": {
                "description": "Test description",
            },
        }

        mock_config = MagicMock()
        mock_config.jira.url = "https://test.atlassian.net"
        mock_config.jira.api_user = "test@test.com"
        mock_config.jira.api_key = "test-api-key"

        with (
            patch("awa.core.activities.jira.ConfigLoader.get_config", return_value=mock_config),
            patch("httpx.AsyncClient") as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            result = await _execute_issue_request(
                method="GET",
                url_suffix="/TEST-123",
                query_params={"expand": "renderedFields"},
            )

            # Assert
            assert result.key == "TEST-123"
            assert result.summary == "Test issue"
            assert result.issue_type == "Story"
            assert result.description == "Test description"

            mock_client.request.assert_called_once_with(
                method="GET",
                url="https://test.atlassian.net/rest/api/2/issue/TEST-123",
                content=None,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                auth=("test@test.com", "test-api-key"),
                params={"expand": "renderedFields"},
            )

    @pytest.mark.asyncio
    async def test_execute_issue_request_no_jira_config(self) -> None:
        """Test request execution with no Jira configuration."""
        # Arrange
        mock_config = MagicMock()
        mock_config.jira = None

        with (
            patch("awa.core.activities.jira.ConfigLoader.get_config", return_value=mock_config),
            pytest.raises(RetryableApplicationError, match="Jira is not configured"),
        ):
            # Act & Assert
            await _execute_issue_request(method="GET")

    @pytest.mark.asyncio
    async def test_execute_issue_request_missing_url(self) -> None:
        """Test request execution with missing URL."""
        # Arrange
        mock_config = MagicMock()
        mock_config.jira.url = None
        mock_config.jira.api_user = "test@test.com"
        mock_config.jira.api_key = "test-api-key"

        with (
            patch("awa.core.activities.jira.ConfigLoader.get_config", return_value=mock_config),
            pytest.raises(RetryableApplicationError, match="Jira URL is not configured"),
        ):
            # Act & Assert
            await _execute_issue_request(method="GET")

    @pytest.mark.asyncio
    async def test_execute_issue_request_missing_api_user(self) -> None:
        """Test request execution with missing API user."""
        # Arrange
        mock_config = MagicMock()
        mock_config.jira.url = "https://test.atlassian.net"
        mock_config.jira.api_user = None
        mock_config.jira.api_key = "test-api-key"

        with (
            patch("awa.core.activities.jira.ConfigLoader.get_config", return_value=mock_config),
            pytest.raises(RetryableApplicationError, match="Jira API user is not configured"),
        ):
            # Act & Assert
            await _execute_issue_request(method="GET")

    @pytest.mark.asyncio
    async def test_execute_issue_request_missing_api_key(self) -> None:
        """Test request execution with missing API key."""
        # Arrange
        mock_config = MagicMock()
        mock_config.jira.url = "https://test.atlassian.net"
        mock_config.jira.api_user = "test@test.com"
        mock_config.jira.api_key = None

        with (
            patch("awa.core.activities.jira.ConfigLoader.get_config", return_value=mock_config),
            pytest.raises(RetryableApplicationError, match="Jira API key is not configured"),
        ):
            # Act & Assert
            await _execute_issue_request(method="GET")

    @pytest.mark.asyncio
    async def test_execute_issue_request_http_error(self) -> None:
        """Test request execution with HTTP 4xx error (non-retryable)."""
        # Arrange
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Not found"}

        mock_config = MagicMock()
        mock_config.jira.url = "https://test.atlassian.net"
        mock_config.jira.api_user = "test@test.com"
        mock_config.jira.api_key = "test-api-key"

        with (
            patch("awa.core.activities.jira.ConfigLoader.get_config", return_value=mock_config),
            patch("httpx.AsyncClient") as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act & Assert
            with pytest.raises(FatalApplicationError, match="Failed to create requested Jira issue"):
                await _execute_issue_request(method="GET")

    @pytest.mark.asyncio
    async def test_execute_issue_request_http_5xx_error(self) -> None:
        """Test request execution with HTTP 5xx error (retryable)."""
        # Arrange
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 503
        mock_response.json.return_value = {"error": "Service unavailable"}

        mock_config = MagicMock()
        mock_config.jira.url = "https://test.atlassian.net"
        mock_config.jira.api_user = "test@test.com"
        mock_config.jira.api_key = "test-api-key"

        with (
            patch("awa.core.activities.jira.ConfigLoader.get_config", return_value=mock_config),
            patch("httpx.AsyncClient") as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act & Assert
            with pytest.raises(RetryableApplicationError, match="Failed to create requested Jira issue"):
                await _execute_issue_request(method="GET")

    @pytest.mark.asyncio
    async def test_execute_issue_request_api_v2_url(self) -> None:
        """Test that the API v2 URL is used correctly."""
        # Arrange
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {"key": "TEST-123"}

        mock_config = MagicMock()
        mock_config.jira.url = "https://test.atlassian.net"
        mock_config.jira.api_user = "test@test.com"
        mock_config.jira.api_key = "test-api-key"

        with (
            patch("awa.core.activities.jira.ConfigLoader.get_config", return_value=mock_config),
            patch("httpx.AsyncClient") as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            await _execute_issue_request(method="GET", url_suffix="/TEST-123")

            # Assert
            mock_client.request.assert_called_once()
            call_args = mock_client.request.call_args
            assert call_args[1]["url"] == "https://test.atlassian.net/rest/api/2/issue/TEST-123"

    @pytest.mark.asyncio
    async def test_execute_issue_request_response_parsing_edge_cases(self) -> None:
        """Test parsing of various response formats."""
        # Arrange
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "key": "TEST-123",
            # Missing fields
        }

        mock_config = MagicMock()
        mock_config.jira.url = "https://test.atlassian.net"
        mock_config.jira.api_user = "test@test.com"
        mock_config.jira.api_key = "test-api-key"

        with (
            patch("awa.core.activities.jira.ConfigLoader.get_config", return_value=mock_config),
            patch("httpx.AsyncClient") as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            result = await _execute_issue_request(method="GET")

            # Assert
            assert result.key == "TEST-123"
            assert result.summary is None
            assert result.issue_type is None
            assert result.description is None

    @pytest.mark.asyncio
    async def test_execute_issue_request_response_with_partial_fields(self) -> None:
        """Test parsing response with partial field data."""
        # Arrange
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "key": "TEST-123",
            "fields": {
                "summary": "Test issue",
                # Missing issuetype
            },
            "renderedFields": {
                # Missing description
            },
        }

        mock_config = MagicMock()
        mock_config.jira.url = "https://test.atlassian.net"
        mock_config.jira.api_user = "test@test.com"
        mock_config.jira.api_key = "test-api-key"

        with (
            patch("awa.core.activities.jira.ConfigLoader.get_config", return_value=mock_config),
            patch("httpx.AsyncClient") as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            result = await _execute_issue_request(method="GET")

            # Assert
            assert result.key == "TEST-123"
            assert result.summary == "Test issue"
            assert result.issue_type is None
            assert result.description is None

    @pytest.mark.asyncio
    async def test_add_comment_with_markdown_conversion(self) -> None:
        """Test that comments are properly converted from markdown to wiki format."""
        # Arrange
        key = "TEST-123"
        comment = "**Bold text** and `code`"
        expected_response = JiraIssueResponse(key=key)

        with (
            patch("awa.core.activities.jira._execute_issue_request", return_value=expected_response) as mock_execute,
            patch("awa.core.activities.jira.convert_markdown_to_jira_wiki_format") as mock_convert,
        ):
            mock_convert.return_value = "*Bold text* and {{code}}"

            # Act
            await _add_comment(key, comment)

            # Assert
            mock_convert.assert_called_once_with(comment)
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            body_json = call_args[1]["body_json"]
            body = json.loads(body_json)
            assert body["body"] == "*Bold text* and {{code}}"

    @pytest.mark.asyncio
    async def test_add_comment_empty_comment(self) -> None:
        """Test adding an empty comment."""
        # Arrange
        key = "TEST-123"
        comment = ""
        expected_response = JiraIssueResponse(key=key)

        with (
            patch("awa.core.activities.jira._execute_issue_request", return_value=expected_response) as mock_execute,
            patch("awa.core.activities.jira.convert_markdown_to_jira_wiki_format") as mock_convert,
        ):
            mock_convert.return_value = ""

            # Act
            await _add_comment(key, comment)

            # Assert
            mock_convert.assert_called_once_with(comment)
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            body_json = call_args[1]["body_json"]
            body = json.loads(body_json)
            assert body["body"] == ""

    def test_build_request_body_basic(self) -> None:
        """Test building request body with basic fields."""
        # Arrange
        request = JiraIssueRequest(
            project_id="TEST",
            summary="Test issue",
            description="Test description",
        )

        with patch("awa.core.activities.jira.convert_markdown_to_jira_wiki_format") as mock_convert:
            mock_convert.return_value = "Test description"

            # Act
            result = _build_request_body(request)

            # Assert
            assert result["fields"]["summary"] == "Test issue"
            assert result["fields"]["project"]["key"] == "TEST"
            assert result["fields"]["issuetype"]["name"] == "Story"
            mock_convert.assert_called_once_with("Test description")

    def test_build_request_body_with_all_fields(self) -> None:
        """Test building request body with all fields."""
        # Arrange
        request = JiraIssueRequest(
            project_id="TEST",
            summary="Test issue",
            description="Test description",
            issue_type="Bug",
            parent="TEST-100",
            tags=["tag1", "tag2"],
        )

        with patch("awa.core.activities.jira.convert_markdown_to_jira_wiki_format") as mock_convert:
            mock_convert.return_value = "Test description"

            # Act
            result = _build_request_body(request)

            # Assert
            assert result["fields"]["summary"] == "Test issue"
            assert result["fields"]["project"]["key"] == "TEST"
            assert result["fields"]["issuetype"]["name"] == "Bug"
            assert result["fields"]["parent"]["key"] == "TEST-100"
            assert result["fields"]["labels"] == ["tag1", "tag2"]
            mock_convert.assert_called_once_with("Test description")

    def test_determine_issue_type_explicit(self) -> None:
        """Test determining issue type when explicitly set."""
        # Arrange
        request = JiraIssueRequest(
            project_id="TEST",
            issue_type="Epic",
        )

        # Act
        result = _determine_issue_type(request)

        # Assert
        assert result == "Epic"

    def test_determine_issue_type_with_parent(self) -> None:
        """Test determining issue type with parent (should be Subtask)."""
        # Arrange
        request = JiraIssueRequest(
            project_id="TEST",
            parent="TEST-100",
        )

        # Act
        result = _determine_issue_type(request)

        # Assert
        assert result == "Subtask"

    def test_determine_issue_type_default(self) -> None:
        """Test determining issue type with defaults."""
        # Arrange
        request = JiraIssueRequest(
            project_id="TEST",
        )

        # Act
        result = _determine_issue_type(request)

        # Assert
        assert result == "Story"


class TestMarkdownToJiraWikiConversion:
    """Test cases for markdown to Jira Wiki format conversion functions."""

    def test_convert_markdown_to_jira_wiki_format_empty(self) -> None:
        """Test converting empty markdown string."""
        # Act
        result = convert_markdown_to_jira_wiki_format("")

        # Assert
        assert result == ""

    def test_convert_markdown_to_jira_wiki_format_none(self) -> None:
        """Test converting None markdown string."""
        # Act
        result = convert_markdown_to_jira_wiki_format(None)

        # Assert
        assert result == ""

    def test_convert_markdown_to_jira_wiki_format_headings(self) -> None:
        """Test converting markdown headings to Jira format."""
        # Arrange
        markdown = "# Heading 1\n## Heading 2\n### Heading 3"

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = "h1. Heading 1\nh2. Heading 2\nh3. Heading 3"
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_bold_italic(self) -> None:
        """Test converting bold and italic text."""
        # Arrange
        markdown = "**bold text** and *italic text* and __bold__ and _italic_"

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = "*bold text* and _italic text_ and *bold* and _italic_"
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_strikethrough(self) -> None:
        """Test converting strikethrough text."""
        # Arrange
        markdown = "~~strikethrough text~~"

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = "-strikethrough text-"
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_inline_code(self) -> None:
        """Test converting inline code."""
        # Arrange
        markdown = "Use `code` in text"

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = "Use {{code}} in text"
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_code_blocks(self) -> None:
        """Test converting code blocks."""
        # Arrange
        markdown = "```python\nprint('hello')\n```"

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = "{code:python}\nprint('hello')\n{code}"
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_code_blocks_no_language(self) -> None:
        """Test converting code blocks without language."""
        # Arrange
        markdown = "```\nsome code\n```"

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = "{code}\nsome code\n{code}"
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_lists(self) -> None:
        """Test converting lists."""
        # Arrange
        markdown = "- Item 1\n- Item 2\n  - Nested item\n1. Numbered item"

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = "* Item 1\n* Item 2\n** Nested item\n# Numbered item"
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_checkbox_lists(self) -> None:
        """Test converting checkbox lists."""
        # Arrange
        markdown = "- [ ] Unchecked\n- [x] Checked"

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = "* (/) Unchecked\n* (/) Checked"
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_links(self) -> None:
        """Test converting links."""
        # Arrange
        markdown = "[Link text](https://example.com)"

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = "[Link text|https://example.com]"
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_images(self) -> None:
        """Test converting images."""
        # Arrange
        markdown = "![Alt text](https://example.com/image.png)"

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = "![Alt text|https://example.com/image.png]"
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_horizontal_rules(self) -> None:
        """Test converting horizontal rules."""
        # Arrange
        markdown = "---\nText\n***"

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = "----\nText\n----"
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_blockquotes(self) -> None:
        """Test converting blockquotes."""
        # Arrange
        markdown = "> This is a quote"

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = "bq. This is a quote"
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_tables(self) -> None:
        """Test converting tables."""
        # Arrange
        markdown = "| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |"

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = "||Header 1||Header 2||\n|Cell 1|Cell 2|"
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_complex_mixed(self) -> None:
        """Test converting complex mixed markdown content."""
        # Arrange
        markdown = """# Title

**Bold text** and *italic text*

- List item 1
- List item 2

```python
print('hello')
```

> Quote here

| Column | Value |
|--------|-------|
| Test   | Data  |"""

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = """h1. Title

*Bold text* and _italic text_

* List item 1
* List item 2

{code:python}
print('hello')
{code}

bq. Quote here

||Column||Value||
|Test|Data|"""
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_nested_code_blocks(self) -> None:
        """Test converting markdown with nested code blocks and inline code."""
        # Arrange
        markdown = """Here's some text with `inline code`.

```python
def example():
    return "This has `nested` code"
```

More text with `more inline code`."""

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = """Here's some text with {{inline code}}.

{code:python}
def example():
    return "This has `nested` code"
{code}

More text with {{more inline code}}."""
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_malformed_code_blocks(self) -> None:
        """Test converting markdown with malformed code blocks."""
        # Arrange
        markdown = """```python
def example():
    return "unclosed code block

More text here."""

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = """{code:python}
def example():
    return "unclosed code block

More text here."""
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_complex_formatting(self) -> None:
        """Test converting markdown with complex nested formatting."""
        # Arrange
        markdown = """**Bold with *italic inside* text**

~~Strikethrough with **bold**~~

> Quote with **bold**"""

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = """*Bold with _italic inside_ text*

-Strikethrough with *bold*-

bq. Quote with *bold*"""
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_nested_bold_with_italic_and_strikethrough(self) -> None:
        """Test converting markdown with bold containing both italic and strikethrough."""
        # Arrange
        markdown = "**bold, *italic* ~~strikethrough~~ text**"

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = "*bold, _italic_ -strikethrough- text*"
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_table_edge_cases(self) -> None:
        """Test converting markdown tables with edge cases."""
        # Arrange
        markdown = """| Header | Header 2 |
|--------|---------|
| Cell   | Cell 2  |
| Cell 3 |         |"""

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = """||Header||Header 2||
|Cell|Cell 2|
|Cell 3||"""
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_mixed_list_types(self) -> None:
        """Test converting markdown with mixed list types."""
        # Arrange
        markdown = """- Bullet item 1
1. Numbered item 1
- [ ] Checkbox item
- Bullet item 2
2. Numbered item 2
- [x] Checked item"""

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = """* Bullet item 1
# Numbered item 1
* (/) Checkbox item
* Bullet item 2
# Numbered item 2
* (/) Checked item"""
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_whitespace_handling(self) -> None:
        """Test converting markdown with various whitespace scenarios."""
        # Arrange
        markdown = """   # Heading with leading spaces
**Bold**   with   extra   spaces
-   List   item   with   spaces
>   Quote   with   spaces"""

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = """   # Heading with leading spaces
*Bold*   with   extra   spaces
* List   item   with   spaces
bq. Quote   with   spaces"""
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_special_characters(self) -> None:
        """Test converting markdown with special characters."""
        # Arrange
        markdown = """**Bold with special chars: @#$%^&*()**

`code with special chars: @#$%^&*()`

> Quote with special chars: @#$%^&*()"""

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = """*Bold with special chars: @#$%^&*()*

{{code with special chars: @#$%^&*()}}

bq. Quote with special chars: @#$%^&*()"""
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_empty_code_block(self) -> None:
        """Test converting markdown with empty code blocks."""
        # Arrange
        markdown = """```python

```

```javascript
// Empty code block
```"""

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = """{code:python}

{code}

{code:javascript}
// Empty code block
{code}"""
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_unicode_characters(self) -> None:
        """Test converting markdown with unicode characters."""
        # Arrange
        markdown = """**Bold with unicode: éñçüöä**

`code with unicode: éñçüöä`

> Quote with unicode: éñçüöä"""

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = """*Bold with unicode: éñçüöä*

{{code with unicode: éñçüöä}}

bq. Quote with unicode: éñçüöä"""
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_multiple_horizontal_rules(self) -> None:
        """Test converting markdown with multiple horizontal rules."""
        # Arrange
        markdown = """First section
---
Second section
***
Third section
___"""

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = """First section
----
Second section
----
Third section
----"""
        assert result == expected

    def test_convert_markdown_to_jira_wiki_format_complex_nested_lists(self) -> None:
        """Test converting markdown with complex nested lists."""
        # Arrange
        markdown = """- Level 1
  - Level 2
    - Level 3
      - Level 4
1. Numbered Level 1
   1. Numbered Level 2
      - Mixed Level 3
        - Mixed Level 4"""

        # Act
        result = convert_markdown_to_jira_wiki_format(markdown)

        # Assert
        expected = """* Level 1
** Level 2
*** Level 3
**** Level 4
# Numbered Level 1
## Numbered Level 2
**** Mixed Level 3
***** Mixed Level 4"""
        assert result == expected

    def test_build_request_body_with_empty_description(self) -> None:
        """Test building request body with empty description."""
        # Arrange
        request = JiraIssueRequest(
            project_id="TEST",
            summary="Test issue",
            description="",
        )

        with patch("awa.core.activities.jira.convert_markdown_to_jira_wiki_format") as mock_convert:
            mock_convert.return_value = ""

            # Act
            result = _build_request_body(request)

            # Assert
            assert result["fields"]["summary"] == "Test issue"
            assert result["fields"]["description"] == ""
            mock_convert.assert_called_once_with("")

    def test_build_request_body_with_none_description(self) -> None:
        """Test building request body with None description."""
        # Arrange
        request = JiraIssueRequest(
            project_id="TEST",
            summary="Test issue",
            description=None,
        )

        with patch("awa.core.activities.jira.convert_markdown_to_jira_wiki_format") as mock_convert:
            mock_convert.return_value = ""

            # Act
            result = _build_request_body(request)

            # Assert
            assert result["fields"]["summary"] == "Test issue"
            assert result["fields"]["description"] == ""
            mock_convert.assert_called_once_with(None)

    def test_build_request_body_without_optional_fields(self) -> None:
        """Test building request body without optional fields."""
        # Arrange
        request = JiraIssueRequest(
            project_id="TEST",
            summary="Test issue",
            description="Test description",
            # No tags, parent, or issue_type
        )

        with patch("awa.core.activities.jira.convert_markdown_to_jira_wiki_format") as mock_convert:
            mock_convert.return_value = "Test description"

            # Act
            result = _build_request_body(request)

            # Assert
            assert result["fields"]["summary"] == "Test issue"
            assert result["fields"]["project"]["key"] == "TEST"
            assert result["fields"]["issuetype"]["name"] == "Story"
            assert "labels" not in result["fields"]
            assert result["fields"]["parent"] == {}  # Parent is always included as empty dict

    def test_determine_issue_type_with_empty_string(self) -> None:
        """Test determining issue type with empty string."""
        # Arrange
        request = JiraIssueRequest(
            project_id="TEST",
            issue_type="",
        )

        # Act
        result = _determine_issue_type(request)

        # Assert
        assert result == "Story"  # Should default to Story even with empty string

    def test_determine_issue_type_with_whitespace(self) -> None:
        """Test determining issue type with whitespace-only string."""
        # Arrange
        request = JiraIssueRequest(
            project_id="TEST",
            issue_type="   ",
        )

        # Act
        result = _determine_issue_type(request)

        # Assert
        assert result == "   "  # Whitespace is preserved as-is
