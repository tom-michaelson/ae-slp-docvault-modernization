#!/usr/bin/env python3
"""AWA AI Documentation Generator.

This script generates context-specific rule files for multiple AI development tools
based on source rules and metadata configurations. It supports referencing existing
documentation and code files through VitePress include syntax.

Features:
- Metadata-driven configuration for each source rule
- Dynamic content inclusion from existing docs/code
- Support for Cursor, GitHub Copilot, Claude, and OpenCode
- Glob pattern targeting for context-specific rules
"""

import argparse
import logging
import re
from pathlib import Path
from typing import Any, ClassVar

import yaml

# Set up logging
logger = logging.getLogger(__name__)


class DocumentationReferenceProcessor:
    """Processes VitePress @include references to include content from existing files."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    def process_references(self, content: str) -> str:
        """Process VitePress @include directives for AI tool generation."""
        # Pattern to match <!--@include: path --> directives
        pattern = r"<!--@include:\s*([^\s]+)\s*-->"

        def replace_include(match: re.Match[str]) -> str:
            include_path = match.group(1).strip()
            return self._resolve_vitepress_include(include_path, "")

        return re.sub(pattern, replace_include, content, flags=re.MULTILINE)

    def _resolve_vitepress_include(self, include_path: str, comment: str) -> str:
        """Resolve a VitePress @include directive to actual content."""
        # Convert relative path from docs/ai/ to absolute path
        if include_path.startswith("../"):
            # Path relative to docs/ai/, convert to absolute from project root
            relative_from_docs = include_path[3:]  # Remove "../"
            source_path = self.project_root / "docs" / relative_from_docs
        elif include_path.startswith("../../"):
            # Path relative to project root from docs/ai/
            relative_from_root = include_path[6:]  # Remove "../../"
            source_path = self.project_root / relative_from_root
        else:
            # Assume absolute path from project root
            source_path = self.project_root / include_path.lstrip("/")

        if not source_path.exists():
            return f"<!-- Include file not found: {include_path} -->"

        try:
            content = source_path.read_text()
            # Remove the first h1 header if present to avoid duplication
            content = self._remove_duplicate_h1_header(content)
            if comment:
                return f"<!-- {comment} -->\n{content}"
            return content
        except (OSError, UnicodeDecodeError) as e:  # pragma: no cover - filesystem edge
            return f"<!-- Error reading {include_path}: {e!s} -->"

    def _remove_duplicate_h1_header(self, content: str) -> str:
        """Remove the first H1 header and duplicate intro content to avoid duplication when including files."""
        lines = content.split("\n")
        if not lines:
            return content

        # Find the first H1 header (starts with # but not ##)
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("# ") and not stripped.startswith("## "):
                # Remove the H1 header and any immediately following content
                j = i + 1

                # Skip blank lines after header
                while j < len(lines) and lines[j].strip() == "":
                    j += 1

                # Skip the next paragraph if it appears to be descriptive intro text
                # (common pattern: header followed by description paragraph)
                if j < len(lines) and lines[j].strip() and not lines[j].startswith("#"):
                    # This looks like a description paragraph, skip it
                    j += 1
                    # Skip any trailing blank lines after the description
                    while j < len(lines) and lines[j].strip() == "":
                        j += 1

                return "\n".join(lines[j:])

        return content

    def _convert_to_vitepress_syntax(self, config_text: str) -> str:
        """Convert legacy reference syntax to VitePress-native include syntax."""
        config: dict[str, str] = {}
        for line in config_text.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                config[key.strip()] = value.strip().strip('"')

        source = config.get("source", "")
        if not source:
            return "<!-- No source specified -->"

        source_path = self.project_root / source
        if not source_path.exists():
            return f"<!-- Source file not found: {source} -->"

        # Check if section extraction is needed
        if "section" in config:
            section_name = config["section"]
            content = source_path.read_text()
            section_content = self._extract_section(content, section_name)
            return section_content
        if "lines" in config:
            lines = config["lines"]
            content = source_path.read_text()
            line_content = self._extract_lines(content, lines)
            return line_content
        # For full file inclusion, convert to relative path and use VitePress syntax
        if source.startswith("docs/"):
            relative_path = "../" + source[5:]  # Remove 'docs/' prefix
        elif source.startswith("README.md"):
            relative_path = "../../" + source  # Go up from docs/ai/
        else:
            relative_path = source

        if source.endswith(".md"):
            return f"<!--@include: {relative_path}-->"
        return f"<<< @/{source}"

    def _resolve_reference(self, config_text: str) -> str:  # pragma: no cover - legacy
        """Legacy method - kept for backward compatibility but converts to VitePress syntax."""
        return self._convert_to_vitepress_syntax(config_text)

    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract a specific section from markdown content."""
        lines = content.split("\n")
        section_lines: list[str] = []
        in_section = False
        section_level: int | None = None

        for line in lines:
            if line.startswith("#") and section_name.lower() in line.lower():
                in_section = True
                section_level = len(line) - len(line.lstrip("#"))
                section_lines.append(line)
            elif in_section:
                if line.startswith("#"):
                    current_level = len(line) - len(line.lstrip("#"))
                    if section_level is not None and current_level <= section_level:
                        break
                section_lines.append(line)

        return "\n".join(section_lines) if section_lines else f"<!-- Section '{section_name}' not found -->"

    def _extract_lines(self, content: str, line_range: str) -> str:
        """Extract specific lines from content (e.g., '1-30')."""
        try:
            if "-" in line_range:
                start, end = map(int, line_range.split("-"))
            else:
                start = end = int(line_range)

            lines = content.split("\n")
            return "\n".join(lines[start - 1 : end])
        except (ValueError, IndexError):  # pragma: no cover - invalid input
            return f"<!-- Invalid line range: {line_range} -->"


