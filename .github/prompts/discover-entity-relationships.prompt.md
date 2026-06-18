---
model: opus
---

# Discover Entity Relationships

For an `api-endpoint` item, infer the EF Core entity graph the .NET side will need
so that planning / implementation don't fabricate relationships ad-hoc. Reads
the item's database dependencies and the legacy migration/schema files; writes a single
JSON file.

**This command writes `{entry_point_folder_path}/relationship-discovery.json`.**

## Input parameters

| Arg | Purpose |
| --- | --- |
| `item_key` | Item key (typically `api-endpoint`; safe to no-op for pure `ui-feature`) |
| `item_type` | `api-endpoint` or `ui-feature` |
| `entry_point_folder_path` | Absolute path to the item's docs folder |
| `legacy_dir` | Absolute path to the legacy source |
| `page_key` *(optional)* | Page the item belongs to, used only for log context |
| `domain` *(optional)* | Domain label, used only for log context |

## Input sources

- `{entry_point_folder_path}/database-dependencies.json` — tables + operations.
- Legacy ORM schema / migrations:
  - `{legacy_dir}/src/db/migrations/*.js` (or `.ts`) — Sequelize / Knex migrations
  - `{legacy_dir}/src/models/**/*.js` (or `.ts`) — ORM model definitions (Sequelize, Prisma, Mongoose)
  - `{legacy_dir}/prisma/schema.prisma` — if Prisma is used
  - `{legacy_dir}/src/db/schema.js` (or `.ts`) — if a central schema file exists

## Process

1. Load `database-dependencies.json`; collect the set of tables.
2. From the migration + model + schema files, infer:
   - Primary keys and their types.
   - Foreign keys (both directions).
   - Relationship cardinality: `OneToMany`, `ManyToOne`, `ManyToMany`, `OneToOne`.
   - Cascade behavior if it appears in the schema or migration.
3. Build the output per the schema below.

## Output — `relationship-discovery.json`

```json
{
  "itemKey": "upload-document",
  "generatedAt": "2026-04-24T10:00:00Z",
  "entities": [
    {
      "name": "Document",
      "table": "documents",
      "primaryKey": {"name": "Id", "type": "Guid"},
      "fields": [
        {"name": "Title", "column": "title", "type": "string"},
        {"name": "OwnerId", "column": "owner_id", "type": "string"},
        {"name": "Status", "column": "status", "type": "string"}
      ],
      "relationships": [
        {
          "kind": "OneToMany",
          "field": "Versions",
          "targetEntity": "DocumentVersion",
          "mappedBy": "Document",
          "cascade": ["all"],
          "fetch": "lazy"
        }
      ]
    },
    {
      "name": "DocumentVersion",
      "table": "document_versions",
      "primaryKey": {"name": "Id", "type": "Guid"},
      "fields": [
        {"name": "FileUri", "column": "file_uri", "type": "string"},
        {"name": "Version", "column": "version", "type": "int"},
        {"name": "DocumentId", "column": "document_id", "type": "Guid"}
      ],
      "relationships": [
        {
          "kind": "ManyToOne",
          "field": "Document",
          "targetEntity": "Document",
          "joinColumn": "document_id",
          "fetch": "lazy"
        }
      ]
    }
  ],
  "notes": [
    "document_versions.document_id FK: ON DELETE CASCADE (migration: create_document_versions)."
  ]
}
```

## Rules

- Use EF Core / standard vocabulary (`OneToMany`, `ManyToOne`, `HasMany`, `BelongsTo`, etc.) to describe the .NET entity graph.
- Map legacy ORM column types to EF Core-friendly ones (`decimal(18,2)` stays as-is; `VARCHAR(255)` → `string`; `BOOLEAN` → `bool`).
- When cardinality is ambiguous, default to `ManyToOne` on the FK side and note it.

## Success criteria

- [ ] Every table from `database-dependencies.json` appears as an `entities` entry (or is explicitly noted as a non-entity reference table).
- [ ] Every FK in the DDL produces a bidirectional relationship entry (one side is optional if uninteresting).
- [ ] JSON parses successfully.

## Error handling

- **No `database-dependencies.json`:** write an empty `entities: []` + note the fact.
- **Unparseable migration or schema file:** emit a warning, skip that file, continue.
- **`item_type != "api-endpoint"`:** write `entities: []` and a note that the command is a no-op for UI-only items. Do not fail.
