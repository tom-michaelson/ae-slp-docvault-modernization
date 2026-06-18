# Troubleshooting

## Developer setup

### Corporate Proxy Certificate Issues

When working behind a corporate proxy, you may encounter certificate-related errors if you use `uv` to install Python. This is common in enterprise environments where security tools perform SSL/TLS inspection (man-in-the-middle decryption) of HTTPS traffic.

#### Symptoms

You may see errors like this when trying to use `uv`:

```bash
➜  agentic-workflow-accelerator git:(main) uv run -m awa.main docs
error: Failed to download https://github.com/astral-sh/python-build-standalone/releases/download/20250212/cpython-3.12.9%2B20250212-aarch64-apple-darwin-install_only_stripped.tar.gz
  Caused by: Request failed after 3 retries
  Caused by: error sending request for url (https://github.com/astral-sh/python-build-standalone/releases/download/20250212/cpython-3.12.9%2B20250212-aarch64-apple-darwin-install_only_stripped.tar.gz)
  Caused by: client error (Connect)
  Caused by: invalid peer certificate: UnknownIssuer
```

#### Solutions

##### Install Python outside of `uv`

Install a supported version of Python from the official Python website (see `.python-version` for version).

##### Disable proxy

To install standalone Python through `uv`, disabling proxy software may be required. Contact your corporate IT department for guidance.

Common corporate proxy and security tools that may cause these issues:

- NetSkope
- Zscaler
- Cisco Umbrella
- Palo Alto Networks
- Blue Coat/Symantec
- McAfee Web Gateway
- Forcepoint
- Fortinet FortiGate
- Check Point
- Microsoft Defender for Cloud Apps

### Process Interference Issues

Strange errors like `FailedToLoadModuleSSR` or unexpected service behavior can occur when multiple AWA processes are running simultaneously from previous sessions, if they did not shut down properly.

#### Symptoms

- UI shows blank page with `FailedToLoadModuleSSR` error
- Services fail to start or behave unexpectedly
- Port conflicts or connection errors
- Inconsistent behavior between different runs

**Common error messages:**

- `FailedToLoadModuleSSR` in browser tab title
- `Address already in use` or `EADDRINUSE` errors
- `Connection refused` when trying to access services
- `Port 8000 is already in use` or similar port conflict messages
- `Failed to bind to address` errors during service startup

#### Solutions

##### Kill all known AWA processes

First, try stopping all AWA services:

```bash
make stop
```

##### Find and kill stray processes

If issues persist, manually search for and kill any running AWA or Temporal processes:

**macOS/Linux:**

```bash
# Find AWA processes
ps aux | grep -E "(awa|temporal)" | grep -v grep

# Kill all AWA processes
pkill -f "awa.main" || true
pkill -f "temporal" || true

# For more aggressive cleanup (use with caution)
pkill -f "awa" || true
```

**Windows:**

```powershell
# Find AWA processes
Get-Process | Where-Object {$_.ProcessName -like "*awa*" -or $_.ProcessName -like "*temporal*"}

# Kill AWA processes by name
taskkill /f /im "python.exe" /fi "WINDOWTITLE eq *awa*" 2>$null
taskkill /f /im "uv.exe" /fi "WINDOWTITLE eq *awa*" 2>$null
taskkill /f /im "node.exe" /fi "WINDOWTITLE eq *awa*" 2>$null
```

##### Fresh start

After killing stray processes, start services fresh:

```bash
make clean
make install
make start
```

#### Prevention

- Always use `make stop` before starting services
- Check for stray processes before starting: `ps aux | grep awa` (macOS/Linux) or `Get-Process | Where-Object {$_.ProcessName -like "*awa*"}` (Windows)
- Use `make clean-start` for a completely fresh start
- Avoid running multiple AWA instances simultaneously

### Workflow Connection Issues (IPv6 Systems)

On systems with IPv6 preference, workflows may hang during execution due to connection issues with the Temporal server.

#### Symptoms

- Workflows hang after "Starting workflow" message
- Multiple temporal workers spawning simultaneously
- Connection attempts to IPv6 addresses in logs: `dial tcp [::1]:7233: connect: connection refused`
- Repeated worker discovery messages: "Discovered X workflows and Y activities"

#### Solution

Force IPv4 connections by setting the Temporal server host in your `.env` files:

**Core AWA Repository** (`.env`):
```bash
TEMPORAL_SERVER_HOST=127.0.0.1
```

**Cookbook Repository** (`recipes/.env`):
```bash
TEMPORAL_SERVER_HOST=127.0.0.1
```

After applying the fix, restart AWA:

```bash
make clean
make start
```

#### Verification

Check logs for IPv4 connections (`127.0.0.1:7233`) instead of IPv6 (`[::1]:7233`) and confirm workflows complete without hanging.
