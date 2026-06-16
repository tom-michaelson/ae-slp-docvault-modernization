# Analyze Page Patterns

Analyze patterns for a page - identify required patterns and check availability in a single step.

**This command maps page features to known patterns and checks their availability in the Pattern Registry.**

## Input Parameters

You will receive:
- **page_key**: The page folder name (e.g., `2046-ba-request`). This is the existing folder under `docs/entry-points/ui-pages/` created by the Discover workflow.
- **domain**: The domain name (e.g., `company`)

Example invocation:
```
/develop.analyze-page-patterns page_key: 2046-ba-request domain: company
```

**IMPORTANT:** The `page_key` must match an existing folder in `docs/entry-points/ui-pages/`. This command reads from and writes to this existing folder.

## Input Sources

Read the page analysis from:
- `docs/entry-points/ui-pages/{page-key}/page-analysis.json` (output from `/develop.analyze-page-components`)

Reference the pattern catalog at:
- `docs/target-architecture/frontend-architecture/page-patterns/`
- `docs/target-architecture/api-design/`
- `docs/target-architecture/backend-architecture/`

Use the Pattern Registry for availability checks:
- `docs/target-architecture/patterns/ui-patterns.json`
- `docs/target-architecture/patterns/api-patterns.json`
- `docs/target-architecture/patterns/batch-patterns.json`
- `docs/target-architecture/patterns/trigger-patterns.json`

## Pattern Identification Rules

### UI Patterns

Map UI features to patterns:

| Feature Type | Pattern Name | Pattern ID |
|-------------|--------------|------------|
| Data grid with editing | Editable Data Grid | `editable-data-grid` |
| Read-only data grid | Read-Only Data Grid | `read-only-data-grid` |
| Tabbed layout | Tab Container | `tab-container` |
| Multi-tab form | Multi-Tab Form | `multi-tab-form` |
| Master-detail view | Master-Detail View | `master-detail-view` |
| File attachment list | File Attachment Panel | `file-attachment-panel` |
| Search/filter panel | Search Filter Panel | `search-filter-panel` |
| Modal dialog | Modal Dialog | `modal-dialog` |
| Confirmation dialog | Confirmation Dialog | `confirmation-dialog` |
| Data panel (read-only) | Data Display Panel | `data-display-panel` |
| Form with validation | Validated Form | `validated-form` |
| Navigation menu | Navigation Menu | `navigation-menu` |
| Breadcrumb trail | Breadcrumb Navigation | `breadcrumb-navigation` |

### API Patterns

Map API endpoints to patterns:

| Endpoint Type | Pattern Name | Pattern ID |
|--------------|--------------|------------|
| Standard CRUD | CRUD Endpoint | `crud-endpoint` |
| Paginated list | Paginated List | `paginated-list` |
| Bulk create/update | Bulk Operations | `bulk-operations` |
| Bulk delete | Bulk Delete | `bulk-delete` |
| File upload | File Upload | `file-upload` |
| File download | File Download | `file-download` |
| Search endpoint | Search Endpoint | `search-endpoint` |
| Export to file | Data Export | `data-export` |
| Import from file | Data Import | `data-import` |
| Validation endpoint | Validation Endpoint | `validation-endpoint` |

### Batch Patterns

Map batch jobs to patterns:

| Job Type | Pattern Name | Pattern ID |
|----------|--------------|------------|
| Scheduled job | Scheduled Batch Job | `scheduled-batch-job` |
| Event-driven job | Event-Driven Batch | `event-driven-batch` |
| Report generation | Report Generator | `report-generator` |
| Data sync | Data Synchronization | `data-sync` |
| Cleanup job | Cleanup Batch | `cleanup-batch` |

### Trigger Patterns

Map triggers to patterns:

| Trigger Type | Pattern Name | Pattern ID |
|-------------|--------------|------------|
| Audit logging | Audit Trigger | `audit-trigger` |
| Cascade delete | Cascade Delete Trigger | `cascade-delete-trigger` |
| Cascade update | Cascade Update Trigger | `cascade-update-trigger` |
| Validation trigger | Validation Trigger | `validation-trigger` |
| Notification trigger | Notification Trigger | `notification-trigger` |

