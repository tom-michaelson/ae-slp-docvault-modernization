"""Phase 1: validate prerequisites — health-check both apps.

This phase used to invoke ``/visual-comparison.validate-prerequisites`` via the
agent, but the work is just two ``curl`` calls + writing a JSON result. Doing
it inline (via the ``run_command`` activity) is faster, deterministic, and
sidesteps an issue where the Claude CLI exits non-zero in AWA's subprocess
environment even when the agent completed successfully.

The slash command is still kept under ``.claude/commands/`` for interactive use.
"""

import shlex
from pathlib import Path

from temporalio import workflow

from cookbook.recipes.workflows.develop import utils
from sdk_dist.python.awa.client import awa_activity
from sdk_dist.python.awa.client.models.command_result import CommandInput

_HTTP_OK = 200
_HTTP_FOUND = 302


async def _http_status(url: str) -> int:
    """Return the HTTP status code from a curl HEAD-style probe, or 0 on failure."""
    cmd = CommandInput(
        command=(
            f'curl -s -o /dev/null -w "%{{http_code}}" --max-time 10 {shlex.quote(url)}'
        ),
        working_dir=str(Path.home()),
    )
    result = await awa_activity.run_command(cmd)
    raw = (result.output or "").strip()
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


@workflow.defn(name="awa-visual-page-comparison-validate-prerequisites")
class ValidatePrerequisitesWorkflow:
    @workflow.run
    async def run(
        self,
        page_key: str,
        legacy_url: str,
        new_url: str,
        docs_dir: str,
        project_root_dir: str,  # noqa: ARG002 — preserved for parent-workflow signature stability
        agent_provider: str = "claude",  # noqa: ARG002
    ) -> dict:
        output_path = (
            Path(docs_dir)
            / "entry-points"
            / "ui-pages"
            / page_key
            / "visual-comparison"
            / "ui-validation-result.json"
        )

        # Probe both apps.
        legacy_code = await _http_status(f"{legacy_url.rstrip('/')}/")
        new_code = await _http_status(f"{new_url.rstrip('/')}/")

        legacy_healthy = legacy_code in (_HTTP_OK, _HTTP_FOUND)
        new_healthy = new_code == _HTTP_OK

        result = {
            "pageKey": page_key,
            "legacyUrl": legacy_url,
            "newUrl": new_url,
            "legacyHealthy": legacy_healthy,
            "newHealthy": new_healthy,
            "legacyStatusCode": legacy_code,
            "newStatusCode": new_code,
            "legacyMessage": "" if legacy_healthy else f"HTTP {legacy_code}",
            "newMessage": "" if new_healthy else f"HTTP {new_code}",
        }
        await utils.write_json(output_path, result)
        workflow.logger.info(
            f"validate-prerequisites: legacy={legacy_code} new={new_code}",
        )
        return result
