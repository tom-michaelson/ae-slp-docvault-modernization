"""Unit tests for CLI constants module."""

from awa.core.cli import constants


class TestServiceConstants:
    """Test cases for service-related constants."""

    def test_service_constants_are_strings(self) -> None:
        """Test that all service constants are strings."""
        assert isinstance(constants.SERVICE_API, str)
        assert isinstance(constants.SERVICE_UI, str)
        assert isinstance(constants.SERVICE_TEMPORAL_SERVER, str)
        assert isinstance(constants.SERVICE_TEMPORAL_WORKER, str)

    def test_service_constants_values(self) -> None:
        """Test that service constants have expected values."""
        assert constants.SERVICE_API == "api"
        assert constants.SERVICE_UI == "ui"
        assert constants.SERVICE_TEMPORAL_SERVER == "temporal_server"
        assert constants.SERVICE_TEMPORAL_WORKER == "temporal_worker"

    def test_all_services_list(self) -> None:
        """Test that ALL_SERVICES contains all service constants."""
        expected_services = {
            constants.SERVICE_API,
            constants.SERVICE_UI,
            constants.SERVICE_TEMPORAL_SERVER,
            constants.SERVICE_TEMPORAL_WORKER,
        }
        assert set(constants.ALL_SERVICES) == expected_services
        assert len(constants.ALL_SERVICES) == 4


class TestProcessManagementConstants:
    """Test cases for process management constants."""

    def test_process_discovery_constants(self) -> None:
        """Test process discovery and validation constants."""
        assert constants.MIN_PS_OUTPUT_FIELDS == 2
        assert constants.MIN_PS_PARTS_FOR_ARGS == 3
        assert constants.MIN_WMIC_CSV_PARTS == 3
        assert constants.MIN_TASKLIST_CSV_PARTS == 2
        assert constants.MAX_TASKLIST_CSV_PARTS == 8

    def test_timeout_constants_are_numeric(self) -> None:
        """Test that timeout constants are numeric values."""
        timeout_constants = [
            constants.PROCESS_TERMINATION_TIMEOUT,
            constants.VERIFICATION_TIMEOUT_EXTENDED,
            constants.VERIFICATION_TIMEOUT_DEFAULT,
            constants.GRACEFUL_TERMINATION_TIMEOUT,
            constants.VERIFICATION_TIMEOUT_FINAL,
            constants.DEFAULT_STOP_TIMEOUT,
        ]
        for timeout in timeout_constants:
            assert isinstance(timeout, (int, float))
            assert timeout > 0

    def test_timeout_values(self) -> None:
        """Test that timeout constants have expected values."""
        assert constants.PROCESS_TERMINATION_TIMEOUT == 12.0
        assert constants.VERIFICATION_TIMEOUT_EXTENDED == 15.0
        assert constants.VERIFICATION_TIMEOUT_DEFAULT == 10.0
        assert constants.GRACEFUL_TERMINATION_TIMEOUT == 8.0
        assert constants.VERIFICATION_TIMEOUT_FINAL == 5.0
        assert constants.DEFAULT_STOP_TIMEOUT == 90.0

    def test_retry_and_attempt_constants(self) -> None:
        """Test retry and attempt constants."""
        assert constants.MAX_VERIFICATION_ATTEMPTS == 5
        assert constants.MAX_TERMINATION_RETRIES == 3
        assert constants.DEFAULT_RETRY_ATTEMPTS == 3
        assert isinstance(constants.MAX_VERIFICATION_ATTEMPTS, int)
        assert isinstance(constants.MAX_TERMINATION_RETRIES, int)
        assert isinstance(constants.DEFAULT_RETRY_ATTEMPTS, int)

    def test_backoff_constants(self) -> None:
        """Test backoff-related constants."""
        assert constants.VERIFICATION_BACKOFF_INITIAL == 0.5
        assert constants.VERIFICATION_BACKOFF_MULTIPLIER == 1.5
        assert constants.RETRY_BACKOFF_BASE == 1.5

        assert isinstance(constants.VERIFICATION_BACKOFF_INITIAL, float)
        assert isinstance(constants.VERIFICATION_BACKOFF_MULTIPLIER, float)
        assert isinstance(constants.RETRY_BACKOFF_BASE, float)

        # Backoff values should be positive
        assert constants.VERIFICATION_BACKOFF_INITIAL > 0
        assert constants.VERIFICATION_BACKOFF_MULTIPLIER > 1  # Should be > 1 for exponential backoff
        assert constants.RETRY_BACKOFF_BASE > 1  # Should be > 1 for exponential backoff


