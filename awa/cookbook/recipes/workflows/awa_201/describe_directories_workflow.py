import os
from pathlib import Path

from pydantic import BaseModel
from temporalio import workflow

from cookbook.recipes import constants
from cookbook.recipes.models.chunking import ChunkAndSummarizeInput, ChunkingStrategy
from cookbook.recipes.workflows.common.chunk_and_summarize_workflow import ChunkAndSummarizeWorkflow
from sdk_dist.python.awa.client import awa_activity, awa_workflow
from sdk_dist.python.awa.client.models import FolderInfo, TransformParams, WorkflowPaths

MAX_CONCURRENT_TRANSFORMS = os.environ.get("MAX_CONCURRENT_TRANSFORMS", constants.DEFAULT_MAX_CONCURRENT_TRANSFORMS)


class DescribeDirectoriesWorkflowInput(BaseModel):
    workflow_paths: WorkflowPaths
    source_dir: str
    directory_descriptions_dir: str
    short_descriptions_dir: str
    max_content_length: int = 50000  # Maximum content length before chunking
    max_chunk_length: int = 20000  # Maximum length per chunk


@workflow.defn(name="describe-directories-workflow")
class DescribeDirectoriesWorkflow:
    @workflow.run
    async def run(
        self,
        workflow_input: DescribeDirectoriesWorkflowInput,
    ) -> None:
        # Get all directories in the source directory using activity
        all_directory_paths = await awa_activity.list_all_directories_recursive(workflow_input.source_dir)

        # Convert string paths back to Path objects for processing
        all_directories = [Path(p) for p in all_directory_paths]

        # Group directories by depth level (relative to source_dir)
        directories_by_depth: dict[int, list[Path]] = {}
        for directory in all_directories:
            relative_path = directory.relative_to(workflow_input.source_dir)
            depth = len(relative_path.parts)
            if depth not in directories_by_depth:
                directories_by_depth[depth] = []
            directories_by_depth[depth].append(directory)

        # Process each depth level from deepest to shallowest
        # Within each depth level, process directories with controlled concurrency
        for depth in sorted(directories_by_depth.keys(), reverse=True):
            directories_at_depth = directories_by_depth[depth]

            # Create coroutine functions for all directories at this depth level
            coroutine_funcs = [
                lambda the_directory=directory: self._describe_single_directory(
                    directory=the_directory,
                    source_dir=workflow_input.source_dir,
                    directory_descriptions_dir=workflow_input.directory_descriptions_dir,
                    short_descriptions_dir=workflow_input.short_descriptions_dir,
                    workflow_paths=workflow_input.workflow_paths,
                    max_content_length=workflow_input.max_content_length,
                    max_chunk_length=workflow_input.max_chunk_length,
                )
                for directory in directories_at_depth
            ]

            # Run with controlled concurrency
            await awa_workflow.run_with_controlled_concurrency(
                coroutine_funcs=coroutine_funcs,
                max_concurrency=MAX_CONCURRENT_TRANSFORMS,
            )

    async def _describe_single_directory(
        self,
        directory: Path,
        source_dir: str,
        directory_descriptions_dir: str,
        short_descriptions_dir: str,
        workflow_paths: WorkflowPaths,
        max_content_length: int,
        max_chunk_length: int,
    ) -> None:
        """Describe a single directory based on its files and subdirectories."""
        # Convert string parameters to Path objects
        source_dir_path = Path(source_dir)
        directory_descriptions_dir_path = Path(directory_descriptions_dir)
        short_descriptions_dir_path = Path(short_descriptions_dir)

        # Get relative path from source_dir to maintain directory structure
        relative_path = directory.relative_to(source_dir_path)

        # Get directory information using activity
        dir_info: FolderInfo = await awa_activity.get_directory_info(str(directory))

        # Collect file descriptions
        file_descriptions = []
        for file_name in dir_info.files:
            file_path = directory / file_name
            # Get the relative path of the file from source_dir
            file_relative_path = file_path.relative_to(source_dir_path)
            short_desc_file = short_descriptions_dir_path / file_relative_path

            short_description = await awa_activity.read_file(str(short_desc_file), default="")
            if short_description:
                file_descriptions.append(f"{file_name}: {short_description.strip()}")

        # Collect subdirectory descriptions
        subdir_descriptions = []
        for subdir_name in dir_info.subdirectories:
            subdir_path = directory / subdir_name
            # Get the relative path of the subdirectory from source_dir
            subdir_relative_path = subdir_path.relative_to(source_dir_path)
            subdir_desc_file = directory_descriptions_dir_path / subdir_relative_path / "description.md"

            subdir_description = await awa_activity.read_file(str(subdir_desc_file), default="")
            if subdir_description:
                subdir_descriptions.append(f"{subdir_name}: {subdir_description.strip()}")

        # Only describe directory if it has files or subdirectories
        if file_descriptions or subdir_descriptions:
            # Combine all descriptions for chunking check
            all_descriptions = file_descriptions + subdir_descriptions

            # Check if we need to chunk and summarize
            total_length = sum(len(desc) for desc in all_descriptions)

            if total_length > max_content_length:
                # Use the chunk and summarize workflow for large content
                workflow.logger.info(
                    f"Directory {directory} has {total_length} chars of descriptions, using chunking",
                )

                chunk_result = await workflow.execute_child_workflow(
                    ChunkAndSummarizeWorkflow,
                    ChunkAndSummarizeInput(
                        content_items=all_descriptions,
                        max_content_length=max_content_length,
                        max_chunk_length=max_chunk_length,
                        chunking_strategy=ChunkingStrategy.LIST_ITEMS,
                        context_data={
                            "directory_name": str(directory),
                            "directory_type": "directory_description",
                        },
                        baml_path=str(
                            Path(workflow_paths.baml_src)
                            / ".."
                            / ".."
                            / "common"
                            / "baml_src"
                            / "chunking_summarization.baml",
                        ),
                        chunk_summary_function="SummarizeDirectoryChunk",
                        final_summary_function="SummarizeDirectoryFinal",
                    ),
                    id=f"ChunkAndSummarize-{workflow.uuid4()}",
                    static_summary=f"ChunkAndSummarize-{relative_path.as_posix().replace('/', '-')}"[:200],
                )

                directory_description = chunk_result.final_summary
            else:
                # Use regular BAML to describe the directory
                transform_params = TransformParams(
                    baml_function_name="DescribeDirectory",
                    request={
                        "directory_name": str(directory),
                        "files": file_descriptions,
                        "sub_directories": subdir_descriptions,
                    },
                )
                directory_description = await awa_workflow.execute_baml_transform(
                    transform_params=transform_params,
                    baml_path=str(Path(workflow_paths.baml_src) / "describe_directory.baml"),
                    additional_workflow_id_part=relative_path.as_posix().replace("/", "-"),
                )

            # Save the description to directory_descriptions_dir with mirrored structure
            output_dir = directory_descriptions_dir_path / relative_path
            output_file = output_dir / "description.md"

            await awa_activity.write_file(
                file_path=str(output_file),
                content=directory_description,
            )
