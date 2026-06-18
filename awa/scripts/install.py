"""AWA Installation Script - Installs AWA package globally with configuration setup."""

import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

# Constants
PYTHON_MIN_MAJOR = 3
PYTHON_MIN_MINOR = 12


class Colors:
    """Color constants for terminal output."""

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    WHITE = "\033[97m"
    RESET = "\033[0m"


def print_colored(message: str, color: str = Colors.WHITE) -> None:
    """Print colored message to terminal."""
    print(f"{color}{message}{Colors.RESET}")


def print_header(message: str) -> None:
    """Print header message."""
    print_colored(f"\n{'=' * 60}", Colors.BLUE)
    print_colored(f"  {message}", Colors.BLUE)
    print_colored(f"{'=' * 60}", Colors.BLUE)


def print_success(message: str) -> None:
    """Print success message."""
    print_colored(f"✓ {message}", Colors.GREEN)


def print_error(message: str) -> None:
    """Print error message."""
    print_colored(f"✗ {message}", Colors.RED)


def print_info(message: str) -> None:
    """Print info message."""
    print_colored(f"i {message}", Colors.BLUE)  # Fixed unicode character


def run_command(
    command: str,
    capture_output: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess | Exception | None:
    """Run a shell command and return the result."""
    try:
        if capture_output:
            result = subprocess.run(  # noqa: S602
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=check,
            )
        else:
            result = subprocess.run(  # noqa: S602
                command,
                shell=True,
                check=check,
            )

        if not check and result.returncode != 0:
            return None
        return result
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print_error(f"Unexpected error running command: {command}")
        print_error(f"Error: {e!s}")
        if check:
            return None
        return e


def get_global_config_dir() -> Path:
    """Get the global config directory path."""
    config_dir = Path.home() / ".awa"
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        print_success(f"Global config directory: {config_dir}")
        return config_dir
    except OSError as e:
        print_error(f"Failed to create global config directory: {e}")
        raise


def check_python_version() -> bool:
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < PYTHON_MIN_MAJOR or (version.major == PYTHON_MIN_MAJOR and version.minor < PYTHON_MIN_MINOR):
        print_error(f"Python {PYTHON_MIN_MAJOR}.{PYTHON_MIN_MINOR}+ required, found {version.major}.{version.minor}")
        return False

    print_success(f"Python version {version.major}.{version.minor} is compatible")
    return True


def find_awa_wheel() -> Path | None:
    """Find the AWA wheel file in the current directory."""
    current_dir = Path.cwd()

    # Look for wheel files matching AWA pattern
    wheel_patterns = [
        "dist/awa-*.whl",
        "dist/slalom_agentic_workflow_accelerator-*.whl",
    ]

    for pattern in wheel_patterns:
        wheel_files = list(current_dir.glob(pattern))
        if wheel_files:
            wheel_file = wheel_files[0]  # Take the first match
            print_success(f"Found AWA wheel: {wheel_file}")
            return wheel_file

    print_error("No AWA wheel file found. Please ensure you have built the package.")
    print_info("Run 'uv build' to create the wheel file.")
    return None


def get_installed_awa_version() -> str | None:
    """Get the currently installed AWA version."""
    try:
        result = run_command("awa --version", capture_output=True, check=False)
        if result and hasattr(result, "returncode") and result.returncode == 0:
            version = result.stdout.strip()
            print_info(f"Currently installed AWA version: {version}")
            return version

        return None
    except (subprocess.SubprocessError, OSError):
        return None


def detect_existing_installation() -> dict:
    """Detect existing AWA installation and configuration."""
    installation_info = {
        "awa_installed": False,
        "awa_version": None,
        "config_exists": False,
        "config_files": [],
        "config_dir": None,
    }

    # Check for installed version
    version = get_installed_awa_version()
    installation_info["awa_version"] = version
    installation_info["awa_installed"] = version is not None

    # Check for global config
    config_dir = get_global_config_dir()
    installation_info["config_dir"] = config_dir

    config_file = config_dir / "config.yaml"
    env_file = config_dir / ".env"
    services_file = config_dir / "services.json"

    config_files = []
    if config_file.exists():
        config_files.append(config_file)
    if env_file.exists():
        config_files.append(env_file)
    if services_file.exists():
        config_files.append(services_file)

    installation_info["config_files"] = config_files
    installation_info["config_exists"] = len(config_files) > 0

    if installation_info["config_exists"]:
        print_info("Existing global configuration found")
    else:
        print_info("No existing global configuration found")

    return installation_info


def backup_existing_config(installation_info: dict) -> bool:
    """Backup existing configuration if it exists."""
    if not installation_info["config_exists"]:
        print_info("No existing configuration to backup")
        return True

    try:
        config_dir = get_global_config_dir()
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        backup_dir = config_dir / f"backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup existing files
        for config_file in installation_info["config_files"]:
            if config_file.exists():
                shutil.copy2(config_file, backup_dir / config_file.name)
                print_success(f"Backed up {config_file.name} to {backup_dir}")

        return True

    except (OSError, shutil.Error) as e:
        print_error(f"Failed to backup configuration: {e}")
        return False


def install_awa_wheel(wheel_path: str | Path | None, upgrade: bool = False) -> bool:
    """Install the AWA wheel file."""
    if wheel_path is None:
        print_error("No wheel path provided")
        return False

    if isinstance(wheel_path, str):
        wheel_path = Path(wheel_path)

    if not wheel_path.exists():
        print_error(f"Wheel file not found: {wheel_path}")
        return False

    try:
        command = (
            f"uv pip install --system --upgrade '{wheel_path}'"
            if upgrade
            else f"uv pip install --system '{wheel_path}'"
        )

        print_info(f"Installing AWA from: {wheel_path}")
        result = run_command(command, capture_output=False, check=True)

        if result is not None:
            print_success("AWA installation completed successfully")
            return True
        print_error("AWA installation failed")
        return False

    except (subprocess.SubprocessError, OSError) as e:
        print_error(f"Failed to install AWA: {e}")
        return False


def main() -> None:
    """Install AWA package globally with configuration setup."""
    print_header("AWA Installation")

    # Step 1: Check Python version
    if not check_python_version():
        print_error("Python version check failed")
        sys.exit(1)

    # Step 2: Find AWA wheel
    wheel_path = find_awa_wheel()
    if not wheel_path:
        print_error("Could not find AWA wheel file")
        sys.exit(1)

    # Step 3: Detect existing installation
    installation_info = detect_existing_installation()
    is_upgrade = installation_info["awa_installed"]

    if is_upgrade:
        print_info(f"Upgrading existing AWA installation (v{installation_info['awa_version']})")
    else:
        print_info("Fresh AWA installation")

    # Step 4: Get installation options
    force_install = "--force" in sys.argv

    # Step 5: Backup existing configuration if upgrading
    if is_upgrade and not backup_existing_config(installation_info):
        print_error("Failed to backup existing configuration")
        if not force_install:
            print_error("Use --force to continue without backup")
            sys.exit(1)

    # Step 6: Install AWA
    if not install_awa_wheel(wheel_path, upgrade=is_upgrade):
        print_error("AWA installation failed")
        sys.exit(1)

    # Step 7: Display next steps
    print_success("AWA installation completed successfully!")
    print_info("Next steps:")
    print_info("1. Run 'awa init' to set up your configuration")
    print_info("2. Run 'awa start' to begin using AWA")

    if is_upgrade:
        print_info("3. Your previous configuration has been backed up")
        print_info("4. Run 'awa init --force' if you need to reconfigure")


if __name__ == "__main__":
    main()
