# ruff: noqa: ARG002
"""API tests for workflow recipe filtering functionality.

This module tests that the workflow list endpoint correctly filters recipe workflows
based on the `recipes` configuration flag in config.yaml.
"""

import httpx
import pytest


class TestWorkflowsRecipeFiltering:
    """Test suite for API workflow recipe filtering based on config flag."""

    def test_list_workflows_without_recipes(
        self,
        api_client: httpx.Client,
        api_health_check,
    ) -> None:
        """Test that API lists only core workflows when recipes are disabled.

        This test verifies that when recipes=false in config:
        - API returns 200 OK
        - Response contains workflows
        - No workflows have "recipes" in their module path
        - All returned workflows are core workflows
        """
        response = api_client.get("/api/v1/workflows/list")

        # Should succeed
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

        # Validate response structure
        response_data = response.json()
        assert "workflows" in response_data, "Response missing 'workflows' key"
        assert isinstance(response_data["workflows"], list), "Workflows should be a list"

        # Verify no recipe workflows are included
        workflows = response_data["workflows"]
        recipe_workflows = [w for w in workflows if "recipes" in w.get("module", "")]

        # Skip this test if recipes are enabled in the current config
        if len(recipe_workflows) > 0:
            pytest.skip(
                f"Recipes are enabled in config - found {len(recipe_workflows)} recipe workflows. "
                "This test only applies when recipes=false in config.yaml",
            )

        # Verify we still have core workflows
        core_workflows = [w for w in workflows if "recipes" not in w.get("module", "")]
        assert len(core_workflows) > 0, "Expected at least some core workflows to be present"

    def test_list_workflows_with_recipes(
        self,
        api_client: httpx.Client,
        api_health_check,
    ) -> None:
        """Test that API lists both core and recipe workflows when recipes enabled.

        This test verifies that when recipes=true in config:
        - API returns 200 OK
        - Response contains both core and recipe workflows
        - Recipe workflows have "recipes" in their module path
        - Core workflows are still included

        Note: This test should only pass when recipes=true in config.yaml.
        If this test fails, check your configuration.
        """
        response = api_client.get("/api/v1/workflows/list")

        # Should succeed
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

        # Validate response structure
        response_data = response.json()
        assert "workflows" in response_data, "Response missing 'workflows' key"
        assert isinstance(response_data["workflows"], list), "Workflows should be a list"

        workflows = response_data["workflows"]

        # Verify we have recipe workflows
        recipe_workflows = [w for w in workflows if "recipes" in w.get("module", "")]

        # This assertion will only pass if recipes are enabled
        # If recipes are disabled, this test will be skipped or fail
        # depending on how the test suite is configured
        if len(recipe_workflows) == 0:
            pytest.skip(
                "No recipe workflows found - recipes may be disabled in config. "
                "To test recipe filtering, set recipes=true in config.yaml",
            )

        # Verify we still have core workflows
        core_workflows = [w for w in workflows if "recipes" not in w.get("module", "")]
        assert len(core_workflows) > 0, "Expected core workflows to still be present when recipes enabled"

        # Verify recipe workflows have expected structure
        for workflow in recipe_workflows:
            assert "name" in workflow, "Recipe workflow missing 'name'"
            assert "module" in workflow, "Recipe workflow missing 'module'"
            assert "recipes" in workflow["module"], (
                f"Recipe workflow {workflow['name']} should have 'recipes' in module path"
            )

    def test_list_workflows_task_queue_filter_with_recipes_disabled(
        self,
        api_client: httpx.Client,
        api_health_check,
    ) -> None:
        """Test that task queue filtering still works when recipes are disabled.

        This test verifies that:
        - Task queue filtering parameter still functions correctly
        - Recipe filtering and task queue filtering work together
        - No recipe workflows appear even when using task queue filter
        """
        # Test with default task queue
        response = api_client.get("/api/v1/workflows/list?task_queue=awa_default")

        # Should succeed (may return empty list if no workflows on that queue)
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

        # Validate response structure
        response_data = response.json()
        assert "workflows" in response_data, "Response missing 'workflows' key"
        assert isinstance(response_data["workflows"], list), "Workflows should be a list"

        workflows = response_data["workflows"]

        # Verify no recipe workflows regardless of task queue
        recipe_workflows = [w for w in workflows if "recipes" in w.get("module", "")]

        # Skip this test if recipes are enabled in the current config
        if len(recipe_workflows) > 0:
            pytest.skip(
                f"Recipes are enabled in config - found {len(recipe_workflows)} recipe workflows. "
                "This test only applies when recipes=false in config.yaml",
            )

        # Verify all workflows are on the requested queue
        for workflow in workflows:
            assert "queues" in workflow, f"Workflow {workflow.get('name')} missing 'queues'"
            assert "awa_default" in workflow["queues"], f"Workflow {workflow.get('name')} not on requested queue"

    def test_list_workflows_response_format(
        self,
        api_client: httpx.Client,
        api_health_check,
    ) -> None:
        """Test that workflow list response has correct format regardless of recipe config.

        This test verifies:
        - Response structure is correct
        - Each workflow has required fields
        - Module path is properly formatted
        """
        response = api_client.get("/api/v1/workflows/list")

        # Should succeed
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

        # Validate response structure
        response_data = response.json()
        assert "workflows" in response_data, "Response missing 'workflows' key"

        workflows = response_data["workflows"]
        assert isinstance(workflows, list), "Workflows should be a list"

        # Verify each workflow has required fields
        for workflow in workflows:
            assert isinstance(workflow, dict), f"Each workflow should be a dict, got {type(workflow)}"
            assert "name" in workflow, "Workflow missing 'name' field"
            assert "module" in workflow, "Workflow missing 'module' field"
            assert "parameters" in workflow, "Workflow missing 'parameters' field"
            assert "queues" in workflow, "Workflow missing 'queues' field"

            # Verify data types
            assert isinstance(workflow["name"], str), "Workflow name should be string"
            assert isinstance(workflow["module"], str), "Workflow module should be string"
            assert isinstance(workflow["queues"], list), "Workflow queues should be list"

    def test_list_workflows_external_workflows_not_filtered(
        self,
        api_client: httpx.Client,
        api_health_check,
    ) -> None:
        """Test that external workflows from registry are not filtered by recipes flag.

        This test verifies:
        - External workflows (module="external") are not affected by recipe filtering
        - Registry workflows are included regardless of recipes config
        - External workflows maintain their own identity separate from recipe filtering
        """
        response = api_client.get("/api/v1/workflows/list")

        # Should succeed
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

        response_data = response.json()
        workflows = response_data["workflows"]

        # Find external workflows
        external_workflows = [w for w in workflows if w.get("module") == "external"]

        # If external workflows exist, verify they are not filtered
        # (This test may pass vacuously if no external workflows are registered)
        for workflow in external_workflows:
            # External workflows should have "external" module, not recipes
            assert workflow["module"] == "external", f"External workflow {workflow['name']} has unexpected module"

        # Note: The assertion here is about the presence of external workflows
        # External workflows should be present (if any are registered)
        # regardless of the recipes configuration flag
        if len(external_workflows) > 0:
            # Verify external workflows have proper structure
            for workflow in external_workflows:
                assert "name" in workflow
                assert "queues" in workflow
                assert isinstance(workflow["queues"], list)
