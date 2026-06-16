# Take Screenshots for UI Feature (Headless Mode)

Takes screenshots of a UI feature in the Passage application using **headless browser mode** (no visible browser window).

## Arguments

- `$ARGUMENTS` - The UI feature folder name (e.g., "2105-infrastructure-company-company-maintenance-address")

## What This Does

1. Reads the feature's `metadata.json` and `functional-description.md` from `./docs/entry-points/ui-features/$ARGUMENTS/`
2. Logs into Passage using the login script (in headless mode - no visible browser)
3. Navigates to the feature via menu tree
4. Takes screenshots and moves them to `./docs/entry-points/ui-features/$ARGUMENTS/screenshots/`
5. Creates a `SCREENSHOTS_COMPLETE` marker file in the screenshots directory
6. Closes browser and kills all browser processes

**Note:** In headless mode, all browser operations happen invisibly. Use `mcp__playwright__browser_snapshot()` to understand the current page state since you cannot see the browser.

**Warning:** For action features (New, Modify, Delete), action buttons are NOT visible. They are revealed by **hovering over the "Menu" element** in panel headers. See "Step 5b" and "Accessing Action Menus" sections below.

## Step 1: Read Feature Documentation

Read these files to understand the feature:
- `./docs/entry-points/ui-features/inventory.json` - Master inventory with all features and their relationships
- `./docs/entry-points/ui-features/$ARGUMENTS/functional-description.md` - Understand UI states to capture

**Use inventory.json for navigation hierarchy:**

1. Find the feature entry by matching `key` == `$ARGUMENTS`
2. Determine the navigation chain by following parent references:
   - If feature has `pageKey`: find the page entry to get `menuPath`
   - If feature has `panelKey`: find the panel entry to know which tab to click
   - If feature has `parentKey`: find the parent entry (could be page or panel)
3. The entry with `menuPath` is always the top-level page

**Example hierarchy for `2105-infrastructure-company-company-maintenance-address-modify`:**
```
Action (target feature):
  key: "2105-infrastructure-company-company-maintenance-address-modify"
  pageKey: "2105-infrastructure-company-company-maintenance"
  panelKey: "2105-infrastructure-company-company-maintenance-address"
  actionName: "Modify"

Panel (tab to click):
  key: "2105-infrastructure-company-company-maintenance-address"
  parentKey: "2105-infrastructure-company-company-maintenance"

Page (has menuPath):
  key: "2105-infrastructure-company-company-maintenance"
  menuPath: "Infrastructure > Company > Company Maintenance"
```

This tells you: Navigate via menuPath → click Retrieve → select row → click Address tab → click Modify button.

## Step 2: Login to Passage

Read and execute the login script:

```
Read file: ./.claude/tools/playwright/passage-login.js
Execute with: mcp__playwright__browser_run_code(code=<file contents>)
```

This logs in with JKILPACK/PassageIsDaBomb1! and waits for the main menu.

This ensures all UI elements are visible and screenshots capture the full interface without truncation.

**Headless Note:** You won't see the browser, but the login is happening. Use snapshots to verify state.

## Step 3: Navigate Menu Tree

Parse `menuPath` (e.g., "Infrastructure > Company > Company Maintenance") and click each level.

For each menu level:
1. `mcp__playwright__browser_snapshot()` - Get current refs
2. `mcp__playwright__browser_click(element="<menu item> treeitem", ref=<ref>)` - Click to expand/open

The final item opens the page as a dialog.

**Headless Tip:** Always take a snapshot before clicking to ensure you have the correct element refs.

## Step 4: Load Data

Most pages have empty grids initially:
1. `mcp__playwright__browser_snapshot()`
2. `mcp__playwright__browser_click(element="Retrieve button", ref=<ref>)`
3. `mcp__playwright__browser_wait_for(time=2)`

## Step 5: For Child Features (with parentKey)

1. Click a row in the parent grid to select it
2. `mcp__playwright__browser_snapshot()`
3. Click the appropriate tab (tab name often matches feature name, e.g., "Company Address")
4. `mcp__playwright__browser_wait_for(time=1)`

