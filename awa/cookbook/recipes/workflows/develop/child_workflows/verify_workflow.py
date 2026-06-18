"""Batch-level verification: build + test with bounded fix loop."""

from pathlib import Path

from temporalio import workflow

from cookbook.recipes.workflows.develop import utils
from sdk_dist.python.awa.client import awa_activity
from sdk_dist.python.awa.client.models.command_result import CommandInput, CommandResult

_MAX_FIX_ATTEMPTS = 5


@workflow.defn(name="awa-develop-verify")
class VerifyWorkflow:
    """Run build then test; on failure invoke the appropriate fix slash command.

    Assumes a Gradle project at ``{target_repo_dir}/source``. Writes a
    ``.VERIFIED`` marker in ``verify_dir`` on success so re-runs skip the work.
    """

    @workflow.run
    async def run(
        self,
        domain: str,
        batch_id: str,
        working_dir: str,
        target_repo_dir: str,
        verify_dir: str,
        agent_provider: str = "claude",
    ) -> bool:
        verified_marker = Path(verify_dir) / ".VERIFIED"
        if await utils.file_exists_non_empty(verified_marker):
            workflow.logger.info(f"Batch {batch_id} already verified; skipping.")
            return True

        source_dir = str(Path(target_repo_dir) / "source" / "api")
        build_log = str(Path(verify_dir) / "build-errors.txt")
        test_log = str(Path(verify_dir) / "test-failures.txt")

        for attempt in range(1, _MAX_FIX_ATTEMPTS + 1):
            build_result = await _run(source_dir, "./gradlew clean build -x test")
            if not build_result.success:
                await _save(build_log, build_result.output)
                workflow.logger.warning(f"Build failed (attempt {attempt}).")
                if attempt == _MAX_FIX_ATTEMPTS:
                    return False
                await utils.run_slash_command(
                    slash_command=(
                        f"/fix-build-errors error_file={build_log} "
                        f"domain={domain} batch_id={batch_id} "
                        f"target_repo_dir={target_repo_dir}"
                    ),
                    name=f"FixBuild_{batch_id}_attempt{attempt}",
                    working_dir=working_dir,
                    agent_provider=agent_provider,
                )
                continue

            await _save(build_log, "")
            test_result = await _run(source_dir, "./gradlew test")
            if not test_result.success:
                await _save(test_log, test_result.output)
                workflow.logger.warning(f"Tests failed (attempt {attempt}).")
                if attempt == _MAX_FIX_ATTEMPTS:
                    return False
                await utils.run_slash_command(
                    slash_command=(
                        f"/fix-test-failures error_file={test_log} "
                        f"domain={domain} batch_id={batch_id} "
                        f"target_repo_dir={target_repo_dir}"
                    ),
                    name=f"FixTests_{batch_id}_attempt{attempt}",
                    working_dir=working_dir,
                    agent_provider=agent_provider,
                )
                continue

            await _save(test_log, "")
            await awa_activity.write_file(str(verified_marker), "ok")
            return True

        return False


async def _run(working_dir: str, command: str) -> CommandResult:
    return await awa_activity.run_command(
        CommandInput(command=command, working_dir=working_dir),
    )


async def _save(path: str, content: str) -> None:
    await awa_activity.write_file(path, content)
