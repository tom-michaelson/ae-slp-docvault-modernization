"""Test data file writing utilities."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from tests.api.generation.core.constants import BASIC_SUFFIX, INVALID_SUFFIX, VARIANTS_SUFFIX
from tests.api.generation.core.validation import FileSystemValidator, TestDataValidator, ValidationError

logger = logging.getLogger(__name__)


class TestDataWriter:
    """Handles writing test data to files."""

    def __init__(self, output_dir: str | Path) -> None:
        """Initialize test data writer.

        Args:
            output_dir: Directory to write test data files

        Raises:
            ValidationError: If output directory cannot be created or is not writable

        """
        self.output_dir = Path(output_dir)

        # Validate and create output directory
        FileSystemValidator.validate_output_directory(self.output_dir)

        logger.info(f"Initialized TestDataWriter with output directory: {self.output_dir}")

    def write_basic_payload(self, schema_name: str, payload: dict[str, Any]) -> str:
        """Write basic payload to file.

        Args:
            schema_name: Name of the schema
            payload: Basic payload data

        Returns:
            Path to written file

        Raises:
            ValidationError: If payload structure is invalid

        """
        TestDataValidator.validate_payload_structure(payload, schema_name)

        filename = f"{self._schema_to_filename(schema_name)}_{BASIC_SUFFIX}.json"
        file_path = self.output_dir / filename

        self._write_json_file(file_path, payload)
        return str(file_path)

    def write_payload_variants(self, schema_name: str, variants: list[dict[str, Any]]) -> str:
        """Write payload variants to file.

        Args:
            schema_name: Name of the schema
            variants: List of payload variants

        Returns:
            Path to written file

        Raises:
            ValidationError: If variant structure is invalid

        """
        # Validate each variant
        for variant in variants:
            TestDataValidator.validate_variant_structure(variant)

        filename = f"{self._schema_to_filename(schema_name)}_{VARIANTS_SUFFIX}.json"
        file_path = self.output_dir / filename

        self._write_json_file(file_path, variants)
        return str(file_path)

    def write_invalid_payloads(self, schema_name: str, invalid_payloads: list[dict[str, Any]]) -> str:
        """Write invalid payloads to file.

        Args:
            schema_name: Name of the schema
            invalid_payloads: List of invalid payloads

        Returns:
            Path to written file

        Raises:
            ValidationError: If invalid payload structure is invalid

        """
        # Validate each invalid payload entry
        for invalid_payload in invalid_payloads:
            required_keys = ["description", "payload", "expected_error"]
            missing_keys = [key for key in required_keys if key not in invalid_payload]
            if missing_keys:
                raise ValidationError(
                    f"Invalid payload entry missing required keys: {missing_keys}",
                    {"missing_keys": missing_keys},
                )

        filename = f"{self._schema_to_filename(schema_name)}_{INVALID_SUFFIX}.json"
        file_path = self.output_dir / filename

        self._write_json_file(file_path, invalid_payloads)
        return str(file_path)

    def write_schema_data_set(
        self,
        schema_name: str,
        basic_payload: dict[str, Any] | None = None,
        variants: list[dict[str, Any]] | None = None,
        invalid_payloads: list[dict[str, Any]] | None = None,
    ) -> dict[str, str]:
        """Write complete test data set for a schema.

        Args:
            schema_name: Name of the schema
            basic_payload: Basic payload data
            variants: List of payload variants
            invalid_payloads: List of invalid payloads

        Returns:
            Dictionary mapping data types to file paths

        """
        files_written = {}

        if basic_payload:
            files_written[BASIC_SUFFIX] = self.write_basic_payload(schema_name, basic_payload)

        if variants:
            files_written[VARIANTS_SUFFIX] = self.write_payload_variants(schema_name, variants)

        if invalid_payloads:
            files_written[INVALID_SUFFIX] = self.write_invalid_payloads(schema_name, invalid_payloads)

        logger.info(f"Wrote {len(files_written)} files for schema {schema_name}")
        return files_written

    def _schema_to_filename(self, schema_name: str) -> str:
        """Convert schema name to filename format.

        Args:
            schema_name: CamelCase schema name

        Returns:
            snake_case filename

        """
        # Convert CamelCase to snake_case
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", schema_name)
        name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()
        return name

    def _write_json_file(self, file_path: Path, data: dict[str, Any] | list[dict[str, Any]]) -> None:
        """Write data to JSON file with proper formatting.

        Args:
            file_path: Path to write the file
            data: Data to write

        Raises:
            ValidationError: If file cannot be written

        """
        try:
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Generated test data file: {file_path}")
        except (OSError, TypeError) as e:
            raise ValidationError(
                f"Failed to write test data file {file_path}",
                {"original_error": str(e)},
            ) from e

    def cleanup_old_files(self, schema_names: list[str]) -> int:
        """Clean up old test data files for given schemas.

        Args:
            schema_names: List of schema names to clean up

        Returns:
            Number of files removed

        """
        files_removed = 0

        for schema_name in schema_names:
            base_filename = self._schema_to_filename(schema_name)
            patterns = [
                f"{base_filename}_{BASIC_SUFFIX}.json",
                f"{base_filename}_{VARIANTS_SUFFIX}.json",
                f"{base_filename}_{INVALID_SUFFIX}.json",
            ]

            for pattern in patterns:
                file_path = self.output_dir / pattern
                if file_path.exists():
                    try:
                        file_path.unlink()
                        files_removed += 1
                        logger.debug(f"Removed old file: {file_path}")
                    except OSError as e:
                        logger.warning(f"Failed to remove file {file_path}: {e}")

        if files_removed > 0:
            logger.info(f"Cleaned up {files_removed} old test data files")

        return files_removed
