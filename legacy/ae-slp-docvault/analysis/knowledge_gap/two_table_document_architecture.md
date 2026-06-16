# Knowledge Gap: Two-Table Document Architecture

## Description

The database schema contains two tables with identical schemas — `documents` and `documents_v2` — connected by a PostgreSQL trigger. The rationale, migration status, and intended final state of this architecture are not documented anywhere.

From the code, a partial picture can be inferred:
- `documents` is the "original" table (migration 001).
- `documents_v2` appears to be a migration target (migration 002, name suggests v2).
- A trigger (`003-create-trigger.sql`) syncs `documents` → `documents_v2` on INSERT, but omits `tags`.
- The upload route (`routes/upload.js`) writes to `documents`.
- All read routes (`routes/documents.js`, `routes/tags.js`, `routes/search.js`) read from `documents_v2`.
- Direct tag updates (`PUT /api/documents/:id/tags`) write to `documents_v2` but not back to `documents`.

**What is not documented:**
- Why were two tables created? Was `documents_v2` intended to add a column that `documents` did not have? The schemas are identical.
- Is `documents` still needed, or is it only kept because the upload route writes to it?
- Is the trigger the intended long-term sync mechanism, or was the upload route supposed to be migrated to write to `documents_v2` directly?
- What happens to `documents` rows that have tags updated via the tags route? The update goes to `documents_v2` only — `documents` has stale tag data.
- Should `documents` and `documents_v2` stay in sync bidirectionally? Currently they can diverge: a tag update to `documents_v2` is not reflected back to `documents`.

The comment `-- NOTE: NEW.tags deliberately omitted from the INSERT` in the trigger SQL is the only documentation, and it says nothing about why.

## Area Affected

- **Module / Component**: `backend/src/db/migrations/`, `backend/src/routes/upload.js`, `backend/src/routes/documents.js`
- **Domain**: Data Model, Infrastructure

## Impact

- The tag-loss bug on upload (see `analysis/bug/upload_trigger_drops_tags.md`) is a direct consequence of this undocumented architecture — a developer fixing that bug cannot know whether the "right" fix is to update the trigger, move the write to `documents_v2`, or migrate both tables into one.
- Any new feature that stores data must decide which table to write to without guidance, risking data going to the table that is not read.
- The bidirectional sync gap (tags updated in `documents_v2` not reflected in `documents`) means `documents` data is stale as soon as any tag operation runs.

## Recommended Actions

1. Document the migration intent in a `SCHEMA.md` or inline SQL comments: is `documents_v2` the final schema, and is `documents` being phased out?
2. If `documents_v2` is the migration target: update the upload route to write directly to `documents_v2`, drop the trigger, and plan the deprecation of `documents`.
3. If the two-table architecture is permanent: document why, add bidirectional sync to the trigger (or remove direct writes to either table from application code).
4. Add the `tags` column to the trigger INSERT as an immediate patch regardless of the longer-term decision.

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Verification Method

Static Analysis

## Notes or Next Steps

- `broken-project-docvault.md` confirms this is an "unfinished migration" — this context is not in the repository's main documentation.
