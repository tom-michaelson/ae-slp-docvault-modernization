from pathlib import Path

from temporalio import workflow

from sdk_dist.python.awa.client import awa_activity


@workflow.defn(name="truncate-files")
class TruncateFilesWorkflow:
    """Workflow to create truncated copies of files for classification."""

    @workflow.run
    async def run(
        self,
        source_files: list[str],
        destination_path: str,
        max_content_length: int = 5000,
    ) -> list[str]:
        """Create truncated copies of files for classification.

        This workflow reads each source file and creates a copy with only the first
        max_content_length characters, which is useful for AI classification tasks
        where we don't need the entire file content.

        Args:
            source_files: List of source file paths to truncate
            destination_path: Directory where truncated files will be saved
            max_content_length: Maximum number of characters to keep from each file

        Returns:
            List of paths to the truncated files

        """
        workflow.logger.info(f"Creating truncated copies of {len(source_files)} files")

        truncated_files = []

        for source_file in source_files:
            source_path = Path(source_file)

            # Preserve directory structure in destination
            relative_path = source_path.name
            if source_path.parent.name:
                # If the file is in a subdirectory, maintain that structure
                relative_parts = []
                current = source_path.parent
                while current.name and current != source_path.parent.parent:
                    relative_parts.insert(0, current.name)
                    current = current.parent
                if relative_parts:
                    relative_path = Path(*relative_parts) / source_path.name

            dest_file_path = Path(destination_path) / relative_path

            try:
                # Read the source file using AWA SDK
                content = await awa_activity.read_file(source_file, default="")

                # Truncate the content
                truncated_content = content[:max_content_length]

                # Write truncated content to destination using AWA SDK
                await awa_activity.write_file(str(dest_file_path), truncated_content)

                truncated_files.append(str(dest_file_path))
                workflow.logger.debug(f"Truncated {source_file} -> {dest_file_path}")

            except (OSError, UnicodeError) as e:
                workflow.logger.warning(f"Failed to truncate {source_file}: {e}")
                # Still add the original file path if truncation fails
                truncated_files.append(source_file)

        workflow.logger.info(f"Successfully created {len(truncated_files)} truncated files")
        return truncated_files