## Process

### Step 1: Load Page Analysis

Read and parse `docs/entry-points/ui-pages/{page-key}/page-analysis.json`

### Step 2: Map Components to Patterns

For each component (UI feature, API endpoint, batch job, trigger):
1. Check component type against pattern rules
2. Consider interactions and data requirements
3. Assign most specific pattern that matches
4. Note any components requiring multiple patterns

### Step 3: Check Pattern Registry

For each identified pattern:
1. Check if pattern exists in the appropriate registry file
2. If found: Record as "used" pattern with version, paths, etc.
3. If not found: Add to "gaps" with actionable information

### Step 4: Determine Gap Actions

For patterns not found, determine the action needed:

| Condition | Action | Priority |
|-----------|--------|----------|
| Documentation exists, no implementation | "Create reference implementation based on documentation" | high |
| Implementation exists, no documentation | "Document existing implementation" | medium |
| Neither exists | "Design, document, and implement pattern" | high |

### Step 5: Generate Output Files

Write two files to `docs/entry-points/ui-pages/{page-key}/`:
- `pattern-gaps.{domain}.json` - Patterns that need to be created/implemented
- `used-patterns.{domain}.json` - Patterns that are available and being used

## Output Files

### pattern-gaps.{domain}.json

Write to `docs/entry-points/ui-pages/{page-key}/pattern-gaps.{domain}.json`:

```json
{
  "pageKey": "2046-ba-request",
  "domain": "company",
  "generatedAt": "2026-01-26T10:00:00Z",
  "gaps": [
    {
      "patternId": "multi-tab-form",
      "patternName": "Multi-Tab Form",
      "patternType": "ui",
      "requiredFor": ["company-details-form"],
      "documentationExists": true,
      "documentationPath": "docs/target-architecture/frontend-architecture/page-patterns/multi-tab-form.md",
      "implementationExists": false,
      "action": "Create reference implementation based on documentation",
      "priority": "high"
    }
  ],
  "summary": {
    "totalGaps": 2,
    "gapsWithDocs": 1,
    "gapsWithoutDocs": 1
  }
}
```

### used-patterns.{domain}.json

Write to `docs/entry-points/ui-pages/{page-key}/used-patterns.{domain}.json`:

```json
{
  "pageKey": "2046-ba-request",
  "domain": "company",
  "generatedAt": "2026-01-26T10:00:00Z",
  "usedPatterns": [
    {
      "patternId": "editable-data-grid",
      "patternName": "Editable Data Grid",
      "patternType": "ui",
      "version": 2,
      "usedFor": ["company-grid", "address-grid"],
      "registryPath": "docs/target-architecture/patterns/ui/editable-data-grid.md"
    }
  ],
  "summary": {
    "totalUsed": 5,
    "byType": {
      "ui": 3,
      "api": 2,
      "batch": 0,
      "trigger": 0
    }
  }
}
```

## Success Criteria

- [ ] Page analysis file read successfully
- [ ] All UI features mapped to patterns
- [ ] All API endpoints mapped to patterns
- [ ] All batch jobs mapped to patterns
- [ ] All triggers mapped to patterns
- [ ] Pattern registry checked for each pattern
- [ ] pattern-gaps.{domain}.json file written
- [ ] used-patterns.{domain}.json file written
- [ ] Summary statistics calculated

## Error Handling

**Missing Page Analysis**:
- Report error: "Page analysis not found"
- Suggest running `/develop.analyze-page-components` first

**Unknown Feature Type**:
- Log warning about unmapped feature
- Include in gaps with `"patternId": "unknown"` for manual review

**Multiple Patterns for Single Feature**:
- Include all applicable patterns
- Note in `requiredFor` field that feature requires multiple patterns

**Missing Registry File**:
- Treat all patterns of that type as gaps
- Continue processing

## Notes

- This command combines pattern identification and availability checking into a single step
- Outputs are per-page (not domain-level) for use with PatternRegistrationWorkflow
- Pattern IDs must match those in the Pattern Registry
- When in doubt, assign the more specific pattern
- The `readyForImplementation` status depends on gaps being empty
