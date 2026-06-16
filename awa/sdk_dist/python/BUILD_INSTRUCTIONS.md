# AWA Client Package Build Instructions

This document provides instructions for building the AWA Client Python package for PyPI distribution.

## Overview

The build system provides cross-platform support for Windows, macOS, and Linux with comprehensive validation, testing, and packaging capabilities.

## Build Scripts

### Python Script (Primary)

- **File**: `build_package.py`
- **Purpose**: Main build logic with full cross-platform support
- **Dependencies**: Python 3.12+, build tools

### Shell Wrapper (Unix/Linux/macOS)

- **File**: `build_package.sh`
- **Purpose**: Convenient shell interface with environment validation
- **Usage**: `./build_package.sh [OPTIONS]`

### PowerShell Wrapper (Windows)

- **File**: `build_package.ps1`
- **Purpose**: Windows PowerShell interface with environment validation
- **Usage**: `.\build_package.ps1 [OPTIONS]`

## Prerequisites

### System Requirements

- Python 3.12 or later
- Package manager: `uv` (recommended) or `pip`
- Git (for version control)

## Usage

### Basic Build

```bash
# Unix/Linux/macOS
./build_package.sh

# Windows PowerShell
.\build_package.ps1

# Direct Python (all platforms)
python build_package.py
```

## Build Artifacts

After a successful build, the following artifacts are created in the `dist/` directory:

```
dist/
├── awa_client-0.1.0.tar.gz      # Source distribution
├── awa_client-0.1.0-py3-none-any.whl  # Wheel distribution
├── checksums.txt                 # SHA256 checksums
└── build-manifest.txt           # Build metadata
```

### File Descriptions

- **Source Distribution (.tar.gz)**: Contains source code and can be installed on any platform
- **Wheel Distribution (.whl)**: Pre-built binary distribution for faster installation
- **checksums.txt**: SHA256 hashes for verifying package integrity
- **build-manifest.txt**: Build metadata including platform, Python version, and build info
