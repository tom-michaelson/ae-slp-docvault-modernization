# AWA Unit Testing Standards
# ------------------------------------------------------
# This file defines comprehensive standards for writing unit tests in the AWA recipes project.
# These standards ensure consistent, maintainable, and effective tests across the codebase.

version: "1.0.0"

metadata:
  description: "Comprehensive unit testing standards for AWA Python development using pytest"
  applies_to: ["*.py", "tests/**/*.py"]
  author: "AWA Team"

# Core Testing Framework
framework:
  primary: "pytest"
  extensions:
    - "pytest-asyncio"  # For testing async code
    - "pytest-cov"      # For test coverage
    - "pytest-timeout"  # For test timeouts

# Overall Testing Structure and Organization
structure:
  # Test file naming convention
  naming:
    pattern: "test_*.py"
    examples:
      - "test_file_io.py"
      - "test_api.py"

  # Test organization
  organization:
    guideline: "Group related tests in classes with descriptive names"
    class_naming: "Test{ComponentName}"
    examples:
      - "TestFileIOActivities"
      - "TestJsonUtils"

  # Test method naming
  method_naming:
    pattern: "test_{feature/scenario}_{expected_outcome}"
    examples:
      - "test_parse_json_valid_json_string"
      - "test_read_single_file_basic"

# Test Patterns and Design
patterns:
  # Core AAA Pattern
  aaa_pattern:
    description: "Structure tests using Arrange-Act-Assert pattern"
    example: |
      # Arrange
      file_path = "/test_file.txt"
      content = "hello world"

      # Act
      await activity_env.run(write_file_activity, path, content)
      result = await activity_env.run(read_file_activity, path)

      # Assert
      assert result == content
      assert memfs.exists(path)

  # Assertion Guidelines
  assertions:
    rules:
      - "Use specific assertions that clearly communicate intent"
      - "Assert only what's relevant to the test case"
      - "Test one behavior per test method"
    examples:
      - "assert result == expected"
      - "assert result is not None"
      - "assert 'error' in str(exception_info.value)"
      - "assert isinstance(result, list)"
      - "assert mock_function.call_count == 3"

# Fixtures and Test Data Management
fixtures:
  purpose: "Use fixtures for consistent test setup, teardown, and test data"
  scope_usage:
    function: "Default; use for most test fixtures that need isolation"
    class: "For fixtures shared across test methods in a class"
    module: "For fixtures shared across test classes in a module"
    session: "For expensive setup operations shared across tests"

  examples:
    basic: |
      @pytest.fixture
      def sample_data():
          return {"key": "value", "number": 42}

    filesystem: |
      @pytest.fixture
      def memfs() -> Generator[MemoryFileSystem, None, None]:
          """Provide an in-memory filesystem for testing."""
          fs = fsspec.filesystem("memory")
          with patch("awa.core.utils.file_system_utils.FileSystemUtils.get_filesystem", return_value=fs):
              yield fs
              fs.rm("/", recursive=True)  # Clean up after each test

    temporal_activity: |
      @pytest.fixture
      def activity_env():
          return ActivityEnvironment()

# Mocking Strategies
mocking:
  boundaries:
    description: "Mock at system boundaries"
    rules:
      - "Mock external services, file I/O, and network calls"
      - "Mock AWA utilities rather than built-in functions"
      - "Use clear and explicit return values for mocks"

  tools:
    unittest_mock: "Use unittest.mock.patch for object mocking"
    pytest_monkeypatch: "Use pytest.monkeypatch for environment variables"
    asyncmock: "Use AsyncMock for mocking async functions"

  examples:
    simple_mock: |
      @patch("awa.core.utils.file_system_utils.FileSystemUtils.get_filesystem")
      def test_with_mock(mock_get_fs):
          mock_fs = MagicMock()
          mock_get_fs.return_value = mock_fs
          # Test code that uses the filesystem

    async_mock: |
      @patch("awa.core.activities.file_io.read_file_activity")
      async def test_with_async_mock(mock_read):
          mock_read.return_value = "mock content"
          # Test async code that reads files

