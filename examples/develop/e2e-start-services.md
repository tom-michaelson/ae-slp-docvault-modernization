Start the Passage API server and Angular UI dev server, verify both are healthy, and return process IDs.

## Arguments

You will receive a JSON string as argument with: $ARGUMENTS

- `docsDir` — Directory path to create for E2E outputs
- `baseApiUrl` — Base URL for the API health check (default: `http://localhost:8080`)
- `baseUiUrl` — Base URL for the UI health check (default: `http://localhost:4200`)
- `springProfile` — Spring profile to activate (default: `e2e`)
- `outputFile` — Path to write the result JSON

## Instructions

1. **Ensure port 8080 is free.** Run `lsof -ti :8080` — if any process is using it, kill it with `kill -9 <pid>`.

2. **Ensure port 4200 is free.** Run `lsof -ti :4200` — if any process is using it, kill it with `kill -9 <pid>`.

3. **Create the output directory** at the `docsDir` path (use `mkdir -p`).

4. **Start the API in the background:**
   ```bash
   cd passage-api
   ./gradlew bootRun --args='--spring.profiles.active=<springProfile>' &> /tmp/bootrun.log &
   ```
   Capture the background PID (`$!`) as `apiPid`.

5. **Wait for the API to become healthy.** Poll `<baseApiUrl>/actuator/health` every 3 seconds for up to 90 seconds. Use `curl -sf` to check. If the endpoint returns successfully, the API is healthy.

6. **If the API health check fails after 90 seconds**, read the last 50 lines of `/tmp/bootrun.log` to diagnose. Report the error in the output JSON with `apiHealthy: false`.

7. **Start the Angular UI dev server in the background:**
   ```bash
   cd passage-ui
   npx ng serve --port 4200 &> /tmp/ng-serve.log &
   ```
   Capture the background PID (`$!`) as `uiPid`.

8. **Wait for the UI to become healthy.** Poll `<baseUiUrl>` every 3 seconds for up to 60 seconds. Use `curl -sf -o /dev/null` to check for HTTP 200.

9. **If the UI health check fails after 60 seconds**, read the last 30 lines of `/tmp/ng-serve.log` to diagnose. Report the error in the output JSON with `uiHealthy: false`.

10. **Write the result** as JSON to the `outputFile` path.

## Output Format

Write a JSON file to `outputFile` with this exact structure:
```json
{
  "apiPid": "12345",
  "uiPid": "67890",
  "apiHealthy": true,
  "uiHealthy": true,
  "baseApiUrl": "http://localhost:8080",
  "baseUiUrl": "http://localhost:4200",
  "message": "Both services started and healthy"
}
```

If either service failed:
```json
{
  "apiPid": "12345",
  "uiPid": "67890",
  "apiHealthy": true,
  "uiHealthy": false,
  "baseApiUrl": "http://localhost:8080",
  "baseUiUrl": "http://localhost:4200",
  "message": "UI health check failed after 60s. Last ng-serve.log: ..."
}
```

## Constraints

- Do NOT proceed past the health checks — only start services and verify health
- Always return a valid JSON file even on failure
- The PID fields must always be present (even if processes died, report the original PIDs)
- Kill any existing processes on ports 8080 and 4200 before starting
