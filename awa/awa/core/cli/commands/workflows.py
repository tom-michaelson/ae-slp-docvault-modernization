"""CLI commands for workflow management."""

import asyncio
import json
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from awa.core.engine.temporal_client import TemporalClient
from awa.core.logger.logger import LoggerComponent, get_logger, init_logging
from awa.core.models.api import WorkflowRun
from awa.core.utils.workflow_metadata import format_workflow_parameters, get_workflow_metadata

app = typer.Typer(name="workflows", help="Access Workflow data with subcommands.")
console = Console()


@app.command(name="runs")
def workflow_runs(
    json_output: Annotated[
        bool,
        typer.Option("--json", "-j", help="Output in JSON format"),
    ] = False,
) -> None:
    """List Temporal Workflow Runs."""
    init_logging()
    asyncio.run(_runs(json_output))


@app.command(name="list")
def list_workflows(
    json_output: Annotated[
        bool,
        typer.Option("--json", "-j", help="Output in JSON format"),
    ] = False,
) -> None:
    """List all available workflows in the system."""
    init_logging()

    asyncio.run(_list_workflows(json_output))


async def _runs(json_output: bool = False) -> None:
    client = await TemporalClient.create()
    runs = await client.list_workflow_runs()

    if json_output:
        # Output as JSON
        workflows_data = []

        for run in runs:
            workflow_data = {
                "type": run.type,
                "id": run.id,
                "status": run.status,
                "start": str(run.started),
                "duration": run.duration,
                "monitor": run.monitor,
            }

            workflows_data.append(workflow_data)

        output = {"workflows": workflows_data}

        console.print(json.dumps(output, indent=2))
    else:
        output_workflow_runs(runs)


def output_workflow_runs(runs: list[WorkflowRun]) -> None:
    # Prints a list of workflow runs to the console in a formatted, readable manner
    logger = get_logger(LoggerComponent.CLI)
    longest_field_length = {
        "type": 0,
        "id": 0,
        "status": 0,
        "start": 0,
        "duration": 0,
    }

    for run in runs:
        # Compare the fields of each run, and set column width to the longest value per field
        start_time = run.started.strftime("%d/%m/%Y, %H:%M:%S")
        longest_field_length["type"] = max(longest_field_length["type"], len(run.type))
        longest_field_length["id"] = max(longest_field_length["id"], len(run.id))
        longest_field_length["status"] = max(longest_field_length["status"], len(run.status))
        longest_field_length["start"] = max(longest_field_length["start"], len(start_time))
        longest_field_length["duration"] = max(longest_field_length["duration"], len(run.duration))

    logger.info("Listing Workflow Runs\n")
    run_log_str = "\n"
    header = (
        f"""{"Workflow Type":<{longest_field_length["type"]}}   """
        f"""{"Run ID":<{longest_field_length["id"]}}   {"Status":<{longest_field_length["status"]}}   """
        f"""{"Start Time":<{longest_field_length["start"]}}   {"Duration":<{longest_field_length["duration"]}}"""
    )

    run_log_str += f"{'\033[94m'}{header}{'\033[0m'}\n"
    run_log_str += f"{'\033[94m'}{'-' * len(header)}{'\033[0m'}\n"

    for run in runs:
        start_time = run.started.strftime("%d/%m/%Y, %H:%M:%S")
        run_log_str += (
            f"""{run.type:<{longest_field_length["type"]}}   """
            f"""{run.id:<{longest_field_length["id"]}}   {run.status:<{longest_field_length["status"]}}   """
            f"""{start_time:<{longest_field_length["start"]}}   {run.duration:<{longest_field_length["duration"]}}\n"""
            f"""{"\033[96m"}{run.monitor}{"\033[0m"}\n\n"""
        )
    run_log_str += "\n"
    logger.info(run_log_str)


async def _list_workflows(json_output: bool = False) -> None:
    """List all available workflows in the system.

    Args:
        json_output: Whether to output in JSON format instead of table format.

    """
    logger = get_logger(LoggerComponent.CLI)

    try:
        workflow_metadata = get_workflow_metadata()

        if json_output:
            # Output as JSON
            workflows_data = []

            for metadata in workflow_metadata:
                workflow_data = {
                    "name": metadata.name,
                    "module": metadata.module,
                    "parameters": format_workflow_parameters(metadata),
                }

                workflows_data.append(workflow_data)

            output = {"workflows": workflows_data}
            console.print(json.dumps(output, indent=2))

        # Output as human-readable table
        elif not workflow_metadata:
            console.print("No workflows found.")

        else:
            table = Table(title="Available Workflows")
            table.add_column("Name", style="cyan")
            table.add_column("Module", style="yellow")
            table.add_column("Parameters", style="green")

            for metadata in workflow_metadata:
                formatted_parameters = format_workflow_parameters(metadata)
                parameters_str = ", ".join(formatted_parameters) if formatted_parameters else "None"

                table.add_row(
                    metadata.name,
                    metadata.module,
                    parameters_str,
                )

            console.print(table)

        logger.info(f"Found {len(workflow_metadata)} workflows")

    except Exception as e:
        logger.exception("Failed to list workflows")
        console.print(f"[red]Error: Failed to list workflows: {e!s}[/red]")
        raise typer.Exit(code=1) from e
