#!/usr/bin/env python3
"""Dependency verification script for AWA.

Validates that all required dependencies are installed and meet minimum version requirements.
Works on Windows, macOS, and Linux.
"""

from __future__ import annotations

import platform
import re
import subprocess
import sys
from dataclasses import dataclass

# Note: We intentionally don't import AWA modules here since this script
# runs before dependencies are installed and may cause import errors.


@dataclass
class Dependency:
    """Represents a dependency with its requirements and check commands."""

    name: str
    min_version: str
    commands: list[str]  # Commands to try (first available wins)
    version_args: list[str]  # Arguments to get version
    version_regex: str  # Regex to extract version from output
    description: str


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @staticmethod
    def green(text: str) -> str:
        return f"{Colors.GREEN}{text}{Colors.RESET}"

    @staticmethod
    def red(text: str) -> str:
        return f"{Colors.RED}{text}{Colors.RESET}"

    @staticmethod
    def yellow(text: str) -> str:
        return f"{Colors.YELLOW}{text}{Colors.RESET}"

    @staticmethod
    def blue(text: str) -> str:
        return f"{Colors.BLUE}{text}{Colors.RESET}"

    @staticmethod
    def bold(text: str) -> str:
        return f"{Colors.BOLD}{text}{Colors.RESET}"


def _parse_version(version_string: str, regex_pattern: str) -> str | None:
    """Extract version from string using regex pattern.

    Args:
        version_string: String containing version information
        regex_pattern: Regex pattern to extract version

    Returns:
        Version string or None if not found

    """
    match = re.search(regex_pattern, version_string)
    return match.group(1) if match else None


def _compare_versions(current: str, minimum: str) -> bool:
    """Compare two version strings.

    Args:
        current: Current version string
        minimum: Minimum required version string

    Returns:
        True if current >= minimum

    """

    def version_tuple(v: str) -> tuple[int, ...]:
        # Remove any non-numeric suffixes and split by dots
        clean_version = re.sub(r"[^\d.]", "", v.split("-")[0])
        return tuple(map(int, clean_version.split(".")))

    try:
        return version_tuple(current) >= version_tuple(minimum)
    except ValueError:
        # If version parsing fails, assume it's compatible
        return True


def _check_dependency(dep: Dependency) -> tuple[bool, str, str | None]:
    """Check if a dependency is installed and meets version requirements.

    Args:
        dep: Dependency object to check

    Returns:
        Tuple of (success, message, version_found)

    """
    is_windows = platform.system() == "Windows"

    # For pnpm on Windows, we may need to try different command wrappers
    if dep.name == "pnpm" and is_windows:
        # dep.commands is typically just ["pnpm"]
        # We try raw, then powershell, then pwsh
        commands_to_try = [
            [*dep.commands, *dep.version_args],
            ["powershell", "-Command", *dep.commands, *dep.version_args],
            ["pwsh", "-Command", *dep.commands, *dep.version_args],
        ]
    else:
        commands_to_try = [[cmd, *dep.version_args] for cmd in dep.commands]

    for command_parts in commands_to_try:
        try:
            result = subprocess.run(
                command_parts,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            success = result.returncode == 0
            output_text = result.stdout + result.stderr

            if success:
                version = _parse_version(output_text, dep.version_regex)

                if version:
                    # Check if version meets minimum requirement
                    if _compare_versions(version, dep.min_version):
                        return True, f"{dep.name} {version} (>= {dep.min_version})", version
                    return False, f"{dep.name} {version} found, but requires >= {dep.min_version}", version
                # Debug: show what output we got if we can't parse the version
                return False, f"{dep.name} found but version could not be determined from output: '{output_text}'", None
        except FileNotFoundError:
            # Command not found in PATH, continue to next command option
            continue
        except (OSError, subprocess.SubprocessError):
            # Other subprocess errors, continue to next command option
            continue

    return False, f"{dep.name} not found", None


def _get_dependencies() -> list[Dependency]:
    """Get list of dependencies to check based on the current platform.

    Returns:
        List of Dependency objects

    """
    is_windows = platform.system() == "Windows"

    return [
        Dependency(
            name="Python",
            min_version="3.12.0",
            commands=["python", "python3", "py"] if is_windows else ["python3", "python"],
            version_args=["--version"],
            version_regex=r"Python (\d+\.\d+\.\d+)",
            description="Python interpreter",
        ),
        Dependency(
            name="Node.js",
            min_version="22.16.0",
            commands=["node"],
            version_args=["--version"],
            version_regex=r"v(\d+\.\d+\.\d+)",
            description="Node.js runtime",
        ),
        Dependency(
            name="uv",
            min_version="0.7.12",
            commands=["uv"],
            version_args=["--version"],
            version_regex=r"uv (\d+\.\d+\.\d+)",
            description="Python package manager",
        ),
        Dependency(
            name="pnpm",
            min_version="10.6.2",
            commands=["pnpm"],
            version_args=["--version"],
            version_regex=r"(\d+\.\d+\.\d+)",
            description="Node.js package manager",
        ),
        Dependency(
            name="make",
            min_version="3.81",
            commands=["make", "gmake"] if not is_windows else ["make", "mingw32-make"],
            version_args=["--version"],
            version_regex=r"GNU Make (\d+\.\d+)" if not is_windows else r"Make (\d+\.\d+)",
            description="Build automation tool",
        ),
        Dependency(
            name="Temporal CLI",
            min_version="1.3.0",
            commands=["temporal"],
            version_args=["--version"],
            version_regex=r"temporal version (\d+\.\d+\.\d+)",
            description="Temporal workflow engine CLI",
        ),
    ]


def _print_header() -> None:
    """Print the script header."""
    print(Colors.bold("=" * 60))
    print(Colors.bold("AWA Dependency Verification"))
    print(Colors.bold("=" * 60))
    print(f"Platform: {Colors.blue(platform.system())} {Colors.blue(platform.release())}")
    print(f"Architecture: {Colors.blue(platform.machine())}")
    print()


def _print_summary(results: list[tuple[Dependency, bool, str, str | None]]) -> None:
    """Print summary of dependency check results.

    Args:
        results: List of (dependency, success, message, version) tuples

    """
    print(Colors.bold("=" * 60))
    print(Colors.bold("SUMMARY"))
    print(Colors.bold("=" * 60))

    success_count = sum(1 for _, success, _, _ in results if success)
    total_count = len(results)

    print(f"Dependencies checked: {total_count}")
    print(f"Successful: {Colors.green(str(success_count))}")
    print(f"Failed: {Colors.red(str(total_count - success_count))}")
    print()

    if success_count == total_count:
        print(Colors.green("[OK] All dependencies are installed and meet requirements!"))
    else:
        print(Colors.red("[FAIL] Some dependencies are missing or don't meet requirements."))
        print(Colors.red("Please install or update the missing dependencies before proceeding."))
        print()


def main() -> None:
    """Run dependency verification."""
    _print_header()

    dependencies = _get_dependencies()
    results = []

    print(Colors.bold("Checking dependencies..."))
    print()

    for dep in dependencies:
        print(f"Checking {dep.name}...", end=" ")
        sys.stdout.flush()

        success, message, version = _check_dependency(dep)
        results.append((dep, success, message, version))

        if success:
            print(Colors.green(f"[OK] {message}"))
        else:
            print(Colors.red(f"[FAIL] {message}"))

    print()
    _print_summary(results)

    # Exit with appropriate code
    all_success = all(success for _, success, _, _ in results)
    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
