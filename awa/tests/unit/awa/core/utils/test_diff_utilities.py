"""Test cases for diff utilities."""

from unittest.mock import AsyncMock

import pytest

from awa.core.utils.diff_utilities import (
    ActionType,
    Chunk,
    Commit,
    DiffError,
    FileChange,
    Parser,
    Patch,
    PatchAction,
    apply_commit,
    identify_files_added,
    identify_files_needed,
    load_files,
    patch_to_commit,
    process_patch,
    text_to_patch,
)

WRITE_CALL_COUNT = 3
REMOVE_CALL_COUNT = 2
OPEN_CALL_COUNT = 2


def test_parser_update_file() -> None:
    """Test parsing an update file action."""
    current_files = {"example.py": "def hello():\n    print('Hello')\n\ndef main():\n    hello()"}
    lines = [
        "*** Begin Patch",
        "*** Update File: example.py",
        " def hello():",
        "     print('Hello')",
        " ",
        "-def main():",
        "-    hello()",
        "+def main():",
        "+    hello()",
        "+    goodbye()",
        "*** End Patch",
    ]
    parser = Parser(current_files=current_files, lines=lines, index=1)
    parser.parse()

    # Verify the patch was parsed correctly
    assert "example.py" in parser.patch.actions
    assert parser.patch.actions["example.py"].type == ActionType.UPDATE
    assert len(parser.patch.actions["example.py"].chunks) == 1

    # Verify the chunk
    chunk = parser.patch.actions["example.py"].chunks[0]
    assert chunk.del_lines == ["def main():", "    hello()"]
    assert chunk.ins_lines == ["def main():", "    hello()", "    goodbye()"]


def test_parser_add_file() -> None:
    """Test parsing an add file action."""
    current_files = {}
    lines = [
        "*** Begin Patch",
        "*** Add File: new_file.py",
        "+def hello():",
        "+    print('Hello')",
        "*** End Patch",
    ]
    parser = Parser(current_files=current_files, lines=lines, index=1)
    parser.parse()

    # Verify the patch was parsed correctly
    assert "new_file.py" in parser.patch.actions
    assert parser.patch.actions["new_file.py"].type == ActionType.ADD
    assert parser.patch.actions["new_file.py"].new_file == "def hello():\n    print('Hello')"


def test_parser_delete_file() -> None:
    """Test parsing a delete file action."""
    current_files = {"to_delete.py": "content"}
    lines = [
        "*** Begin Patch",
        "*** Delete File: to_delete.py",
        "*** End Patch",
    ]
    parser = Parser(current_files=current_files, lines=lines, index=1)
    parser.parse()

    # Verify the patch was parsed correctly
    assert "to_delete.py" in parser.patch.actions
    assert parser.patch.actions["to_delete.py"].type == ActionType.DELETE


def test_parser_error_cases() -> None:
    """Test various error cases in the parser."""
    # Test missing file
    current_files = {}
    lines = [
        "*** Begin Patch",
        "*** Update File: missing_file.py",
        "*** End Patch",
    ]
    parser = Parser(current_files=current_files, lines=lines, index=1)
    with pytest.raises(DiffError, match="missing file"):
        parser.parse()

    # Test duplicate update
    current_files = {"file.py": "content"}
    lines = [
        "*** Begin Patch",
        "*** Update File: file.py",
        " content",
        "*** Update File: file.py",
        "*** End Patch",
    ]
    parser = Parser(current_files=current_files, lines=lines, index=1)
    with pytest.raises(DiffError, match="Duplicate update"):
        parser.parse()

    # Test missing end patch
    current_files = {"file.py": "content"}
    lines = [
        "*** Begin Patch",
        "*** Update File: file.py",
        " content",
    ]
    parser = Parser(current_files=current_files, lines=lines, index=1)
    with pytest.raises(DiffError, match="Unexpected end of input"):
        parser.parse()


