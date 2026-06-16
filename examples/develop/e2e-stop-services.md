Stop API and UI processes that were started by `/e2e-start-services`.

## Arguments

You will receive a JSON string as argument with: $ARGUMENTS

- `apiPid` — (optional) PID of the API process to kill
- `uiPid` — (optional) PID of the UI dev server process to kill

## Instructions

1. **Stop API process:**
   - If `apiPid` is provided, run `kill -9 {apiPid}` (ignore errors if already dead)
   - Also check `lsof -ti :8080` for any remaining processes on port 8080 and kill them

2. **Stop UI process:**
   - If `uiPid` is provided, run `kill -9 {uiPid}` (ignore errors if already dead)
   - Also check `lsof -ti :4200` for any remaining processes on port 4200 and kill them

3. **If no PIDs provided**, just kill whatever is on ports 8080 and 4200:
   ```bash
   lsof -ti :8080 | xargs kill -9 2>/dev/null || true
   lsof -ti :4200 | xargs kill -9 2>/dev/null || true
   ```

4. **Verify** both ports are free:
   ```bash
   lsof -ti :8080 || echo "Port 8080 free"
   lsof -ti :4200 || echo "Port 4200 free"
   ```

## Constraints

- No output file is needed — this is a cleanup command
- Do not fail if processes are already dead
- Always attempt to free both ports regardless of PID arguments
