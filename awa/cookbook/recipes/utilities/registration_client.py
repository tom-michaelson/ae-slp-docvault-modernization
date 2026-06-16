"""Client for registering workers with the AWA API."""

import os
from typing import Any

import httpx

from cookbook.recipes.utilities.constants import DEFAULT_AWA_API_BASE_URL
from cookbook.recipes.utilities.logger import LoggerComponent, get_logger

logger = get_logger(LoggerComponent.REGISTRATION)


class WorkerRegistrationClient:
    """Client for registering Temporal workers with the AWA API."""

    def __init__(self, base_url: str | None = None) -> None:
        """Initialize the registration client.

        Args:
            base_url: The base URL of the AWA API. If not provided, will use AWA_API_BASE_URL env var.

        Raises:
            ValueError: If no base URL is provided or found in environment.

        """
        self.base_url = base_url or os.environ.get("AWA_API_BASE_URL") or DEFAULT_AWA_API_BASE_URL
        if not self.base_url:
            raise ValueError("AWA_API_BASE_URL variable is required")
        self.base_url = self.base_url.rstrip("/")

    async def register_worker(self, registration_payload: dict[str, Any]) -> dict[str, Any]:
        """Register worker with the AWA API.

        Args:
            registration_payload: Dictionary containing worker registration details.

        Returns:
            Response data from the API.

        Raises:
            httpx.HTTPStatusError: If the API returns an error status code.
            httpx.RequestError: If there's a network or request error.

        """
        url = f"{self.base_url}/api/v1/workers/register"

        # Get service token for authentication if available
        service_token = os.getenv("AWA_SERVICE_TOKEN")
        headers = {}
        if service_token:
            headers["Authorization"] = f"Bearer {service_token}"
            logger.debug("Using service token for worker registration authentication")
        else:
            logger.debug("No service token configured for worker registration")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    json=registration_payload,
                    headers=headers,
                    timeout=30.0,  # 30 second timeout
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.exception(f"HTTP error during worker registration: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError:
                logger.exception("Request error during worker registration")
                raise
