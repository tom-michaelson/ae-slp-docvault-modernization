import pytest
from pydantic import ValidationError

from cookbook.recipes.workflows.isolated_agent.models.workflow_input import SampleIsolatedAgentAnalyzeWorkflowInput


class TestSampleIsolatedAgentAnalyzeWorkflowInput:
    def test_valid_input(self) -> None:
        obj = SampleIsolatedAgentAnalyzeWorkflowInput(directory_path="/dir", output_directory="/out")
        assert obj.directory_path == "/dir"
        assert obj.output_directory == "/out"

    def test_default_output_directory(self) -> None:
        obj = SampleIsolatedAgentAnalyzeWorkflowInput(directory_path="/dir")
        assert obj.output_directory == "awa-agent-output"

    def test_missing_directory_path_raises(self) -> None:
        data = {"output_directory": "out"}
        with pytest.raises(ValidationError) as exc:
            SampleIsolatedAgentAnalyzeWorkflowInput(**data)
        assert "directory_path" in str(exc.value)

    def test_empty_string_values(self) -> None:
        obj = SampleIsolatedAgentAnalyzeWorkflowInput(directory_path="", output_directory="")
        assert obj.directory_path == ""
        assert obj.output_directory == ""

    def test_types(self) -> None:
        obj = SampleIsolatedAgentAnalyzeWorkflowInput(directory_path="/dir", output_directory="/out")
        assert isinstance(obj.directory_path, str)
        assert isinstance(obj.output_directory, str)

    def test_special_characters(self) -> None:
        obj = SampleIsolatedAgentAnalyzeWorkflowInput(
            directory_path="/path/with spaces!@#",
            output_directory="f\u00f6o",
        )
        assert "/path/with spaces!@#" in obj.directory_path
        assert obj.output_directory == "f\u00f6o"

    def test_unicode(self) -> None:
        obj = SampleIsolatedAgentAnalyzeWorkflowInput(directory_path="/路径", output_directory="输出")
        assert obj.directory_path == "/路径"
        assert obj.output_directory == "输出"

    def test_long_strings(self) -> None:
        long_str = "a" * 1000
        obj = SampleIsolatedAgentAnalyzeWorkflowInput(directory_path=long_str, output_directory=long_str)
        assert obj.directory_path == long_str
        assert obj.output_directory == long_str

    def test_equality(self) -> None:
        a = SampleIsolatedAgentAnalyzeWorkflowInput(directory_path="/a", output_directory="b")
        b = SampleIsolatedAgentAnalyzeWorkflowInput(directory_path="/a", output_directory="b")
        assert a == b

    def test_inequality(self) -> None:
        a = SampleIsolatedAgentAnalyzeWorkflowInput(directory_path="/a", output_directory="b")
        b = SampleIsolatedAgentAnalyzeWorkflowInput(directory_path="/a", output_directory="c")
        assert a != b

    def test_serialization(self) -> None:
        obj = SampleIsolatedAgentAnalyzeWorkflowInput(directory_path="/a", output_directory="b")
        d = obj.model_dump()
        assert d["directory_path"] == "/a"
        assert d["output_directory"] == "b"
        json_str = obj.model_dump_json()
        assert "/a" in json_str
        assert "b" in json_str

    def test_copy_and_update(self) -> None:
        obj = SampleIsolatedAgentAnalyzeWorkflowInput(directory_path="/a", output_directory="b")
        copy = obj.model_copy()
        assert obj == copy
        updated = obj.model_copy(update={"output_directory": "c"})
        assert updated.output_directory == "c"
        assert obj.output_directory == "b"

    def test_field_descriptions(self) -> None:
        schema = SampleIsolatedAgentAnalyzeWorkflowInput.model_json_schema()
        props = schema["properties"]
        assert "description" in props["directory_path"]
        assert "description" in props["output_directory"]
        assert "directory to analyze" in props["directory_path"]["description"]
        assert props["output_directory"]["description"] == "Directory where analysis results will be saved"

    def test_all_fields_required(self) -> None:
        schema = SampleIsolatedAgentAnalyzeWorkflowInput.model_json_schema()
        required = schema["required"]
        assert "directory_path" in required
        # output_directory is not required (has default)
        assert len(required) == 1
