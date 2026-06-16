import pathlib
from unittest.mock import AsyncMock, patch

import pytest

from cookbook.recipes.workflows.isolated_agent.models.workflow_input import SampleIsolatedAgentActWorkflowInput
from cookbook.recipes.workflows.isolated_agent.sample_isolated_agent_act_workflow import SampleIsolatedAgentActWorkflow
from sdk_dist.python.awa.client.models import TaskResponseModel


@pytest.mark.asyncio
async def test_run_happy_path(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    workflow = SampleIsolatedAgentActWorkflow()
    repo_path = tmp_path.joinpath("repo")
    repo_path.mkdir()
    input_data = SampleIsolatedAgentActWorkflowInput(repo_path=str(repo_path), branch="main")
    fake_result = TaskResponseModel(status="completed", reason="success", output="success")

    monkeypatch.setattr(
        "temporalio.workflow.logger",
        type("Logger", (), {"info": lambda *_a, **_k: None})(),
        raising=False,
    )  # type: ignore[assignment]

    mock_workflow_info = type(
        "Info",
        (),
        {
            "workflow_id": "testid",
            "workflow_type": "sample-isolated-agent-act",
        },
    )()

    with (
        patch("temporalio.workflow.info", return_value=mock_workflow_info),
        patch(
            "cookbook.recipes.workflows.isolated_agent.sample_isolated_agent_act_workflow.awa_workflow.isolated_agent",
            new_callable=AsyncMock,
        ) as mock_isolated_agent,
    ):
        mock_isolated_agent.return_value = fake_result
        result = await workflow.run(input_data)
        assert result == fake_result


@pytest.mark.asyncio
async def test_run_child_workflow_error(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    workflow = SampleIsolatedAgentActWorkflow()
    repo_path = tmp_path.joinpath("repo")
    repo_path.mkdir()
    input_data = SampleIsolatedAgentActWorkflowInput(repo_path=str(repo_path), branch="main")

    monkeypatch.setattr(
        "temporalio.workflow.logger",
        type("Logger", (), {"info": lambda *_a, **_k: None})(),
        raising=False,
    )  # type: ignore[assignment]

    mock_workflow_info = type(
        "Info",
        (),
        {
            "workflow_id": "testid",
            "workflow_type": "sample-isolated-agent-act",
        },
    )()

    with (
        patch("temporalio.workflow.info", return_value=mock_workflow_info),
        patch(
            "cookbook.recipes.workflows.isolated_agent.sample_isolated_agent_act_workflow.awa_workflow.isolated_agent",
            new_callable=AsyncMock,
        ) as mock_isolated_agent,
    ):
        mock_isolated_agent.side_effect = RuntimeError("isolated agent failed")
        with pytest.raises(RuntimeError, match="isolated agent failed"):
            await workflow.run(input_data)
