---
model: opus
argument-hint: <pageKey> [output_dir]
---

# Capture Screenshots — Legacy

Captures every screenshot in the page's `page-capture-plan.json` against the
**legacy React/Node.js app** (`http://localhost:3000` by default). No login, no menu
tree — direct URL navigation.

## Arguments

- `$0` — page key (folder under `docs/entry-points/ui-pages/`). Examples: `home`, `document-list`.
- `$1` — *(optional)* override the screenshots output directory.

## Directory Setup

`SCREENSHOTS_DIR` is the single output directory:

- If `$1` is provided: `SCREENSHOTS_DIR = $1`
- Otherwise: `SCREENSHOTS_DIR = docs/entry-points/ui-pages/$0/visual-comparison/legacy/`

All screenshots and the `SCREENSHOTS_COMPLETE` marker MUST be written to
`SCREENSHOTS_DIR`. Do not create subdirectories under it.

## Step 0: Read Capture Plan (required)

Read `docs/entry-points/ui-pages/$0/visual-comparison/page-capture-plan.json`. The `screenshots` array is your authoritative checklist — capture every entry. Note `legacyPath` for the navigation base.

If the file doesn't exist, run `/visual-comparison.create-page-plan $0` first.

Build a TodoWrite task list:
- One task per screenshot (use the `name` field)
- Final task: "Run validation sub-agent"
- Final task: "Create SCREENSHOTS_COMPLETE marker"

Mark a screenshot task complete only after the file exists in `SCREENSHOTS_DIR`.

## Step 1: Idempotency Check

If `SCREENSHOTS_DIR/SCREENSHOTS_COMPLETE` already exists, this capture is
already done. Stop here.

## Step 2: Navigate to the Page

```
mcp__playwright__browser_navigate(url="http://localhost:3000<legacyPath>")
mcp__playwright__browser_wait_for(time=2)
mcp__playwright__browser_snapshot()
```

The legacy React/Node.js app is server-rendered — no SPA wait beyond the initial
HTML response. If the snapshot looks empty/loading, wait an extra second or two.

## Step 3: Seed State (if the page needs it)

Some pages need a non-empty state to capture meaningful baselines. Common
seeding actions for this project:

- **Home**: navigate to `/` — already populated from seed data. Nothing to do.
- **Documents**: a fresh session may have no uploaded documents. To capture
  populated baselines, first ensure documents exist by uploading one via the
  upload page:
  ```
  mcp__playwright__browser_navigate(url="http://localhost:3000/documents/upload")
  mcp__playwright__browser_snapshot()
  # Fill in the upload form and submit to POST a document
  mcp__playwright__browser_click(element="[ UPLOAD DOCUMENT ] submit", ref=<ref>)
  mcp__playwright__browser_navigate(url="http://localhost:3000<legacyPath>")
  ```

If the capture plan includes `empty-state`, capture the empty version FIRST in
a fresh context (clear cookies via a new browser context), then seed and
capture the populated baseline.

## Step 4: Capture Baselines

Create the directory:
```bash
mkdir -p SCREENSHOTS_DIR
```

For each `category: "baseline"` entry in the capture plan, in order:

1. Snapshot to confirm you're in the expected state (matches the entry's
   `expectedElements`).
2. If the entry's `navigationHint` requires interaction (e.g. clicking a tab),
   perform it: snapshot → click → wait.
3. Take the screenshot:
   ```
   mcp__playwright__browser_take_screenshot(filename="screenshots/<name>.png")
   ```
4. Move it:
   ```bash
   mv ./.playwright-mcp/screenshots/<name>.png SCREENSHOTS_DIR/
   ```

## Step 5: Capture Flows

For each `category: "flow"` entry:

1. Get back to a known starting state (often `main-view`).
2. Replay the steps described in the entry's `description` and `navigationHint`.
   Use snapshots between clicks to keep element refs fresh.
3. Take the screenshot at the post-action state:
   ```
   mcp__playwright__browser_take_screenshot(filename="screenshots/<name>.png")
   mv ./.playwright-mcp/screenshots/<name>.png SCREENSHOTS_DIR/
   ```

If a flow can't be replayed (element missing, error), log it and continue with
the next flow. Do not abort the whole capture.

## Step 6: Validate via Sub-Agent

Spawn a Task sub-agent to objectively verify the output (do NOT self-assess):

```
Validate legacy screenshot capture for page "$0".

1. Read docs/entry-points/ui-pages/$0/visual-comparison/page-capture-plan.json
2. List all .png files in SCREENSHOTS_DIR/
3. For every screenshot in the plan, verify:
   - A .png file with the exact name exists in SCREENSHOTS_DIR
   - The file size > 0 bytes
4. Report:
   - Total expected vs total found
   - Missing files (list)
   - Empty files (list)
5. VERDICT: PASS if all expected screenshots exist and are non-empty, else FAIL.
```

If the sub-agent returns FAIL, re-capture the missing/empty screenshots and
re-run validation.

## Step 7: Create the Marker

Only after PASS:

```bash
echo "$(date -Iseconds)" > SCREENSHOTS_DIR/SCREENSHOTS_COMPLETE
```

## Step 8: Cleanup

```
mcp__playwright__browser_close()
```

Do NOT use `pkill -f chrome` — it would kill parallel agents.

## Success Criteria

- [ ] Capture plan read, TodoWrite list created
- [ ] Page navigated via direct URL (no menu tree)
- [ ] Required seed state created (if applicable)
- [ ] Every baseline screenshot captured to `SCREENSHOTS_DIR`
- [ ] Every flow screenshot captured to `SCREENSHOTS_DIR`
- [ ] Validation sub-agent returned PASS
- [ ] `SCREENSHOTS_COMPLETE` marker written
- [ ] Browser closed via MCP
