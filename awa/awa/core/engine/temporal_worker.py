import asyncio
import contextlib

from temporalio.worker import UnsandboxedWorkflowRunner, Worker
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner

from awa.core import constants
from awa.core.engine.temporal_client import TemporalClient
from awa.core.engine.workflow_interceptor import LoggingWorkflowInterceptor
from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.config.env_config import EnvConfig
from awa.core.utils.config_loader import ConfigLoader
from awa.core.utils.core_worker_registry import register_core_workflows
from awa.core.utils.temporal_discovery import TemporalDiscovery
from awa.core.utils.temporal_utils import _get_active_worker_pollers


class TemporalWorker:
    def __init__(self, temporal_client: TemporalClient) -> None:
        self.worker_started_event = asyncio.Event()
        self.logger = get_logger(LoggerComponent.WORKER)
        self.default_task_queue = constants.TASK_QUEUE
        self._worker_task: asyncio.Task | None = None
        self.temporal_client = temporal_client
        self._worker: Worker | None = None

    async def _construct_temporal_worker(self) -> None:
        self.logger.info(f'Starting Temporal Worker for queue "{self.default_task_queue}"...')
        client = await self.temporal_client.get_client()

        # Load configuration and check if recipes are enabled
        config = ConfigLoader.get_config()
        include_recipes = config.recipes

        # Log recipe configuration status
        if include_recipes:
            self.logger.info("Recipe workflows ENABLED in configuration")
        else:
            self.logger.info("Recipe workflows DISABLED in configuration")

        # Dynamically discover workflows and activities
        discovery = TemporalDiscovery(include_recipes=include_recipes)
        workflows, activities = discovery.discover_workflows_and_activities(dependencies=[client])

        # Get decorator-defined names for logging and categorize by type
        core_workflow_names = []
        recipe_workflow_names = []
        for w in workflows:
            workflow_name = self._get_workflow_name(w)
            # Check if workflow is from recipes module
            module_name = getattr(w, "__module__", "")
            if "recipes" in module_name:
                recipe_workflow_names.append(workflow_name)
            else:
                core_workflow_names.append(workflow_name)

        core_activity_names = []
        recipe_activity_names = []
        for a in activities:
            activity_name = self._get_activity_name(a)
            # Check if activity is from recipes module
            module_name = getattr(a, "__module__", "") if hasattr(a, "__module__") else ""
            if not module_name and hasattr(a, "__func__"):
                module_name = getattr(a.__func__, "__module__", "")
            if "recipes" in module_name:
                recipe_activity_names.append(activity_name)
            else:
                core_activity_names.append(activity_name)

        # Log workflow and activity counts by type
        self.logger.info(
            f"Discovered {len(core_workflow_names)} core workflow(s) and "
            f"{len(recipe_workflow_names)} recipe workflow(s)",
        )
        self.logger.info(
            f"Discovered {len(core_activity_names)} core activity/activities and "
            f"{len(recipe_activity_names)} recipe activity/activities",
        )

        # Log detailed registration information
        all_workflow_names = core_workflow_names + recipe_workflow_names
        all_activity_names = core_activity_names + recipe_activity_names
        self.logger.info(
            f"Registering {len(workflows)} workflows and {len(activities)} activities with Temporal Worker.\n"
            f"Workflows:\n  - {'\n  - '.join(all_workflow_names)}\n"
            f"Activities:\n  - {'\n  - '.join(all_activity_names)}",
        )

        # Register core workflows in the registry (creates JSON file)
        await register_core_workflows(workflows, self.default_task_queue)

        debug_mode = EnvConfig.get_env_config().debug_mode
        self.logger.info(f"Running Temporal Worker. task_queue={self.default_task_queue}, debug_mode={debug_mode}")

        # Create and store the worker with logging interceptor
        self._worker = Worker(
            client,
            task_queue=self.default_task_queue,
            workflows=workflows,
            activities=activities,
            debug_mode=debug_mode,
            workflow_runner=UnsandboxedWorkflowRunner()
            if debug_mode  # To enable local debugging of live workflows
            else SandboxedWorkflowRunner(),
            interceptors=[LoggingWorkflowInterceptor()],
        )

    async def _temporal_worker(self) -> None:
        if self._worker is None:
            raise RuntimeError("Worker not constructed")
        # Set event and run worker concurrently
        await asyncio.gather(
            self._set_worker_started_event(),
            self._worker.run(),
        )

    async def _set_worker_started_event(self) -> None:
        await asyncio.sleep(1)  # TODO Make this check more robust: AWA-97
        if not self.worker_started_event.is_set():
            self.worker_started_event.set()

    def _get_workflow_name(self, workflow_class: type) -> str:
        """Extract the workflow name from a workflow class.

        Args:
            workflow_class: The workflow class to extract the name from

        Returns:
            str: The workflow name (decorator-defined or class name)

        """
        defn = getattr(workflow_class, "__temporal_workflow_definition", None)
        if defn and hasattr(defn, "name") and defn.name:
            return defn.name
        return getattr(workflow_class, "__name__", str(workflow_class))

    def _get_activity_name(self, activity: object) -> str:
        """Extract the activity name from an activity function or method.

        Args:
            activity: The activity function or method to extract the name from

        Returns:
            str: The activity name (decorator-defined or function name)

        """
        defn = getattr(activity, "__temporal_activity_definition", None)
        if defn and hasattr(defn, "name") and defn.name:
            return defn.name
        return getattr(activity, "__name__", str(activity))

    async def is_healthy(self) -> bool:
        """Check if the Temporal worker is running and healthy (internal state only).

        Returns:
            bool: True if the worker is running, False otherwise

        """
        return self.worker_started_event.is_set() and self._worker_task is not None and not self._worker_task.done()

    async def start(self) -> None:
        """Start the Temporal worker service (non-blocking)."""
        if not self.worker_started_event.is_set() and (not self._worker_task or self._worker_task.done()):
            await self._construct_temporal_worker()
            self._worker_task = asyncio.create_task(self._temporal_worker())
            # Wait for worker to be ready
            await self.worker_started_event.wait()

    async def stop(self, timeout_sec: float = constants.DEFAULT_WORKER_TIMEOUT) -> None:
        """Stop the Temporal worker service gracefully with timeout."""
        self.logger.info("Stopping worker")
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                async with asyncio.timeout(timeout_sec):
                    with contextlib.suppress(asyncio.CancelledError):
                        await self._worker_task
            except TimeoutError:
                self.logger.warning(f"Worker stop timed out after {timeout_sec}s")
            self.worker_started_event.clear()

    async def restart(self) -> None:
        """Restart the Temporal worker."""
        await self.stop()
        await self.start()

    async def wait_until_ready(self, timeout_sec: float = constants.DEFAULT_WORKER_TIMEOUT) -> bool:
        """Wait for worker to be ready.

        Args:
            timeout_sec: Maximum time to wait in seconds

        Returns:
            bool: True if worker became ready, False if timeout

        """
        try:
            async with asyncio.timeout(timeout_sec):
                await self.worker_started_event.wait()
            return True
        except TimeoutError:
            return False

    async def run_with_retries(self, max_retries: int = constants.WORKER_START_MAX_RETRIES) -> None:
        """Start worker with retry logic.

        This is the unified logic used by ServiceManager, CLI, Docker, etc.
        Blocks until worker stops or fails permanently.
        """
        for attempt in range(max_retries):
            try:
                await self.start()
                # Block until worker fails or is stopped
                if self._worker_task is not None:
                    await self._worker_task
                break  # Normal shutdown
            except Exception as e:
                if attempt == max_retries - 1:
                    self.logger.exception(f"Worker failed permanently after {max_retries} attempts")
                    raise

                # Exponential backoff (cap at 60 seconds)
                delay = min(2**attempt, 60)
                self.logger.warning(f"Worker failed (attempt {attempt + 1}/{max_retries}), retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
                await self.stop()  # Clean shutdown before retry

    # Legacy methods for backward compatibility
    async def check_service_status(self) -> bool:
        """Check if the Temporal worker is running.

        Returns:
            bool: True if the worker is running, False otherwise

        """
        # Check for active worker pollers
        active_pollers = await _get_active_worker_pollers(self.default_task_queue)
        if active_pollers:
            self.worker_started_event.set()
            return True

        # Keep existing fallback logic as secondary check
        return self.worker_started_event.is_set()

    async def start_temporal_worker(self) -> None:
        """Start the Temporal worker service."""
        try:
            await self.start()
        except Exception:
            # If anything fails, try to clean up
            await self.stop()
            raise

    async def stop_temporal_worker(self) -> None:
        """Stop the Temporal worker service."""
        try:
            await self.stop()
            self.logger.info("Temporal worker shutdown complete")
        except Exception:
            self.logger.exception("Error stopping worker")
            # Continue with cleanup even if there's an error
            self.worker_started_event.clear()
            if self._worker_task:
                self._worker_task.cancel()


if __name__ == "__main__":
    import asyncio

    from awa.core.engine.temporal_client import TemporalClient

    async def main() -> None:
        client = await TemporalClient.create()
        worker = TemporalWorker(client)
        await worker.run_with_retries()

    asyncio.run(main())
