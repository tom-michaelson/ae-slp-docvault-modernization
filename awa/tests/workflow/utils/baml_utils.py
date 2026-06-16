import re
from pathlib import Path


def get_baml_prompt(function_name: str, baml_src_path: str = "awa/core/baml_src") -> str:
    """Extract the prompt content from a BAML function definition.

    Args:
        function_name: Name of the function to extract prompt from (e.g., "Judge_Output")
        baml_src_path: Path to the BAML source directory

    Returns:
        The prompt content as a string, or None if not found

    Raises:
        FileNotFoundError: If no BAML file containing the function is found.

    """
    # Find the BAML file containing the function
    baml_file = find_baml_file_with_function(function_name, baml_src_path)

    if not baml_file:
        raise FileNotFoundError(
            f"No BAML file containing function '{function_name}' found in '{baml_src_path}'",
        )

    # Extract the prompt from the function
    return extract_prompt_from_function(baml_file, function_name)


def find_baml_file_with_function(function_name: str, baml_src_path: str) -> Path | None:
    """Find the BAML file that contains the specified function.

    Args:
        function_name: Name of the function to search for
        baml_src_path: Path to the BAML source directory

    Returns:
        Path to the BAML file, or None if not found

    """
    baml_dir = Path(baml_src_path)
    if not baml_dir.exists():
        return None

    for baml_file in baml_dir.glob("*.baml"):
        try:
            content = baml_file.read_text(encoding="utf-8")
            if f"function {function_name}(" in content:
                return baml_file
        except (OSError, UnicodeDecodeError):
            continue

    return None


def extract_prompt_from_function(baml_file: Path, function_name: str) -> str:
    """Extract the prompt content from a specific function in a BAML file.

    Raises:
        ValueError: If the function or prompt is not found in the BAML file.
        Exception: For any other file reading or parsing errors.

    """

    def extract() -> str:
        lines = baml_file.read_text(encoding="utf-8").splitlines()
        in_function = False
        brace_count = 0
        function_lines = []

        # Step 1: Find the function header
        header_pattern = re.compile(rf"function\s+{re.escape(function_name)}\s*\(.*\)\s*->.*{{")
        for _idx, line in enumerate(lines):
            if not in_function and header_pattern.match(line.strip()):
                in_function = True
                brace_count = line.count("{") - line.count("}")
                function_lines.append(line)
                continue
            if in_function:
                brace_count += line.count("{") - line.count("}")
                function_lines.append(line)
                if brace_count == 0:
                    break

        if not function_lines:
            raise ValueError(f"Function '{function_name}' not found in file '{baml_file}'.")

        # Step 2: Join function body and extract prompt
        function_body = "\n".join(function_lines)
        prompt_pattern = re.compile(r'prompt\s+#"(.*?)"#', re.DOTALL)
        prompt_match = prompt_pattern.search(function_body)
        if prompt_match:
            return prompt_match.group(1).strip()
        raise ValueError(f"Prompt not found in function '{function_name}' in file '{baml_file}'.")

    return extract()


def list_baml_functions(baml_src_path: str = "awa/core/baml_src") -> dict[str, str]:
    """List all functions and their corresponding BAML files.

    Args:
        baml_src_path: Path to the BAML source directory

    Returns:
        Dictionary mapping function names to their BAML file paths

    """
    functions = {}
    baml_dir = Path(baml_src_path)

    if not baml_dir.exists():
        return functions

    for baml_file in baml_dir.glob("*.baml"):
        try:
            content = baml_file.read_text(encoding="utf-8")
            # Find all function definitions
            function_matches = re.findall(r"function\s+(\w+)\s*\(", content)
            for func_name in function_matches:
                functions[func_name] = str(baml_file)
        except (OSError, UnicodeDecodeError):
            continue

    return functions


def get_baml_file_content(baml_file_name: str, baml_src_path: str = "awa/core/baml_src") -> str | None:
    """Get the full content of a BAML file by name.

    Args:
        baml_file_name: Name of the BAML file (e.g., "judge_output.baml")
        baml_src_path: Path to the BAML source directory

    Returns:
        The full content of the BAML file, or None if not found

    """
    baml_file = Path(baml_src_path) / baml_file_name
    if not baml_file.exists():
        return None

    try:
        return baml_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
