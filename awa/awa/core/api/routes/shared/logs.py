"""Log collection API endpoints.

This module provides endpoints for retrieving workflow logs.
Real-time log streaming is handled via Socket.IO.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from awa.core.utils.workflow_logging_utils import find_workflow_log_file

router = APIRouter()


class WorkflowLogsResponse(BaseModel):
    """Response containing workflow logs."""

    workflow_id: str
    logs: list[str]
    total_lines: int
    has_more: bool


@router.get(
    "/logs/workflows/{workflow_id}",
    summary="Logs: Get workflow logs",
    description="Get execution logs for a workflow.",
)
async def get_workflow_logs(
    workflow_id: str,
    offset: int = 0,
    limit: int = 1000,
) -> WorkflowLogsResponse:
    """Get historical logs for a workflow.

    Args:
        workflow_id: Workflow ID
        offset: Line offset (0-based)
        limit: Maximum number of lines to return
        current_user: Authenticated user (required for access control)

    Returns:
        Workflow logs response

    Raises:
        HTTPException: If logs not found

    """
    # Get log file path for this workflow
    log_path = find_workflow_log_file(workflow_id)

    if not log_path or not log_path.exists():
        raise HTTPException(status_code=404, detail=f"No logs found for workflow {workflow_id}")

    try:
        with log_path.open() as f:
            # Read all lines
            lines = f.readlines()
            total_lines = len(lines)

            # Apply offset and limit
            start = min(offset, total_lines)
            end = min(start + limit, total_lines)
            selected_lines = lines[start:end]

            return WorkflowLogsResponse(
                workflow_id=workflow_id,
                logs=[line.rstrip() for line in selected_lines],
                total_lines=total_lines,
                has_more=end < total_lines,
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading logs: {e}") from e
