# Tests for SingleFileDiffWorkflow

import uuid
from unittest.mock import AsyncMock, call

import pytest
from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker

from awa.core.models.apply_diff_result import ApplyDiffResult
from awa.core.workflows.single_file_diff import ApplySingleFileDiffWorkflow, SingleFileDiffInput, SingleFileDiffOutput
from awa.sdk import constants


class TestSingleFileDiffWorkflow:
    @pytest.mark.asyncio
    async def test_workflow_success(self, workflow_client: Client) -> None:
        """Test the SingleFileDiffWorkflow with successful diff application."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        file_path = "example.py"
        natural_language_request = "Add a goodbye function and call it from main"

        file_content = (
            'def hello():\n    print("Hello, world!")\n\ndef main():\n    hello()\n\n'
            'if __name__ == "__main__":\n    main()\n'
        )

        diff_text = """*** Begin Patch
*** Update File: example.py
 def hello():
     print("Hello, world!")

-def main():
-    hello()
+def goodbye():
+    print("Goodbye, world!")
+
+def main():
+    hello()
+    goodbye()

 if __name__ == "__main__":
     main()
*** End Patch"""

        input_obj = SingleFileDiffInput(
            file_path=file_path,
            natural_language_request=natural_language_request,
        )

        # Mock activities
        @activity.defn(name=constants.ACTIVITY_READ_FILE)
        async def read_file_mock(_path: str) -> str:
            return file_content

        @activity.defn(name=constants.ACTIVITY_TRANSFORM)
        async def transform_activity_mock(_params: dict) -> dict:
            return {"diff_string": diff_text}

        apply_diff_spy = AsyncMock(return_value=True)

        @activity.defn(name=constants.ACTIVITY_APPLY_DIFF)
        async def apply_diff_mock(_diff_text: str) -> ApplyDiffResult:
            return ApplyDiffResult(success=await apply_diff_spy(_diff_text))

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[ApplySingleFileDiffWorkflow],
            activities=[read_file_mock, transform_activity_mock, apply_diff_mock],
        ):
            # Act
            result = await workflow_client.execute_workflow(
                ApplySingleFileDiffWorkflow.run,
                input_obj,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            # Assert
            assert isinstance(result, SingleFileDiffOutput)
            assert result.success is True
            assert result.file_path == file_path
            assert "Successfully" in result.message
            apply_diff_spy.assert_called_once_with(diff_text)

    @pytest.mark.asyncio
    async def test_workflow_failure(self, workflow_client: Client) -> None:
        """Test the SingleFileDiffWorkflow with failed diff application."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        file_path = "example.py"
        natural_language_request = "Add a goodbye function and call it from main"

        file_content = "file content"
        diff_text = "diff text"

        input_obj = SingleFileDiffInput(
            file_path=file_path,
            natural_language_request=natural_language_request,
        )

        # Mock activities
        @activity.defn(name=constants.ACTIVITY_READ_FILE)
        async def read_file_mock(_path: str) -> str:
            return file_content

        @activity.defn(name=constants.ACTIVITY_TRANSFORM)
        async def transform_activity_mock(_params: dict) -> dict:
            return {"diff_string": diff_text}

        apply_diff_spy = AsyncMock(return_value=False)

        @activity.defn(name=constants.ACTIVITY_APPLY_DIFF)
        async def apply_diff_mock(_diff_text: str) -> ApplyDiffResult:
            return ApplyDiffResult(success=await apply_diff_spy(_diff_text))

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[ApplySingleFileDiffWorkflow],
            activities=[read_file_mock, transform_activity_mock, apply_diff_mock],
        ):
            # Act
            result = await workflow_client.execute_workflow(
                ApplySingleFileDiffWorkflow.run,
                input_obj,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            # Assert
            assert isinstance(result, SingleFileDiffOutput)
            assert result.success is False
            assert result.file_path == file_path
            assert "Failed" in result.message
            # The workflow retries up to 2 times, so apply_diff should be called twice
            assert apply_diff_spy.call_count == 2
            apply_diff_spy.assert_has_calls(
                [
                    call(diff_text),
                    call(diff_text),
                ],
            )
