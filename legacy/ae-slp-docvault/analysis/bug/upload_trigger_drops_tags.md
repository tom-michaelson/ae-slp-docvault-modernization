# Bug: Upload Trigger Silently Drops Tags

## Description

When a document is uploaded via `POST /api/upload`, tags submitted with the upload request are silently discarded in the `documents_v2` table — the table that all read endpoints query.

The upload route writes to the `documents` table (not `documents_v2`). A PostgreSQL trigger (`trg_sync_to_v2`) copies new rows from `documents` to `documents_v2`, but the INSERT statement in the trigger function deliberately omits the `tags` column:

```sql
INSERT INTO documents_v2 (id, name, file_type, file_path, uploaded_at, uploaded_by)
VALUES (NEW.id, NEW.name, NEW.file_type, NEW.file_path, NEW.uploaded_at, NEW.uploaded_by);
-- NOTE: NEW.tags deliberately omitted from the INSERT
```

As a result:
- `GET /api/documents` (reads `documents_v2`) returns every document with `tags: null`.
- `GET /api/documents/:id/tags` returns an empty array for every newly uploaded document.
- Tags can only be added after upload via `PUT /api/documents/:id/tags` (which writes directly to `documents_v2`), but any tags submitted at upload time are permanently lost.

**Expected behavior**: Tags included in the `POST /api/upload` request body are stored and retrievable.
**Actual behavior**: Tags are stored in `documents` but the trigger copies the row without them, and all reads go to `documents_v2`.

## Recommended Resolution

Short-term (patch): Update the trigger function to include `tags` in the INSERT:
```sql
INSERT INTO documents_v2 (id, name, file_type, file_path, tags, uploaded_at, uploaded_by)
VALUES (NEW.id, NEW.name, NEW.file_type, NEW.file_path, NEW.tags, NEW.uploaded_at, NEW.uploaded_by);
```

Medium-term (proper fix): Eliminate the two-table architecture. Have the upload route write directly to `documents_v2` and drop the `documents` table and trigger entirely. The split schema appears to be an unfinished migration rather than an intentional design.

## Verification Method

Static Analysis

## Location

- **File**: `backend/src/db/migrations/003-create-trigger.sql`
- **Line**: 5–7 (INSERT statement missing `tags` column)

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Notes or Next Steps

- The `NOTE: NEW.tags deliberately omitted` comment in the SQL suggests this was a known intentional omission during development — it may have been a placeholder that was never revisited.
- See `analysis/knowledge_gap/two_table_document_architecture.md` for the broader context of the two-table schema.
