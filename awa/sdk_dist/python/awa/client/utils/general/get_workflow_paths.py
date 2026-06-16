from pathlib import Path

from temporalio.workflow import Info

from awa.client.models.workflow_paths import WorkflowPaths
from awa.client.utils.general.get_workflow_paths_direct import get_workflow_paths_direct


def get_workflow_paths(workflow_dir: Path, workflow_info: Info) -> WorkflowPaths:
    """Get workflow paths using Temporal workflow info.

    Args:
        workflow_dir: The base workflow directory.
        workflow_info: Temporal workflow info containing workflow type and ID.

    Returns:
        WorkflowPaths: Object containing all relevant workflow paths.

    """
    return get_workflow_paths_direct(
        workflow_dir,
        workflow_info.workflow_type,
        workflow_info.workflow_id,
    )
