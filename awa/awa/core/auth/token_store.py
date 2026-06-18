import json
import stat
from pathlib import Path
from typing import Any

CREDENTIALS_FILE = Path.home() / ".awa" / "credentials.json"


def get_credentials_path() -> Path:
    return CREDENTIALS_FILE


def load_credentials() -> dict[str, Any]:
    """Load credentials from the credentials file."""
    if not CREDENTIALS_FILE.exists():
        return {}
    with CREDENTIALS_FILE.open() as f:
        return json.load(f)


def store_credentials(credentials: dict[str, Any]) -> None:
    """Store credentials in the credentials file."""
    CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CREDENTIALS_FILE.open("w") as f:
        json.dump(credentials, f, indent=2)
    CREDENTIALS_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)
