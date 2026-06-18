"""Shared constants for test data generation scripts."""

from __future__ import annotations

# Schema parsing constants
MIN_NAME_PARTS_FOR_SCHEMA = 2

# File naming constants
GENERATED_DIR_NAME = "generated"
BASIC_SUFFIX = "basic"
VARIANTS_SUFFIX = "variants"
INVALID_SUFFIX = "invalid"

# Test data generation limits
MAX_INVALID_CASES = 10
MAX_OPTIONAL_FIELDS = 2
MAX_ARRAY_ITEMS = 2

# Default values
DEFAULT_TEST_DATA_DIR = "tests/api/test-data"
DEFAULT_GENERATED_DIR = "tests/api/test-data/generated"

# HTTP methods for endpoint processing
SUPPORTED_HTTP_METHODS = {"POST", "PUT", "PATCH"}

# OpenAPI schema references
OPENAPI_SCHEMA_REF_PREFIX = "#/components/schemas/"
