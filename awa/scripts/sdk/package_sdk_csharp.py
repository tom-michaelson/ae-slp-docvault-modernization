#!/usr/bin/env python3
"""Package the C# SDK: update version and run dotnet pack.

This script is independently runnable and can be invoked by the Temporal workflow.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 300) -> tuple[bool, str]:
    """Run a command with timeout and capture output."""
    try:
        res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True, timeout=timeout)
        return True, res.stdout
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout} seconds: {' '.join(cmd)}"
    except subprocess.CalledProcessError as e:
        return False, (e.stdout or "") + "\n" + (e.stderr or "")


def update_csproj_version(csproj_path: Path, version: str) -> bool:
    content = csproj_path.read_text(encoding="utf-8")
    updated = content
    patterns = [
        (r"<Version>.*?</Version>", f"<Version>{version}</Version>"),
        (r"<PackageVersion>.*?</PackageVersion>", f"<PackageVersion>{version}</PackageVersion>"),
        (r"<AssemblyVersion>.*?</AssemblyVersion>", f"<AssemblyVersion>{version}</AssemblyVersion>"),
        (r"<FileVersion>.*?</FileVersion>", f"<FileVersion>{version}</FileVersion>"),
    ]
    tag_updated = False
    for pattern, replacement in patterns:
        if re.search(pattern, updated):
            updated = re.sub(pattern, replacement, updated)
            tag_updated = True
    if not tag_updated and "<PropertyGroup>" in updated:
        updated = updated.replace("<PropertyGroup>", f"<PropertyGroup>\n    <Version>{version}</Version>")
        tag_updated = True
    if tag_updated and updated != content:
        csproj_path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Package C# SDK")
    parser.add_argument("--version", required=True, help="Version to set before packing")
    parser.add_argument(
        "--project-root",
        default=Path(__file__).resolve().parents[2],
        type=Path,
        help="Project root (defaults to repo root)",
    )
    args = parser.parse_args()

    sdk_csharp_dir = args.project_root / "sdk_dist" / "csharp"
    csproj_path = sdk_csharp_dir / "Awa.Client" / "Awa.Client.csproj"
    if not csproj_path.exists():
        print(f"❌ .csproj not found: {csproj_path}")
        raise SystemExit(1)

    # Update version
    if update_csproj_version(csproj_path, args.version):
        print(f"✅ Updated C# version to {args.version}")
    else:
        print("i  No version tags updated (may already be set)")

    # First, restore packages using only nuget.org to avoid CodeArtifact auth issues
    print("📦 Restoring packages from nuget.org only...")
    ok, out = run(
        [
            "dotnet",
            "restore",
            "Awa.Client/Awa.Client.csproj",
            "--source",
            "https://api.nuget.org/v3/index.json",
        ],
        cwd=sdk_csharp_dir,
        timeout=60,  # Shorter timeout for restore
    )
    if not ok:
        print(f"❌ dotnet restore failed:\n{out}")
        raise SystemExit(1)
    print("✅ Packages restored successfully")

    # Build project - now with --no-restore since we already restored
    print("🔨 Building C# project...")
    print(f"   Working directory: {sdk_csharp_dir}")
    print("   Project file: Awa.Client/Awa.Client.csproj")
    ok, out = run(
        [
            "dotnet",
            "build",
            "Awa.Client/Awa.Client.csproj",
            "-c",
            "Release",
            "--no-restore",
        ],
        cwd=sdk_csharp_dir,
    )
    if not ok:
        print(f"❌ dotnet build failed:\n{out}")
        raise SystemExit(1)
    print("✅ C# project built successfully")

    # Pack - also skip restore here
    print("📦 Building NuGet package...")
    print("   Output directory: Awa.Client/bin/Release")
    ok, out = run(
        [
            "dotnet",
            "pack",
            "Awa.Client/Awa.Client.csproj",
            "-c",
            "Release",
            "-o",
            "Awa.Client/bin/Release",
            "--no-restore",
        ],
        cwd=sdk_csharp_dir,
    )
    if not ok:
        print(f"❌ dotnet pack failed:\n{out}")
        raise SystemExit(1)
    print("✅ C# package built successfully")


if __name__ == "__main__":
    main()
