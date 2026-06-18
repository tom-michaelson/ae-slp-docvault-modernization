---
model: opus
argument-hint: <pageKey> [output_dir]
---

# Capture Screenshots — New

Captures every screenshot in the page's `page-capture-plan.json` against the
**new Angular** application (`http://localhost:4200` by default).

**CRITICAL:** Screenshot filenames MUST exactly match the legacy capture's
filenames (same `name` values from `page-capture-plan.json`). Mismatched
filenames break the pair-wise comparison in the next step.

## Arguments

- `$0` — page key (folder under `docs/entry-points/ui-pages/`).
- `$1` — *(optional)* override the screenshots output directory.

## Directory Setup

`SCREENSHOTS_DIR` is the single output directory:

- If `$1` is provided: `SCREENSHOTS_DIR = $1`
- Otherwise: `SCREENSHOTS_DIR = docs/entry-points/ui-pages/$0/visual-comparison/new/`

All screenshots and the `SCREENSHOTS_COMPLETE` marker MUST be written to
`SCREENSHOTS_DIR`. Do not create subdirectories under it.

## Step 0: Read Capture Plan (required)

Read `docs/entry-points/ui-pages/$0/visual-comparison/page-capture-plan.json`. Note `newPath` for the navigation base.

If the plan doesn't exist, run `/visual-comparison.create-page-plan $0` first.

Build a TodoWrite task list mirroring the legacy capture command's list. Use
the same `name` values — that's how the comparison pairs the screenshots.

## Step 1: Idempotency Check

If `SCREENSHOTS_DIR/SCREENSHOTS_COMPLETE` exists, the capture is already done.
Stop.

## Step 2: Navigate to the Page

```
mcp__playwright__browser_navigate(url="http://localhost:4200<newPath>")
mcp__playwright__browser_wait_for(time=3)
mcp__playwright__browser_snapshot()
```

Angular SPAs need a couple seconds for the initial bundle to load. If the
snapshot still shows a "Loading..." placeholder, wait another 2 seconds.

## Step 3: Seed State (if the page needs it)

State seeding for this project's modern app:
- **Home**: data is fetched from `/api/documents` — already populated.
  Nothing to seed.
- **Documents**: state is managed via the API. To capture populated baselines,
  first ensure documents exist by uploading one on the upload page (the action
  fires `DocumentService.upload` which POSTs to `/api/documents`):
  ```
  mcp__playwright__browser_navigate(url="http://localhost:4200/documents/upload")
  mcp__playwright__browser_snapshot()
  mcp__playwright__browser_click(element="[ UPLOAD DOCUMENT ]", ref=<ref>)
  mcp__playwright__browser_navigate(url="http://localhost:4200<newPath>")
  ```

If the capture plan includes `empty-state`, capture it FIRST in a fresh
browser context (clears localStorage so `DocumentService` starts with no
session data and an empty document list), then seed and capture the populated baseline.

## Step 4: Capture Baselines

```bash
mkdir -p SCREENSHOTS_DIR
```

For each `category: "baseline"` in the capture plan:

1. Snapshot, verify the state matches `expectedElements`.
2. Perform any required interaction from `navigationHint`.
3. Capture and move:
   ```
   mcp__playwright__browser_take_screenshot(filename="screenshots/<name>.png")
   ```
   ```bash
   mv ./.playwright-mcp/screenshots/<name>.png SCREENSHOTS_DIR/
   ```

The new app uses standard buttons/links (no hover-to-reveal menus), so most
interactions are straightforward clicks.

## Step 5: Capture Flows

For each `category: "flow"`:

1. Reset to a known starting state.
2. Replay the steps described in `description` + `navigationHint`. Snapshot
   between clicks. Modern Angular dialogs/modals may take a tick to animate in
   — add `mcp__playwright__browser_wait_for(time=1)` after triggering them.
3. Capture and move the screenshot using the entry's `name`.

Failed flow → log and continue.

## Step 6: Validate via Sub-Agent

Spawn a Task sub-agent (do NOT self-assess):

```
Validate new-app screenshot capture for page "$0".

1. Read docs/entry-points/ui-pages/$0/visual-comparison/page-capture-plan.json
2. List all .png files in SCREENSHOTS_DIR/
3. For every screenshot in the plan, verify:
   - A .png with the exact name exists in SCREENSHOTS_DIR
   - File size > 0 bytes
4. Cross-check against the legacy directory if it exists:
   - SCREENSHOTS_DIR (new) vs docs/entry-points/ui-pages/$0/visual-comparison/legacy/
   - Report any name mismatches between the two directories
5. Report total expected, total found, missing, empty, mismatched.
6. VERDICT: PASS if all expected files exist, are non-empty, and align with
   legacy filenames. Else FAIL.
```

Re-capture on FAIL.

## Step 7: Create the Marker

Only after PASS:

```bash
echo "$(date -Iseconds)" > SCREENSHOTS_DIR/SCREENSHOTS_COMPLETE
```

## Step 8: Cleanup

```
mcp__playwright__browser_close()
```

## Angular-Specific Tips

- Initial SPA load can take 2–5s on a cold dev server. Wait long enough.
- The `DocumentService` stores a session token in `localStorage` keyed
  `docvault.userId`. A brand-new browser context gets a fresh session and an
  empty document list — handy for capturing the empty-state baseline cleanly.
- The new app's documents page lives at `/documents` (lowercase). The capture
  plan tracks legacy and new paths separately as `newPath` and `legacyPath`.

## Success Criteria

- [ ] Capture plan read, TodoWrite list mirrors legacy
- [ ] Page navigated via direct URL
- [ ] Required seed state created (if applicable)
- [ ] Every baseline screenshot captured with matching filename
- [ ] Every flow screenshot captured with matching filename
- [ ] Validation sub-agent returned PASS (including filename alignment with legacy)
- [ ] `SCREENSHOTS_COMPLETE` marker written
- [ ] Browser closed via MCP
