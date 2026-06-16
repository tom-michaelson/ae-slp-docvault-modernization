import pathlib
from unittest.mock import patch

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

    fake_result = TaskResponseModel(status="completed", result="success")

    async def fake_execute_child_workflow(*_args: object, **_kwargs: object) -> TaskResponseModel:
        return fake_result

    monkeypatch.setattr("temporalio.workflow.execute_child_workflow", fake_execute_child_workflow, raising=False)  # type: ignore[assignment]
    monkeypatch.setattr(
        "temporalio.workflow.logger",
        type("Logger", (), {"info": lambda *_a, **_k: None})(),
        raising=False,
    )  # type: ignore[assignment]
    with patch(
        "temporalio.workflow.info",
        return_value=type("Info", (), {"workflow_id": "testid", "workflow_type": "sample-isolated-agent-act"})(),
    ):
        result = await workflow.run(input_data)
    assert result == fake_result


@pytest.mark.asyncio
async def test_run_child_workflow_error(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    workflow = SampleIsolatedAgentActWorkflow()
    repo_path = tmp_path.joinpath("repo")
    repo_path.mkdir()
    input_data = SampleIsolatedAgentActWorkflowInput(repo_path=str(repo_path), branch="main")

    async def fake_execute_child_workflow(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("child workflow failed")

    monkeypatch.setattr("temporalio.workflow.execute_child_workflow", fake_execute_child_workflow, raising=False)  # type: ignore[assignment]
    monkeypatch.setattr(
        "temporalio.workflow.logger",
        type("Logger", (), {"info": lambda *_a, **_k: None})(),
        raising=False,
    )  # type: ignore[assignment]
    with (
        patch(
            "temporalio.workflow.info",
            return_value=type(
                "Info",
                (),
                {"workflow_id": "testid", "workflow_type": "sample-isolated-agent-act"},
            )(),
        ),
        pytest.raises(RuntimeError, match="child workflow failed"),
    ):
        await workflow.run(input_data)