class MetadataRuleGenerator:
    """Generates AI tool rules based on source files and metadata."""

    SUPPORTED_AGENTS: ClassVar[list[str]] = ["cursor", "copilot", "claude", "opencode"]
    FRIENDLY_NAMES: ClassVar[dict[str, str]] = {
        "cursor": "Cursor",
        "copilot": "Copilot",
        "claude": "Claude",
        "opencode": "OpenCode",
    }

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.source_dir = project_root / "docs" / "ai"
        self.reference_processor = DocumentationReferenceProcessor(project_root)

    # -------------------------------------------------------------------------------------
    # Reading & Metadata
    # -------------------------------------------------------------------------------------
    def _read_source_file(self, filename: str) -> str:
        """Read content from a source rule or agent file, excluding legacy Configuration section.

        For agent spec files (agents/*.md) we keep frontmatter out of generated outputs
        (subagent generation crafts its own frontmatter) by stripping initial frontmatter block.
        """
        file_path = self.source_dir / filename
        if not file_path.exists():
            return ""
        content = file_path.read_text()

        # Strip frontmatter for agent specs; generation functions add their own
        if filename.startswith("agents/"):
            content = re.sub(r"^---\n.*?\n---\n", "", content, flags=re.DOTALL)

        # Remove legacy configuration section
        config_pattern = r"## Configuration\s*\n.*?```yaml\s*\n.*?\n```\s*\n"
        content = re.sub(config_pattern, "", content, flags=re.DOTALL)

        return self.reference_processor.process_references(content)

    def _read_metadata_file(self, filename: str) -> dict[str, Any]:
        """Read metadata configuration.

        Priority:
        1. Embedded "## Configuration" YAML block (legacy style for rules)
        2. Frontmatter YAML (for agent spec files in agents/*.md)
        """
        file_path = self.source_dir / filename
        if not file_path.exists():
            return {}

        content = file_path.read_text()

        # 1. Embedded configuration section
        pattern = r"## Configuration\s*\n.*?```yaml\s*\n(.*?)\n```"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            yaml_content = match.group(1)
            yaml_content = self._preprocess_yaml_backticks(yaml_content)
            try:
                loaded = yaml.safe_load(yaml_content)
                if isinstance(loaded, dict):
                    # Propagate root description to provider sections lacking one
                    root_description = str(loaded.get("description") or "").strip()
                    if root_description:
                        for provider_key in ["claude", "opencode"]:
                            section = loaded.get(provider_key)
                            if isinstance(section, dict) and section.get("subagent"):
                                desc_val = str(section.get("description") or "").strip()
                                if not desc_val:
                                    # inject root description
                                    loaded[provider_key] = {**section, "description": root_description}
                                elif desc_val != section.get("description"):
                                    # trim whitespace if needed
                                    loaded[provider_key] = {**section, "description": desc_val}
                    return loaded
            except yaml.YAMLError:  # pragma: no cover - invalid YAML
                return {}

        # 2. Frontmatter for agent specs (--- ... --- at file start)
        frontmatter_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if frontmatter_match:
            fm_text = frontmatter_match.group(1)
            try:
                fm_loaded = yaml.safe_load(fm_text) or {}
                if isinstance(fm_loaded, dict):
                    # Capture a root-level description (common pattern) to propagate if
                    # per-agent description fields are omitted or blank.
                    root_description = fm_loaded.get("description")

                    result: dict[str, Any] = {}
                    for key in ["claude", "opencode"]:
                        section = fm_loaded.get(key)
                        if isinstance(section, dict) and section.get("subagent"):
                            desc_val = section.get("description")
                            # Normalize description whitespace (YAML block scalars may preserve newlines/spaces)
                            desc_clean = str(desc_val or "").strip()
                            root_clean = str(root_description or "").strip()
                            # Treat empty string or missing key as needing injection
                            if root_clean and ("description" not in section or not desc_clean):
                                section = {**section, "description": root_clean}
                            elif desc_clean and desc_clean != desc_val:
                                # Trim excess whitespace
                                section = {**section, "description": desc_clean}
                            result[key] = section
                    # Attach marker if deprecated top-level model found (used in validation)
                    if "model" in fm_loaded:
                        result["__deprecated_root_model__"] = True
                    return result
            except yaml.YAMLError:  # pragma: no cover - invalid frontmatter
                return {}

        return {}

    def _preprocess_yaml_backticks(self, yaml_content: str) -> str:  # pragma: no cover - retained for compatibility
        return yaml_content

    def _discover_source_files(self) -> list[str]:
        """Discover all source rule files in the source directory.

        Includes top-level docs/ai/*.md files (excluding index/meta) and
        agent specification files under docs/ai/agents/*.md,
        command files under docs/ai/commands/*.md, and
        hook files under docs/ai/hooks/*.md.
        Returned paths are relative to docs/ai (e.g. 'core-instructions.md' or 'agents/code-simplifier.md').
        """
        source_files: list[str] = []
        # Top-level rule files
        for file_path in self.source_dir.glob("*.md"):
            if file_path.name in ["index.md"]:
                continue
            if not file_path.name.endswith(".meta.md"):
                source_files.append(file_path.name)
        # Agent specification files
        agents_dir = self.source_dir / "agents"
        if agents_dir.exists() and agents_dir.is_dir():
            for agent_file in agents_dir.glob("*.md"):
                # Exclude catalog index
                if agent_file.name == "index.md":
                    continue
                source_files.append(f"agents/{agent_file.name}")
        # Command files
        commands_dir = self.source_dir / "commands"
        if commands_dir.exists() and commands_dir.is_dir():
            source_files.extend(f"commands/{command_file.name}" for command_file in commands_dir.glob("*.md"))
        # Hook files
        hooks_dir = self.source_dir / "hooks"
        if hooks_dir.exists() and hooks_dir.is_dir():
            source_files.extend(f"hooks/{hook_file.name}" for hook_file in hooks_dir.glob("*.md"))
        return sorted(source_files)

    # -------------------------------------------------------------------------------------
    # Agent Type Helpers
    # -------------------------------------------------------------------------------------
    def _is_claude_subagent(self, metadata: dict[str, Any]) -> bool:
        claude_config = metadata.get("claude", {})
        return bool(claude_config.get("subagent", False))

    def _is_opencode_subagent(self, metadata: dict[str, Any]) -> bool:
        opencode_config = metadata.get("opencode", {})
        return bool(opencode_config.get("subagent", False))

    def _is_claude_command(self, metadata: dict[str, Any]) -> bool:
        claude_config = metadata.get("claude", {})
        return bool(claude_config.get("command", False))

    def _is_opencode_command(self, metadata: dict[str, Any]) -> bool:
        opencode_config = metadata.get("opencode", {})
        return bool(opencode_config.get("command", False))

    def _is_claude_hook(self, metadata: dict[str, Any]) -> bool:
        claude_config = metadata.get("claude", {})
        return bool(claude_config.get("hook", False))

    def _is_opencode_hook(self, metadata: dict[str, Any]) -> bool:
        opencode_config = metadata.get("opencode", {})
        return bool(opencode_config.get("hook", False))

    # -------------------------------------------------------------------------------------
    # Generation Helpers (Claude)
    # -------------------------------------------------------------------------------------
    def _generate_claude_subagent_file(self, source_file: str, metadata: dict[str, Any]) -> str:
        claude_config = metadata.get("claude", {})
        raw_name = claude_config.get("name", source_file.rsplit(".", 1)[0])
        name = raw_name.replace("agents/", "")
        description = claude_config.get("description", "").strip()
        model = claude_config.get("model", "inherit")
        color = claude_config.get("color", "blue")
        frontmatter = f"""---
name: {name}
description: {description}
model: {model}
color: {color}
---

"""
        content = self._read_source_file(source_file)
        return frontmatter + content

    def _generate_claude_file(self, source_filename: str, metadata: dict[str, Any]) -> str:
        claude_config = metadata.get("claude", {})
        description = claude_config.get("description", f"Command from {source_filename}")
        header = f"# {description}\n\n"
        source_content = self._read_source_file(source_filename)
        return header + source_content

    # -------------------------------------------------------------------------------------
    # Generation Helpers (Cursor / Copilot)
    # -------------------------------------------------------------------------------------
    def _generate_cursor_file(self, source_filename: str, metadata: dict[str, Any]) -> str:
        cursor_config = metadata.get("cursor", {})
        globs = cursor_config.get("globs", ["**/*"])
        if globs is None:
            globs = ""
        elif isinstance(globs, list):
            globs = ", ".join(globs)

        frontmatter = {
            "description": cursor_config.get("description", f"Rules from {source_filename}"),
            "globs": globs,
            "alwaysApply": cursor_config.get("alwaysApply", False),
        }

        yaml_lines = [
            f'description: "{frontmatter["description"]}"',
            f"globs: {frontmatter['globs']}",
            f"alwaysApply: {str(frontmatter['alwaysApply']).lower()}",
        ]
        yaml_content = "\n".join(yaml_lines) + "\n"
        source_content = self._read_source_file(source_filename)
        return f"---\n{yaml_content}---\n\n{source_content}"

    def _generate_copilot_file(self, source_filename: str, metadata: dict[str, Any]) -> str:
        copilot_config = metadata.get("copilot", {})
        output_type = copilot_config.get("output_type", "instructions")

        if output_type == "instructions":
            apply_to = copilot_config.get("applyTo", ["**/*"])
            yaml_content = "applyTo: "
            if isinstance(apply_to, list):
                if len(apply_to) == 1:
                    yaml_content += f'"{apply_to[0]}"\n'
                else:
                    yaml_content += "\n" + "".join(f'  - "{item}"\n' for item in apply_to)
            else:
                yaml_content += f'"{apply_to}"\n'
            source_content = self._read_source_file(source_filename)
            return f"---\n{yaml_content}---\n\n{source_content}"

        # prompts type
        source_content = self._read_source_file(source_filename)
        return source_content

    # -------------------------------------------------------------------------------------
    # Generation Helpers (OpenCode)
    # -------------------------------------------------------------------------------------
    def _generate_opencode_subagent_file(self, source_file: str, metadata: dict[str, Any]) -> str:
        """Generate OpenCode subagent file without extra source comment."""
        opencode_config = metadata.get("opencode", {})
        raw_name = opencode_config.get("name", source_file.rsplit(".", 1)[0])
        name = raw_name.replace("agents/", "")
        description = (
            opencode_config.get("description", "").strip() or metadata.get("claude", {}).get("description", "").strip()
        )
        # Use yaml.dump to properly quote description if it contains special characters
        description_yaml = yaml.dump({"description": description}, default_flow_style=False).strip()
        # Extract just the value part after "description: "
        description_value = (
            description_yaml.split("description: ", 1)[1] if "description: " in description_yaml else f'"{description}"'
        )

        frontmatter = f"""---
name: {name}
description: {description_value}
---

"""
        content = self._read_source_file(source_file)
        return frontmatter + content

    def _generate_claude_command_file(self, source_file: str, metadata: dict[str, Any]) -> str:
        claude_config = metadata.get("claude", {})
        description = claude_config.get("description", f"Command from {source_file}")
        header = f"# {description}\n\n"
        source_content = self._read_source_file(source_file)
        return header + source_content

    def _generate_opencode_command_file(self, source_filename: str, metadata: dict[str, Any]) -> str:
        opencode_config = metadata.get("opencode", {})
        description = opencode_config.get("description", f"Command from {source_filename}")
        agent = opencode_config.get("agent", "code-author")
        model = opencode_config.get("model", "inherit")
        # Use yaml.dump to properly quote description if it contains special characters
        description_yaml = yaml.dump({"description": description}, default_flow_style=False).strip()
        # Extract just the value part after "description: "
        description_value = (
            description_yaml.split("description: ", 1)[1] if "description: " in description_yaml else f'"{description}"'
        )

        # Build frontmatter with trailing blank line for separation
        frontmatter = f"""---
description: {description_value}
agent: {agent}
model: {model}
---

"""
        source_content = self._read_source_file(source_filename)
        return frontmatter + source_content

    def _generate_claude_hook_file(self, source_file: str, _metadata: dict[str, Any]) -> str:
        """Generate Claude hook file (shell script) from documentation content."""
        # metadata parameter kept for interface consistency but not currently used
        # Extract the shell script content from the markdown
        content = self._read_source_file(source_file)
        # Look for bash code blocks

        bash_match = re.search(r"```bash\s*\n(.*?)\n```", content, re.DOTALL)
        if bash_match:
            return bash_match.group(1).strip()
        # Fallback: return the whole content if no bash block found
        return content.strip()

    def _generate_opencode_hook_file(self, source_file: str, _metadata: dict[str, Any]) -> str:
        """Generate OpenCode hook file (shell script) from documentation content."""
        # metadata parameter kept for interface consistency but not currently used
        # Extract the shell script content from the markdown
        content = self._read_source_file(source_file)
        # Look for bash code blocks

        bash_match = re.search(r"```bash\s*\n(.*?)\n```", content, re.DOTALL)
        if bash_match:
            return bash_match.group(1).strip()
        # Fallback: return the whole content if no bash block found
        return content.strip()

    # -------------------------------------------------------------------------------------
    # Rule Output Assembly per Agent
    # -------------------------------------------------------------------------------------
    def _generate_cursor_rule(self, source_file: str, metadata: dict[str, Any]) -> tuple[Path, str, str]:
        output_dir = self.project_root / ".cursor" / "rules"
        # Strip directory prefix to flatten the structure
        base_name = source_file.rsplit(".", 1)[0].split("/")[-1]
        filename = f"{base_name}.mdc"
        content = self._generate_cursor_file(source_file, metadata)
        if source_file == "core-instructions.md":
            content += self._generate_agent_rule_index("cursor")
        return output_dir, filename, content

    def _generate_copilot_rule(self, source_file: str, metadata: dict[str, Any]) -> tuple[Path, str, str]:
        copilot_config = metadata.get("copilot", {})
        output_type = copilot_config.get("output_type", "instructions")
        base_rule = copilot_config.get("base_rule", False)

        if base_rule:
            output_dir = self.project_root / ".github"
            filename = "copilot-instructions.md"
            content = self._read_source_file(source_file)
            if source_file == "core-instructions.md":
                content += self._generate_agent_rule_index("copilot")
        else:
            if output_type == "instructions":
                output_dir = self.project_root / ".github" / "instructions"
                # Strip directory prefix to flatten the structure
                base_name = source_file.rsplit(".", 1)[0].split("/")[-1]
                filename = f"{base_name}.instructions.md"
            else:
                output_dir = self.project_root / ".github" / "prompts"
                # Strip directory prefix to flatten the structure
                base_name = source_file.rsplit(".", 1)[0].split("/")[-1]
                filename = f"{base_name}.md"
            content = self._generate_copilot_file(source_file, metadata)
        return output_dir, filename, content

    def _generate_claude_rule(self, source_file: str, metadata: dict[str, Any]) -> tuple[Path, str, str]:
        claude_config = metadata.get("claude", {})
        base_rule = claude_config.get("base_rule", False)
        is_subagent = self._is_claude_subagent(metadata)
        is_command = self._is_claude_command(metadata)
        is_hook = self._is_claude_hook(metadata)

        if is_hook:
            output_dir = self.project_root / ".claude" / "hooks"
            filename = claude_config.get("filename", source_file.rsplit(".", 1)[0] + ".sh")
            content = self._generate_claude_hook_file(source_file, metadata)
        elif is_subagent:
            output_dir = self.project_root / ".claude" / "agents"
            raw_name = claude_config.get("name", source_file.rsplit(".", 1)[0])
            subagent_name = raw_name.replace("agents/", "")
            filename = f"{subagent_name}.md"
            content = self._generate_claude_subagent_file(source_file, metadata)
        elif is_command:
            output_dir = self.project_root / ".claude" / "commands"
            command_name = claude_config.get("command_name", source_file.rsplit(".", 1)[0].replace("commands/", ""))
            filename = f"{command_name}.md"
            content = self._generate_claude_command_file(source_file, metadata)
        elif base_rule:
            output_dir = self.project_root
            filename = "CLAUDE.md"
            content = self._read_source_file(source_file)
            if source_file == "core-instructions.md":
                content += self._generate_agent_rule_index("claude")
        else:
            output_location = claude_config.get("output_location", ".claude/commands/")
            output_dir = self.project_root / output_location.strip("/")
            command_name = claude_config.get("command_name", source_file.rsplit(".", 1)[0])
            filename = f"{command_name}.md"
            content = self._generate_claude_file(source_file, metadata)
        return output_dir, filename, content

    def _generate_opencode_rule(self, source_file: str, metadata: dict[str, Any]) -> tuple[Path, str, str]:
        opencode_config = metadata.get("opencode", {})
        base_rule = opencode_config.get("base_rule", False)
        is_subagent = self._is_opencode_subagent(metadata)
        is_command = self._is_opencode_command(metadata)

        if is_subagent:
            output_dir = self.project_root / ".opencode" / "agent"
            raw_name = opencode_config.get("name", source_file.rsplit(".", 1)[0])
            subagent_name = raw_name.replace("agents/", "")
            filename = f"{subagent_name}.md"
            content = self._generate_opencode_subagent_file(source_file, metadata)
        elif is_command:
            output_dir = self.project_root / ".opencode" / "command"
            command_name = opencode_config.get("command_name", source_file.rsplit(".", 1)[0].replace("commands/", ""))
            filename = f"{command_name}.md"
            content = self._generate_opencode_command_file(source_file, metadata)
        elif base_rule:
            output_dir = self.project_root
            filename = "AGENTS.md"  # Mirrors CLAUDE.md content for OpenCode
            content = self._read_source_file(source_file)
            if source_file == "core-instructions.md":
                content += self._generate_agent_rule_index("opencode")
        else:
            # Command-style output with configurable location & name
            output_location = opencode_config.get("output_location", ".opencode/command/")
            output_dir = self.project_root / output_location.strip("/")
            command_name = opencode_config.get("command_name", source_file.rsplit(".", 1)[0])
            filename = f"{command_name}.md"
            content = self._generate_opencode_command_file(source_file, metadata)
        return output_dir, filename, content

    # -------------------------------------------------------------------------------------
    # Public Generation Methods
    # -------------------------------------------------------------------------------------
    def generate_agent_rules(self, agent: str) -> list[str]:
        if agent not in self.SUPPORTED_AGENTS:
            raise ValueError(f"Unknown agent: {agent}")

        source_files = self._discover_source_files()
        generated_files: list[str] = []

        for source_file in source_files:
            metadata = self._read_metadata_file(source_file)
            if not metadata or agent not in metadata:
                continue

            # Skip hooks for agents that don't support them
            if source_file.startswith("hooks/") and agent in ["cursor", "copilot", "opencode"]:
                continue

            if agent == "cursor":
                output_dir, filename, content = self._generate_cursor_rule(source_file, metadata)
            elif agent == "copilot":
                output_dir, filename, content = self._generate_copilot_rule(source_file, metadata)
            elif agent == "claude":
                output_dir, filename, content = self._generate_claude_rule(source_file, metadata)
            else:  # opencode
                output_dir, filename, content = self._generate_opencode_rule(source_file, metadata)

            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / filename
            # Ensure content has no trailing whitespace and ends with single newline
            formatted_content = "\n".join(line.rstrip() for line in content.splitlines())
            if formatted_content and not formatted_content.endswith("\n"):
                formatted_content += "\n"
            output_path.write_text(formatted_content)
            generated_files.append(str(output_path.relative_to(self.project_root)))

        return generated_files

    def _validate_base_rules(self) -> None:
        source_files = self._discover_source_files()
        for agent in self.SUPPORTED_AGENTS:
            base_rule_files: list[str] = []
            for source_file in source_files:
                metadata = self._read_metadata_file(source_file)
                if not metadata or agent not in metadata:
                    continue
                agent_config = metadata[agent]
                if isinstance(agent_config, dict) and agent_config.get("base_rule", False):
                    base_rule_files.append(source_file)
            if len(base_rule_files) > 1:
                error_msg = f"❌ Multiple files have base_rule: true for {agent}:\n"
                for file in base_rule_files:
                    error_msg += f"   - {file}\n"
                error_msg += "\nOnly one file per agent can have base_rule: true. "
                error_msg += "Consider consolidating content or removing base_rule from all but one file."
                raise ValueError(error_msg)

    def _validate_agent_models(self) -> None:
        """Validate absence of deprecated root-level model and warn on missing provider models."""
        source_files = self._discover_source_files()
        for source_file in source_files:
            file_path = self.source_dir / source_file
            if not file_path.exists():
                continue
            text = file_path.read_text()
            fm_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
            if not fm_match:
                continue
            try:
                fm_loaded = yaml.safe_load(fm_match.group(1)) or {}
            except yaml.YAMLError:
                continue
            if not isinstance(fm_loaded, dict):
                continue
            if "model" in fm_loaded:
                raise ValueError(
                    "Deprecated root-level 'model' found in "
                    f"{source_file}. Move model under provider section (e.g., claude.model).",
                )
            # Provider model checks
            for agent_key in ["claude", "opencode"]:
                section = fm_loaded.get(agent_key)
                if (
                    isinstance(section, dict)
                    and section.get("subagent")
                    and agent_key == "claude"
                    and not section.get("model")
                ):
                    logger.warning(
                        "No claude.model specified for subagent in %s (defaulting to 'inherit').",
                        source_file,
                    )
                # For opencode we allow implicit inherit; no warning currently.

    def _generate_agent_rule_index(self, agent: str) -> str:
        if agent not in self.SUPPORTED_AGENTS:
            return ""

        source_files = self._discover_source_files()
        rule_entries: list[str] = []

        for source_file in source_files:
            if source_file == "core-instructions.md":
                continue
            metadata = self._read_metadata_file(source_file)
            if not metadata or agent not in metadata:
                continue
            agent_config = metadata[agent]
            if not isinstance(agent_config, dict):
                continue
            include_in_index = agent_config.get("include_in_index", False)
            if not include_in_index:
                continue

            description = agent_config.get("description", "")
            # Check if it's a command or hook
            is_command = source_file.startswith("commands/") or agent_config.get("command", False)
            is_hook = source_file.startswith("hooks/") or agent_config.get("hook", False)

            # For base rule index, skip agents (only include commands and hooks)
            if source_file.startswith("agents/"):
                continue
            if agent == "claude":
                command_name = agent_config.get("command_name")
                if command_name and description:
                    rule_entries.append(f"- **/{command_name}**: {description}")
                elif is_command and description:
                    rule_entries.append(
                        f"- **{source_file.replace('commands/', '').replace('.md', '')}**: {description}",
                    )
                elif is_hook and description:
                    rule_entries.append(
                        f"- **{source_file.replace('hooks/', '').replace('.md', '')} hook**: {description}",
                    )
            elif description:
                if is_command:
                    rule_entries.append(
                        f"- **{source_file.replace('commands/', '').replace('.md', '')}**: {description}",
                    )
                elif is_hook:
                    rule_entries.append(
                        f"- **{source_file.replace('hooks/', '').replace('.md', '')} hook**: {description}",
                    )
                else:
                    rule_entries.append(f"- **{description}**")

        if not rule_entries:
            return ""

        rule_entries.sort()
        if agent == "claude":
            index_content = (
                "\n\n## Available AI Rules\n\nThe following specialized AI rules are available as slash commands:\n\n"
            )
        else:
            friendly = self.FRIENDLY_NAMES.get(agent, agent.title())
            index_content = (
                f"\n\n## Available {friendly} Rules\n\n"
                f"The following specialized rules are configured for {friendly}:\n\n"
            )
        index_content += "\n".join(rule_entries) + "\n"
        return index_content

    def generate_all_rules(self) -> dict[str, list[str]]:
        self._validate_base_rules()
        self._validate_agent_models()
        results: dict[str, list[str]] = {}
        for agent in self.SUPPORTED_AGENTS:
            try:
                generated_files = self.generate_agent_rules(agent)
                results[agent] = generated_files
                logger.info("Generated %d files for %s", len(generated_files), agent)
                for file in generated_files:
                    logger.info("   - %s", file)
            except (OSError, UnicodeDecodeError, yaml.YAMLError):  # pragma: no cover - runtime errors
                logger.exception("Error generating rules for %s", agent)
                results[agent] = []
        return results

    # -------------------------------------------------------------------------------------
    # Cleaning
    # -------------------------------------------------------------------------------------
    def clean_generated_files(self) -> None:
        """Remove all generated rule files by clearing target directories and base files."""
        directories_to_clear = [
            self.project_root / ".cursor" / "rules",
            self.project_root / ".github" / "instructions",
            self.project_root / ".github" / "prompts",
            self.project_root / ".claude" / "commands",
            self.project_root / ".claude" / "agents",
            self.project_root / ".claude" / "hooks",
            self.project_root / ".opencode" / "command",
            self.project_root / ".opencode" / "agent",
        ]

        for directory in directories_to_clear:
            if directory.exists() and directory.is_dir():
                for child in directory.iterdir():
                    if child.is_file():
                        child.unlink()
                        logger.info("Removed %s", child.relative_to(self.project_root))

        # Base/global files
        base_files = [
            self.project_root / "CLAUDE.md",
            self.project_root / "AGENTS.md",
            self.project_root / ".github" / "copilot-instructions.md",
        ]
        for file_path in base_files:
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                logger.info("Removed %s", file_path.relative_to(self.project_root))

    # -------------------------------------------------------------------------------------
    # Validation & Listing
    # -------------------------------------------------------------------------------------
    def validate_source_files(self) -> bool:
        source_files = self._discover_source_files()
        all_valid = True
        logger.info("Found %d source files:", len(source_files))
        for source_file in source_files:
            logger.info("  %s", source_file)
            metadata = self._read_metadata_file(source_file)
            if not metadata:
                logger.warning("    No metadata file found")
                continue
            for agent in self.SUPPORTED_AGENTS:
                if agent in metadata:
                    logger.info("    %s configuration found", agent)
        return all_valid


