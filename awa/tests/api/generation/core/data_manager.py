"""Test data manager for loading and validating test data files."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from tests.api.generation.core.constants import (
    DEFAULT_TEST_DATA_DIR,
    GENERATED_DIR_NAME,
    MIN_NAME_PARTS_FOR_SCHEMA,
)

logger = logging.getLogger(__name__)


class TestDataManager:
    """Manages test data files for API test generation."""

    def __init__(self, test_data_dir: str | Path = DEFAULT_TEST_DATA_DIR) -> None:
        """Initialize the TestDataManager.

        Args:
            test_data_dir: Path to the directory containing test data files

        """
        self.test_data_dir = Path(test_data_dir)
        self.generated_data_dir = self.test_data_dir / GENERATED_DIR_NAME
        self.schema_mappings = self._discover_schema_mappings()
        self._validate_test_data_dir()

    def _discover_schema_mappings(self) -> dict[str, dict[str, str]]:
        """Auto-discover test data files and map them to schemas.

        Returns:
            Dictionary mapping schema names to their test data files

        """
        mappings = {}

        # Search both main directory and generated subdirectory
        search_dirs = [self.test_data_dir, self.generated_data_dir]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            # Look for files following the pattern: {schema_name}_{type}.json
            for json_file in search_dir.glob("*.json"):
                if json_file.name in ["README.md", "openapi_spec.json"]:
                    continue

                # Parse filename to extract schema and type
                name_parts = json_file.stem.split("_")
                if len(name_parts) >= MIN_NAME_PARTS_FOR_SCHEMA:
                    # Last part is the type (basic, variants, invalid)
                    data_type = name_parts[-1]
                    # Everything before is the schema name
                    schema_name_snake = "_".join(name_parts[:-1])
                    schema_name = self._snake_to_camel(schema_name_snake)

                    if schema_name not in mappings:
                        mappings[schema_name] = {}
                    # Generated files take precedence over manual files for the same schema+type
                    if data_type not in mappings[schema_name] or search_dir == self.generated_data_dir:
                        mappings[schema_name][data_type] = str(json_file)

        # Fallback: Legacy mapping for existing files in main directory
        legacy_mappings = {
            "WorkflowRunPayload": {
                "basic": "workflow_run_basic.json",
                "variants": "workflow_run_variants.json",
                "invalid": "invalid_payloads.json",
            },
        }

        # Merge legacy mappings for files that exist (only if not already mapped)
        for schema_name, files in legacy_mappings.items():
            if schema_name not in mappings:
                mappings[schema_name] = {}
            for data_type, filename in files.items():
                if data_type not in mappings[schema_name]:
                    file_path = self.test_data_dir / filename
                    if file_path.exists():
                        mappings[schema_name][data_type] = str(file_path)

        logger.info(f"Discovered test data for {len(mappings)} schemas: {list(mappings.keys())}")
        return mappings

    def _snake_to_camel(self, snake_str: str) -> str:
        """Convert snake_case to CamelCase.

        Args:
            snake_str: String in snake_case

        Returns:
            String in CamelCase

        """
        components = snake_str.split("_")
        return "".join(word.capitalize() for word in components)

    def _validate_test_data_dir(self) -> None:
        """Validate that the test data directory exists and log available files."""
        if not self.test_data_dir.exists():
            raise FileNotFoundError(f"Test data directory not found: {self.test_data_dir}")

        # Log discovered schemas and their available data types
        for schema_name, files in self.schema_mappings.items():
            available_types = list(files.keys())
            logger.debug(f"Schema {schema_name} has data types: {available_types}")

    def load_basic_payload(self, schema_name: str = "WorkflowRunPayload") -> dict[str, Any] | None:
        """Load a basic payload for the given schema.

        Args:
            schema_name: Name of the schema to get payload for

        Returns:
            Basic payload dictionary or None if not found

        """
        return self._load_schema_data(schema_name, "basic")

    def load_valid_payload_variants(self, schema_name: str = "WorkflowRunPayload") -> list[dict[str, Any]]:
        """Load multiple valid payload variants for testing.

        Args:
            schema_name: Name of the schema to get variants for

        Returns:
            List of payload variants with descriptions

        """
        data = self._load_schema_data(schema_name, "variants")
        return data if isinstance(data, list) else []

    def load_invalid_payloads(self, schema_name: str = "WorkflowRunPayload") -> list[dict[str, Any]]:
        """Load invalid payloads for error testing.

        Args:
            schema_name: Name of the schema to get invalid payloads for

        Returns:
            List of invalid payloads with expected errors

        """
        data = self._load_schema_data(schema_name, "invalid")
        return data if isinstance(data, list) else []

    def _load_schema_data(self, schema_name: str, data_type: str) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Load data for a specific schema and type.

        Args:
            schema_name: Name of the schema
            data_type: Type of data (basic, variants, invalid)

        Returns:
            Loaded data or None if not found

        """
        schema_files = self.schema_mappings.get(schema_name, {})
        file_path = schema_files.get(data_type)

        if not file_path:
            logger.debug(f"No {data_type} data file found for schema: {schema_name}")
            return None

        return self._load_json_file_from_path(Path(file_path))

    def get_payload_for_endpoint(self, path: str, method: str, schema_name: str | None = None) -> dict[str, Any] | None:
        """Get an appropriate payload for a specific endpoint.

        Args:
            path: API endpoint path
            method: HTTP method
            schema_name: Schema name if known

        Returns:
            Appropriate payload or None

        """
        # Try to use provided schema name first
        if schema_name and schema_name in self.schema_mappings:
            return self.load_basic_payload(schema_name)

        # Default mapping for known endpoints
        if (
            method.upper() == "POST"
            and "/workflows" in path
            and (schema_name == "WorkflowRunPayload" or not schema_name)
        ):
            return self.load_basic_payload("WorkflowRunPayload")
        if method.upper() == "POST" and "/workers/register" in path:
            return self.load_basic_payload("WorkerRegistration")

        # Add more endpoint-specific logic here as needed
        logger.info(f"No specific payload available for {method} {path}")
        return None

    def get_payload_variants_for_endpoint(
        self,
        path: str,
        method: str,
        schema_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get payload variants for comprehensive testing of an endpoint.

        Args:
            path: API endpoint path
            method: HTTP method
            schema_name: Schema name if known

        Returns:
            List of payload variants

        """
        # Try to use provided schema name first
        if schema_name and schema_name in self.schema_mappings:
            return self.load_valid_payload_variants(schema_name)

        # Default mapping for known endpoints
        if (
            method.upper() == "POST"
            and "/workflows" in path
            and (schema_name == "WorkflowRunPayload" or not schema_name)
        ):
            return self.load_valid_payload_variants("WorkflowRunPayload")
        if method.upper() == "POST" and "/workers/register" in path:
            return self.load_valid_payload_variants("WorkerRegistration")

        return []

    def get_invalid_payloads_for_endpoint(
        self,
        path: str,
        method: str,
        schema_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get invalid payloads for error testing of an endpoint.

        Args:
            path: API endpoint path
            method: HTTP method
            schema_name: Schema name if known

        Returns:
            List of invalid payloads with expected errors

        """
        # Try to use provided schema name first
        if schema_name and schema_name in self.schema_mappings:
            return self.load_invalid_payloads(schema_name)

        # Default mapping for known endpoints
        if (
            method.upper() == "POST"
            and "/workflows" in path
            and (schema_name == "WorkflowRunPayload" or not schema_name)
        ):
            return self.load_invalid_payloads("WorkflowRunPayload")
        if method.upper() == "POST" and "/workers/register" in path:
            return self.load_invalid_payloads("WorkerRegistration")

        return []

    def _load_json_file_common(self, file_path: Path) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Load and parse JSON data from a file path.

        Args:
            file_path: Full path to the JSON file to load

        Returns:
            Parsed JSON data or None if file not found or invalid

        """
        try:
            with file_path.open(encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Test data file not found: {file_path}")
            return None
        except json.JSONDecodeError:
            logger.exception(f"Invalid JSON in test data file {file_path}")
            return None
        except OSError:
            logger.exception(f"Error loading test data file {file_path}")
            return None

    def _load_json_file(self, filename: str) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Load and parse a JSON file from the test data directory.

        Args:
            filename: Name of the JSON file to load

        Returns:
            Parsed JSON data or None if file not found or invalid

        """
        file_path = self.test_data_dir / filename
        return self._load_json_file_common(file_path)

    def _load_json_file_from_path(self, file_path: Path) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Load and parse a JSON file from an absolute path.

        Args:
            file_path: Full path to the JSON file to load

        Returns:
            Parsed JSON data or None if file not found or invalid

        """
        return self._load_json_file_common(file_path)

    def list_available_workflows(self) -> list[str]:
        """Get a list of workflow names available in the test data.

        Returns:
            List of workflow names from variants file

        """
        variants = self.load_valid_payload_variants("WorkflowRunPayload")
        workflow_names = set()

        for variant in variants:
            if "payload" in variant and "name" in variant["payload"]:
                workflow_names.add(variant["payload"]["name"])

        return sorted(workflow_names)

    def get_workflow_input_variations(self, workflow_name: str) -> list[dict[str, Any]]:
        """Get input variations for a specific workflow.

        Args:
            workflow_name: Name of the workflow (e.g., 'awa-hello-human')

        Returns:
            List of input variations for the workflow

        """
        simple_name = workflow_name.replace("awa-", "").replace("-", "_")
        if simple_name == "hello_human":
            return self._load_json_file("hello_human_inputs.json") or []
        if simple_name == "hello_world":
            return self._load_json_file("hello_world_inputs.json") or []
        if simple_name == "transform":
            return self._load_json_file("transform_inputs.json") or []

        logger.info(f"No input variations available for workflow: {workflow_name}")
        return []

    def get_available_schemas(self) -> list[str]:
        """Get list of all schemas that have test data available.

        Returns:
            List of schema names

        """
        return list(self.schema_mappings.keys())

    def refresh_schema_mappings(self) -> None:
        """Refresh the schema mappings by re-scanning the test data directory."""
        self.schema_mappings = self._discover_schema_mappings()
        logger.info("Refreshed schema mappings")
