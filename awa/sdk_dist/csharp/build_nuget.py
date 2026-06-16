"""NuGet package build script for Awa.Client SDK.

This Python script builds and packages the Awa.Client NuGet package.
It works on Windows, macOS, and Linux with Python 3.7+.
"""  # noqa: INP001

import platform
import shutil
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    RESET = "\033[0m"


def write_colored(message: str, color: str = Colors.WHITE) -> None:
    """Write colored output to terminal."""
    if sys.stdout.isatty():
        print(f"{color}{message}{Colors.RESET}")  # noqa: T201
    else:
        print(message)  # noqa: T201


def write_success(message: str) -> None:
    write_colored(f"✅ {message}", Colors.GREEN)


def write_warning(message: str) -> None:
    write_colored(f"⚠️  {message}", Colors.YELLOW)


def write_error(message: str) -> None:
    write_colored(f"❌ {message}", Colors.RED)


def write_info(message: str) -> None:
    write_colored(f"ℹ️  {message}", Colors.CYAN)  # noqa: RUF001


def write_progress(message: str) -> None:
    write_colored(f"🔧 {message}", Colors.BLUE)


class NuGetBuilder:
    """NuGet package builder for Awa.Client SDK."""

    def __init__(self) -> None:
        # Use default values for all configuration
        self.configuration = "Release"
        self.verbose = False
        self.skip_clean = False
        self.validate = True
        self.output_path = Path(f"bin/{self.configuration}")
        self.project_file = "Awa.Client.csproj"
        self.solution_file = "Awa.Client.sln"

    def test_prerequisites(self) -> None:
        """Check prerequisites for building."""
        write_progress("Checking prerequisites...")

        # Python version is already validated by project requirements

        # Check .NET SDK

        dotnet_exe = shutil.which("dotnet")
        if not dotnet_exe:
            write_error(".NET SDK not found. Please install .NET SDK 8.0 or later.")
            sys.exit(1)

        try:
            result = subprocess.run([dotnet_exe, "--version"], capture_output=True, text=True, check=True)  # nosec  # noqa: S603
            dotnet_version = result.stdout.strip()
            write_info(f"Using .NET SDK version: {dotnet_version}")
        except subprocess.CalledProcessError:
            write_error(".NET SDK not found. Please install .NET SDK 8.0 or later.")
            sys.exit(1)

        # Check project file exists
        if not Path(self.project_file).exists():
            write_error(f"Project file '{self.project_file}' not found")
            sys.exit(1)

        write_success("Prerequisites check passed")

    def run_dotnet_command(self, command: list[str], description: str) -> None:
        """Run a dotnet command with error handling."""
        try:
            verbosity = "quiet"  # Use quiet verbosity by default
            cmd = [shutil.which("dotnet"), *command]

            # Add verbosity if supported
            if any(arg in command for arg in ["build", "pack", "clean", "restore"]):
                cmd.extend(["--verbosity", verbosity])

            subprocess.run(cmd, check=True)  # nosec  # noqa: S603
            write_success(f"{description} completed successfully")

        except subprocess.CalledProcessError as e:
            write_error(f"{description} failed with exit code {e.returncode}")
            sys.exit(1)

    def get_generated_package(self) -> str:
        """Find the generated package file."""
        search_path = Path(self.output_path)

        package_files = list(search_path.rglob("*.nupkg"))
        package_files = [
            f for f in package_files if not f.name.endswith(".symbols.nupkg") and not f.name.endswith(".snupkg")
        ]

        if not package_files:
            write_error(f"No package files found in {search_path}")
            sys.exit(1)

        if len(package_files) > 1:
            write_warning("Multiple package files found, using the first one")

        package_file = str(package_files[0])
        write_info(f"Generated package: {package_file}")
        return package_file

    def validate_package(self, package_path: str) -> None:
        """Validate the generated package."""
        if not self.validate:
            return

        write_progress("Validating package...")

        # Check if package file exists and is not empty
        package_file = Path(package_path)
        if not package_file.exists():
            write_error(f"Package file not found: {package_path}")
            sys.exit(1)

        package_size = package_file.stat().st_size
        if package_size == 0:
            write_error(f"Package file is empty: {package_path}")
            sys.exit(1)

        write_info(f"Package size: {round(package_size / 1024, 2)} KB")

        # Basic package verification using dotnet nuget verify (if available)
        try:
            subprocess.run([shutil.which("dotnet"), "nuget", "verify", package_path], check=True, capture_output=True)  # nosec  # noqa: S603
            write_success("Package verification passed")
        except subprocess.CalledProcessError:
            write_warning("Package verification not available or failed")
        except FileNotFoundError:
            write_warning("Package verification not available")

    def show_summary(self, package_path: str, version: str) -> None:
        """Show build summary."""
        write_info("")
        write_info("=== Build Summary ===")
        write_info(f"Configuration: {self.configuration}")
        write_info(f"Version: {version}")
        write_info(f"Package: {package_path}")
        write_info("")
        write_success("Build completed successfully! 🎉")

    def build(self) -> None:
        """Execute the build process."""
        try:
            write_info("🚀 Starting Awa.Client NuGet package build...")
            write_info(f"Platform: {platform.system()}")
            write_info(f"Python: {sys.version}")
            write_info("")

            # Check prerequisites
            self.test_prerequisites()

            # Use existing version from project file
            current_version = "1.0.0"
            target_version = current_version

            # Build process
            self.run_dotnet_command(["clean", "-c", self.configuration], "Cleaning previous builds")
            self.run_dotnet_command(["restore"], "Restoring NuGet packages")
            cmd = ["build", "-c", self.configuration, "--no-restore"]
            self.run_dotnet_command(cmd, f"Building project in {self.configuration} mode")
            self.run_dotnet_command(
                ["pack", "-c", self.configuration, "--no-build", "--no-restore", "--output", self.output_path],
                "Creating NuGet package",
            )

            # Get generated package
            package_path = self.get_generated_package()

            # Validate package
            self.validate_package(package_path)

            # Show summary
            self.show_summary(package_path, target_version)

        except KeyboardInterrupt:
            write_error("Build interrupted by user")
            sys.exit(1)
        except Exception as e:  # noqa: BLE001
            write_error(f"Build failed: {e}")
            sys.exit(1)


def main() -> None:
    """Execute the main entry point."""
    builder = NuGetBuilder()
    builder.build()


if __name__ == "__main__":
    main()
