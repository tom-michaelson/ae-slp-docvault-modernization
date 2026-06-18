from awa.core.decorators.exposed import exposed


class TestExposedDecorator:
    """Test the @exposed decorator functionality."""

    def test_decorator_adds_metadata(self) -> None:
        """Test that decorator adds exposure metadata to classes."""

        @exposed("Test description")
        class TestWorkflow:
            pass

        assert hasattr(TestWorkflow, "__exposed__")
        assert hasattr(TestWorkflow, "__description__")
        assert TestWorkflow.__exposed__ is True
        assert TestWorkflow.__description__ == "Test description"

    def test_decorator_preserves_class_type(self) -> None:
        """Test that decorator preserves original class."""

        @exposed("Test description")
        class TestWorkflow:
            def test_method(self) -> str:
                return "test"

        # Class should be callable and methods should work
        instance = TestWorkflow()
        assert instance.test_method() == "test"
        assert TestWorkflow.__name__ == "TestWorkflow"

    def test_decorator_with_empty_description(self) -> None:
        """Test decorator behavior with empty description."""

        @exposed("")
        class TestWorkflow:
            pass

        assert TestWorkflow.__exposed__ is True
        assert TestWorkflow.__description__ == ""

    def test_workflow_without_decorator_not_exposed(self) -> None:
        """Test that workflow without decorator is not exposed by default."""

        class TestWorkflow:
            pass

        # Without decorator, workflow should not have __exposed__ attribute
        # or it should be False
        assert not getattr(TestWorkflow, "__exposed__", False)
        assert getattr(TestWorkflow, "__description__", None) is None
