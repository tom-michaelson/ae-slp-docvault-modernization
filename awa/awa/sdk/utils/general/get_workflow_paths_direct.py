from pathlib import Path

from awa.sdk.models.workflow_paths import WorkflowPaths


def _find_project_root(workflow_dir: Path) -> str:
    """Find the closest parent directory that contains the makefile.

    Args:
        workflow_dir: The workflow directory to start searching from.

    Returns:
        str: The path to the project root directory, or empty string if not found.

    """
    current_dir = workflow_dir
    while current_dir != current_dir.parent:  # Stop at filesystem root
        if (current_dir / "makefile").exists():
            return str(current_dir)
        current_dir = current_dir.parent
    return ""  # Return empty string if no project root found


def get_workflow_paths_direct(workflow_dir: Path, workflow_type: str, workflow_id: str) -> WorkflowPaths:
    """Get workflow paths using direct workflow type and ID parameters.

    Args:
        workflow_dir: The base workflow directory.
        workflow_type: The type/name of the workflow.
        workflow_id: The unique identifier of the workflow instance.

    Returns:
        WorkflowPaths: Object containing all relevant workflow paths including
            project root, workflow root, input, output, BAML source, and agent prompts.

    """
    return WorkflowPaths(
        project_root=_find_project_root(workflow_dir),
        workflow_root=str(workflow_dir),
        input=str(workflow_dir / "input"),
        output=str(workflow_dir / "output" / workflow_type / workflow_id),
        baml_src=str(workflow_dir / "baml_src"),
        agent_prompts=str(workflow_dir / "agent_prompts"),
    )
