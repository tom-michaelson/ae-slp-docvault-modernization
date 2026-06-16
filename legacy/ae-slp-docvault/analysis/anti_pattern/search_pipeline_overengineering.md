# Anti-Pattern: Search Pipeline Overengineering

## Description

The search feature routes every query through three custom classes — `SearchOrchestrator` → `IndexManager` → `FallbackSearchProvider` — before executing a single `WHERE name ILIKE $1` PostgreSQL query. This is three layers of abstraction for what is, in practice, one database call.

The stated purpose of this architecture is to provide "a clean extension point for adding Elasticsearch or similar later." In reality:
- `IndexManager.isIndexAvailable()` always returns `false`. The branch that would use a real index throws `new Error('Search index not implemented')`.
- `SearchOrchestrator.rerank()` maps every result to `{ ...result, score: 1.0 }` — a no-op that serves no ranking purpose.
- `FallbackSearchProvider.search()` also adds `score: 1.0` to every result — duplicating the no-op in the orchestrator.
- The `IndexManager` constructor sets `this.indexReady = false` with no mechanism to ever set it to `true`.

The complete abstraction adds approximately 100 lines of custom code and 3 class instantiations to execute what could be written as:

```js
// Direct replacement — same behavior, 5 lines
router.get('/', async (req, res) => {
  const { q } = req.query;
  if (!q?.trim()) return res.status(400).json({ error: "Query parameter 'q' is required" });
  const { rows } = await pool.query(
    'SELECT * FROM documents_v2 WHERE name ILIKE $1 ORDER BY uploaded_at DESC',
    [`%${q.toLowerCase()}%`]
  );
  res.json({ results: rows, query: q, total: rows.length });
});
```

**Verdict: unjustified overengineering.**

## Category

Architecture, Design

## Occurrences

| File | Line | Code Snippet | Description |
|------|------|--------------|-------------|
| `backend/src/services/SearchOrchestrator.js` | 1–54 | `class SearchOrchestrator` | Top-level orchestrator: normalizes query and calls rerank (no-op) |
| `backend/src/services/SearchOrchestrator.js` | 43–48 | `rerank(results) { return results.map(r => ({...r, score: 1.0})) }` | Re-ranking function that sets every score to 1.0 |
| `backend/src/services/IndexManager.js` | 1–33 | `class IndexManager` | Manages a search index that is always unavailable |
| `backend/src/services/IndexManager.js` | 11 | `this.indexReady = false;` | Index flag hardcoded false; never set to true anywhere |
| `backend/src/services/IndexManager.js` | 26–29 | `throw new Error('Search index not implemented')` | Dead code branch: the index-available path throws immediately |
| `backend/src/services/FallbackSearchProvider.js` | 1–22 | `class FallbackSearchProvider` | Wrapper class for a single ILIKE query |
| `backend/src/services/FallbackSearchProvider.js` | 18 | `score: 1.0` | Duplicate score assignment already done by SearchOrchestrator.rerank |
| `backend/src/routes/search.js` | 8 | `const orchestrator = new SearchOrchestrator();` | Module-level instantiation of the entire pipeline |

## Impact

- **Maintainability**: A developer unfamiliar with the codebase must read and understand 3 files and trace 4 function calls to understand what search does.
- **Performance**: Three object instantiations, four function calls, and two `Array.map` passes for every search request instead of one database call.
- **Misleading architecture**: The README states the orchestrator provides "a clean extension point for Elasticsearch." This creates false confidence — adding a real search provider requires significant surgery to a system that is more complex than it appears.
- **Dead code risk**: `IndexManager`'s `isIndexAvailable()` branch is dead code that will throw if it ever executes, and the `score: 1.0` assignment is done twice.

## Recommended Resolution

Replace the three-class pipeline with a direct database query in `routes/search.js` using `pool.query()`. If a real search index integration is genuinely planned, implement a single function (not three classes) at that time with actual index logic. Do not build the abstraction before the concrete requirement exists.

## Verification Method

Static Analysis

## Date Analyzed

2026-05-27

## Notes or Next Steps

- The three classes can be deleted entirely. Their only caller is `routes/search.js`.
- See `analysis/knowledge_gap/` for the undocumented assumption that this abstraction is "the extension point for Elasticsearch."
