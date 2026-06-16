# `legacy/`

The legacy codebase that `awa-discover` analyzes. Everything here is **read-only
input** — the discovery workflow never mutates this tree.

## Current legacy application

[eShopOnWeb](https://github.com/dotnet-architecture/eShopOnWeb) — an ASP.NET
Core reference app standing in for a legacy .NET web application.

## Getting the code

Clone the repo into this directory:

```bash
git clone https://github.com/dotnet-architecture/eShopOnWeb.git
```

Or, if already cloned as a sibling, symlink it:

```bash
ln -s ../../eShopOnWeb ./eShopOnWeb
```

## Running it locally

Screenshots in phase 2 of the discover workflow hit a running instance.

```bash
cd eShopOnWeb
docker compose up
# Web UI:    http://localhost:5106
# Admin:     http://localhost:5106/admin   (Blazor WASM)
# PublicApi: http://localhost:5200
```

## Pointing the workflow at it

The discover workflow reads `target_dir` and `app_url` from its input. Defaults
currently assume `../eShopOnWeb` — once the clone lives here, pass:

```bash
uv run python -m awa workflow start awa-discover \
  --input '{"target_dir": "legacy/eShopOnWeb", "app_url": "http://localhost:5106"}'
```