class TestCommandTimeoutConstants:
    """Test cases for command timeout constants."""

    def test_command_timeout_constants(self) -> None:
        """Test command timeout constants."""
        timeout_constants = [
            constants.COMMAND_TIMEOUT_SHORT,
            constants.COMMAND_TIMEOUT_STANDARD,
            constants.COMMAND_TIMEOUT_MEDIUM,
            constants.COMMAND_TIMEOUT_LONG,
            constants.COMMAND_TIMEOUT_EXTENDED,
        ]
        for timeout in timeout_constants:
            assert isinstance(timeout, int)
            assert timeout > 0

    def test_command_timeout_ordering(self) -> None:
        """Test that command timeouts are in logical order."""
        assert constants.COMMAND_TIMEOUT_SHORT <= constants.COMMAND_TIMEOUT_STANDARD
        assert constants.COMMAND_TIMEOUT_STANDARD <= constants.COMMAND_TIMEOUT_MEDIUM
        assert constants.COMMAND_TIMEOUT_MEDIUM <= constants.COMMAND_TIMEOUT_LONG
        assert constants.COMMAND_TIMEOUT_LONG <= constants.COMMAND_TIMEOUT_EXTENDED

    def test_command_timeout_values(self) -> None:
        """Test command timeout values."""
        assert constants.COMMAND_TIMEOUT_SHORT == 3
        assert constants.COMMAND_TIMEOUT_STANDARD == 5
        assert constants.COMMAND_TIMEOUT_MEDIUM == 8
        assert constants.COMMAND_TIMEOUT_LONG == 10
        assert constants.COMMAND_TIMEOUT_EXTENDED == 15


class TestProcessLimitConstants:
    """Test cases for process limit constants."""

    def test_process_limits(self) -> None:
        """Test process limit constants."""
        assert isinstance(constants.MAX_PROCESS_TREE_DEPTH, int)
        assert isinstance(constants.PROCESS_CHECK_INTERVAL, float)
        assert isinstance(constants.MIN_SAFE_PROCESS_GROUP, int)

        assert constants.MAX_PROCESS_TREE_DEPTH > 0
        assert constants.PROCESS_CHECK_INTERVAL > 0
        assert constants.MIN_SAFE_PROCESS_GROUP >= 1

    def test_ps_field_indices(self) -> None:
        """Test ps field index constants."""
        assert isinstance(constants.PS_ARGS_FIELD_INDEX, int)
        assert isinstance(constants.PS_COMM_FIELD_INDEX, int)
        assert isinstance(constants.MIN_PS_BASIC_FIELDS, int)

        assert constants.PS_ARGS_FIELD_INDEX >= 0
        assert constants.PS_COMM_FIELD_INDEX >= 0
        assert constants.MIN_PS_BASIC_FIELDS >= 1


class TestConstantsIntegrity:
    """Test cases for overall constants integrity."""

    def test_no_duplicate_values(self) -> None:
        """Test that service constants don't have duplicate values."""
        service_values = [
            constants.SERVICE_API,
            constants.SERVICE_UI,
            constants.SERVICE_TEMPORAL_SERVER,
            constants.SERVICE_TEMPORAL_WORKER,
        ]
        assert len(service_values) == len(set(service_values))

    def test_timeout_ordering(self) -> None:
        """Test that timeout constants have logical ordering."""
        # Final timeout should be shortest
        assert constants.VERIFICATION_TIMEOUT_FINAL <= constants.VERIFICATION_TIMEOUT_DEFAULT
        assert constants.VERIFICATION_TIMEOUT_DEFAULT <= constants.VERIFICATION_TIMEOUT_EXTENDED

        # Process termination timeout should be reasonable relative to verification timeouts
        assert constants.PROCESS_TERMINATION_TIMEOUT >= constants.VERIFICATION_TIMEOUT_DEFAULT

    def test_delay_constants(self) -> None:
        """Test delay constants are present and valid."""
        delay_constants = [
            constants.PROCESS_GROUP_TERMINATION_DELAY,
            constants.GRACEFUL_TERMINATION_DELAY,
            constants.FINAL_CLEANUP_DELAY,
            constants.RETRY_DELAY,
        ]
        for delay in delay_constants:
            assert isinstance(delay, float)
            assert delay > 0

    def test_intro_and_help_constants(self) -> None:
        """Test intro and help string constants."""
        assert isinstance(constants.INTRO, str)
        assert isinstance(constants.SERVICES_HELP_LIST, str)
        assert isinstance(constants.UI_PACKAGE_MODE_WARNING, str)

        # Check that help list contains expected content
        for service in constants.ALL_SERVICES:
            assert service in constants.SERVICES_HELP_LIST

    def test_all_constants_are_mostly_immutable_types(self) -> None:
        """Test that most constants use immutable types."""
        # Get all module attributes that don't start with underscore
        constant_names = [name for name in dir(constants) if not name.startswith("_")]

        # Allow list for known mutable types that are acceptable
        allowed_mutable = {"ALL_SERVICES"}  # This is a list, but it's acceptable

        for name in constant_names:
            value = getattr(constants, name)
            if name not in allowed_mutable:
                # Should be immutable types only
                assert isinstance(value, (str, int, float, tuple, type(None))), (
                    f"Constant {name} has mutable type {type(value)}"
                )
