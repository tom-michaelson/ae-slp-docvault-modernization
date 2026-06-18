"""Test to ensure all API endpoints require authentication except for allowed exceptions."""

import inspect
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.routing import APIRoute

from awa.core.api.api import Api
from awa.core.api.auth import require_authenticated_user, require_service_authentication
from awa.core.api.routes.shared.health import health


class TestAuthenticationEnforcement:
    """Test suite to ensure all endpoints require authentication."""

    # List of endpoints that should NOT require authentication
    AUTHENTICATION_EXEMPT_ENDPOINTS = frozenset(
        {
            "/api/v1/health",  # Health check should always be public
            "/api/v1/agents/stream/{session_id}/live",  # Public streaming endpoint for development/testing
            "/openapi.json",  # OpenAPI spec should be public for integration
            "/docs",  # Swagger UI should be public for development
            "/docs/oauth2-redirect",  # OAuth redirect for Swagger UI
            "/redoc",  # ReDoc documentation should be public
        },
    )

    def test_all_endpoints_require_authentication(self) -> None:
        """Test that all API endpoints require authentication except for exempt ones.

        This test prevents developers from accidentally creating unprotected endpoints.
        All endpoints must use 'require_authenticated_user' as a dependency,
        or be listed in AUTHENTICATION_EXEMPT_ENDPOINTS.
        """
        # Create API instance to inspect routes
        api = Api()
        app = api.app

        # Get all routes from the FastAPI app
        unprotected_endpoints = []

        for route in app.routes:
            # Skip non-API routes (like static files, etc.)
            if not hasattr(route, "path") or not hasattr(route, "endpoint"):
                continue

            route_path = route.path
            endpoint_func = route.endpoint

            # Skip if this is an exempt endpoint
            if route_path in self.AUTHENTICATION_EXEMPT_ENDPOINTS:
                continue

            # Check if the endpoint has authentication either at endpoint level or router level
            has_endpoint_auth = self._endpoint_has_auth_dependency(endpoint_func)
            has_router_auth = self._route_has_auth_dependency(route)

            if not has_endpoint_auth and not has_router_auth:
                unprotected_endpoints.append(route_path)

        # Assert that no unprotected endpoints were found
        if unprotected_endpoints:
            pytest.fail(
                f"Found {len(unprotected_endpoints)} endpoint(s) that don't require authentication:\\n"
                + "\\n".join(f"  - {path}" for path in unprotected_endpoints)
                + "\\n\\nAll endpoints must use 'require_authenticated_user' or 'require_service_authentication' "
                + "dependency, except for exempt endpoints: "
                + ", ".join(self.AUTHENTICATION_EXEMPT_ENDPOINTS)
                + "\\n\\nTo fix: Add authentication dependency to endpoint or add to exempt list if truly public.",
            )

    def _endpoint_has_auth_dependency(self, endpoint_func: Callable[..., Any]) -> bool:
        """Check if an endpoint function has an authentication dependency.

        Args:
            endpoint_func: The FastAPI endpoint function to check

        Returns:
            bool: True if the endpoint has an authentication dependency, False otherwise

        """
        # Inspect the function signature for auth dependencies
        sig = inspect.signature(endpoint_func)

        # Check each parameter for authentication dependencies
        for param_name, param in sig.parameters.items():
            # Skip 'self' parameter for methods
            if param_name == "self":
                continue

            # Check if parameter has a default value that is a Depends() call
            if param.default != inspect.Parameter.empty and self._is_auth_dependency(param.default):
                return True

            # Check type annotations for Annotated types with Depends() metadata
            if hasattr(param.annotation, "__origin__") and hasattr(param.annotation, "__metadata__"):
                # This is an Annotated type, check its metadata
                for metadata in param.annotation.__metadata__:
                    if self._is_auth_dependency(metadata):
                        return True

        return False

    def _route_has_auth_dependency(self, route: APIRoute) -> bool:
        """Check if a route has authentication dependencies at the router level.

        Args:
            route: The FastAPI route to check

        Returns:
            bool: True if the route has authentication dependencies

        """
        # Check if route has dependant with dependencies
        if not hasattr(route, "dependant"):
            return False

        dependencies = getattr(route.dependant, "dependencies", [])

        # Check if any dependency is an auth dependency
        for dep in dependencies:
            if hasattr(dep, "call"):
                dep_func = dep.call
                if dep_func in (require_authenticated_user, require_service_authentication):
                    return True

        return False

    def _is_auth_dependency(self, dependency: object) -> bool:
        """Check if a dependency is an authentication dependency.

        Args:
            dependency: The dependency to check

        Returns:
            bool: True if it's an authentication dependency

        """
        # Check if it's a Depends() call
        if hasattr(dependency, "dependency"):
            dep_func = dependency.dependency
            # Accept both user authentication and service authentication
            return dep_func in (require_authenticated_user, require_service_authentication)

        return False

    def test_health_endpoint_is_not_protected(self) -> None:
        """Test that the health endpoint specifically does NOT require authentication."""
        # The health endpoint should not use any authentication dependencies
        assert not self._endpoint_has_auth_dependency(health), (
            "Health endpoint should not require authentication to allow monitoring tools "
            "and load balancers to check service status"
        )

    def test_authentication_exempt_list_is_minimal(self) -> None:
        """Test that we don't accidentally add too many exempt endpoints."""
        # This test serves as a reminder to be intentional about exempt endpoints
        max_exempt_endpoints = 6  # Adjusted for docs endpoints, health check, and streaming endpoint

        assert len(self.AUTHENTICATION_EXEMPT_ENDPOINTS) <= max_exempt_endpoints, (
            f"Found {len(self.AUTHENTICATION_EXEMPT_ENDPOINTS)} exempt endpoints, "
            f"but maximum allowed is {max_exempt_endpoints}. "
            "If you need more exempt endpoints, please review the security implications "
            "and update this test."
        )

    def test_all_workflow_endpoints_require_auth(self) -> None:
        """Specifically test that all workflow-related endpoints require authentication."""
        api = Api()
        app = api.app

        workflow_endpoints = []
        unprotected_workflow_endpoints = []

        for route in app.routes:
            if not hasattr(route, "path") or not hasattr(route, "endpoint"):
                continue

            # Check if this is a workflow-related endpoint
            if "/workflow" in route.path.lower():
                workflow_endpoints.append(route.path)

                # Skip exempt endpoints
                if route.path in self.AUTHENTICATION_EXEMPT_ENDPOINTS:
                    continue

                # Check if it requires authentication either at endpoint level or router level
                has_endpoint_auth = self._endpoint_has_auth_dependency(route.endpoint)
                has_router_auth = self._route_has_auth_dependency(route)

                if not has_endpoint_auth and not has_router_auth:
                    unprotected_workflow_endpoints.append(route.path)

        # Assert that all workflow endpoints are protected
        assert not unprotected_workflow_endpoints, (
            f"Found workflow endpoints that don't require authentication: "
            f"{unprotected_workflow_endpoints}. All workflow endpoints must be protected."
        )

        # Ensure we found some workflow endpoints (so the test is meaningful)
        assert len(workflow_endpoints) > 0, "No workflow endpoints found. This test may need to be updated."
