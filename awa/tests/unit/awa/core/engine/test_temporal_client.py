from unittest.mock import AsyncMock, patch

import pytest

from awa.core.engine.temporal_client import TemporalClient
from awa.sdk.models.exceptions.invalid_input_error import InvalidInputApplicationError


@pytest.mark.asyncio
class TestTemporalClient:
    async def test_execute_workflow_with_input(self) -> None:
        client = await TemporalClient.create()
        with patch.object(client, "get_client", new_callable=AsyncMock) as mock_get_client:
            mock_temporal_client = AsyncMock()
            mock_get_client.return_value = mock_temporal_client
            mock_temporal_client.execute_workflow.return_value = {"result": "ok"}
            with patch("awa.core.utils.temporal_utils.TemporalUtils.generate_workflow_id", return_value="workflow_id"):
                result = await client.execute_workflow("workflow", '{"foo": "bar"}', "queue")
                assert result == {"result": "ok"}
                mock_temporal_client.execute_workflow.assert_called_once()

    async def test_execute_workflow_without_input(self) -> None:
        client = await TemporalClient.create()
        with patch.object(client, "get_client", new_callable=AsyncMock) as mock_get_client:
            mock_temporal_client = AsyncMock()
            mock_get_client.return_value = mock_temporal_client
            mock_temporal_client.execute_workflow.return_value = {"result": "ok"}
            with patch("awa.core.utils.temporal_utils.TemporalUtils.generate_workflow_id", return_value="workflow_id"):
                result = await client.execute_workflow("workflow", None, "queue")
                assert result == {"result": "ok"}
                mock_temporal_client.execute_workflow.assert_called_once()

    async def test_execute_workflow_none_workflow(self) -> None:
        client = await TemporalClient.create()
        with pytest.raises(ValueError, match="Workflow is required"):
            await client.execute_workflow(None, None, None)

    async def test_start_workflow_with_input(self) -> None:
        client = await TemporalClient.create()
        with patch.object(client, "get_client", new_callable=AsyncMock) as mock_get_client:
            mock_temporal_client = AsyncMock()
            mock_get_client.return_value = mock_temporal_client
            mock_temporal_client.start_workflow.return_value = {"result": "ok"}
            with patch("awa.core.utils.temporal_utils.TemporalUtils.generate_workflow_id", return_value="workflow_id"):
                result = await client.start_workflow("workflow", '{"foo": "bar"}', "queue")
                assert result == {"result": "ok"}
                mock_temporal_client.start_workflow.assert_called_once()

    async def test_start_workflow_invalid_json_input(self) -> None:
        """Test that invalid JSON input raises InvalidInputApplicationError."""
        client = await TemporalClient.create()
        with patch.object(client, "get_client", new_callable=AsyncMock) as mock_get_client:
            mock_temporal_client = AsyncMock()
            mock_get_client.return_value = mock_temporal_client
            with patch("awa.core.utils.temporal_utils.TemporalUtils.generate_workflow_id", return_value="workflow_id"):
                # Test malformed JSON
                with pytest.raises(InvalidInputApplicationError, match="Invalid JSON format in input field"):
                    await client.start_workflow("workflow", "{invalid json", "queue")

                # Test single quotes with invalid syntax (triggers ValueError from ast.literal_eval)
                with pytest.raises(InvalidInputApplicationError, match="Invalid JSON format in input field"):
                    await client.start_workflow("workflow", "{'invalid': syntax}", "queue")

    async def test_execute_workflow_invalid_json_input(self) -> None:
        """Test that invalid JSON input raises InvalidInputApplicationError for execute_workflow."""
        client = await TemporalClient.create()
        with patch.object(client, "get_client", new_callable=AsyncMock) as mock_get_client:
            mock_temporal_client = AsyncMock()
            mock_get_client.return_value = mock_temporal_client
            with patch("awa.core.utils.temporal_utils.TemporalUtils.generate_workflow_id", return_value="workflow_id"):
                # Test malformed JSON
                with pytest.raises(InvalidInputApplicationError, match="Invalid JSON format in input field"):
                    await client.execute_workflow("workflow", "{invalid json", "queue")

                # Test single quotes with invalid syntax (triggers ValueError from ast.literal_eval)
                with pytest.raises(InvalidInputApplicationError, match="Invalid JSON format in input field"):
                    await client.execute_workflow("workflow", "{'invalid': syntax}", "queue")

    async def test_start_workflow_without_input(self) -> None:
        client = await TemporalClient.create()
        with patch.object(client, "get_client", new_callable=AsyncMock) as mock_get_client:
            mock_temporal_client = AsyncMock()
            mock_get_client.return_value = mock_temporal_client
            mock_temporal_client.start_workflow.return_value = {"result": "ok"}
            with patch("awa.core.utils.temporal_utils.TemporalUtils.generate_workflow_id", return_value="workflow_id"):
                result = await client.start_workflow("workflow", None, "queue")
                assert result == {"result": "ok"}
                mock_temporal_client.start_workflow.assert_called_once()

    async def test_start_workflow_none_workflow(self) -> None:
        client = await TemporalClient.create()
        with pytest.raises(ValueError, match="Workflow is required"):
            await client.start_workflow(None, None, None)

    @patch("awa.core.engine.temporal_client.get_workflow_queue")
    async def test_start_workflow_dynamic_queue_lookup_found(self, mock_get_queue: AsyncMock) -> None:
        """Test that start_workflow uses dynamic queue lookup when task_queue is None."""
        client = await TemporalClient.create()
        mock_get_queue.return_value = "dynamic-queue"

        with patch.object(client, "get_client", new_callable=AsyncMock) as mock_get_client:
            mock_temporal_client = AsyncMock()
            mock_get_client.return_value = mock_temporal_client
            mock_temporal_client.start_workflow.return_value = {"result": "ok"}
            with patch("awa.core.utils.temporal_utils.TemporalUtils.generate_workflow_id", return_value="workflow_id"):
                result = await client.start_workflow("TestWorkflow", '{"foo": "bar"}', None)

                assert result == {"result": "ok"}
                mock_get_queue.assert_called_once_with("TestWorkflow")
                mock_temporal_client.start_workflow.assert_called_once()

                # Verify the task_queue parameter was set to the dynamic value
                call_args = mock_temporal_client.start_workflow.call_args
                assert call_args.kwargs["task_queue"] == "dynamic-queue"

    @patch("awa.core.engine.temporal_client.get_workflow_queue")
    async def test_start_workflow_dynamic_queue_lookup_not_found(self, mock_get_queue: AsyncMock) -> None:
        """Test that start_workflow falls back to default queue when dynamic lookup returns None."""
        client = await TemporalClient.create()
        mock_get_queue.return_value = None

        with patch.object(client, "get_client", new_callable=AsyncMock) as mock_get_client:
            mock_temporal_client = AsyncMock()
            mock_get_client.return_value = mock_temporal_client
            mock_temporal_client.start_workflow.return_value = {"result": "ok"}
            with patch("awa.core.utils.temporal_utils.TemporalUtils.generate_workflow_id", return_value="workflow_id"):
                result = await client.start_workflow("UnknownWorkflow", None, None)

                assert result == {"result": "ok"}
                mock_get_queue.assert_called_once_with("UnknownWorkflow")
                mock_temporal_client.start_workflow.assert_called_once()

                # Verify the task_queue parameter was set to the default value
                call_args = mock_temporal_client.start_workflow.call_args
                assert call_args.kwargs["task_queue"] == client.default_task_queue

    @patch("awa.core.engine.temporal_client.get_workflow_queue")
    async def test_start_workflow_provided_queue_skips_lookup(self, mock_get_queue: AsyncMock) -> None:
        """Test that start_workflow skips dynamic lookup when task_queue is provided."""
        client = await TemporalClient.create()

        with patch.object(client, "get_client", new_callable=AsyncMock) as mock_get_client:
            mock_temporal_client = AsyncMock()
            mock_get_client.return_value = mock_temporal_client
            mock_temporal_client.start_workflow.return_value = {"result": "ok"}
            with patch("awa.core.utils.temporal_utils.TemporalUtils.generate_workflow_id", return_value="workflow_id"):
                result = await client.start_workflow("TestWorkflow", None, "provided-queue")

                assert result == {"result": "ok"}
                mock_get_queue.assert_not_called()  # Should skip dynamic lookup
                mock_temporal_client.start_workflow.assert_called_once()

                # Verify the task_queue parameter was set to the provided value
                call_args = mock_temporal_client.start_workflow.call_args
                assert call_args.kwargs["task_queue"] == "provided-queue"

    @patch("awa.core.engine.temporal_client.get_workflow_queue")
    async def test_execute_workflow_dynamic_queue_lookup_found(self, mock_get_queue: AsyncMock) -> None:
        """Test that execute_workflow uses dynamic queue lookup when task_queue is None."""
        client = await TemporalClient.create()
        mock_get_queue.return_value = "dynamic-queue"

        with patch.object(client, "get_client", new_callable=AsyncMock) as mock_get_client:
            mock_temporal_client = AsyncMock()
            mock_get_client.return_value = mock_temporal_client
            mock_temporal_client.execute_workflow.return_value = {"result": "ok"}
            with patch("awa.core.utils.temporal_utils.TemporalUtils.generate_workflow_id", return_value="workflow_id"):
                result = await client.execute_workflow("TestWorkflow", '{"foo": "bar"}', None)

                assert result == {"result": "ok"}
                mock_get_queue.assert_called_once_with("TestWorkflow")
                mock_temporal_client.execute_workflow.assert_called_once()

                # Verify the task_queue parameter was set to the dynamic value
                call_args = mock_temporal_client.execute_workflow.call_args
                assert call_args.kwargs["task_queue"] == "dynamic-queue"

    @patch("awa.core.engine.temporal_client.get_workflow_queue")
    async def test_execute_workflow_dynamic_queue_lookup_not_found(self, mock_get_queue: AsyncMock) -> None:
        """Test that execute_workflow falls back to default queue when dynamic lookup returns None."""
        client = await TemporalClient.create()
        mock_get_queue.return_value = None

        with patch.object(client, "get_client", new_callable=AsyncMock) as mock_get_client:
            mock_temporal_client = AsyncMock()
            mock_get_client.return_value = mock_temporal_client
            mock_temporal_client.execute_workflow.return_value = {"result": "ok"}
            with patch("awa.core.utils.temporal_utils.TemporalUtils.generate_workflow_id", return_value="workflow_id"):
                result = await client.execute_workflow("UnknownWorkflow", None, None)

                assert result == {"result": "ok"}
                mock_get_queue.assert_called_once_with("UnknownWorkflow")
                mock_temporal_client.execute_workflow.assert_called_once()

                # Verify the task_queue parameter was set to the default value
                call_args = mock_temporal_client.execute_workflow.call_args
                assert call_args.kwargs["task_queue"] == client.default_task_queue

    @patch("awa.core.engine.temporal_client.get_workflow_queue")
    async def test_execute_workflow_provided_queue_skips_lookup(self, mock_get_queue: AsyncMock) -> None:
        """Test that execute_workflow skips dynamic lookup when task_queue is provided."""
        client = await TemporalClient.create()

        with patch.object(client, "get_client", new_callable=AsyncMock) as mock_get_client:
            mock_temporal_client = AsyncMock()
            mock_get_client.return_value = mock_temporal_client
            mock_temporal_client.execute_workflow.return_value = {"result": "ok"}
            with patch("awa.core.utils.temporal_utils.TemporalUtils.generate_workflow_id", return_value="workflow_id"):
                result = await client.execute_workflow("TestWorkflow", None, "provided-queue")

                assert result == {"result": "ok"}
                mock_get_queue.assert_not_called()  # Should skip dynamic lookup
                mock_temporal_client.execute_workflow.assert_called_once()

                # Verify the task_queue parameter was set to the provided value
                call_args = mock_temporal_client.execute_workflow.call_args
                assert call_args.kwargs["task_queue"] == "provided-queue"
