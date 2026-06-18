import pytest
from pydantic import ValidationError

from cookbook.recipes.workflows.isolated_agent.models.workflow_input import SampleIsolatedAgentActWorkflowInput


class TestSampleIsolatedAgentActWorkflowInput:
    def test_valid_input(self) -> None:
        obj = SampleIsolatedAgentActWorkflowInput(repo_path="/repo/path", branch="dev")
        assert obj.repo_path == "/repo/path"
        assert obj.branch == "dev"

    def test_default_branch(self) -> None:
        obj = SampleIsolatedAgentActWorkflowInput(repo_path="/repo/path")
        assert obj.branch == "main"

    def test_missing_repo_path_raises(self) -> None:
        data = {"branch": "main"}
        with pytest.raises(ValidationError) as exc:
            SampleIsolatedAgentActWorkflowInput(**data)
        assert "repo_path" in str(exc.value)

    def test_empty_string_values(self) -> None:
        obj = SampleIsolatedAgentActWorkflowInput(repo_path="", branch="")
        assert obj.repo_path == ""
        assert obj.branch == ""

    def test_types(self) -> None:
        obj = SampleIsolatedAgentActWorkflowInput(repo_path="/repo", branch="main")
        assert isinstance(obj.repo_path, str)
        assert isinstance(obj.branch, str)

    def test_special_characters(self) -> None:
        obj = SampleIsolatedAgentActWorkflowInput(repo_path="/path/with spaces!@#", branch="f\u00f6o")
        assert "/path/with spaces!@#" in obj.repo_path
        assert obj.branch == "f\u00f6o"

    def test_unicode(self) -> None:
        obj = SampleIsolatedAgentActWorkflowInput(repo_path="/路径", branch="分支")
        assert obj.repo_path == "/路径"
        assert obj.branch == "分支"

    def test_long_strings(self) -> None:
        long_str = "a" * 1000
        obj = SampleIsolatedAgentActWorkflowInput(repo_path=long_str, branch=long_str)
        assert obj.repo_path == long_str
        assert obj.branch == long_str

    def test_equality(self) -> None:
        a = SampleIsolatedAgentActWorkflowInput(repo_path="/a", branch="b")
        b = SampleIsolatedAgentActWorkflowInput(repo_path="/a", branch="b")
        assert a == b

    def test_inequality(self) -> None:
        a = SampleIsolatedAgentActWorkflowInput(repo_path="/a", branch="b")
        b = SampleIsolatedAgentActWorkflowInput(repo_path="/a", branch="c")
        assert a != b

    def test_serialization(self) -> None:
        obj = SampleIsolatedAgentActWorkflowInput(repo_path="/a", branch="b")
        d = obj.model_dump()
        assert d["repo_path"] == "/a"
        assert d["branch"] == "b"
        json_str = obj.model_dump_json()
        assert "/a" in json_str
        assert "b" in json_str

    def test_copy_and_update(self) -> None:
        obj = SampleIsolatedAgentActWorkflowInput(repo_path="/a", branch="b")
        copy = obj.model_copy()
        assert obj == copy
        updated = obj.model_copy(update={"branch": "c"})
        assert updated.branch == "c"
        assert obj.branch == "b"

    def test_field_descriptions(self) -> None:
        schema = SampleIsolatedAgentActWorkflowInput.model_json_schema()
        props = schema["properties"]
        assert "description" in props["repo_path"]
        assert "description" in props["branch"]
        assert "git repository" in props["repo_path"]["description"]
        assert props["branch"]["description"] == "Branch to work on"

    def test_all_fields_required(self) -> None:
        schema = SampleIsolatedAgentActWorkflowInput.model_json_schema()
        required = schema["required"]
        assert "repo_path" in required
        # branch is not required (has default)
        assert len(required) == 1