def test_patch_to_commit() -> None:
    """Test converting a patch to a commit."""
    patch = Patch()

    # Add an update action
    update_action = PatchAction(type=ActionType.UPDATE)
    update_action.chunks.append(
        Chunk(
            orig_index=1,
            del_lines=["old line"],
            ins_lines=["new line"],
        ),
    )
    patch.actions["update_file.py"] = update_action

    # Add an add action
    add_action = PatchAction(type=ActionType.ADD, new_file="new content")
    patch.actions["new_file.py"] = add_action

    # Add a delete action
    delete_action = PatchAction(type=ActionType.DELETE)
    patch.actions["delete_file.py"] = delete_action

    # Original files
    orig = {
        "update_file.py": "line 1\nold line\nline 3",
        "delete_file.py": "content to delete",
    }

    # Convert to commit
    commit = patch_to_commit(patch, orig)

    # Verify commit
    expected_changes = 3
    assert len(commit.changes) == expected_changes

    # Verify update
    assert commit.changes["update_file.py"].type == ActionType.UPDATE
    assert commit.changes["update_file.py"].old_content == "line 1\nold line\nline 3"
    assert commit.changes["update_file.py"].new_content == "line 1\nnew line\nline 3"

    # Verify add
    assert commit.changes["new_file.py"].type == ActionType.ADD
    assert commit.changes["new_file.py"].new_content == "new content"

    # Verify delete
    assert commit.changes["delete_file.py"].type == ActionType.DELETE
    assert commit.changes["delete_file.py"].old_content == "content to delete"


def test_text_to_patch() -> None:
    """Test converting text to a patch."""
    text = """*** Begin Patch
*** Update File: example.py
 def hello():
     print('Hello')

-def main():
-    hello()
+def main():
+    hello()
+    goodbye()
*** End Patch"""

    orig = {"example.py": "def hello():\n    print('Hello')\n\ndef main():\n    hello()"}

    patch, fuzz = text_to_patch(text, orig)

    # Verify the patch
    assert "example.py" in patch.actions
    assert patch.actions["example.py"].type == ActionType.UPDATE
    assert len(patch.actions["example.py"].chunks) == 1

    # Verify the fuzz factor
    assert fuzz == 0


def test_identify_files() -> None:
    """Test identifying files needed or added by a patch."""
    text = """*** Begin Patch
*** Update File: file1.py
 content
*** Delete File: file2.py
*** Add File: file3.py
+content
*** End Patch"""

    needed = identify_files_needed(text)
    added = identify_files_added(text)

    assert sorted(needed) == ["file1.py", "file2.py"]
    assert added == ["file3.py"]


@pytest.mark.asyncio
async def test_apply_commit() -> None:
    """Test applying a commit."""
    # Create async mock functions
    write_fn = AsyncMock()
    remove_fn = AsyncMock()

    # Create a commit
    commit = Commit()

    # Add update change
    commit.changes["update_file.py"] = FileChange(
        type=ActionType.UPDATE,
        old_content="old",
        new_content="new",
    )

    # Add update change with move
    commit.changes["move_file.py"] = FileChange(
        type=ActionType.UPDATE,
        old_content="old",
        new_content="new",
        move_path="new_path.py",
    )

    # Add add change
    commit.changes["add_file.py"] = FileChange(
        type=ActionType.ADD,
        new_content="new",
    )

    # Add delete change
    commit.changes["delete_file.py"] = FileChange(
        type=ActionType.DELETE,
        old_content="old",
    )

    # Apply the commit
    await apply_commit(commit, write_fn, remove_fn)

    # Verify the functions were called correctly
    assert write_fn.call_count == WRITE_CALL_COUNT
    assert remove_fn.call_count == REMOVE_CALL_COUNT

    # Verify update
    write_fn.assert_any_call("update_file.py", "new")

    # Verify update with move
    write_fn.assert_any_call("new_path.py", "new")
    remove_fn.assert_any_call("move_file.py")

    # Verify add
    write_fn.assert_any_call("add_file.py", "new")

    # Verify delete
    remove_fn.assert_any_call("delete_file.py")


@pytest.mark.asyncio
async def test_process_patch() -> None:
    """Test processing a patch end-to-end."""
    # Create async mock functions
    open_fn = AsyncMock(side_effect=lambda path: {"file.py": "old content"}[path])
    write_fn = AsyncMock()
    remove_fn = AsyncMock()

    text = """*** Begin Patch
*** Update File: file.py
-old content
+new content
*** End Patch"""

    result = await process_patch(text, open_fn, write_fn, remove_fn)

    # Verify the result
    assert result.startswith("Applied patch")

    # Verify the functions were called correctly
    open_fn.assert_called_once_with("file.py")
    write_fn.assert_called_once()
    remove_fn.assert_not_called()


@pytest.mark.asyncio
async def test_load_files() -> None:
    """Test loading files."""
    open_fn = AsyncMock(side_effect=lambda path: f"content of {path}")
    paths = ["file1.py", "file2.py"]

    result = await load_files(paths, open_fn)

    assert result == {
        "file1.py": "content of file1.py",
        "file2.py": "content of file2.py",
    }
    assert open_fn.call_count == OPEN_CALL_COUNT
