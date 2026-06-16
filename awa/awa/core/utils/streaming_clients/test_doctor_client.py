"""Streaming client for Test Doctor workflow."""

from awa.core.utils.agent_streaming_utils import AgentExecutionStatus, AgentStreaming, FileStatus


class TestDoctorStreaming:
    """Streaming utilities specifically for the Test Doctor workflow.

    Events are emitted to the session_id provided. If a parent_session_id is also provided,
    events will be emitted to both child and parent sessions for consolidated viewing.
    """

    def __init__(
        self,
        session_id: str | None,
        parent_session_id: str | None = None,
    ) -> None:
        """Initialize with session ID.

        Args:
            session_id: Session ID for this workflow
            parent_session_id: Optional parent session ID (if provided, emits to both)

        """
        self.session_id = session_id
        self.parent_session_id = parent_session_id

    def _get_session_ids(self) -> list[str]:
        """Get all session IDs to emit to (child and optionally parent).

        Returns:
            List of session IDs to emit events to

        """
        session_ids = []

        # Always emit to child session if it exists
        if self.session_id:
            session_ids.append(self.session_id)

        # Also emit to parent session if it exists and differs from child
        if self.parent_session_id and self.parent_session_id != self.session_id:
            session_ids.append(self.parent_session_id)

        return session_ids

    async def file_started(self, file_path: str) -> None:
        """Publish that file processing has started."""
        await AgentStreaming.publish_file_processed_multi(
            self._get_session_ids(),
            file_path,
            FileStatus.STARTED.value,
            "Beginning test generation pipeline",
        )

    async def file_completed(self, file_path: str) -> None:
        """Publish that file processing has completed."""
        await AgentStreaming.publish_file_processed_multi(
            self._get_session_ids(),
            file_path,
            FileStatus.COMPLETED.value,
            "Test generation pipeline completed successfully",
        )

    async def file_skipped(self, file_path: str, reason: str) -> None:
        """Publish that file was skipped."""
        await AgentStreaming.publish_file_processed_multi(
            self._get_session_ids(),
            file_path,
            FileStatus.SKIPPED.value,
            reason,
        )

    async def generator_started(self, file_path: str) -> None:
        """Publish that test generator agent has started."""
        await AgentStreaming.publish_agent_execution_multi(
            self._get_session_ids(),
            "TestGenerator",
            "Generate unit tests",
            file_path,
            AgentExecutionStatus.STARTED.value,
        )

    async def generator_completed(self, file_path: str) -> None:
        """Publish that test generator agent has completed."""
        await AgentStreaming.publish_agent_execution_multi(
            self._get_session_ids(),
            "TestGenerator",
            "Generate unit tests",
            file_path,
            AgentExecutionStatus.COMPLETED.value,
            "Tests generated successfully",
        )

    async def generator_failed(self, file_path: str, error: str) -> None:
        """Publish that test generator agent has failed."""
        await AgentStreaming.publish_agent_execution_multi(
            self._get_session_ids(),
            "TestGenerator",
            "Generate unit tests",
            file_path,
            AgentExecutionStatus.FAILED.value,
            error,
        )

    async def linter_started(self, file_path: str) -> None:
        """Publish that test linter agent has started."""
        await AgentStreaming.publish_agent_execution_multi(
            self._get_session_ids(),
            "TestLinter",
            "Lint and validate tests",
            file_path,
            AgentExecutionStatus.STARTED.value,
        )

    async def linter_completed(self, file_path: str) -> None:
        """Publish that test linter agent has completed."""
        await AgentStreaming.publish_agent_execution_multi(
            self._get_session_ids(),
            "TestLinter",
            "Lint and validate tests",
            file_path,
            AgentExecutionStatus.COMPLETED.value,
            "Tests linted and validated successfully",
        )

    async def linter_failed(self, file_path: str, error: str) -> None:
        """Publish that test linter agent has failed."""
        await AgentStreaming.publish_agent_execution_multi(
            self._get_session_ids(),
            "TestLinter",
            "Lint and validate tests",
            file_path,
            AgentExecutionStatus.FAILED.value,
            error,
        )

    async def workflow_started(self, total_files: int) -> None:
        """Publish that the main workflow has started."""
        await AgentStreaming.publish_step_start_multi(
            self._get_session_ids(),
            "test-doctor",
            f"Starting test generation for {total_files} files",
        )

    async def workflow_completed(self, processed_files: int) -> None:
        """Publish that the main workflow has completed."""
        await AgentStreaming.publish_step_complete_multi(
            self._get_session_ids(),
            "test-doctor",
            f"Successfully processed {processed_files} files",
        )

    async def progress_update(self, current: int, total: int) -> None:
        """Publish progress update."""
        await AgentStreaming.publish_progress_multi(
            self._get_session_ids(),
            current,
            total,
            "Files processed",
        )

    async def git_diff_started(self) -> None:
        """Publish that git diff analysis has started."""
        await AgentStreaming.publish_step_start_multi(
            self._get_session_ids(),
            "GitDiffAnalysis",
            "Analyzing changes between branches",
        )

    async def git_diff_completed(self, file_count: int) -> None:
        """Publish that git diff analysis has completed."""
        await AgentStreaming.publish_step_complete_multi(
            self._get_session_ids(),
            "GitDiffAnalysis",
            f"Found {file_count} changed files",
        )

    async def filtering_started(self) -> None:
        """Publish that file filtering has started."""
        await AgentStreaming.publish_step_start_multi(
            self._get_session_ids(),
            "FileFiltering",
            "Filtering testable files",
        )

    async def filtering_completed(self, testable_count: int, total_count: int) -> None:
        """Publish that file filtering has completed."""
        await AgentStreaming.publish_step_complete_multi(
            self._get_session_ids(),
            "FileFiltering",
            f"Identified {testable_count} testable files out of {total_count} changed files",
        )
