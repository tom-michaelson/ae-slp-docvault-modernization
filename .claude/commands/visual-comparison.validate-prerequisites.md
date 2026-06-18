# Validate UI Prerequisites

Health-check both the legacy and new applications before running a visual
comparison. This command does NOT start any servers — it assumes the legacy
docker stack and the Angular dev server are already up.

## Arguments

You receive a JSON string as `$ARGUMENTS`:

| Field | Required | Default | Notes |
|---|---|---|---|
| `pageKey` | yes | — | Used to derive the output path |
| `legacyUrl` | no | `http://localhost:5106` | Legacy app base URL |
| `newUrl` | no | `http://localhost:4200` | New Angular app base URL |
| `outputFile` | no | `docs/entry-points/ui-pages/{pageKey}/visual-comparison/ui-validation-result.json` | Where to write the result |

## Instructions

### Step 1: Resolve the output file path

If `outputFile` is not provided, build it from `pageKey`:
```
docs/entry-points/ui-pages/<pageKey>/visual-comparison/ui-validation-result.json
```
Create the parent directory if it doesn't exist:
```bash
mkdir -p docs/entry-points/ui-pages/<pageKey>/visual-comparison/
```

### Step 2: Health-check the legacy app

```bash
curl -s -o /dev/null -w '%{http_code}' --max-time 10 <legacyUrl>/
```

- HTTP **200** or **302** — set `legacyHealthy: true`.
- Anything else (000, 4xx, 5xx) — set `legacyHealthy: false` and put the actual
  status code (or `0` for connection refused) in `legacyStatusCode`. Put a short
  description in `legacyMessage`. Do NOT abort — record and continue.

### Step 3: Health-check the new app

```bash
curl -s -o /dev/null -w '%{http_code}' --max-time 10 <newUrl>/
```

- HTTP **200** — set `newHealthy: true`.
- Anything else — set `newHealthy: false`, record the status code in
  `newStatusCode` and put a short description in `newMessage`.

### Step 4: Write result JSON

Write to `outputFile`:

```json
{
  "pageKey": "<pageKey>",
  "legacyUrl": "<legacyUrl>",
  "newUrl": "<newUrl>",
  "legacyHealthy": true,
  "newHealthy": true,
  "legacyStatusCode": 200,
  "newStatusCode": 200,
  "legacyMessage": "",
  "newMessage": ""
}
```

**Always write the file every time this command runs**, even if it already
exists on disk with the correct content. Use the Write tool to overwrite —
do NOT skip writing on the basis that "the existing file already shows the
right state." The orchestrator infers success from a fresh tool-use, and a
no-op end-of-turn is interpreted as a failed agent run.

## Constraints

- Do NOT start, stop, or restart any servers. This command only observes.
- If either app is unhealthy, set `legacyHealthy`/`newHealthy` accordingly and
  let the user decide whether to continue.

## Success Criteria

- [ ] `ui-validation-result.json` written to the resolved path
- [ ] Both `legacyHealthy` and `newHealthy` reflect the actual curl results
- [ ] Status codes and messages populated for any unhealthy server