def main() -> None:  # pragma: no cover - CLI
    """Entry point for the metadata-driven AI documentation generator."""
    parser = argparse.ArgumentParser(
        description="Generate AI tool documentation from source files and metadata",
    )

    parser.add_argument(
        "command",
        choices=["generate", "clean", "list", "validate"],
        help="Command to execute",
    )

    parser.add_argument(
        "--agent",
        choices=["cursor", "copilot", "claude", "opencode"],
        help="Generate rules for specific agent only",
    )

    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Path to the project root directory",
    )

    args = parser.parse_args()
    generator = MetadataRuleGenerator(args.project_root)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if args.command == "generate":
        logger.info("🚀 Generating AI documentation from source files...")
        if args.agent:
            generated_files = generator.generate_agent_rules(args.agent)
            logger.info("\n📄 Generated %d files for %s", len(generated_files), args.agent)
        else:
            results = generator.generate_all_rules()
            total_files = sum(len(files) for files in results.values())
            logger.info("\n📄 Generated %d total files across all agents", total_files)
    elif args.command == "clean":
        logger.info("🧹 Cleaning generated rule files...")
        generator.clean_generated_files()
    elif args.command == "validate":
        logger.info("🔍 Validating source files and metadata...")
        generator.validate_source_files()
    elif args.command == "list":
        logger.info("📋 Available source files:")
        source_files = generator._discover_source_files()  # noqa: SLF001
        for source_file in source_files:
            logger.info("  📄 %s", source_file)
            metadata = generator._read_metadata_file(source_file)  # noqa: SLF001
            if metadata:
                for agent in MetadataRuleGenerator.SUPPORTED_AGENTS:
                    if agent in metadata:
                        logger.info("    ✅ %s", agent)


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
