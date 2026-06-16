"""Generate comprehensive API tests from OpenAPI specification."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from fastapi.openapi.utils import get_openapi

from awa.core.api.api import Api
from tests.api.generation.core.data_manager import TestDataManager
from tests.api.generation.generate_test_data import TestDataGenerator

# Configure logging for script output
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Global test data manager and schema info
test_data_manager = TestDataManager()
openapi_components = {}


def _extract_request_body_schema(spec: dict[str, Any]) -> str | None:
    """Extract request body schema reference from endpoint spec.

    Args:
        spec: OpenAPI endpoint specification

    Returns:
        Schema name (e.g., 'WorkflowRunPayload') or None if no request body

    """
    request_body = spec.get("requestBody")
    if not request_body:
        return None

    content = request_body.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema", {})

    # Handle schema references like "#/components/schemas/WorkflowRunPayload"
    schema_ref = schema.get("$ref")
    if schema_ref and schema_ref.startswith("#/components/schemas/"):
        return schema_ref.split("/")[-1]

    return None


def _resolve_schema_reference(schema_ref: str) -> dict[str, Any] | None:
    """Resolve a schema reference to its definition.

    Args:
        schema_ref: Schema reference name (e.g., 'WorkflowRunPayload')

    Returns:
        Schema definition dictionary or None if not found

    """
    if not openapi_components:
        return None

    schemas = openapi_components.get("schemas", {})
    return schemas.get(schema_ref)


def _get_payload_for_endpoint(path: str, method: str, spec: dict[str, Any]) -> dict[str, Any] | None:
    """Get appropriate test payload for an endpoint.

    Args:
        path: API endpoint path
        method: HTTP method
        spec: OpenAPI endpoint specification

    Returns:
        Test payload dictionary or None

    """
    # Extract schema name from request body
    schema_name = _extract_request_body_schema(spec)
    if not schema_name:
        return None

    # Get payload from test data manager
    return test_data_manager.get_payload_for_endpoint(path, method, schema_name)


def _get_payload_variants_for_endpoint(path: str, method: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Get payload variants for comprehensive endpoint testing.

    Args:
        path: API endpoint path
        method: HTTP method
        spec: OpenAPI endpoint specification

    Returns:
        List of payload variants

    """
    schema_name = _extract_request_body_schema(spec)
    if not schema_name:
        return []

    return test_data_manager.get_payload_variants_for_endpoint(path, method, schema_name)


