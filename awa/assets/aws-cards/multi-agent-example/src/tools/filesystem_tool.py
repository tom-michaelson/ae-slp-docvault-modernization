import json
import os
import shutil
from typing import Any

from multi_agent_orchestrator.types import ConversationMessage, ParticipantRole

filesystem_tools_description = [
    {
        "toolSpec": {
            "name": "File_Reading_Tool",
            "description": "List all files in a specified directory along with their contents.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "directory_path": {
                            "type": "string",
                            "description": "The path to the directory to list files from.",
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "Whether to recursively list files in subdirectories.",
                            "default": False,
                        },
                        "file_pattern": {
                            "type": "string",
                            "description": "Optional pattern to filter files (e.g., '*.txt')",
                            "default": "*",
                        },
                    },
                    "required": ["directory_path"],
                },
            },
        },
    },
    {
        "toolSpec": {
            "name": "File_Writing_Tool",
            "description": "Create or overwrite a file to a specified directory with the provided contents.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "directory_path": {
                            "type": "string",
                            "description": "The path to the directory.",
                        },
                        "file_name": {"type": "string", "description": "The filename."},
                        "file_content": {
                            "type": "string",
                            "description": "Whether to recursively list files in subdirectories.",
                            "default": False,
                        },
                    },
                    "required": ["directory_path", "file_name", "file_content"],
                },
            },
        },
    },
    {
        "toolSpec": {
            "name": "File_Copy_Tool",
            "description": "Copy a file to a specified directory, overwriting it if already present.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "file_source": {
                            "type": "string",
                            "description": "The path to the source file.",
                        },
                        "file_dest": {"type": "string", "description": "The path the file should be copied to."},
                    },
                    "required": ["file_source", "file_dest"],
                },
            },
        },
    },
]

filesystem_tools_prompt = """
You are a {{ROLE}}. In addition to your core and most essential capabiltiies, you also have access to a
file system assistant that provides file utilities from specified directories using the following tools:
- File_Reading_Tool, which expects directory_path and optionally accepts recursive or file_pattern.
Assume that any file reads originate in the input folder {{ROLE_INPUT_FOLDER}} unless otherwise specified.
- File_Writing_Tool, which expects directory_path, file_name, and file_content.  Assume that any working
 file writes should be written back to the intput folder {{ROLE_INPUT_FOLDER}} unless otherwise specified.
- File_Copy_Tool, which expects source_file and destination_file.  This function is permitted to copy files
 from the input folder {{ROLE_INPUT_FOLDER}} to the the output folder {{ROLE_OUTPUT_FOLDER}} folder.

If the user provides a directory, infer the approximate location relative to the "work" folder in the current
 working directory. You may also be responsible for loading the contents of those files
 for use in other processes.  If a file is already present in your context, do not reload it.
To use the tool, you strictly apply the provided tool specification.

- Explain your step-by-step process for accessing files
- Only use the File_Reading_Tool for retrieving data. Never guess or make up information.
- Only use the File_Writing_Tool for storing data. Never guess or make up information.
- Only use the File_Copy_Tool for duplicating files within the work directory.  Never guess or make up information.
- If the tool errors, apologize and explain what went wrong
- If asked for the raw contents of a file, reproduce them accurately with no summarization inside of a Markdown code block
- Only use tools if clearly needed to support your task.  Many tasks can be completed without a tool.
- Handle file paths carefully and warn about potential security implications
"""


async def file_tools_handler(response: ConversationMessage, conversation: list[dict[str, Any]]) -> ConversationMessage:
    response_content_blocks = response.content
    print(response_content_blocks)
    tool_results = []

    if not response_content_blocks:
        raise ValueError("No content blocks in response")

    for content_block in response_content_blocks:
        if "toolUse" in content_block:
            tool_use_block = content_block["toolUse"]
            tool_use_name = tool_use_block.get("name")

            if tool_use_name == "File_Reading_Tool":
                tool_response = await read_files(tool_use_block["input"])
                tool_results.append(
                    {
                        "toolResult": {
                            "toolUseId": tool_use_block["toolUseId"],
                            "content": [{"json": {"result": tool_response}}],
                        },
                    },
                )
            elif tool_use_name == "File_Writing_Tool":
                tool_response = await write_file(tool_use_block["input"])
                tool_results.append(
                    {
                        "toolResult": {
                            "toolUseId": tool_use_block["toolUseId"],
                            "content": [{"json": {"result": tool_response}}],
                        },
                    },
                )
            elif tool_use_name == "File_Copy_Tool":
                tool_response = await copy_file(tool_use_block["input"])
                tool_results.append(
                    {
                        "toolResult": {
                            "toolUseId": tool_use_block["toolUseId"],
                            "content": [{"json": {"result": tool_response}}],
                        },
                    },
                )
    message = ConversationMessage(role=ParticipantRole.USER.value, content=tool_results)

    return message


