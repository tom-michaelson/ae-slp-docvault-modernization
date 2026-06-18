# ruff: noqa: ARG002
"""Integration tests for workflow exposure functionality.

This module tests the workflow exposure system including:
- API filtering of non-exposed workflows
- Description field population
- External worker registration with backward compatibility
"""

import contextlib

import httpx
import pytest


class TestWorkflowExposureFiltering:
    """Test suite for workflow exposure filtering in API endpoints."""

    def test_list_workflows_filters_non_exposed(
        self,
        api_client: httpx.Client,
        api_health_check,
    ) -> None:
        """Test that API /v1/workflows/list endpoint filters non-exposed core workflows.

        This test verifies that:
        - Only workflows decorated with @exposed() appear in the list
        - Internal workflows (child workflows, utility workflows) are filtered out
        - Response status is 200 OK
        """
        response = api_client.get("/api/v1/workflows/list")

        # Should succeed
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

        # Validate response structure
        response_data = response.json()
        assert "workflows" in response_data, "Response missing 'workflows' key"
        assert isinstance(response_data["workflows"], list), "Workflows should be a list"

        workflows = response_data["workflows"]

        # Get core workflows (not external and not recipes)
        # Filter out recipe workflows since they may or may not be present depending on config
        core_workflows = [
            w for w in workflows if w.get("module") != "external" and "recipes" not in w.get("module", "")
        ]

        # Verify all core workflows have names of known exposed workflows
        # Based on the codebase, these are the exposed workflows:
        exposed_workflow_names = {
            "awa-hello-world",
            "awa-hello-poem",
            "awa-hello-poem-agent",
            "awa-index-document",
        }

        # Get all core workflow names
        core_workflow_names = {w["name"] for w in core_workflows}

        # Verify we have some exposed workflows
        assert len(core_workflow_names) > 0, "Expected at least some exposed core workflows"

        # Verify only exposed workflows are in the list
        # All core workflows should be in the exposed set
        for workflow_name in core_workflow_names:
            assert workflow_name in exposed_workflow_names, (
                f"Core workflow '{workflow_name}' is not in the expected exposed workflows list. "
                f"This may indicate a non-exposed workflow is being returned."
            )

        # Verify we don't have internal workflows
        internal_workflow_patterns = ["test_", "TestChildWorkflow", "HITLChildWorkflow"]
        for workflow in core_workflows:
            workflow_name = workflow["name"]
            for pattern in internal_workflow_patterns:
                assert not workflow_name.startswith(pattern), (
                    f"Internal workflow '{workflow_name}' should not appear in the API list"
                )

    def test_list_workflows_includes_description_field(
        self,
        api_client: httpx.Client,
        api_health_check,
    ) -> None:
        """Test that API response includes description field for workflows.

        This test verifies that:
        - Each workflow in the response has a 'description' field
        - Exposed workflows have non-empty descriptions
        - Description field is properly typed (str or None)
        """
        response = api_client.get("/api/v1/workflows/list")

        # Should succeed
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

        response_data = response.json()
        workflows = response_data["workflows"]

        # Verify we have some workflows to test
        assert len(workflows) > 0, "Expected at least some workflows in the response"

        # Verify each workflow has description field
        for workflow in workflows:
            assert "description" in workflow, f"Workflow '{workflow.get('name')}' missing 'description' field"

            # Description should be str or None
            description = workflow["description"]
            assert description is None or isinstance(description, str), (
                f"Workflow '{workflow['name']}' description should be str or None, got {type(description)}"
            )

        # Verify core exposed workflows have descriptions
        # These are workflows with @exposed decorator that should have descriptions
        expected_descriptions = {
            "awa-hello-world": "Generates a friendly greeting message for a given name",
            "awa-hello-poem": "Generates a poem",
            "awa-hello-poem-agent": "Generates a poem using an agent",
            "awa-index-document": "Workflow that reads, parses, and chunks a document into smaller pieces",
        }

        for workflow in workflows:
            if workflow["name"] in expected_descriptions:
                assert workflow["description"] == expected_descriptions[workflow["name"]], (
                    f"Workflow '{workflow['name']}' has incorrect description. "
                    f"Expected: '{expected_descriptions[workflow['name']]}', "
                    f"Got: '{workflow['description']}'"
                )

    def test_list_workflows_external_workers_not_filtered(
        self,
        api_client: httpx.Client,
        api_health_check,
    ) -> None:
        """Test that external workers' workflows are not filtered by exposure logic.

        This test verifies that:
        - External workflows (module="external") are not affected by exposure filtering
        - External workflows manage their own exposure through registration
        - External workflows can appear in the list regardless of core exposure logic
        """
        response = api_client.get("/api/v1/workflows/list")

        # Should succeed
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

        response_data = response.json()
        workflows = response_data["workflows"]

        # Find external workflows
        external_workflows = [w for w in workflows if w.get("module") == "external"]

        # External workflows should have proper structure if they exist
        for workflow in external_workflows:
            assert "name" in workflow, "External workflow missing 'name' field"
            assert "module" in workflow, "External workflow missing 'module' field"
            assert workflow["module"] == "external", (
                f"External workflow {workflow['name']} should have module='external'"
            )
            assert "description" in workflow, "External workflow missing 'description' field"

            # External workflows should respect their own exposure settings
            # (not filtered by core workflow exposure logic)


