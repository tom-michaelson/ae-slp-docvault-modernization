# DocVault

A modern, enterprise-ready document management dashboard. Upload, tag, search, and preview documents from a clean React UI backed by a robust Express/PostgreSQL API.

## Architecture

DocVault is split into two packages:

- **`/backend`** — Express REST API with PostgreSQL. Handles document CRUD, search, tagging, uploads, and authentication.
- **`/frontend`** — React 17 SPA with Redux state management. Features a sidebar, search bar, document grid, and inline preview panel (supports PDFs and images).

### Auth

We support multiple authentication strategies to cover different use cases:

- **JWT** — Primary auth for the frontend SPA. Tokens are issued on login and validated via `express-jwt` middleware.
- **Session-based auth** — Carried over from v1. Still works and some internal routes rely on it. Plan is to phase this out eventually.
- **API key auth** — Added for service account integrations. Headers are checked on all `/api` routes. (Integration docs coming soon.)

All three can coexist on the same request pipeline. The middleware stack figures out which one is active and sets `req.user` accordingly.

### State Management

The frontend uses Redux with a modular reducer architecture. Each domain concern gets its own reducer (auth, documents, filters, UI, cache, pagination, etc.) which keeps things organized as the app scales. There's also a custom middleware layer and an `ActionCreatorFactory` that standardizes how we dispatch actions — this saves a lot of boilerplate once you get used to the pattern.

### Search

Search goes through the `SearchOrchestrator` on the backend, which:

1. Normalizes the incoming query
2. Applies active filters
3. Delegates to the `IndexManager` for indexed lookups
4. Falls back to `FallbackSearchProvider` (Postgres `LIKE` queries) if no index hits
5. Re-ranks results with a pluggable scoring function

This gives us a clean extension point for adding Elasticsearch or similar later without touching the API layer.

## Getting Started

### Prerequisites

- Node.js (v16+)
- PostgreSQL (v13+)
- npm

### Setup

```bash
# Backend
cd backend
npm install
npm run migrate
npm start

# Frontend (separate terminal)
cd frontend
npm install
npm start
```

The backend runs on port 3001 (see `.env`) and the frontend dev server runs on port 3000.

### Environment Variables

Configuration is loaded from `.env` files. See `.env.development` for defaults. You can override locally with `.env.local` (gitignored).

Key variables:

| Variable | Description | Default |
|---|---|---|
| `PORT` | Backend server port | `3001` |
| `DATABASE_URL` | Postgres connection string | `postgresql://localhost:5432/docvault` |
| `JWT_SECRET` | Secret for signing JWTs | (set in .env) |
| `SESSION_SECRET` | Secret for session cookies | (set in .env) |
| `UPLOAD_DIR` | Directory for uploaded files | `./uploads` |
| `DEV_SKIP_AUTH` | Skip auth checks in development | `false` |

### Database

Run migrations with:

```bash
cd backend
npm run migrate
```

This sets up the `documents` table, indexes, and triggers.

## Project Structure

```
backend/
  src/
    config.js          # Centralized config loader
    index.js           # Express app setup + middleware
    db/                # Database pool, migrations
    middleware/        # Auth middleware (JWT, session, API key)
    routes/            # Route handlers (auth, documents, search, tags, upload)
    services/          # SearchOrchestrator, IndexManager, FallbackSearchProvider
  uploads/             # Uploaded document storage

frontend/
  src/
    App.jsx            # Root component
    store.js           # Redux store configuration
    components/        # UI components
    context/           # React context providers
    reducers/          # Redux reducers
    middleware/        # Custom Redux middleware
    utils/             # Utility functions
    lib/               # Shared helpers (API client, formatting)
```

## API

Base URL: `http://localhost:3001/api`

### Quick Reference

- `POST /api/auth/login` — Authenticate and receive JWT
- `GET /api/documents` — List documents (paginated)
- `POST /api/upload` — Upload a new document
- `GET /api/search?q=...` — Search documents
- `PUT /api/documents/:id/tags` — Update document tags

## Development

For local dev, set `DEV_SKIP_AUTH=true` in your `.env.local` to bypass authentication. This auto-injects a dev user into the request context so you don't need to deal with login flow during frontend work.

## Roadmap

- [ ] Complete JWT token refresh flow
- [ ] Remove legacy session auth
- [ ] Add Elasticsearch provider for SearchOrchestrator
- [ ] Finish class → functional component migration
- [ ] Consolidate utility functions
- [ ] Update dependencies

## License

Internal use only.