def _get_invalid_payloads_for_endpoint(path: str, method: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Get invalid payloads for error testing of an endpoint.

    Args:
        path: API endpoint path
        method: HTTP method
        spec: OpenAPI endpoint specification

    Returns:
        List of invalid payloads with expected errors

    """
    schema_name = _extract_request_body_schema(spec)
    if not schema_name:
        return []

    return test_data_manager.get_invalid_payloads_for_endpoint(path, method, schema_name)


def _generate_request_code(method_lower: str, path: str, payload: dict[str, Any] | None) -> str:
    """Generate the appropriate request code for a test method.

    Args:
        method_lower: HTTP method in lowercase (e.g., 'post', 'get')
        path: API endpoint path
        payload: Request payload dictionary or None for GET requests

    Returns:
        Python code string for making the HTTP request

    """
    if payload and method_lower in ["post", "put", "patch"]:
        # Format payload as a Python dictionary string with proper indentation
        payload_str = json.dumps(payload, indent=8).replace("\n", "\n            ")
        return f"""payload = {payload_str}
            response = api_client.{method_lower}("{path}", json=payload)"""
    return f"""response = api_client.{method_lower}("{path}")"""


def generate_test_methods(paths: dict[str, Any]) -> str:
    """Generate test methods for each endpoint."""
    test_methods = []

    for path, methods in paths.items():
        for method, spec in methods.items():
            method_upper = method.upper()
            method_lower = method.lower()

            # Generate base function name
            base_function_name = f"test_{method}_{path.replace('/', '_').replace('{', '').replace('}', '').strip('_')}"

            # Generate comprehensive test suite for each endpoint
            test_methods.extend(
                _generate_happy_path_tests(path, method, method_upper, method_lower, base_function_name, spec),
            )
            test_methods.extend(
                _generate_error_handling_tests(path, method, method_upper, method_lower, base_function_name, spec),
            )
            test_methods.extend(
                _generate_schema_validation_tests(path, method, method_upper, method_lower, base_function_name, spec),
            )
            test_methods.extend(
                _generate_performance_tests(path, method, method_upper, method_lower, base_function_name, spec),
            )

    return "\n".join(test_methods)


def _generate_happy_path_tests(
    path: str,
    method: str,
    method_upper: str,
    method_lower: str,
    base_function_name: str,
    spec: dict[str, Any],
) -> list[str]:
    """Generate happy path tests."""
    tests = []
    expected_status = _get_expected_status_code(method, spec)
    custom_validations = _generate_custom_validations(spec, path, method)

    # Get payload for POST/PUT requests
    payload = _get_payload_for_endpoint(path, method, spec)
    request_code = _generate_request_code(method_lower, path, payload)

    # Main happy path test
    # Fix f-string conflicts by using proper string formatting
    test_method = f'''
    def {base_function_name}_happy_path(self, api_client: httpx.Client, api_health_check) -> None:
        """Test {method_upper} {path} - Happy Path."""
        try:
            {request_code}

            # Assert specific expected status code
            assert response.status_code == {expected_status}, (
                f"Expected status {expected_status}, got {{response.status_code}} for {path}"
            )

            # Validate response headers
            assert "content-type" in response.headers, f"Missing content-type header for {path}"
            assert response.headers["content-type"].startswith("application/json"), (
                f"Expected JSON content-type for {path}, "
                f"got {{response.headers.get('content-type', 'None')}}"
            )

            # Basic response validation
            response_data = response.json()
            assert isinstance(response_data, (dict, list)), f"Response is not dict or list for {path}"

            # Custom business logic validations
            {custom_validations}

            # Response time should be reasonable (under 8 seconds)
            # Increased from 5s to 8s to account for concurrent test execution
            assert response.elapsed.total_seconds() < 8.0, (
                f"Response too slow: {{response.elapsed.total_seconds():.2f}}s for {path}"
            )
        except httpx.RequestError as e:
            pytest.fail(f"Request failed for {path}: {{str(e)}}")
        except json.JSONDecodeError:
            pytest.fail(f"Invalid JSON response for {path}. Content: {{response.text[:200]}}...")'''

    tests.append(test_method)

    # Generate additional tests with payload variants for POST/PUT endpoints
    if payload and method_upper in ["POST", "PUT", "PATCH"]:
        payload_variants = _get_payload_variants_for_endpoint(path, method, spec)
        for i, variant in enumerate(payload_variants[:3]):  # Limit to first 3 variants
            variant_payload = variant.get("payload", variant)  # Handle both formats
            variant_description = variant.get("description", f"variant {i + 1}")
            variant_request_code = _generate_request_code(method_lower, path, variant_payload)

            variant_test = f'''
    def {base_function_name}_variant_{i + 1}(self, api_client: httpx.Client, api_health_check) -> None:
        """Test {method_upper} {path} - {variant_description}."""
        try:
            {variant_request_code}

            # Should return successful status
            assert response.status_code == {expected_status}

            # Validate response structure
            response_data = response.json()
            assert isinstance(response_data, (dict, list))
        except httpx.RequestError as e:
            pytest.fail(f"Request failed for {path} variant {i + 1}: {{str(e)}}")
        except json.JSONDecodeError:
            pytest.fail(f"Invalid JSON response for {path} variant {i + 1}. Content: {{response.text[:200]}}...")'''

            tests.append(variant_test)

    # Test with different valid parameters if endpoint has path parameters
    if "{" in path:
        # For now, we'll skip this as we don't have sample valid IDs
        # In a real scenario, you'd want to test with known valid IDs
        pass

    return tests


def _generate_error_handling_tests(
    path: str,
    method: str,
    method_upper: str,
    method_lower: str,
    base_function_name: str,
    spec: dict[str, Any],
) -> list[str]:
    """Generate comprehensive error handling tests."""
    tests = []

    # Test 404 for endpoints with path parameters
    if "{" in path:
        error_test = f'''
    def {base_function_name}_not_found(self, api_client: httpx.Client, api_health_check) -> None:
        """Test {method_upper} {path} - 404 Not Found."""
        try:
            invalid_path = "{path.replace("{", "invalid-").replace("}", "")}"
            response = api_client.{method_lower}(invalid_path)

            # Should return 404 for non-existent resource
            assert response.status_code == 404, (
                f"Expected 404 status, got {{response.status_code}} for invalid path {{invalid_path}}"
            )

            # Should still return JSON response
            content_type = response.headers.get("content-type", "")
            assert content_type.startswith("application/json"), "Expected JSON response for 404 error"
        except httpx.RequestError as e:
            pytest.fail(f"Request failed for invalid path test: {{str(e)}}")'''
        tests.append(error_test)

    # Test with invalid payloads for POST/PUT/PATCH
    if method_upper in ["POST", "PUT", "PATCH"]:
        invalid_payloads = _get_invalid_payloads_for_endpoint(path, method, spec)

        # Generate tests for each invalid payload
        for i, invalid_payload_data in enumerate(invalid_payloads[:5]):  # Limit to first 5
            payload = invalid_payload_data.get("payload", {})
            description = invalid_payload_data.get("description", f"invalid payload {i + 1}")
            expected_error = invalid_payload_data.get("expected_error", "400 or 422")

            # Generate safe function name from description
            safe_name = description.lower().replace(" ", "_").replace("'", "").replace('"', "")
            safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")[:50]  # Limit length

            invalid_test = f'''
    def {base_function_name}_{safe_name}(self, api_client: httpx.Client, api_health_check) -> None:
        """Test {method_upper} {path} - {description}."""
        try:
            invalid_payload = {json.dumps(payload, indent=8)}
            response = api_client.{method_lower}("{path}", json=invalid_payload)

            # Should return error status code ({expected_error})
            assert response.status_code in [400, 422, 404], (
                f"Expected error status code, got {{response.status_code}} for invalid payload test"
            )

            # Should return error details in JSON format
            if response.headers.get("content-type", "").startswith("application/json"):
                try:
                    error_data = response.json()
                    assert isinstance(error_data, dict), "Error response is not a JSON object"
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON in error response: {{response.text[:200]}}...")
        except httpx.RequestError as e:
            pytest.fail(f"Request failed for invalid payload test: {{str(e)}}")'''
            tests.append(invalid_test)

        # Test malformed JSON (if not already covered by invalid payloads)
        malformed_test = f'''
    def {base_function_name}_malformed_json(self, api_client: httpx.Client, api_health_check) -> None:
        """Test {method_upper} {path} - Malformed JSON."""
        try:
            # Send invalid JSON
            response = api_client.{method_lower}(
                "{path}",
                content="{{invalid json",
                headers={{"content-type": "application/json"}}
            )

            # Should return 400 or 422 for malformed data
            assert response.status_code in [400, 422], (
                f"Expected 400 or 422 status for malformed JSON, got {{response.status_code}}"
            )

            # Should return error details
            if response.headers.get("content-type", "").startswith("application/json"):
                try:
                    error_data = response.json()
                    assert isinstance(error_data, dict), "Error response is not a JSON object"
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON in error response for malformed JSON test: {{response.text[:200]}}...")
        except httpx.RequestError as e:
            pytest.fail(f"Request failed for malformed JSON test: {{str(e)}}")'''
        tests.append(malformed_test)

        # Test unsupported content type
        content_type_test = f'''
    def {base_function_name}_unsupported_content_type(self, api_client: httpx.Client, api_health_check) -> None:
        """Test {method_upper} {path} - Unsupported Content Type."""
        try:
            response = api_client.{method_lower}(
                "{path}",
                content="test data",
                headers={{"content-type": "text/plain"}}
            )

            # Should return 415 Unsupported Media Type or 400 Bad Request
            assert response.status_code in [400, 415, 422], (
                f"Expected 400, 415, or 422 status for unsupported content type, "
                f"got {{response.status_code}}"
            )

            # Optional: check for error response
            if response.headers.get("content-type", "").startswith("application/json"):
                try:
                    error_data = response.json()
                    assert isinstance(error_data, dict), "Error response is not a JSON object"
                except json.JSONDecodeError:
                    pass  # Some servers may not return JSON for content-type errors
        except httpx.RequestError as e:
            pytest.fail(f"Request failed for unsupported content type test: {{str(e)}}")'''
        tests.append(content_type_test)

    return tests


def _generate_schema_validation_tests(
    path: str,
    method: str,
    method_upper: str,
    method_lower: str,
    base_function_name: str,
    spec: dict[str, Any],
) -> list[str]:
    """Generate detailed schema validation tests."""
    tests = []

    # Get response schema for validation
    responses = spec.get("responses", {})
    success_response = responses.get("200") or responses.get("201") or responses.get("204")

    if success_response:
        # Get payload for POST/PUT requests
        payload = _get_payload_for_endpoint(path, method, spec)
        request_code = _generate_request_code(method_lower, path, payload)

        schema_test = f'''
    def {base_function_name}_schema_validation(self, api_client: httpx.Client, api_health_check) -> None:
        """Test {method_upper} {path} - Response Schema Validation."""
        try:
            {request_code}

            # Ensure successful response for schema validation
            assert response.status_code in [200, 201, 204], (
                f"Expected status 200/201/204, got {{response.status_code}} for {path}"
            )

            if response.status_code != 204:  # No content responses don't have body
                try:
                    response_data = response.json()
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON response for {path}: {{str(e)}}. Content: {{response.text[:200]}}...")

                # Validate response structure based on endpoint type
                {_generate_schema_validations(spec, path)}

                # Validate no unexpected fields (if response is dict)
                if isinstance(response_data, dict):
                    # Check for common required fields based on endpoint pattern
                    {_generate_field_validations(spec, path)}
        except httpx.RequestError as e:
            pytest.fail(f"Request failed for {path} schema validation: {{str(e)}}")'''
        tests.append(schema_test)

    return tests


def _generate_performance_tests(
    path: str,
    _method: str,  # Prefix with underscore to indicate intentionally unused
    method_upper: str,
    method_lower: str,
    base_function_name: str,
    _spec: dict[str, Any],  # Prefix with underscore to indicate intentionally unused
) -> list[str]:
    """Generate performance and reliability tests."""
    tests = []

    # Only generate performance tests for GET endpoints to avoid side effects
    if method_upper == "GET":
        perf_test = f'''
    @pytest.mark.performance
    def {base_function_name}_performance(self, api_client: httpx.Client, api_health_check) -> None:
        """Test {method_upper} {path} - Performance and Reliability."""
        import time

        # Test multiple requests for consistency
        response_times = []
        status_codes = []
        errors = []

        for i in range(3):
            try:
                start_time = time.time()
                response = api_client.{method_lower}("{path}")
                end_time = time.time()

                response_times.append(end_time - start_time)
                status_codes.append(response.status_code)
            except Exception as e:
                errors.append(f"Request {{i}} failed: {{str(e)}}")

        # If any requests failed, report the errors
        assert not errors, f"Some requests failed: {{errors}}"

        # All requests should return same status code (consistency)
        assert len(set(status_codes)) == 1, f"Inconsistent status codes: {{status_codes}}"

        # Average response time should be reasonable (under 3 seconds)
        # Increased from 2s to 3s to account for concurrent test execution
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 3.0, f"Average response time too slow: {{avg_response_time:.2f}}s for {path}"

        # No response should be extremely slow (under 8 seconds)
        # Increased from 5s to 8s to account for concurrent test execution
        assert max(response_times) < 8.0, f"Slowest response: {{max(response_times):.2f}}s for {path}"'''
        tests.append(perf_test)

    return tests


def _generate_schema_validations(spec: dict[str, Any], path: str) -> str:
    """Generate schema-specific validations based on endpoint."""
    validations = []
    tags = spec.get("tags", [])

    if "health" in tags:
        validations.extend(
            [
                "# Health endpoint must have status structure",
                'assert "status" in response_data',
                'assert isinstance(response_data["status"], dict)',
                'assert "temporal_service" in response_data["status"]',
                'assert "temporal_worker" in response_data["status"]',
                "",
                "# Each service status must have required fields",
                'for service_name, service_status in response_data["status"].items():',
                "    assert isinstance(service_status, dict)",
                '    assert "status" in service_status',
                '    assert service_status["status"] in ["up", "down"]',
            ],
        )
    elif "workflows" in tags:
        if "list" in path:
            validations.extend(
                [
                    "# Workflows list must have workflows array",
                    'assert "workflows" in response_data',
                    'assert isinstance(response_data["workflows"], list)',
                    "",
                    "# Each workflow must have required fields",
                    'for workflow in response_data["workflows"]:',
                    "    assert isinstance(workflow, dict)",
                    '    assert "name" in workflow',
                    '    assert "module" in workflow',
                    '    assert isinstance(workflow["name"], str)',
                    '    assert isinstance(workflow["module"], str)',
                ],
            )
        elif "runs" in path:
            validations.extend(
                [
                    "# Workflow runs response validation",
                    "if isinstance(response_data, list):",
                    "    # List of runs",
                    "    for run in response_data:",
                    "        assert isinstance(run, dict)",
                    "else:",
                    "    # Single run or paginated response",
                    "    assert isinstance(response_data, dict)",
                ],
            )

    return "\n            ".join(validations)


def _generate_field_validations(_spec: dict[str, Any], _path: str) -> str:
    """Generate field-level validations."""
    validations = []

    # Common validations for all endpoints
    validations.extend(
        [
            "# Response should not contain null values for required fields",
            'def check_no_null_required_fields(obj, path=""):',
            "    if isinstance(obj, dict):",
            "        for key, value in obj.items():",
            '            current_path = f"{path}.{key}" if path else key',
            '            if value is None and key in ["status", "name", "id"]:',
            '                raise AssertionError(f"Required field {current_path} is null")',
            "            check_no_null_required_fields(value, current_path)",
            "    elif isinstance(obj, list):",
            "        for i, item in enumerate(obj):",
            '            check_no_null_required_fields(item, f"{path}[{i}]")',
            "",
            "check_no_null_required_fields(response_data)",
        ],
    )

    return "\n                    ".join(validations)


def _get_expected_status_code(method: str, spec: dict[str, Any]) -> int:
    """Determine the expected status code for a successful request."""
    responses = spec.get("responses", {})

    # Return the first successful status code found
    for status_code in ["200", "201", "204"]:
        if status_code in responses:
            return int(status_code)

    # Default based on HTTP method
    if method.upper() == "POST":
        return 200  # AWA typically returns 200 for POST operations
    if method.upper() == "DELETE":
        return 204  # No Content
    return 200  # OK (for GET, PUT, PATCH, etc.)


def _generate_custom_validations(spec: dict[str, Any], path: str = "", method: str = "") -> str:
    """Generate custom validations based on endpoint spec."""
    validations = []

    # Add endpoint-specific validations based on tags or paths
    tags = spec.get("tags", [])
    if "health" in tags:
        validations.extend(
            [
                "# Health endpoint specific validations",
                'assert "status" in response_data',
                'assert "temporal_service" in response_data["status"]',
                'assert "temporal_worker" in response_data["status"]',
            ],
        )
    elif "workflows" in tags:
        # Different validations based on specific workflow endpoints
        if method.upper() == "POST" and "/workflows" in path and "/runs" not in path:
            # POST /api/v1/workflows returns {"data": "success"}
            validations.extend(
                [
                    "# Workflow creation endpoint validation",
                    'assert "data" in response_data',
                    'assert response_data["data"] == "success"',
                ],
            )
        elif "/list" in path or "/runs" in path:
            # GET endpoints return {"workflows": [...]}
            validations.extend(
                [
                    "# Workflow list/runs endpoint validation",
                    'assert "workflows" in response_data',
                    'assert isinstance(response_data["workflows"], list)',
                ],
            )
        else:
            # Generic workflow endpoint validation
            validations.extend(
                [
                    "# Generic workflow endpoint validation",
                    'assert "workflows" in response_data or isinstance(response_data, list) or "data" in response_data',
                ],
            )

    # Ensure proper indentation for validations
    if validations:
        return "\n            ".join(validations)
    return ""


def generate_test_file(openapi_spec: dict[str, Any]) -> str:
    """Generate complete test file content."""
    paths = openapi_spec.get("paths", {})

    file_content = f'''"""Auto-generated API tests from OpenAPI specification.

This file is automatically generated. Do not edit manually.
Regenerate using: python -m tests.api.generation.generate_api_tests

These tests run against a real API environment. Configure the target URL with:
- AWA_TEST_API_URL environment variable (e.g., export AWA_TEST_API_URL=http://localhost:8001)
- Or use the default from AWA configuration (localhost:8001)

Test Coverage:
- Happy Path: Successful requests with proper validation
- Error Handling: 404, 400, 422, 415 error scenarios
- Schema Validation: Response structure and field validation
- Performance: Response time and consistency checks (marked with @pytest.mark.performance)

To run all tests except performance tests:
    pytest -m "not performance" tests/api/

To run only performance tests:
    pytest -m "performance" tests/api/
"""

import httpx
import pytest
import time
import random
import json


class TestGeneratedAPI:
    """Auto-generated comprehensive tests for all API endpoints."""

    @classmethod
    def setup_class(cls):
        """Set up class for tests.

        This adds a short pause between test classes to avoid overwhelming the API server.
        """
        # Add slight delay between test runs to avoid overwhelming server
        # Use random delay between 0.1-0.5 seconds to prevent concurrent test instances
        # from all hitting the server at exactly the same time
        time.sleep(random.uniform(0.1, 0.5))

{generate_test_methods(paths)}
'''

    return file_content


def main() -> None:
    """Generate API tests from OpenAPI specification."""
    # Create API instance
    api = Api()

    # Generate OpenAPI spec
    openapi_spec = get_openapi(
        title="Agentic Workflow Accelerator API",
        version="1.0.0",
        description="API for the Agentic Workflow Accelerator",
        routes=api.app.routes,
    )

    # Initialize global components for schema processing
    global openapi_components  # noqa: PLW0603
    openapi_components = openapi_spec.get("components", {})

    # NEW: Generate test data from schemas before generating tests
    logger.info("Generating test data from OpenAPI schemas...")
    test_data_generator = TestDataGenerator(openapi_spec)
    generated_data = test_data_generator.generate_all_endpoint_data()

    # Report test data generation results
    if generated_data:
        logger.info(f"Generated test data for {len(generated_data)} schemas:")
        for schema_name, info in generated_data.items():
            files = info.get("files", {})
            logger.info(f"  - {schema_name}: {len(files)} files")
    else:
        logger.info("No new test data files generated (all endpoints may already have data)")

    # Generate test file
    test_content = generate_test_file(openapi_spec)

    # Create tests/api directory if it doesn't exist
    test_dir = Path("tests/api")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Write to test file
    test_file = test_dir / "test_generated_api.py"
    test_file.write_text(test_content, encoding="utf-8")

    logger.info("Generated API tests: %s", test_file)

    # Also save the OpenAPI spec for reference
    spec_file = test_dir / "openapi_spec.json"
    spec_file.write_text(json.dumps(openapi_spec, indent=2), encoding="utf-8")

    logger.info("Saved OpenAPI spec: %s", spec_file)

    # Create __init__.py for the tests/api package
    init_file = test_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""API tests package."""\n', encoding="utf-8")
        logger.info("Created package init file: %s", init_file)


if __name__ == "__main__":
    main()
