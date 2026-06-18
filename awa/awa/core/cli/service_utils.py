"""Service validation utilities for AWA CLI commands."""

import typer

from awa.core.cli import constants


def get_all_service_names() -> list[str]:
    """Get all valid service names.

    Returns:
        List of all valid service names

    """
    return [
        constants.SERVICE_TEMPORAL_SERVER,
        constants.SERVICE_TEMPORAL_WORKER,
        constants.SERVICE_API,
        constants.SERVICE_UI,
    ]


def parse_service_list(services_str: str) -> list[str]:
    """Parse comma-delimited service string into a list of service names.

    Args:
        services_str: Comma-delimited string of service names (e.g., "api,ui" or "temporal_server")

    Returns:
        List of service names

    Raises:
        typer.Exit: If any service name is invalid

    """
    if not services_str or not services_str.strip():
        typer.echo("Error: Services string cannot be empty", err=True)
        raise typer.Exit(1)

    # Split by comma and strip whitespace
    services = [service.strip() for service in services_str.split(",")]

    # Remove empty strings
    services = [service for service in services if service]

    # Remove duplicates while preserving order
    seen = set()
    unique_services = []
    for service in services:
        if service not in seen:
            seen.add(service)
            unique_services.append(service)

    if not unique_services:
        typer.echo("Error: No valid service names provided", err=True)
        raise typer.Exit(1)

    # Validate each service name
    validate_service_names(unique_services)

    return unique_services


def validate_service_names(service_names: list[str]) -> None:
    """Validate that all service names are valid.

    Args:
        service_names: List of service names to validate

    Raises:
        typer.Exit: If any service name is invalid

    """
    valid_services = get_all_service_names()
    invalid_services = [name for name in service_names if name not in valid_services]

    if invalid_services:
        typer.echo(f"Error: Invalid service name(s): {', '.join(invalid_services)}", err=True)
        typer.echo(f"Valid service names are: {', '.join(valid_services)}", err=True)
        raise typer.Exit(1)
