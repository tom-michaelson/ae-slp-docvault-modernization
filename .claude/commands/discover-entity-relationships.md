---
model: opus
---

# Discover Entity Relationships

For an `api-endpoint` item, infer the JPA entity graph the Java side will need
so that planning / implementation don't fabricate relationships ad-hoc. Reads
the item's database dependencies and the legacy migration DDL; writes a single
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
- Legacy DDL / EF migrations:
  - `{legacy_dir}/src/Infrastructure/Data/Migrations/*.cs`
  - `{legacy_dir}/src/ApplicationCore/Entities/**/*.cs`
  - `{legacy_dir}/src/Infrastructure/Data/Config/*.cs` (EF type configurations)

## Process

1. Load `database-dependencies.json`; collect the set of tables.
2. From the migration + entity + config files, infer:
   - Primary keys and their types.
   - Foreign keys (both directions).
   - Relationship cardinality: `OneToMany`, `ManyToOne`, `ManyToMany`, `OneToOne`.
   - Cascade behavior if it appears in the DDL.
3. Build the output per the schema below.

## Output — `relationship-discovery.json`

```json
{
  "itemKey": "add-item-to-basket",
  "generatedAt": "2026-04-24T10:00:00Z",
  "entities": [
    {
      "name": "Basket",
      "table": "Baskets",
      "primaryKey": {"name": "Id", "type": "int"},
      "fields": [
        {"name": "BuyerId", "column": "BuyerId", "type": "string"}
      ],
      "relationships": [
        {
          "kind": "OneToMany",
          "field": "items",
          "targetEntity": "BasketItem",
          "mappedBy": "basket",
          "cascade": ["all"],
          "fetch": "lazy"
        }
      ]
    },
    {
      "name": "BasketItem",
      "table": "BasketItems",
      "primaryKey": {"name": "Id", "type": "int"},
      "fields": [
        {"name": "UnitPrice", "column": "UnitPrice", "type": "decimal(18,2)"},
        {"name": "Quantity", "column": "Quantity", "type": "int"},
        {"name": "CatalogItemId", "column": "CatalogItemId", "type": "int"}
      ],
      "relationships": [
        {
          "kind": "ManyToOne",
          "field": "basket",
          "targetEntity": "Basket",
          "joinColumn": "BasketId",
          "fetch": "lazy"
        }
      ]
    }
  ],
  "notes": [
    "BasketItems.BasketId FK: ON DELETE CASCADE (20201202111507_InitialModel.cs)."
  ]
}
```

## Rules

- Use JPA vocabulary (`OneToMany`, `ManyToOne`, etc.) even though the source is EF.
- Map EF column types to JPA-friendly ones (`decimal(18,2)` stays as-is; `nvarchar(40)` → `string`).
- When cardinality is ambiguous, default to `ManyToOne` on the FK side and note it.

## Success criteria

- [ ] Every table from `database-dependencies.json` appears as an `entities` entry (or is explicitly noted as a non-entity reference table).
- [ ] Every FK in the DDL produces a bidirectional relationship entry (one side is optional if uninteresting).
- [ ] JSON parses successfully.

## Error handling

- **No `database-dependencies.json`:** write an empty `entities: []` + note the fact.
- **Unparseable migration:** emit a warning, skip that migration, continue.
- **`item_type != "api-endpoint"`:** write `entities: []` and a note that the command is a no-op for UI-only items. Do not fail.
