# Cross-Platform Process Management

AWA implements cross-platform process group management to ensure proper process termination across different operating systems. This documentation covers the implementation details, platform-specific behavior, and troubleshooting guidance.

## Overview

The cross-platform process management system addresses the Windows-specific issue where `awa stop` fails to properly terminate detached services. The solution ensures proper signal propagation and process tree termination on Windows while preserving existing Unix functionality.

## Architecture

### Platform Detection

AWA uses the `PlatformUtils` class for consistent platform detection throughout the codebase:

```python
from awa.core.utils.platform_utils import PlatformUtils

if PlatformUtils.is_windows():
    # Windows-specific logic
else:
    # Unix-like system logic
```

### Process Group Creation

When starting detached services (`awa start -d`), AWA creates proper process groups based on the platform:

#### Windows
- Uses `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP`
- Creates a new process group that can be terminated as a tree

#### Unix-like Systems (Linux, macOS)
- Uses `start_new_session=True`
- Creates a new session with `os.setsid()` internally

### Process Termination

When stopping services (`awa stop`), AWA uses platform-appropriate termination methods:

#### Windows
1. **Graceful Termination**: Uses `taskkill /T /PID <pid>` to terminate the entire process tree
2. **Force Termination**: Uses `taskkill /F /T /PID <pid>` if graceful termination times out
3. **Timeout**: 5-second timeout for graceful shutdown before force termination

#### Unix-like Systems
1. **Graceful Termination**: Uses `os.killpg(pid, SIGTERM)` to terminate the process group
2. **Fallback**: Uses `os.kill(pid, SIGTERM)` if process group termination fails
3. **Force Termination**: Uses `os.killpg(pid, SIGKILL)` or `os.kill(pid, SIGKILL)`
4. **Timeout**: Same 5-second timeout as Windows

## Implementation Details

### Files Modified

- `awa/core/utils/platform_utils.py` - New platform detection utility
- `awa/core/utils/command_utils.py` - Cross-platform process group creation
- `awa/core/cli/state_manager.py` - Cross-platform process termination

### Key Methods

#### Process Group Creation
```python
# In command_utils.py
async def stream_command_async(command, detach=True):
    if detach:
        if PlatformUtils.is_windows():
            # Windows: CREATE_NEW_PROCESS_GROUP
            proc = await asyncio.create_subprocess_shell(
                command,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                # ... other params
            )
        else:
            # Unix: start_new_session=True
            proc = await asyncio.create_subprocess_shell(
                command,
                start_new_session=True,
                # ... other params
            )
```

#### Process Termination
```python
# In state_manager.py
async def stop_service(service_name: str):
    if PlatformUtils.is_windows():
        await self._stop_service_windows(pid, service_name)
    else:
        await self._stop_service_unix(pid, service_name)
```

## Platform-Specific Behavior

### Windows

**Process Creation:**
- Creates process groups using `CREATE_NEW_PROCESS_GROUP` flag
- Enables proper process tree management
- Child processes inherit the group membership

**Process Termination:**
- Uses Windows `taskkill` utility for process tree termination
- Graceful termination with `/T` flag (terminate tree)
- Force termination with `/F /T` flags if needed
- Handles UTF-8 encoding for subprocess output

**Dependencies:**
- Requires `taskkill` utility (standard on Windows 10+)
- No additional packages needed

### Unix-like Systems (Linux, macOS)

**Process Creation:**
- Creates new sessions using `start_new_session=True`
- Calls `os.setsid()` internally to create process groups
- Standard Unix process group behavior

**Process Termination:**
- Uses `os.killpg()` for process group termination
- Falls back to `os.kill()` for individual processes
- Standard POSIX signal handling (SIGTERM, SIGKILL)

**Dependencies:**
- No additional dependencies
- Uses standard Python `os` module functionality

## Error Handling

The implementation includes comprehensive error handling for various scenarios:

### Process Not Found
```python
try:
    os.killpg(pid, signal.SIGTERM)
except ProcessLookupError:
    # Process already terminated - log and continue
    logger.debug(f"Process {pid} already terminated")
```

