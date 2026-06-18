"""Remote File IO Workflow.

This workflow demonstrates how to use AWA's file IO activities with remote storage systems
including AWS S3.
"""

from temporalio import workflow

from cookbook.recipes.decorators.recipe_exposed import recipe_exposed
from sdk_dist.python.awa.client import awa_activity

with workflow.unsafe.imports_passed_through():
    from .models.remote_file_io_models import (
        FileOperationResult,
        RemoteFileIOWorkflowInput,
        RemoteFileIOWorkflowOutput,
        RemoteStorageType,
    )


@recipe_exposed("Demonstrates remote file IO operations with AWS S3")
@workflow.defn(name="remote-file-io")
class RemoteFileIOWorkflow:
    """Workflow demonstrating remote file IO operations across different storage providers.

    This workflow uses a fail-fast approach: if any critical operation fails (typically due
    to authentication or configuration issues), the entire workflow fails immediately.
    This provides clear feedback for test/demo scenarios.
    """

    @workflow.run
    async def run(self, workflow_input: RemoteFileIOWorkflowInput) -> RemoteFileIOWorkflowOutput:
        """Execute remote file IO operations to demonstrate functionality.

        Args:
            workflow_input: The workflow input containing storage configuration

        Returns:
            RemoteFileIOWorkflowOutput with operation results

        Raises:
            ActivityError: If any file operation fails (auth, permissions, etc.)

        """
        workflow.logger.info(
            f"Starting remote file IO workflow for {workflow_input.storage_type} at {workflow_input.remote_base_path}",
        )

        operations: list[FileOperationResult] = []

        # Prepare remote paths based on storage type
        remote_paths = self._prepare_remote_paths(workflow_input)

        # 1. Write a test file - if this fails, the workflow should fail immediately
        # This is a test workflow - we want fast feedback on configuration issues
        workflow.logger.info(f"Writing test file to: {remote_paths['test_file']}")
        await awa_activity.write_file(
            remote_paths["test_file"],
            workflow_input.test_content,
        )
        operations.append(
            FileOperationResult(
                operation="write_file",
                success=True,
                path=remote_paths["test_file"],
                message=f"Successfully wrote {len(workflow_input.test_content)} bytes to remote file",
            ),
        )

        # 2. Read the test file back
        workflow.logger.info(f"Reading test file from: {remote_paths['test_file']}")
        content = await awa_activity.read_file(remote_paths["test_file"])
        operations.append(
            FileOperationResult(
                operation="read_file",
                success=True,
                path=remote_paths["test_file"],
                message=f"Successfully read {len(content)} bytes from remote file",
                data=content[:100] + "..." if len(content) > 100 else content,  # noqa: PLR2004
            ),
        )

        # 3. Create test directory structure with multiple files
        test_files = self._get_test_files(remote_paths["test_directory"], workflow_input.test_content)
        for file_path, file_content in test_files:
            workflow.logger.info(f"Creating file in directory: {file_path}")
            await awa_activity.write_file(file_path, file_content)
            operations.append(
                FileOperationResult(
                    operation="create_directory_file",
                    success=True,
                    path=file_path,
                    message=f"Successfully created file with {len(file_content)} bytes",
                ),
            )

        # 4. List directory contents
        workflow.logger.info(f"Listing directory contents: {remote_paths['test_directory']}")
        files = await awa_activity.list_directory(remote_paths["test_directory"])
        operations.append(
            FileOperationResult(
                operation="list_directory",
                success=True,
                path=remote_paths["test_directory"],
                message=f"Successfully listed directory with {len(files)} items",
                data=files,
            ),
        )

        # 5. Read entire directory
        workflow.logger.info(f"Reading all files in directory: {remote_paths['test_directory']}")
        file_contents = await awa_activity.read_directory(remote_paths["test_directory"])
        # Convert list of file dictionaries to a summary format for display
        file_summaries = []
        for file_info in file_contents:
            if isinstance(file_info, dict) and "file" in file_info and "content" in file_info:
                content = file_info["content"]
                preview = content[:50] + "..." if len(content) > 50 else content  # noqa: PLR2004
                file_summaries.append(f"File: {file_info['file']}\nContent preview: {preview}")
            else:
                # Handle unexpected format
                file_summaries.append(str(file_info))

        operations.append(
            FileOperationResult(
                operation="read_directory",
                success=True,
                path=remote_paths["test_directory"],
                message=f"Successfully read {len(file_contents)} files from directory",
                data=file_summaries,
            ),
        )

        # 6. Cleanup if requested
        if workflow_input.cleanup_after_test:
            workflow.logger.info("Cleanup requested - files will remain for manual verification")
            operations.append(
                FileOperationResult(
                    operation="cleanup",
                    success=True,
                    path=workflow_input.remote_base_path,
                    message="Cleanup skipped - files preserved for manual verification",
                ),
            )

        # Generate summary
        summary = self._generate_summary(operations, workflow_input)

        return RemoteFileIOWorkflowOutput(
            storage_type=workflow_input.storage_type,
            remote_base_path=workflow_input.remote_base_path,
            operations=operations,
            summary=summary,
        )

    def _prepare_remote_paths(self, workflow_input: RemoteFileIOWorkflowInput) -> dict[str, str]:
        """Prepare remote paths based on storage type and base path.

        Args:
            workflow_input: Workflow input

        Returns:
            Dictionary of prepared remote paths

        """
        base_path = workflow_input.remote_base_path.rstrip("/")

        # Ensure base path has correct protocol prefix
        if workflow_input.storage_type == RemoteStorageType.AWS_S3 and not base_path.startswith("s3://"):
            workflow.logger.warning("S3 path should start with s3:// - path may not work correctly")

        return {
            "test_file": f"{base_path}/{workflow_input.test_file_name}",
            "test_directory": f"{base_path}/{workflow_input.test_directory_name}",
        }

    def _get_test_files(self, base_path: str, content: str) -> list[tuple[str, str]]:
        """Generate test files for directory structure.

        Args:
            base_path: Base directory path
            content: Base content for files

        Returns:
            List of (file_path, file_content) tuples

        """
        test_files = [
            "readme.md",
            "data/file1.txt",
            "data/file2.txt",
            "config/settings.json",
        ]

        files = []
        for file_name in test_files:
            file_path = f"{base_path}/{file_name}"
            file_content = f"{content}\nFile: {file_name}"

            if file_name.endswith(".json"):
                file_content = '{"message": "' + content + '", "file": "' + file_name + '"}'

            files.append((file_path, file_content))

        return files

    def _generate_summary(
        self,
        operations: list[FileOperationResult],
        workflow_input: RemoteFileIOWorkflowInput,
    ) -> str:
        """Generate a summary of operations performed.

        Args:
            operations: List of operation results
            workflow_input: Workflow input

        Returns:
            Summary string

        """
        total_ops = len(operations)
        successful_ops = sum(1 for op in operations if op.success)
        failed_ops = total_ops - successful_ops

        summary_lines = [
            f"Remote File IO Test Summary for {workflow_input.storage_type.value}",
            f"Base Path: {workflow_input.remote_base_path}",
            f"Total Operations: {total_ops}",
            f"Successful: {successful_ops}",
            f"Failed: {failed_ops}",
            "",
            "Operations performed:",
        ]

        for op in operations:
            status = "✓" if op.success else "✗"
            summary_lines.append(f"  {status} {op.operation}: {op.message}")

        if failed_ops > 0:
            summary_lines.extend(
                [
                    "",
                    "Note: Some operations failed. Please check:",
                    "1. Remote storage credentials are configured",
                    "2. The base path exists and is accessible",
                    "3. Required permissions are granted",
                ],
            )
        else:
            summary_lines.extend(
                [
                    "",
                    "✓ All operations completed successfully!",
                    "Remote file IO is working correctly for this storage provider.",
                ],
            )

        return "\n".join(summary_lines)
