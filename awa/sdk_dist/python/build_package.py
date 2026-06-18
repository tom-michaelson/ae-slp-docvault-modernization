#!/usr/bin/env python3
"""Cross-platform PyPI package build script for awa-client."""

import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


class Colors:
    """ANSI color codes for cross-platform colored output."""

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    END = "\033[0m"

    @classmethod
    def disable_on_windows(cls) -> None:
        """Disable colors on Windows if not supported."""
        if platform.system() == "Windows" and not os.environ.get("FORCE_COLOR"):
            for attr in dir(cls):
                if not attr.startswith("_") and attr != "disable_on_windows":
                    setattr(cls, attr, "")


class BuildError(Exception):
    """Custom exception for build errors."""


class PackageBuilder:
    """Main package builder class."""

    def __init__(self) -> None:
        self.project_root = Path(__file__).parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"

        # Disable colors on Windows if not supported
        if platform.system() == "Windows":
            Colors.disable_on_windows()

    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message with color coding."""
        color_map = {
            "INFO": Colors.CYAN,
            "SUCCESS": Colors.GREEN,
            "WARNING": Colors.YELLOW,
            "ERROR": Colors.RED,
            "STEP": Colors.BLUE + Colors.BOLD,
        }

        color = color_map.get(level, Colors.WHITE)
        sys.stdout.write(f"{color}[{level}]{Colors.END} {message}\n")
        sys.stdout.flush()

    def run_command(self, command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
        """Run a command and handle errors."""
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd or self.project_root,
                check=True,
                capture_output=True,
                text=True,
            )
            return result
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: {' '.join(command)}"
            if e.stdout:
                error_msg += f"\nStdout: {e.stdout}"
            if e.stderr:
                error_msg += f"\nStderr: {e.stderr}"
            raise BuildError(error_msg) from e

    def install_dependencies(self) -> None:
        """Install build dependencies."""
        self.log("Installing dependencies...", "STEP")

        if shutil.which("uv"):
            self.run_command(["uv", "sync", "--group", "build"])
        else:
            self.run_command([sys.executable, "-m", "pip", "install", "-e", ".[dev,build]"])

        self.log("Dependencies installed ✓", "SUCCESS")

    def run_linting(self) -> None:
        """Run code linting and formatting checks."""
        self.log("Running linting checks...", "STEP")

        runner = ["uv", "run"] if shutil.which("uv") else [sys.executable, "-m"]

        # Run ruff check
        try:
            self.run_command([*runner, "ruff", "check", "."])
            self.log("Ruff linting check ✓", "SUCCESS")
        except BuildError:
            self.log("Ruff linting issues found", "WARNING")

        # Run ruff format check
        try:
            self.run_command([*runner, "ruff", "format", "--check", "."])
            self.log("Ruff formatting check ✓", "SUCCESS")
        except BuildError:
            self.log("Ruff formatting issues found", "WARNING")

    def clean_build_artifacts(self) -> None:
        """Clean previous build artifacts."""
        self.log("Cleaning build artifacts...", "STEP")

        directories_to_clean = [
            self.dist_dir,
            self.build_dir,
            self.project_root / "*.egg-info",
        ]

        for directory in directories_to_clean:
            if directory.name.endswith("*.egg-info"):
                # Handle glob pattern for egg-info directories
                for egg_info in self.project_root.glob("*.egg-info"):
                    if egg_info.is_dir():
                        shutil.rmtree(egg_info)
            elif directory.exists():
                shutil.rmtree(directory)

        self.log("Build artifacts cleaned ✓", "SUCCESS")

    def build_package(self) -> None:
        """Build the package."""
        self.log("Building package...", "STEP")

        # Ensure dist directory exists
        self.dist_dir.mkdir(exist_ok=True)

        runner = ["uv", "run"] if shutil.which("uv") else [sys.executable, "-m"]

        self.run_command([*runner, "python", "-m", "build"])
        self.log("Package built ✓", "SUCCESS")

    def generate_checksums(self) -> None:
        """Generate checksums for built packages."""
        self.log("Generating checksums...", "STEP")

        if not self.dist_dir.exists():
            self.log("No dist directory found", "WARNING")
            return

        checksum_file = self.dist_dir / "checksums.txt"

        with checksum_file.open("w") as f:
            for file_path in sorted(self.dist_dir.glob("*")):
                if file_path.is_file() and file_path.name != "checksums.txt":
                    # Calculate SHA256 hash
                    sha256_hash = hashlib.sha256()
                    with file_path.open("rb") as package_file:
                        for chunk in iter(lambda: package_file.read(4096), b""):
                            sha256_hash.update(chunk)

                    f.write(f"{sha256_hash.hexdigest()}  {file_path.name}\n")

        self.log("Checksums generated ✓", "SUCCESS")

    def verify_package_contents(self) -> None:
        """Verify package contents using check-manifest."""
        self.log("Verifying package contents...", "STEP")

        runner = ["uv", "run"] if shutil.which("uv") else [sys.executable, "-m"]

        try:
            self.run_command([*runner, "check-manifest"])
            self.log("Package contents verified ✓", "SUCCESS")
        except BuildError:
            self.log("Package contents verification failed", "WARNING")

    def test_package_installation(self) -> None:
        """Test package installation in a temporary environment."""
        self.log("Testing package installation...", "STEP")

        # Find the built wheel
        wheel_files = list(self.dist_dir.glob("*.whl"))
        if not wheel_files:
            self.log("No wheel file found for testing", "WARNING")
            return

        wheel_file = wheel_files[0]

        # Create temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Install package in temporary environment
            self.run_command(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--target",
                    str(temp_path),
                    str(wheel_file),
                ],
            )

            # Test import
            env = os.environ.copy()
            env["PYTHONPATH"] = str(temp_path)

            test_import = subprocess.run(  # noqa: S603
                [
                    sys.executable,
                    "-c",
                    "import awa.client; print('Import successful')",
                ],
                check=False,
                env=env,
                capture_output=True,
                text=True,
            )

            if test_import.returncode == 0:
                self.log("Package installation test ✓", "SUCCESS")
            else:
                raise BuildError(f"Package import failed: {test_import.stderr}")

    def build(self) -> None:
        """Run the main build process."""
        try:
            self.log("Starting package build process...", "STEP")

            # Install dependencies and run checks
            self.install_dependencies()
            self.run_linting()

            # Build process
            self.clean_build_artifacts()
            self.build_package()

            # Post-build validation
            self.generate_checksums()
            self.verify_package_contents()
            self.test_package_installation()

            self.log("Package build completed successfully! 🎉", "SUCCESS")
            self.log(f"Build artifacts available in: {self.dist_dir}", "INFO")

        except BuildError as e:
            self.log(f"Build failed: {e}", "ERROR")
            sys.exit(1)
        except KeyboardInterrupt:
            self.log("Build interrupted by user", "WARNING")
            sys.exit(1)
        except Exception as e:  # noqa: BLE001
            self.log(f"Unexpected error: {e}", "ERROR")
            sys.exit(1)


def main() -> None:
    """Run the main entry point."""
    builder = PackageBuilder()
    builder.build()


if __name__ == "__main__":
    main()
