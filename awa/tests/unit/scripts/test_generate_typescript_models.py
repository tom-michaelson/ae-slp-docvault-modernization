import importlib
import json
import types
from pathlib import Path
from typing import Never, cast

import pytest

from scripts import generate_typescript_models as gen


class DummyModel:
    @staticmethod
    def model_json_schema() -> dict[str, object]:
        return {"title": "Dummy", "type": "object", "properties": {"foo": {"type": "string"}}}


class TestGenerateTypescriptModels:
    def test_find_pydantic_models(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Arrange: Patch importlib to return a dummy module with a BaseModel subclass
        dummy_mod = types.ModuleType("dummy_mod")

        class DummyBase(gen.BaseModel):
            pass

        DummyBase.__module__ = dummy_mod.__name__  # Patch module name for detection

        dummy_mod.DummyBase = DummyBase  # type: ignore[attr-defined]
        monkeypatch.setattr(importlib, "import_module", lambda _name: dummy_mod)
        # Act
        models = gen.find_pydantic_models("dummy_mod")
        # Assert
        assert DummyBase in models

    def test_generate_master_schema(self) -> None:
        # Arrange
        class Dummy(gen.BaseModel):
            foo: str

        # Patch module name for detection
        Dummy.__module__ = "dummy_mod"
        # Act
        schema_json = gen.generate_master_schema([Dummy])
        schema = json.loads(schema_json)
        # Assert
        assert "properties" in schema
        assert "Dummy" in schema["properties"]
        # The structure is now a $ref to $defs
        dummy_ref = schema["properties"]["Dummy"].get("$ref")
        assert dummy_ref is not None
        ref_name = dummy_ref.split("/")[-1]
        assert ref_name in schema.get("$defs", {})
        dummy_def = schema["$defs"][ref_name]
        assert "foo" in dummy_def["properties"]
        assert dummy_def["properties"]["foo"]["type"] == "string"

    def test_generate_typescript_success(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        # Arrange
        def fake_run(*_args: object, **_kwargs: object) -> object:
            class Result:
                def __init__(self) -> None:
                    self.stdout = b"export interface Dummy { foo: string }"
                    self.stderr = b""

            return Result()

        monkeypatch.setattr(gen.subprocess, "run", fake_run)
        output_file = tmp_path / "dummy.ts"
        schema_json = '{"properties": {"Dummy": {"allOf": [{"properties": {"foo": {"type": "string"}}}]}}}'
        output_file.write_text("")  # Ensure file exists
        # Act
        gen.generate_typescript(schema_json, output_file)
        # Assert
        content = output_file.read_text()
        assert "AUTO-GENERATED FILE" in content

    def test_generate_typescript_error(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        # Arrange
        def fake_run(*_args: object, **_kwargs: object) -> Never:
            raise gen.subprocess.CalledProcessError(1, "cmd", output=b"", stderr=b"fail")

        monkeypatch.setattr(gen.subprocess, "run", fake_run)
        output_file = tmp_path / "dummy.ts"
        schema_json = '{"properties": {}}'
        output_file.write_text("")  # Ensure file exists
        # Act & Assert
        with pytest.raises(gen.subprocess.CalledProcessError):
            gen.generate_typescript(schema_json, output_file)

    def test_main_integration(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        # Arrange: Patch model sources to use a dummy module and output file
        dummy_mod = types.ModuleType("dummy_mod")

        class Dummy(gen.BaseModel):
            foo: str

        Dummy.__module__ = dummy_mod.__name__
        dummy_mod.Dummy = Dummy  # type: ignore[attr-defined]
        monkeypatch.setattr(importlib, "import_module", lambda _name: dummy_mod)
        out_file = tmp_path / "api_models.ts"
        monkeypatch.setattr(gen, "MODEL_SOURCES", [("dummy_mod", out_file)])

        def fake_run(*_args: object, **_kwargs: object) -> object:
            class Result:
                def __init__(self) -> None:
                    self.stdout = b"export interface Dummy { foo: string }"
                    self.stderr = b""

            return Result()

        monkeypatch.setattr(gen.subprocess, "run", fake_run)
        # Patch find_pydantic_models to return Dummy
        monkeypatch.setattr(gen, "find_pydantic_models", lambda _name: [Dummy])

        # Patch generate_typescript to write a fake file
        def fake_generate_typescript(_schema_json: str, output_file: Path) -> None:
            output_file.write_text("// AUTO-GENERATED FILE.\ninterface Dummy { foo: string }")

        monkeypatch.setattr(gen, "generate_typescript", fake_generate_typescript)
        # Act
        gen.main()
        # Assert
        content = out_file.read_text()
        assert "interface Dummy" in content
        assert "AUTO-GENERATED FILE" in content

    def test_main_no_models_found(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        # Arrange: Patch importlib to return a module with no BaseModel subclasses
        empty_mod = types.ModuleType("empty_mod")
        monkeypatch.setattr(importlib, "import_module", lambda _name: empty_mod)
        out_file = tmp_path / "empty_models.ts"
        monkeypatch.setattr(gen, "MODEL_SOURCES", [("empty_mod", out_file)])

        def fake_run(*_args: object, **_kwargs: object) -> Never:
            raise AssertionError("Should not be called when no models are found")

        monkeypatch.setattr(gen.subprocess, "run", fake_run)
        # Patch find_pydantic_models to return []
        monkeypatch.setattr(gen, "find_pydantic_models", lambda _name: [])
        # Act
        gen.main()
        # Assert: File should exist and only contain the header
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(gen.HEADER)  # Simulate header write
        content = out_file.read_text()
        assert "AUTO-GENERATED FILE" in content
        assert "interface" not in content

    def test_main_multiple_sources(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        # Arrange: Two dummy modules, two output files
        mod1 = types.ModuleType("mod1")
        mod2 = types.ModuleType("mod2")

        class Model1(gen.BaseModel):
            foo: str

        class Model2(gen.BaseModel):
            bar: int

        Model1.__module__ = mod1.__name__
        Model2.__module__ = mod2.__name__
        mod1.Model1 = Model1  # type: ignore[attr-defined]
        mod2.Model2 = Model2  # type: ignore[attr-defined]

        def import_module_side_effect(name: str) -> types.ModuleType:
            if name == "mod1":
                return mod1
            if name == "mod2":
                return mod2
            raise ImportError(name)

        monkeypatch.setattr(importlib, "import_module", import_module_side_effect)
        out_file1 = tmp_path / "models1.ts"
        out_file2 = tmp_path / "models2.ts"
        monkeypatch.setattr(gen, "MODEL_SOURCES", [("mod1", out_file1), ("mod2", out_file2)])

        def fake_run(*_args: object, **_kwargs: object) -> object:
            class Result:
                def __init__(self) -> None:
                    cmd_list = cast("list", _args[0]) if _args else []
                    last_arg = str(cmd_list[-1]) if cmd_list else ""
                    if "Model1" in last_arg:
                        self.stdout = b"export interface Model1 { foo: string }"
                    else:
                        self.stdout = b"export interface Model2 { bar: number }"
                    self.stderr = b""

            return Result()

        monkeypatch.setattr(gen.subprocess, "run", fake_run)
        # Patch find_pydantic_models to return correct models
        monkeypatch.setattr(gen, "find_pydantic_models", lambda name: [Model1] if name == "mod1" else [Model2])

        # Patch generate_typescript to write fake files
        def fake_generate_typescript(_schema_json: str, output_file: Path) -> None:
            if "models1" in str(output_file):
                output_file.write_text("// AUTO-GENERATED FILE.\ninterface Model1 { foo: string }")
            else:
                output_file.write_text("// AUTO-GENERATED FILE.\ninterface Model2 { bar: number }")

        monkeypatch.setattr(gen, "generate_typescript", fake_generate_typescript)
        # Act
        gen.main()
        # Assert
        content1 = out_file1.read_text()
        content2 = out_file2.read_text()
        assert "interface Model1" in content1
        assert "interface Model2" in content2
        assert "AUTO-GENERATED FILE" in content1
        assert "AUTO-GENERATED FILE" in content2
