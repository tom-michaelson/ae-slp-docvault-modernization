"""Test workflow for demonstrating child workflows."""

from datetime import timedelta

from temporalio import activity, workflow
from temporalio.exceptions import ApplicationError
from temporalio.exceptions import TimeoutError as TemporalTimeoutError

from cookbook.recipes import constants


@workflow.defn(name="test-child-workflow-logging")
class TestChildWorkflowLogging:
    """Test workflow to demonstrate usage of child workflows.

    This workflow:
    1. Logs at the parent workflow level
    2. Calls a simple activity locally
    3. Calls a child workflow in core (awa-hello-world)
    """

    @workflow.run
    async def run(self, input_data: dict) -> dict:
        """Execute test workflow with child workflow calls.

        Args:
            input_data: Dict with 'name' field

        Returns:
            Dict with test results

        """
        name = input_data.get("name", "Test")

        # Parent workflow logging
        workflow.logger.info(f"Starting TestChildWorkflowLogging for name: {name}")

        results = {}

        # Step 1: Call a local activity to test activity logging in parent
        workflow.logger.info("Step 1: Calling local test activity...")
        try:
            local_result = await workflow.execute_activity(
                test_activity,
                args=[f"Parent-{name}"],
                start_to_close_timeout=timedelta(seconds=5),
            )
            results["local_activity"] = local_result
            workflow.logger.info(f"Local activity result: {local_result}")
        except (ApplicationError, TemporalTimeoutError) as e:
            workflow.logger.error(f"Local activity failed: {e}")
            results["local_activity"] = f"Failed: {e}"

        # Step 2: Call core child workflow (awa-hello-world)
        workflow.logger.info("Step 2: Starting child workflow awa-hello-world on core worker...")

        try:
            child_result = await workflow.execute_child_workflow(
                workflow="awa-hello-world",  # Core workflow name
                args=[{"name": f"ChildTest-{name}"}],
                id=f"test_child_{workflow.info().workflow_id}",
                task_queue=constants.AWA_DEFAULT_TASK_QUEUE,  # Run on core worker
                execution_timeout=timedelta(seconds=30),
            )
            results["child_workflow"] = child_result
            workflow.logger.info(f"Child workflow result: {child_result}")
        except (ApplicationError, TemporalTimeoutError) as e:
            workflow.logger.error(f"Child workflow failed: {e}")
            results["child_workflow"] = f"Failed: {e}"

        # Step 3: Call another child workflow with more complex activity pattern
        workflow.logger.info("Step 3: Starting another child workflow for complex test...")
        try:
            # We'll use the same hello world but with different input
            complex_result = await workflow.execute_child_workflow(
                workflow="awa-hello-world",
                args=[{"name": f"ComplexChild-{name}"}],
                id=f"test_complex_child_{workflow.info().workflow_id}",
                task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
                execution_timeout=timedelta(seconds=30),
            )
            results["complex_child"] = complex_result
            workflow.logger.info(f"Complex child workflow result: {complex_result}")
        except (ApplicationError, TemporalTimeoutError) as e:
            workflow.logger.error(f"Complex child workflow failed: {e}")
            results["complex_child"] = f"Failed: {e}"

        # Final logging
        workflow.logger.info("TestChildWorkflowLogging completed successfully")

        return results


@activity.defn
async def test_activity(name: str) -> str:
    """Simple test activity for the parent workflow."""
    activity.logger.info(f"Starting test_activity with name: {name}")

    result = f"Processed: {name}"

    activity.logger.info(f"Activity completed with result: {result}")
    return result
