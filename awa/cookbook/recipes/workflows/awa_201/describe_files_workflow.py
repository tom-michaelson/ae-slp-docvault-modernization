import asyncio
from pathlib import Path

from temporalio import workflow

from sdk_dist.python.awa.client import awa_activity, awa_workflow
from sdk_dist.python.awa.client.models import InputParams, TransformParams, WorkflowPaths


# TODO RH: Refactor this for reusability: execute_baml_transform_set; should include reading input files
# TODO RH: Need to have maximum parallelism somewhere here, config-driven with sane default; for rate limiting
@workflow.defn(name="describe-files")
class DescribeFilesWorkflow:
    @workflow.run
    async def run(
        self,
        workflow_paths: WorkflowPaths,
        file_classifications_by_file: dict[str, dict],
        descriptions_dir: str,
        short_descriptions_dir: str,
        relative_root_dir: str,
    ) -> None:
        # Full descriptions
        describe_code_files_transform_params_by_key: dict[str, TransformParams] = {}
        describe_non_code_files_transform_params_by_key: dict[str, TransformParams] = {}
        for file, classification in file_classifications_by_file.items():
            file_category = classification.get("file_category", "UNKNOWN")
            language = classification.get("language", "UNKNOWN")
            if file_category == "APP_CODE":
                relative_file_path = Path(file).relative_to(relative_root_dir)
                describe_code_files_transform_params_by_key[str(file)] = TransformParams(
                    baml_function_name="DescribeCodeFile",
                    request={
                        "file_name": str(relative_file_path),
                        "language": language,
                    },
                    inputs=[InputParams(name="file_content", path=str(file))],
                )
            else:
                relative_file_path = Path(file).relative_to(relative_root_dir)
                describe_non_code_files_transform_params_by_key[str(file)] = TransformParams(
                    baml_function_name="DescribeNonCodeFile",
                    request={
                        "file_name": str(relative_file_path),
                        "file_category": file_category,
                    },
                    inputs=[InputParams(name="file_content", path=str(file))],
                )

        describe_code_files_task = awa_workflow.execute_baml_transform_batch(
            baml_path=str(Path(workflow_paths.baml_src) / "describe_code_file.baml"),
            baml_requests_by_key=describe_code_files_transform_params_by_key,
        )

        describe_non_code_files_task = awa_workflow.execute_baml_transform_batch(
            baml_path=str(Path(workflow_paths.baml_src) / "describe_non_code_file.baml"),
            baml_requests_by_key=describe_non_code_files_transform_params_by_key,
        )

        describe_files_result, describe_non_code_files_result = await asyncio.gather(
            describe_code_files_task,
            describe_non_code_files_task,
        )

        # Combine results from both batch operations
        all_full_descriptions = {**describe_files_result, **describe_non_code_files_result}

        # Write each full description result to disk
        description_file_tasks = []
        for file_path, full_description_result in all_full_descriptions.items():
            relative_file_path = Path(file_path).relative_to(relative_root_dir)
            description_file_path = Path(descriptions_dir) / relative_file_path
            description_file_tasks.append(
                awa_activity.write_file(
                    file_path=description_file_path,
                    content=full_description_result,
                ),
            )
        await asyncio.gather(*description_file_tasks)

        # Short descriptions
        describe_files_short_transform_params_by_key: dict[str, TransformParams] = {}
        for file in file_classifications_by_file:
            relative_file_path = Path(file).relative_to(relative_root_dir)
            description_file_path = str(Path(descriptions_dir) / relative_file_path)
            describe_files_short_transform_params_by_key[str(file)] = TransformParams(
                baml_function_name="DescribeFileShort",
                request={
                    "file_name": str(relative_file_path),
                },
                inputs=[InputParams(name="file_description", path=description_file_path)],
            )

        describe_files_short_result = await awa_workflow.execute_baml_transform_batch(
            baml_path=str(Path(workflow_paths.baml_src) / "describe_file_short.baml"),
            baml_requests_by_key=describe_files_short_transform_params_by_key,
        )

        # Write each short description result to disk
        short_description_file_tasks = []
        for file_path, short_description_result in describe_files_short_result.items():
            relative_file_path = Path(file_path).relative_to(relative_root_dir)
            short_description_file_path = str(Path(short_descriptions_dir) / relative_file_path)
            short_description_file_tasks.append(
                awa_activity.write_file(
                    file_path=short_description_file_path,
                    content=short_description_result,
                ),
            )
        await asyncio.gather(*short_description_file_tasks)
