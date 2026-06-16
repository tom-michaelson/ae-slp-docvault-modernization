import typer

from awa.core.cli.commands.api import app as add_api
from awa.core.cli.commands.docs import app as add_docs
from awa.core.cli.commands.init import app as add_init
from awa.core.cli.commands.mcp import app as add_mcp
from awa.core.cli.commands.run import app as add_run
from awa.core.cli.commands.server import app as add_server
from awa.core.cli.commands.start import app as add_start
from awa.core.cli.commands.status import app as add_status
from awa.core.cli.commands.stop import app as add_stop
from awa.core.cli.commands.ui import app as add_ui
from awa.core.cli.commands.worker import app as add_worker
from awa.core.cli.commands.workflows import app as add_workflows

from .commands.auth import app as add_auth

app = typer.Typer(pretty_exceptions_enable=True)

app.add_typer(add_run)
app.add_typer(add_mcp)
app.add_typer(add_api)
app.add_typer(add_docs)
app.add_typer(add_ui)
app.add_typer(add_start)
app.add_typer(add_status)
app.add_typer(add_stop)
app.add_typer(add_server)
app.add_typer(add_worker)
app.add_typer(add_init)
app.add_typer(add_workflows)
app.add_typer(add_auth, name="auth")
