# Create Navigation Plan for API Traffic Capture

You are creating a navigation plan for capturing API traffic from a legacy Passage page. The plan lists every interaction step the capture agent should perform, in order.

## Arguments

`$ARGUMENTS` is a JSON string with:
- `pageKey` — page directory key (e.g., `2014-line`)
- `outputFile` — path to write the navigation plan JSON

Parse it: `const args = JSON.parse('$ARGUMENTS')`

## Steps

### Step 1: Read Page Inventory

Read the inventory file at:
```
docs/entry-points/ui-pages/{args.pageKey}/inventory.json
```

This file is a JSON array of UI feature objects. Extract:
- `menuPath` from the first feature (all features on a page share the same menu path)
- All `key` values — these are the UI feature keys
- Any features with `elementType: "ui-panel-data-table"` or `elementType: "ui-panel-display"` — these represent tabs/panels

### Step 2: Read Functional Specs

For each UI feature key from Step 1, read:
```
docs/entry-points/ui-features/{feature_key}/functional-spec.md
```

If a functional spec doesn't exist for a feature, skip it. Focus on features that DO have specs.

From each functional spec, identify:
- Child tabs or panels mentioned
- Any special interaction needed (e.g., "click Retrieve to load data")
- The order of tabs as they appear in the UI

### Step 3: Build the Navigation Plan

Create an ordered list of interaction steps:

1. **Always first:** A `page_load` step (captures background API calls when the page first loads)
   - `capturePhase: "page-load"`

2. **Always second:** A `retrieve` step (click the Retrieve button to load the main data grid)
   - `capturePhase: "retrieve"`

3. **One step per child tab/panel:** In the order they appear in the functional specs
   - `action: "click_tab"`
   - `target: "{tab name}"`
   - `capturePhase: "tab:{tab-name-slug}"` (lowercase, hyphenated)

### Step 4: Write Output

Write the navigation plan JSON to `{args.outputFile}`. The JSON must validate against this schema:

```json
{
  "pageKey": "2014-line",
  "menuPath": "Infrastructure > Pipeline Definition > Line",
  "steps": [
    {
      "stepNumber": 1,
      "action": "page_load",
      "target": null,
      "capturePhase": "page-load",
      "description": "Initial page load — captures background API calls"
    },
    {
      "stepNumber": 2,
      "action": "retrieve",
      "target": "Retrieve",
      "capturePhase": "retrieve",
      "description": "Click Retrieve to load the main data grid"
    },
    {
      "stepNumber": 3,
      "action": "click_tab",
      "target": "Addresses",
      "capturePhase": "tab:addresses",
      "description": "Click the Addresses tab to load address data"
    }
  ],
  "features": ["2014-infrastructure-pipeline-definition-line", "..."]
}
```

## Important

- If no functional specs exist for ANY feature on the page, still produce a minimal plan with just `page_load` and `retrieve` steps
- The `features` array must list ALL UI feature keys from inventory.json, even if some don't have functional specs
- Tab names come from the functional specs — use the exact tab label text as the `target`
- `capturePhase` for tabs must be `tab:{slug}` where slug is the tab name lowercased and hyphenated