## Step 5b: For Action Features (with actionName like "New", "Modify", "Delete")

If the feature has an `actionName` property (e.g., `"actionName": "Modify"`), you need to trigger that action to open the modal. **Actions are accessed via hover menus, NOT visible buttons.**

1. First complete Step 5 to navigate to the correct panel/tab
2. **Select a row** in the panel's grid (click on it to highlight it)
3. `mcp__playwright__browser_snapshot()` - Find the "Menu" generic element in the panel header
4. **Hover over the "Menu" element**: `mcp__playwright__browser_hover(element="Menu element", ref=<menu_ref>)`
5. A menubar will appear with menuitem elements - find the one matching `actionName`
6. **Click the action**: `mcp__playwright__browser_click(element="<actionName> menuitem", ref=<menuitem_ref>)`
7. `mcp__playwright__browser_wait_for(time=1)` - Wait for modal to open

See the "IMPORTANT: Accessing Action Menus" section below for detailed examples.

## Step 6: Capture Screenshots

```bash
mkdir -p ./docs/entry-points/ui-features/$ARGUMENTS/screenshots/
```

Take screenshot:
```
mcp__playwright__browser_take_screenshot(filename="screenshots/<name>.png")
```

Move from Playwright output directory:
```bash
mv ./.playwright-mcp/screenshots/<name>.png ./docs/entry-points/ui-features/$ARGUMENTS/screenshots/
```

**Headless Note:** Screenshots work identically in headless mode. The browser renders the page internally and captures it to an image file.

## Step 7: Create Completion Marker

After all screenshots have been captured and moved, create a `SCREENSHOTS_COMPLETE` marker **file** (NOT a directory):

```bash
# Create a FILE with timestamp - do NOT use mkdir
echo "$(date -Iseconds)" > ./docs/entry-points/ui-features/$ARGUMENTS/screenshots/SCREENSHOTS_COMPLETE
```

**IMPORTANT:** Use the redirect operator `>` to create a file. Do NOT use `mkdir` here. The result should be a text file containing a timestamp, not a directory.

This marker file signals that screenshot capture is complete and includes a timestamp. Other processes can check for the existence of this file to know when screenshots are ready.

## Step 8: Cleanup

```
mcp__playwright__browser_close()
```

**IMPORTANT:** Do NOT use broad `pkill -f chrome` as it will kill Chrome processes from other parallel agents. The workflow handles Chrome cleanup with PID isolation. Only close the browser via the MCP tool above.

## Critical Notes

1. **Screenshot path**: Playwright saves to `.playwright-mcp/` - must move files afterward
2. **Fresh snapshots**: Element refs change after every click - always snapshot before clicking
3. **Empty grids**: Click "Retrieve" to load data
4. **Child features**: Select a parent row before tab content loads
5. **URL never changes**: Don't rely on URL for navigation detection
6. **Headless debugging**: Use `mcp__playwright__browser_snapshot()` frequently to understand page state since you cannot see the browser

## IMPORTANT: Accessing Action Menus (New, Modify, Delete, etc.)

**This is a common UI pattern throughout the Passage application.** Action buttons like "New", "Modify", "Delete" are NOT displayed as visible buttons. They are hidden in dropdown menus that must be revealed.

### How to Access Action Menus

There are TWO ways to reveal action menus:

#### Method 1: Hover over "Menu" element (RECOMMENDED)
Each data panel has a header with the panel title and a "Menu" text element. Hovering over the "Menu" element reveals the action options.

```
1. First, select a row in the grid (click on it)
2. mcp__playwright__browser_snapshot() - Find the "Menu" generic element in the panel header
3. mcp__playwright__browser_hover(element="Menu element in panel header", ref=<menu_ref>)
4. The snapshot will now show a menubar with menuitem elements like:
   - menuitem "New" [ref=xxx]
   - menuitem "Modify" [ref=xxx]
   - menuitem "Delete" [ref=xxx]
5. mcp__playwright__browser_click(element="Modify menuitem", ref=<menuitem_ref>)
```