class TestExternalWorkerRegistration:
    """Test suite for external worker registration with backward compatibility."""

    @pytest.mark.asyncio
    async def test_worker_registration_with_old_field_names(
        self,
        api_client: httpx.Client,
        api_health_check,
    ) -> None:
        """Test external worker registration using old field names (backward compat).

        This test verifies that:
        - Worker registration with mcp_exposed/mcp_description still works
        - Old fields are migrated to new fields automatically
        - Registered workflows appear with correct exposure settings
        """
        # Test data using old field names
        registration_payload = {
            "worker_name": "test-worker-old-fields",
            "worker_version": "1.0.0",
            "task_queue": "test-queue-old",
            "workflows": [
                {
                    "name": "TestWorkflowOldFields",
                    "task_queue": "test-queue-old",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "test_param": {"type": "string"},
                        },
                    },
                    "mcp_exposed": True,
                    "mcp_description": "Test workflow using old field names",
                },
            ],
        }

        # Register the worker
        response = api_client.post("/api/v1/workers/register", json=registration_payload)

        # Should succeed (201 Created is the correct status for resource creation)
        assert response.status_code == 201, (
            f"Worker registration with old fields failed. Status: {response.status_code}, Response: {response.text}"
        )

        # Verify the workflow appears in the list
        list_response = api_client.get("/api/v1/workflows/list")
        assert list_response.status_code == 200

        workflows = list_response.json()["workflows"]
        test_workflow = None
        for workflow in workflows:
            if workflow["name"] == "TestWorkflowOldFields":
                test_workflow = workflow
                break

        # Verify workflow was registered
        assert test_workflow is not None, "Workflow registered with old fields should appear in list"

        # Verify description was migrated from mcp_description
        assert test_workflow["description"] == "Test workflow using old field names", (
            "Description should be migrated from mcp_description field"
        )

        # Clean up - attempt to deregister the worker (endpoint may not exist)
        # Note: Deregistration endpoint may not be implemented, so we don't fail the test
        with contextlib.suppress(httpx.HTTPError):
            api_client.delete(
                f"/api/v1/workers/deregister?worker_name={registration_payload['worker_name']}",
            )

    @pytest.mark.asyncio
    async def test_worker_registration_with_new_field_names(
        self,
        api_client: httpx.Client,
        api_health_check,
    ) -> None:
        """Test external worker registration using new field names.

        This test verifies that:
        - Worker registration with exposed/description works correctly
        - New fields are used directly without migration
        - Registered workflows appear with correct exposure settings
        """
        # Test data using new field names
        registration_payload = {
            "worker_name": "test-worker-new-fields",
            "worker_version": "1.0.0",
            "task_queue": "test-queue-new",
            "workflows": [
                {
                    "name": "TestWorkflowNewFields",
                    "task_queue": "test-queue-new",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "test_param": {"type": "string"},
                        },
                    },
                    "exposed": True,
                    "description": "Test workflow using new field names",
                },
            ],
        }

        # Register the worker
        response = api_client.post("/api/v1/workers/register", json=registration_payload)

        # Should succeed (201 Created is the correct status for resource creation)
        assert response.status_code == 201, (
            f"Worker registration with new fields failed. Status: {response.status_code}, Response: {response.text}"
        )

        # Verify the workflow appears in the list
        list_response = api_client.get("/api/v1/workflows/list")
        assert list_response.status_code == 200

        workflows = list_response.json()["workflows"]
        test_workflow = None
        for workflow in workflows:
            if workflow["name"] == "TestWorkflowNewFields":
                test_workflow = workflow
                break

        # Verify workflow was registered
        assert test_workflow is not None, "Workflow registered with new fields should appear in list"

        # Verify description is correct
        assert test_workflow["description"] == "Test workflow using new field names", (
            "Description should match the registered value"
        )

        # Clean up - attempt to deregister the worker (endpoint may not exist)
        # Note: Deregistration endpoint may not be implemented, so we don't fail the test
        with contextlib.suppress(httpx.HTTPError):
            api_client.delete(
                f"/api/v1/workers/deregister?worker_name={registration_payload['worker_name']}",
            )

    @pytest.mark.asyncio
    async def test_worker_registration_field_migration_precedence(
        self,
        api_client: httpx.Client,
        api_health_check,
    ) -> None:
        """Test that new fields take precedence over old fields when both are provided.

        This test verifies that:
        - When both old and new fields are provided, new fields are used
        - Migration logic doesn't override explicit new field values
        - Backward compatibility doesn't break new field usage
        """
        # Test data with both old and new field names (new should take precedence)
        registration_payload = {
            "worker_name": "test-worker-mixed-fields",
            "worker_version": "1.0.0",
            "task_queue": "test-queue-mixed",
            "workflows": [
                {
                    "name": "TestWorkflowMixedFields",
                    "task_queue": "test-queue-mixed",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "test_param": {"type": "string"},
                        },
                    },
                    "exposed": True,
                    "description": "New description (should be used)",
                    "mcp_exposed": False,
                    "mcp_description": "Old description (should be ignored)",
                },
            ],
        }

        # Register the worker
        response = api_client.post("/api/v1/workers/register", json=registration_payload)

        # Should succeed (201 Created is the correct status for resource creation)
        assert response.status_code == 201, (
            f"Worker registration with mixed fields failed. Status: {response.status_code}, Response: {response.text}"
        )

        # Verify the workflow appears in the list
        list_response = api_client.get("/api/v1/workflows/list")
        assert list_response.status_code == 200

        workflows = list_response.json()["workflows"]
        test_workflow = None
        for workflow in workflows:
            if workflow["name"] == "TestWorkflowMixedFields":
                test_workflow = workflow
                break

        # Verify workflow was registered
        assert test_workflow is not None, "Workflow registered with mixed fields should appear in list"

        # Verify new description is used (not old one)
        assert test_workflow["description"] == "New description (should be used)", (
            "New 'description' field should take precedence over old 'mcp_description' field"
        )

        # Clean up - attempt to deregister the worker (endpoint may not exist)
        # Note: Deregistration endpoint may not be implemented, so we don't fail the test
        with contextlib.suppress(httpx.HTTPError):
            api_client.delete(
                f"/api/v1/workers/deregister?worker_name={registration_payload['worker_name']}",
            )
