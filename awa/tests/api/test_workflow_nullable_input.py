"""Integration tests for nullable workflow input handling.

This module tests the API's handling of workflows with nullable/optional input parameters:
- Schema generation includes x-nullable-input flag
- Workflow execution with null input
- Workflow execution with provided input
"""

import httpx
import pytest


class TestNullableWorkflowInput:
    """Test suite for nullable workflow input functionality."""

    def test_workflow_list_includes_nullable_metadata(
        self,
        api_client: httpx.Client,
        api_health_check,  # noqa: ARG002
    ) -> None:
        """Test that /api/v1/workflows/list includes x-nullable-input indicator.

        This test verifies that:
        - Workflows with nullable inputs have 'x-nullable-input' in their parameters schema
        - The flag is set to True for nullable workflows
        - The schema structure is preserved (properties, types, descriptions)
        """
        response = api_client.get("/api/v1/workflows/list")

        # Should succeed
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

        response_data = response.json()
        assert "workflows" in response_data, "Response missing 'workflows' key"
        workflows = response_data["workflows"]

        # Find a workflow with nullable input (awa-201-generate-documentation-site)
        # This workflow has: workflow_input: Awa201WorkflowInput | SkipJsonSchema[None] = None
        nullable_workflow = None
        for workflow in workflows:
            if workflow["name"] == "awa-201-generate-documentation-site":
                nullable_workflow = workflow
                break

        # If the workflow doesn't exist in this environment, skip the test
        if nullable_workflow is None:
            pytest.skip("awa-201-generate-documentation-site workflow not found in this environment")

        # Verify the workflow has parameters
        assert "parameters" in nullable_workflow, "Workflow should have parameters field"
        parameters = nullable_workflow["parameters"]

        # Verify x-nullable-input flag is present and True
        assert "x-nullable-input" in parameters, "Nullable workflow should have 'x-nullable-input' in parameters schema"
        assert parameters["x-nullable-input"] is True, "'x-nullable-input' should be True for nullable workflows"

        # Verify schema structure is preserved
        assert "properties" in parameters, "Schema should have 'properties' field"
        assert "type" in parameters, "Schema should have 'type' field"
        assert parameters["type"] == "object", "Schema type should be 'object'"

    def test_workflow_list_non_nullable_no_flag(
        self,
        api_client: httpx.Client,
        api_health_check,  # noqa: ARG002
    ) -> None:
        """Test that non-nullable workflows don't have x-nullable-input flag.

        This test verifies that:
        - Workflows with required inputs don't have 'x-nullable-input' flag
        - Or if present, it's not True
        """
        response = api_client.get("/api/v1/workflows/list")

        # Should succeed
        assert response.status_code == 200

        response_data = response.json()
        workflows = response_data["workflows"]

        # Find a workflow with required input (awa-hello-world)
        # This workflow has: name: str (required parameter)
        required_workflow = None
        for workflow in workflows:
            if workflow["name"] == "awa-hello-world":
                required_workflow = workflow
                break

        # If the workflow doesn't exist, skip the test
        if required_workflow is None:
            pytest.skip("awa-hello-world workflow not found in this environment")

        # Verify the workflow has parameters
        parameters = required_workflow.get("parameters", {})

        # Verify x-nullable-input is either absent or not True
        if "x-nullable-input" in parameters:
            assert parameters["x-nullable-input"] is not True, (
                "Required workflow should not have 'x-nullable-input' set to True"
            )

    def test_execute_nullable_workflow_with_empty_input(
        self,
        api_client: httpx.Client,
        api_health_check,  # noqa: ARG002
    ) -> None:
        """Test executing a nullable workflow without providing input.

        This test verifies that:
        - Nullable workflows can be executed with empty string input
        - The execution starts successfully (returns workflow_id)
        - Response status is 200 OK
        """
        # Check if the workflow exists
        list_response = api_client.get("/api/v1/workflows/list")
        workflows = list_response.json()["workflows"]

        has_nullable_workflow = any(w["name"] == "awa-201-generate-documentation-site" for w in workflows)

        if not has_nullable_workflow:
            pytest.skip("awa-201-generate-documentation-site workflow not found")

        # Execute workflow with empty input
        response = api_client.post(
            "/api/v1/workflows",
            json={
                "name": "awa-201-generate-documentation-site",
                "input": "",  # Empty string for null input
            },
        )

        # Should succeed
        assert response.status_code == 200, (
            f"Expected status 200, got {response.status_code}. Response: {response.text}"
        )

        # Verify response indicates success
        response_data = response.json()
        assert "data" in response_data, "Response should include data field"
        assert response_data["data"] == "success", "Response should indicate success"

    def test_execute_nullable_workflow_with_provided_input(
        self,
        api_client: httpx.Client,
        api_health_check,  # noqa: ARG002
    ) -> None:
        """Test executing a nullable workflow with structured input.

        This test verifies that:
        - Nullable workflows can be executed with JSON input
        - The execution starts successfully
        - Response status is 200 OK
        """
        # Check if the workflow exists
        list_response = api_client.get("/api/v1/workflows/list")
        workflows = list_response.json()["workflows"]

        has_nullable_workflow = any(w["name"] == "awa-201-generate-documentation-site" for w in workflows)

        if not has_nullable_workflow:
            pytest.skip("awa-201-generate-documentation-site workflow not found")

        # Execute workflow with structured input
        import json

        input_payload = {
            "target_dir": "/tmp/test-docs",  # noqa: S108
            "agent_provider": "claude",
        }

        response = api_client.post(
            "/api/v1/workflows",
            json={
                "name": "awa-201-generate-documentation-site",
                "input": json.dumps(input_payload),
            },
        )

        # Should succeed
        assert response.status_code == 200, (
            f"Expected status 200, got {response.status_code}. Response: {response.text}"
        )

        # Verify response indicates success
        response_data = response.json()
        assert "data" in response_data, "Response should include data field"
        assert response_data["data"] == "success", "Response should indicate success"

    def test_execute_required_workflow_without_input_accepted(
        self,
        api_client: httpx.Client,
        api_health_check,  # noqa: ARG002
    ) -> None:
        """Test that required workflows are accepted even without input.

        This test verifies that:
        - The API accepts workflow execution requests even with empty input
        - Input validation happens at the workflow level (asynchronously)
        - The workflow will fail during execution, not at the API level

        Note: This behavior means the API is lenient and accepts all requests,
        with validation happening during workflow execution.
        """
        # Check if the workflow exists
        list_response = api_client.get("/api/v1/workflows/list")
        workflows = list_response.json()["workflows"]

        has_required_workflow = any(w["name"] == "awa-hello-world" for w in workflows)

        if not has_required_workflow:
            pytest.skip("awa-hello-world workflow not found")

        # Execute workflow without required input
        response = api_client.post(
            "/api/v1/workflows",
            json={
                "name": "awa-hello-world",
                "input": "",  # Empty input for required parameter
            },
        )

        # Should succeed at API level (validation happens asynchronously in workflow)
        assert response.status_code == 200, (
            f"Expected status 200, got {response.status_code}. Response: {response.text}"
        )

        # Verify response indicates success
        response_data = response.json()
        assert "data" in response_data, "Response should include data field"
        assert response_data["data"] == "success", "Response should indicate success"

    def test_nullable_workflow_schema_has_properties(
        self,
        api_client: httpx.Client,
        api_health_check,  # noqa: ARG002
    ) -> None:
        """Test that nullable workflow schemas include property definitions.

        This test verifies that:
        - Nullable workflows expose their input model's properties
        - Properties include descriptions and types
        - Schema is suitable for UI form generation
        """
        response = api_client.get("/api/v1/workflows/list")
        workflows = response.json()["workflows"]

        # Find nullable workflow
        nullable_workflow = None
        for workflow in workflows:
            if workflow["name"] == "awa-201-generate-documentation-site":
                nullable_workflow = workflow
                break

        if nullable_workflow is None:
            pytest.skip("awa-201-generate-documentation-site workflow not found")

        parameters = nullable_workflow["parameters"]

        # Verify properties exist and are not empty
        assert "properties" in parameters, "Schema should have properties"
        properties = parameters["properties"]
        assert len(properties) > 0, "Properties should not be empty for nullable workflow"

        # Verify properties have proper structure (at least one property should exist)
        for prop_name, prop_schema in properties.items():
            # Each property should have a type or other schema information
            assert isinstance(prop_schema, dict), f"Property {prop_name} should be a dict"
            # Properties typically have 'type', 'description', etc.
            # Just verify it's a non-empty dict
            assert len(prop_schema) > 0, f"Property {prop_name} should have schema information"