async def read_files(input_data):
    """Reads files in the specified directory and returns their contents.

    :param input_data: Dictionary containing directory_path and optional parameters
    :return: Dictionary containing file listings and their contents
    """
    try:
        directory_path = input_data.get("directory_path")
        recursive = input_data.get("recursive", True)
        file_pattern = input_data.get("file_pattern", "*")

        if not os.path.exists(directory_path):
            return {"error": "Directory not found"}

        if not os.path.isdir(directory_path):
            return {"error": "Path is not a directory"}

        file_data = {}

        if recursive:
            for root, _, files in os.walk(directory_path):
                for file in files:
                    if file_pattern == "*" or file.endswith(file_pattern.replace("*", "")):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, encoding="utf-8") as f:
                                file_data[file_path] = {
                                    "content": f.read(),
                                    "size": os.path.getsize(file_path),
                                    "modified": os.path.getmtime(file_path),
                                }
                        except Exception as e:
                            file_data[file_path] = {"error": f"Could not read file: {e!s}"}
        else:
            for file in os.listdir(directory_path):
                if file_pattern == "*" or file.endswith(file_pattern.replace("*", "")):
                    file_path = os.path.join(directory_path, file)
                    if os.path.isfile(file_path):
                        try:
                            with open(file_path, encoding="utf-8") as f:
                                file_data[file_path] = {
                                    "content": f.read(),
                                    "size": os.path.getsize(file_path),
                                    "modified": os.path.getmtime(file_path),
                                }
                        except Exception as e:
                            file_data[file_path] = {"error": f"Could not read file: {e!s}"}

        return {"file_data": json.dumps(file_data)}

    except Exception as e:
        return {"error": type(e).__name__, "message": str(e)}


async def write_file(input_data):
    """Writes a file to the specified directory.

    :param input_data: Dictionary containing directory_path, file_name, and file_content
    :return: Dictionary containing status of write operations
    """
    try:
        directory_path = input_data.get("directory_path")
        file_name = input_data.get("file_name")
        file_content = input_data.get("file_content")

        if not directory_path:
            return {"error": "Directory path not provided"}

        if not file_name:
            return {"error": "No file provided to write"}

        if not file_content:
            return {"error": "No content provided to write"}

        if not os.path.exists(directory_path):
            return {"error": "directory_path invalid"}

        result_data = {}

        file_path = os.path.join(directory_path, file_name)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_content)

            result_data[file_path] = {
                "status": "success",
                "size": os.path.getsize(file_path),
                "modified": os.path.getmtime(file_path),
            }
        except Exception as e:
            result_data[file_path] = {"error": f"Could not write file: {e!s}"}

        return {"write_results": json.dumps(result_data)}

    except Exception as e:
        return {"error": type(e).__name__, "message": str(e)}


async def copy_file(input_data):
    """Copies a file from the specified source to the specified destination.

    :param input_data: Dictionary containing file_source and file_dest
    :return: Dictionary containing status of write operations
    """
    try:
        file_source = input_data.get("file_source")
        file_dest = input_data.get("file_dest")

        if not file_source:
            return {"error": "file_source not provided"}

        if not file_dest:
            return {"error": "file_dest not provided"}

        try:
            if not os.path.exists(file_source):
                return {"error": "file_source does not exist"}

            if os.path.exists(file_dest):
                os.remove(file_dest)

            result_data = {}

            # Copy the file
            shutil.copy(file_source, file_dest)

            result_data[file_dest] = {
                "status": "success",
                "size": os.path.getsize(file_dest),
                "modified": os.path.getmtime(file_dest),
            }
        except FileNotFoundError as e:
            result_data[file_dest] = {"error": f"Could not write source file: {e!s}"}
        print("!!!!!!!!!!!!!!!!! 5")
        print(result_data)
        return {"copy_results": json.dumps(result_data)}

    except Exception as e:
        return {"error": type(e).__name__, "message": str(e)}
