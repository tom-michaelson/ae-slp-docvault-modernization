"""Auth command implementation."""

import time
import webbrowser

import typer

from awa.core.auth import github_copilot
from awa.core.logger.logger import LoggerComponent, get_logger, init_logging

app = typer.Typer()
init_logging()
logger = get_logger(LoggerComponent.CLI)


@app.command(name="login")
def login(provider: str) -> None:
    """Login to a provider. Supported providers: github-copilot."""
    if provider == "github-copilot":
        device_flow_data = github_copilot.initiate_device_flow()
        logger.info("Opening browser for authentication...")
        logger.info(f"If the browser doesn't open, visit: {device_flow_data['verification_uri']}")
        logger.info(f"Enter code: {device_flow_data['user_code']}")
        webbrowser.open(device_flow_data["verification_uri"])
        logger.info("Waiting for authorization...")
        github_token = github_copilot.poll_for_token(device_flow_data["device_code"], device_flow_data["interval"])
        if github_token:
            copilot_token_data = github_copilot.get_copilot_token(github_token)
            if copilot_token_data:
                github_copilot.store_credentials(
                    github_token=github_token,
                    copilot_token=copilot_token_data["token"],
                    expires_at=copilot_token_data["expires_at"],
                )
                logger.info("✅ GitHub Copilot authenticated successfully.")
            else:
                logger.error("❌ Failed to get Copilot token.")
                raise typer.Exit(1)
        else:
            logger.error("❌ GitHub Copilot authentication failed.")
            raise typer.Exit(1)

    else:
        logger.error(f"Provider {provider} not supported.")
        raise typer.Exit(1)


@app.command(name="logout")
def logout(provider: str) -> None:
    """Logout from a provider."""
    if provider == "github-copilot":
        credentials = github_copilot.load_credentials()
        if credentials:
            github_copilot.store_credentials("", "", 0)
            logger.info("✅ Logged out from GitHub Copilot.")
        else:
            logger.info("You are not logged in to GitHub Copilot.")
    else:
        logger.error(f"Provider {provider} not supported.")
        raise typer.Exit(1)


@app.command(name="status")
def status() -> None:
    """Show authentication status for all providers."""
    credentials = github_copilot.load_credentials()
    if credentials and credentials.get("expires_at", 0) > time.time() * 1000:
        logger.info("✅ Logged in to GitHub Copilot.")
    else:
        logger.info("You are not logged in to GitHub Copilot.")
