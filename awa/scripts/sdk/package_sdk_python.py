#!/usr/bin/env python3
"""Package the Python SDK: update pyproject version and uv build.

This script is independently runnable and can be invoked by the Temporal workflow.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None) -> tuple[bool, str]:
    try:
        res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
        return True, res.stdout
    except subprocess.CalledProcessError as e:
        return False, (e.stdout or "") + "\n" + (e.stderr or "")


def update_pyproject_version(pyproject_path: Path, version: str) -> bool:
    content = pyproject_path.read_text(encoding="utf-8")
    updated = re.sub(r'version\s*=\s*"[^"]*"', f'version = "{version}"', content)
    if updated != content:
        pyproject_path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Package Python SDK")
    parser.add_argument("--version", required=True, help="Version to set before building")
    parser.add_argument(
        "--project-root",
        default=Path(__file__).resolve().parents[2],
        type=Path,
        help="Project root (defaults to repo root)",
    )
    args = parser.parse_args()

    sdk_py_dir = args.project_root / "sdk_dist" / "python"
    pyproject_path = sdk_py_dir / "pyproject.toml"
    if not pyproject_path.exists():
        print(f"❌ pyproject.toml not found: {pyproject_path}")
        raise SystemExit(1)

    # Update version
    if update_pyproject_version(pyproject_path, args.version):
        print(f"✅ Updated Python version to {args.version}")
    else:
        print("i  No version updated (may already be set)")

    # Build
    print("📦 Building Python package...")
    ok, out = run(["uv", "build"], cwd=sdk_py_dir)
    if not ok:
        print(out)
        print("❌ uv build failed")
        raise SystemExit(1)
    print("✅ Python package built successfully")


if __name__ == "__main__":
    main()