### Permission Errors
```python
try:
    # Termination logic
except OSError as e:
    logger.warning(f"Permission error terminating process: {e}")
    # Continue with state cleanup
```

### Timeout Handling
```python
try:
    async with asyncio.timeout(5):
        # Wait for graceful termination
        await wait_for_process_termination(pid)
except TimeoutError:
    logger.warning("Timeout - force terminating")
    await force_terminate_process(pid)
```

## Troubleshooting

### Common Issues

#### Windows: "taskkill is not recognized"
**Symptoms:** Error messages about `taskkill` command not found
**Solution:**
1. Verify Windows installation includes standard utilities:
   ```powershell
   taskkill /?
   ```
2. If missing, check Windows installation or use Windows Subsystem for Linux (WSL)

#### Windows: Access Denied Errors
**Symptoms:** Permission errors when terminating processes
**Solutions:**
1. Run AWA with administrator privileges
2. Check if processes are owned by different users
3. Verify no antivirus software is blocking process termination

#### Unix: Process Group Not Found
**Symptoms:** `ProcessLookupError` or `OSError` during termination
**Solutions:**
1. Check if process was started with proper process group creation
2. Verify process hasn't already terminated
3. Check for permission issues with process ownership

#### Cross-Platform: Orphaned Processes
**Symptoms:** Services continue running after `awa stop`
**Solutions:**
1. Check AWA logs for termination errors
2. Manually terminate processes:
   ```bash
   # Windows
   tasklist | findstr "python"
   taskkill /F /T /PID <pid>

   # Unix
   ps aux | grep python
   kill -TERM <pid>
   ```
3. Restart AWA services to clear state

### Debug Logging

Enable debug logging to troubleshoot process management issues:

```bash
# Set log level to debug
export AWA_LOG_LEVEL=DEBUG

# Or use verbose flag
awa start -v
awa stop -v
```

### Manual Verification

#### Verify Dependencies
```bash
# Windows - Check taskkill availability
taskkill /?

# Unix - Check signal support
python -c "import signal; print(signal.SIGTERM)"
```

#### Check Process Trees
```bash
# Windows - View process tree
tasklist /T

# Unix - View process tree
ps -ef --forest
pstree -p
```

### Performance Considerations

- **Startup Time**: Process group creation adds minimal overhead (~1-5ms)
- **Shutdown Time**: Graceful termination timeout is 5 seconds maximum
- **Resource Usage**: No additional memory overhead for cross-platform logic

## Development Guidelines

### Adding Platform-Specific Code

1. Use `PlatformUtils` for consistent platform detection
2. Implement fallback mechanisms for each platform
3. Add comprehensive error handling
4. Include platform-specific tests

Example:
```python
from awa.core.utils.platform_utils import PlatformUtils

def platform_specific_operation():
    try:
        if PlatformUtils.is_windows():
            return windows_implementation()
        else:
            return unix_implementation()
    except (OSError, ProcessLookupError) as e:
        logger.warning(f"Platform operation failed: {e}")
        return fallback_implementation()
```

### Testing Cross-Platform Code

1. Mock platform detection for unit tests
2. Test both success and failure scenarios
3. Include timeout and error handling tests

Example:
```python
@patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
def test_platform_specific_behavior(mock_is_windows):
    mock_is_windows.return_value = True
    # Test Windows-specific behavior

    mock_is_windows.return_value = False
    # Test Unix-specific behavior
```

## Future Enhancements

Potential improvements to the cross-platform process management system:

1. **Process Monitoring**: Add health checks and automatic restart capabilities
2. **Resource Limits**: Implement memory and CPU limits for spawned processes
3. **Service Dependencies**: Add dependency management for service startup order
4. **Container Support**: Enhance process management for containerized environments
5. **Alternative Libraries**: Consider `psutil` for more advanced process management features

## References

- [Python subprocess documentation](https://docs.python.org/3/library/subprocess.html)
- [Windows Process Creation Flags](https://docs.microsoft.com/en-us/windows/win32/procthread/process-creation-flags)
- [POSIX Process Groups](https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap03.html#tag_03_289)
- [Signal Handling in Python](https://docs.python.org/3/library/signal.html)