# Specific Test Types
test_types:
  # Unit Tests
  unit:
    purpose: "Test individual components in isolation"
    scope: "Single function, method, or class"
    mocking: "Mock all external dependencies"
    coverage_target: "High (>90%)"

  # Integration Tests
  integration:
    purpose: "Test interactions between components"
    scope: "Multiple components working together"
    mocking: "Mock external system boundaries only"
    coverage_target: "Medium (>70%)"

  # Async Tests
  async_tests:
    description: "Tests for asynchronous code"
    decorator: "@pytest.mark.asyncio"
    fixtures: "Use @pytest_asyncio.fixture for async setup"
    mocking: "Use AsyncMock for async functions"
    example: |
      @pytest.mark.asyncio
      async def test_async_function():
          result = await my_async_function()
          assert result == expected_value

# Temporal Framework Testing
temporal:
  workflow_tests:
    description: "Tests for Temporal workflows"
    environment: "Use WorkflowEnvironment for integration tests"
    isolation: "Mock activities to isolate workflow logic"
    example: |
      @pytest.mark.asyncio
      async def test_hello_workflow():
          async with await WorkflowEnvironment.start_local() as env:
              client = await env.client()

              # Mock activities if needed
              env.mock_activities(say_hello_activity=lambda name: f"Mock hello {name}")

              # Run the workflow
              result = await client.execute_workflow(
                  HelloWorkflow.run,
                  "World",
                  id="test-workflow-id",
                  task_queue="test-task-queue"
              )

              assert result == "Mock hello World"

  activity_tests:
    description: "Tests for Temporal activities"
    environment: "Use ActivityEnvironment"
    mocking: "Mock external dependencies"
    example: |
      @pytest.mark.asyncio
      async def test_activity():
          env = ActivityEnvironment()
          result = await env.run(my_activity, "input")
          assert result == expected_output

# Error Testing
error_testing:
  rules:
    - "Test both normal and error paths"
    - "Validate error types and messages"
    - "Test boundary conditions and edge cases"

  examples:
    exception_testing: |
      def test_parse_json_invalid_json_raises_error():
          json_str = '{"key": "value", "invalid": }'

          with pytest.raises(json.JSONDecodeError):
              JsonUtils.parse_json(json_str)

    multiple_exceptions: |
      def test_parse_json_malformed_with_single_quotes():
          json_str = "{'key': 'value', 'unclosed': 'string"

          with pytest.raises((ValueError, SyntaxError)):
              JsonUtils.parse_json(json_str)

# Coverage Guidelines
coverage:
  targets:
    minimum: 80
    goal: 90
    critical_paths: 95

  exclusions:
    - "*/__pycache__/*"
    - "*/site-packages/*"
    - "*/.venv/*"
    - "*/baml_client/*"
    - "*.rs"
    - "*.toml"
    - "*.json"
    - "*.yaml"

  report_exclusions:
    - "pragma: no cover"
    - "def __repr__"
    - "if self.debug:"
    - "raise NotImplementedError"
    - "if __name__ == .__main__.:"
    - "@abstractmethod"

# Test Performance
performance:
  rules:
    - "Tests should be fast to maintain developer productivity"
    - "Expensive setups should use session-scoped fixtures"

# Anti-patterns to Avoid
anti_patterns:
  - name: "Test interdependence"
    description: "Tests should be independent and runnable in any order"
    example: "test_b depends on state from test_a"

  - name: "Over-mocking"
    description: "Don't mock the code you are testing; mock its dependencies"
    example: "Mocking internal methods of the class under test"

  - name: "Hardcoded paths"
    description: "Use fixtures and dynamic paths to keep tests portable"
    example: "Referring to '/Users/name/specific/path' in tests"

  - name: "Testing implementation details"
    description: "Test behavior, not implementation"
    example: "Asserting on private method calls or internal state"

  - name: "Unclear test failures"
    description: "Error messages should clearly indicate what failed and why"
    example: "Using generic assert without message"

# Best Practices
best_practices:
  - "Write tests before fixing bugs to prevent regressions"
  - "Test public interfaces rather than implementation details"
  - "Include positive and negative test cases"
  - "Keep test code as clean and maintainable as production code"
  - "Use descriptive test names that explain the scenario and expected outcome"
  - "Test edge cases and boundary conditions"
  - "Avoid testing third-party code, focus on your own logic"
  - "Test one behavior per test method for clarity"
