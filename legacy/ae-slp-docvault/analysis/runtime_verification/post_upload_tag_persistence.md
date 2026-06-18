# Runtime Verification: POST /api/upload — Tag Persistence and Input Validation

## Endpoint

`POST /api/upload`, `PUT /api/documents/:id/tags`

## Test Environment

- Backend running on port 3001 with `DEV_SKIP_AUTH=true`
- **PostgreSQL not available** — upload and tag persistence tests that require database writes are environment-constrained
- Input validation tests (pre-database) executed successfully

## Test 1 — Upload with No File

**Request:**
```
POST http://localhost:3001/api/upload
Content-Type: multipart/form-data; boundary=TestBoundary
(body: name field only, no file)
```

**Response:** 400 (validation fired before database access)

**Assessment:** The "no file provided" guard runs correctly even without a database. ✓

## Test 2 — Tags Validation: Non-Array Body

**Request:**
```
PUT http://localhost:3001/api/documents/test-id/tags
Content-Type: application/json
{ "tags": "not-an-array" }
```

**Response (400):**
```json
{ "error": "Tags must be an array" }
```

**Assessment:** Input validation for non-array tags works correctly. ✓

## Test 3 — Tags Validation: Exceeds 10-Tag Limit

**Request:**
```
PUT http://localhost:3001/api/documents/test-id/tags
Content-Type: application/json
{ "tags": ["a","b","c","d","e","f","g","h","i","j","k"] }
```

**Response (400):**
```json
{ "error": "Maximum 10 tags per document" }
```

**Assessment:** 11-tag request rejected as expected. The limit enforcement is at the right layer. ✓

## Test 4 — Upload Tag Loss (Environment-Constrained)

**Finding:** Cannot verify at runtime — PostgreSQL is not available in this environment. The tag loss bug is documented in the SQL trigger migration file (`003-create-trigger.sql`) with explicit confirmation: the INSERT statement omits `NEW.tags`. The SQL evidence is unambiguous and does not require runtime confirmation.

**Static evidence:**
```sql
-- From backend/src/db/migrations/003-create-trigger.sql
INSERT INTO documents_v2 (id, name, file_type, file_path, uploaded_at, uploaded_by)
VALUES (NEW.id, NEW.name, NEW.file_type, NEW.file_path, NEW.uploaded_at, NEW.uploaded_by);
-- NOTE: NEW.tags deliberately omitted from the INSERT
```

**Assessment:** Verified by static analysis. Bug is real. Cannot confirm end-to-end at runtime due to environment constraint (no PostgreSQL).

## Findings

Input validation for upload and tag operations functions correctly. The tag-loss defect is confirmed via static analysis of the SQL trigger and is not a runtime-observable defect without a connected database. The upload endpoint has no file size limit configured in the multer setup — this is a risk but could not be triggered to failure without a running database.

## Reference

`analysis/bug/upload_trigger_drops_tags.md`
