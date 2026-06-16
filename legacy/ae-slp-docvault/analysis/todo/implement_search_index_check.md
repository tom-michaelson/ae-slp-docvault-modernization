# TODO: Implement Search Index Check

## Description

The `IndexManager.isIndexAvailable()` method always returns `false` because `this.indexReady` is hardcoded to `false` and is never set to `true`. The TODO comment indicates this was supposed to check an external search index (Elasticsearch or Algolia) but was never implemented.

## Original Comment

```
// TODO: implement search index check
// This was supposed to check Elasticsearch/Algolia but was never completed
```

## Location

- **File**: `backend/src/services/IndexManager.js`
- **Line**: 14

## Priority

Medium

## Estimated Effort

Large (4+ hours)

## Verification Method

Static Analysis

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Notes or Next Steps

- The entire `SearchOrchestrator` → `IndexManager` → `FallbackSearchProvider` pipeline exists to support this eventual integration. Since the integration was never built, the pipeline is currently three layers of abstraction wrapping a single ILIKE query.
- If no real search index integration is planned in the near term, the correct action is to delete the three service classes and inline the query, not implement the check.
- See `analysis/anti_pattern/search_pipeline_overengineering.md`.