#### Method 2: Right-click on a selected row
Right-clicking on a grid row also reveals a context menu with the same actions.

```
1. First, select a row in the grid (click on it)
2. mcp__playwright__browser_click(element="<row description>", ref=<row_ref>, button="right")
3. The snapshot will show the context menu with action options
4. Click on the desired action
```

### Menu Pattern Example

In the accessibility snapshot, the "Menu" element appears like this:
```yaml
- group [ref=f1e641]:
  - generic [ref=f1e642]: Company Address   # Panel title
  - generic [ref=f1e644]: Menu              # <-- HOVER ON THIS
```

After hovering, a menubar appears:
```yaml
- menubar [ref=f1e724]:
  - menuitem "New" [ref=f1e725]:
    - generic [ref=f1e726] [cursor=pointer]: New
  - menuitem "Modify" [ref=f1e727]:
    - generic [ref=f1e728] [cursor=pointer]: Modify
```

### Key Points
- **Always select a row first** before trying to access action menus
- **Use hover, not click** on the "Menu" element - clicking may not work
- **Look for the second "Menu"** - there may be multiple Menu elements; the one in the child panel (e.g., Company Address) is usually what you need
- **Actions depend on selection** - the menu options apply to the currently selected grid row

## Example: Company Address Feature

For `2105-infrastructure-company-company-maintenance-address`:

1. Search inventory.json for `key: "2105-infrastructure-company-company-maintenance-address"`
2. Find `parentKey: "2105-infrastructure-company-company-maintenance"`
3. Search inventory.json for that parent key, find `menuPath: "Infrastructure > Company > Company Maintenance"`
4. Execute login script
5. Navigate: Infrastructure → Company → Company Maintenance
6. Click Retrieve, wait for grid
7. Click first company row
8. Click "Company Address" tab
9. Take screenshot, move to target directory
10. Create `SCREENSHOTS_COMPLETE` marker file
11. Close browser, kill processes

## Example: Company Address Modify Action

For `2105-infrastructure-company-company-maintenance-address-modify`:

1. Search inventory.json for `key: "2105-infrastructure-company-company-maintenance-address-modify"`
2. Find `pageKey: "2105-infrastructure-company-company-maintenance"` and `panelKey: "2105-infrastructure-company-company-maintenance-address"`
3. Search for the page key, find `menuPath: "Infrastructure > Company > Company Maintenance"`
4. Execute login script
5. Navigate: Infrastructure → Company → Company Maintenance
6. Click Retrieve, wait for grid
7. Click first company row (in the Company grid)
8. Click "Company Address" tab (derived from panel key or tab name in UI)
9. **Select an address row in the Company Address grid**
10. **Hover over the "Menu" element in the Company Address panel header** (see "Accessing Action Menus" section above)
11. **Click the "Modify" menuitem** that appears in the menubar
12. Take screenshot of modal, move to target directory
13. Create `SCREENSHOTS_COMPLETE` marker file
14. Close browser, kill processes

**Important:** Step 9-11 use the Action Menu pattern. The "Modify" action is NOT a visible button - it's hidden in a menu that appears when you hover over the "Menu" element.

## Success Criteria

- [ ] Headless mode configured in .mcp.json (prerequisite)
- [ ] Logged in via login script
- [ ] Navigated to correct page
- [ ] Data loaded (clicked Retrieve)
- [ ] Child tab accessed (if applicable)
- [ ] Screenshot(s) captured and moved to feature's screenshots/ folder
- [ ] `SCREENSHOTS_COMPLETE` marker file created in screenshots/ folder
- [ ] Browser closed and processes killed

## Troubleshooting Headless Mode

### Browser Still Showing?
- Ensure you restarted Claude Code after modifying `.mcp.json`
- Verify the `--headless` flag is in the args array

### Screenshots Are Black/Empty?
- Add `mcp__playwright__browser_wait_for(time=2)` before taking screenshots to ensure content has rendered
- Some dynamic content may need longer wait times in headless mode

### Navigation Fails?
- Use `mcp__playwright__browser_snapshot()` more frequently to debug
- The accessibility snapshot shows the full page structure even in headless mode
