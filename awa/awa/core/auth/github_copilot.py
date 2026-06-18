import logging
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import httpx
from loguru import logger

from . import token_store

# Official GitHub Copilot Extension client ID
CLIENT_ID = "Iv1.b507a08c87ecfe98"
DEVICE_CODE_URL = "https://github.com/login/device/code"
ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"  # noqa: S105
COPILOT_TOKEN_URL = "https://api.github.com/copilot_internal/v2/token"  # noqa: S105
USER_AGENT = "GitHubCopilotChat/0.26.7"
SCOPE = "read:user"
POLL_TIMEOUT = 300  # 5 minutes
HTTP_OK = 200


@contextmanager
def _suppress_http_logs() -> Generator[None, None, None]:
    """Temporarily suppress HTTP logs during polling."""
    httpx_logger = logging.getLogger("httpx")
    httpcore_logger = logging.getLogger("httpcore")
    original_httpx_level = httpx_logger.level
    original_httpcore_level = httpcore_logger.level

    try:
        httpx_logger.setLevel(logging.WARNING)
        httpcore_logger.setLevel(logging.WARNING)
        yield
    finally:
        httpx_logger.setLevel(original_httpx_level)
        httpcore_logger.setLevel(original_httpcore_level)


def initiate_device_flow() -> dict[str, Any]:
    """Initiate the GitHub OAuth device flow."""
    with _suppress_http_logs(), httpx.Client() as client:
        response = client.post(
            DEVICE_CODE_URL,
            json={"client_id": CLIENT_ID, "scope": SCOPE},
            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        return response.json()


def poll_for_token(device_code: str, interval: int) -> str | None:
    """Poll for the GitHub OAuth token."""
    start_time = time.time()
    with _suppress_http_logs():
        while time.time() - start_time < POLL_TIMEOUT:
            time.sleep(interval)
            with httpx.Client() as client:
                response = client.post(
                    ACCESS_TOKEN_URL,
                    json={
                        "client_id": CLIENT_ID,
                        "device_code": device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    },
                    headers={"Accept": "application/json", "User-Agent": USER_AGENT},
                )
                data = response.json()
                if "access_token" in data:
                    return data["access_token"]
                if data.get("error") == "authorization_pending":
                    continue
                return None
        return None


def get_copilot_token(github_token: str) -> dict[str, Any] | None:
    """Exchange the GitHub OAuth token for a Copilot API token."""
    with _suppress_http_logs():
        with httpx.Client() as client:
            response = client.get(
                COPILOT_TOKEN_URL,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {github_token}",
                    "User-Agent": USER_AGENT,
                    "Editor-Version": "vscode/1.99.3",
                    "Editor-Plugin-Version": "copilot-chat/0.26.7",
                    "Copilot-Integration-Id": "vscode-chat",
                },
            )
            if response.status_code == HTTP_OK:
                return response.json()
            logger.error(f"Failed to get Copilot token: {response.status_code} {response.text}")
        return None


def get_active_token() -> str | None:
    """Get the active Copilot token, refreshing if necessary."""
    credentials = token_store.load_credentials()
    github_copilot_creds = credentials.get("github_copilot")
    if not github_copilot_creds:
        return None

    if github_copilot_creds.get("expires_at", 0) > time.time() * 1000:
        return github_copilot_creds.get("copilot_token")

    refreshed_token_data = get_copilot_token(github_copilot_creds.get("github_token"))
    if not refreshed_token_data:
        return None

    store_credentials(
        github_token=github_copilot_creds.get("github_token"),
        copilot_token=refreshed_token_data["token"],
        expires_at=refreshed_token_data["expires_at"],
    )
    return refreshed_token_data["token"]


def store_credentials(github_token: str, copilot_token: str, expires_at: int) -> None:
    """Store the GitHub Copilot credentials."""
    credentials = token_store.load_credentials()
    credentials["github_copilot"] = {
        "type": "oauth",
        "github_token": github_token,
        "copilot_token": copilot_token,
        "expires_at": expires_at * 1000,  # Convert to milliseconds
    }
    token_store.store_credentials(credentials)


def load_credentials() -> dict[str, Any] | None:
    """Load the GitHub Copilot credentials."""
    credentials = token_store.load_credentials()
    return credentials.get("github_copilot")
