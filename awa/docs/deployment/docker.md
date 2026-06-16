---
outline: [2, 3]
---

# Docker Deployment

This guide covers deploying AWA using Docker containers for both development and production environments.

## Overview

AWA Docker setup consists of 6 services:

- **PostgreSQL Database**: Persistent data storage for Temporal
- **Temporal Server**: Workflow engine (API only)
- **Temporal Admin Tools**: Command-line tools for Temporal administration
- **Temporal UI**: Web-based monitoring interface (separate service)
- **FastAPI Service**: REST API for workflow execution
- **Astro UI**: Web-based user interface

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available for containers

See [Installation - Docker](/installation/docker) for detailed instructions.

## Quick Start

### 1. Clone the repo

<!--@include: ../installation/parts/clone.md-->

### 2. Configure Environment

If you have not run AWA locally before (you've never run `make install`), copy the example environment file and configure your settings:

```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

**Set (at least) the `HOME_DIR` value** in your `.env` file in the root of the repo. Review our reference [Environment Configuration](/reference/configuration/environment) doc for a full reference of all supported environment variables.

:::code-group

```sh [.env]
HOME_DIR=/Users/michael.bluth
```

:::

See [Configuration](#configuration) for more details.

### 3. Run with Docker

Run AWA and all supporting services:

```bash
make start-docker
```

Or, if you're developing AWA locally, you can run just the supporting services (Langfuse, LiteLLM):

```bash
make start-docker-supporting
```

These commands will:

- Build all Docker images
- Start all services
- Display service URLs

### 4. Access Services

#### AWA

- **UI**: http://localhost:8000
- **API**: http://localhost:8001/docs
- **Temporal UI**: http://localhost:8002
- **Temporal Server**: http://localhost:7233
- **PostgreSQL**: Available via `docker exec`
- **Temporal Admin Tools**: Available via `docker exec` (see troubleshooting section)

#### Supporting

- **Langfuse**: http://localhost:3001
- **LiteLLM**: http://localhost:4002

### Other Docker Commands

```bash
# Full setup and start AWA and all supporting services
make start-docker

# Full setup and start only AWA (no Langfuse or LiteLLM)
make start-docker-supporting

# Build all images
make docker-build

# Start services
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

## Configuration

### Environment

Review our reference [Environment Configuration](/reference/configuration/environment) doc for a full reference of all supported environment variables.

Key environment variables for Docker deployment are below. By default, you should not need to modify any of these.

| Variable                      | Description                  | Default                        |
| ----------------------------- | ---------------------------- | ------------------------------ |
| `POSTGRES_PASSWORD`           | PostgreSQL password          | `temporal`                     |
| `POSTGRES_USER`               | PostgreSQL user              | `temporal`                     |
| `POSTGRES_DB`                 | PostgreSQL database          | `temporal`                     |
| `POSTGRES_HOST`               | PostgreSQL host              | `postgres`                     |
| `POSTGRES_DEFAULT_PORT`       | PostgreSQL default port      | `5432`                         |
| `TEMPORAL_VERSION`            | Temporal server version      | `1.27.2`                       |
| `TEMPORAL_ADMINTOOLS_VERSION` | Temporal admin tools version | `1.27.2-tctl-1.18.2-cli-1.3.0` |
| `TEMPORAL_UI_VERSION`         | Temporal UI version          | `2.34.0`                       |
| `POSTGRESQL_VERSION`          | PostgreSQL version           | `16`                           |

### Application

The `config.yaml` file in the root of the repository is mounted into the API container. See [Application Configuration](/reference/configuration/application) for details on how to use this file.

## Service Architecture

### Network Configuration

All services communicate through the `awa-network` Docker network:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ PostgreSQL  │    │   Temporal  │    │     API     │    │     UI      │
│   (5432)    │◄──►│   (7233)    │◄──►│    (8001)   │◄──►│   (8000)    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                           ▲
                           │
                    ┌─────────────┐    ┌─────────────┐
                    │ Temporal UI │    │Admin Tools  │
                    │   (8002)    │◄──►│   (CLI)     │
                    └─────────────┘    └─────────────┘
```

### Volume Mounts

- **PostgreSQL Data**: Persistent storage for database (`postgres_data`)
- **Configuration**: Read-only config file mounting

### Service Implementation

Each service uses dedicated entry point scripts for proper signal handling and service isolation:

- **API Service**: Uses `start_api_server()` function via `uv run -m awa.core.api`
- **UI Service**: Uses `pnpm run preview --host 0.0.0.0` for production serving
- **Temporal Service**: Uses official `temporalio/auto-setup` image
- **Temporal Admin Tools Service**: Uses official `temporalio/admin-tools` image for CLI operations
- **Temporal UI Service**: Uses official `temporalio/ui` image
- **PostgreSQL Service**: Uses official `postgres` image

### Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Network Security**: Use Docker networks for service isolation
3. **User Permissions**: Containers run as non-root users
4. **Volume Security**: Use read-only mounts where possible
5. **Database Security**: Use strong passwords for PostgreSQL in production

## Troubleshooting

### Common Issues

#### 1. Port Conflicts

If ports are already in use:

```bash
# Check what's using the ports
lsof -i :8000
lsof -i :7233
lsof -i :8080
lsof -i :4321
lsof -i :5432

# Stop conflicting services or change ports in docker-compose.yml
```

#### 2. Service Health Checks Failing

```bash
# Check service status
docker compose ps

# View detailed logs
docker compose logs <service-name>

# Restart specific service
docker compose restart <service-name>
```

#### 3. Permission Issues

```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Rebuild images
make docker-build
```

#### 4. Memory Issues

If containers are running out of memory:

```bash
# Check resource usage
docker stats

# Increase Docker memory limit in Docker Desktop settings
# Or add memory limits to docker-compose.yml
```

#### 5. LiteLLM Authentication Error

If you encounter this error when using LiteLLM:

```json
{
  "error": {
    "message": "Authentication Error, No connected db.",
    "type": "auth_error",
    "param": "None",
    "code": 401
  }
}
```

**Root Cause**: This error occurs due to LiteLLM's authentication mechanism. When you set a `master_key` in LiteLLM configuration, and the API key passed in the request is not the master key, LiteLLM assumes it's a user-created key from the database and attempts to validate it against the connected database.

**Solution**: Ensure you're using the correct API key:

- **Option 1**: Use the master key defined in your LiteLLM configuration (`litellm_config.yaml`):

  ```yaml
  general_settings:
    master_key: sk-awa # Use this key in your requests
  ```

- **Option 2**: If you need to use database-managed keys, ensure:
  - LiteLLM has proper database connectivity
  - The key exists in the LiteLLM database
  - Database authentication is properly configured

**Quick Fix**: In your AWA configuration, make sure the LiteLLM API key matches your master key:

```yaml
# config.yaml
llm:
  providers:
    lite_llm:
      api_key: sk-awa # Must match master_key in litellm_config.yaml
```

### Debug Commands

```bash
# Enter container shell
docker compose exec api bash
docker compose exec temporal bash
docker compose exec temporal-admin-tools bash
docker compose exec ui bash
docker compose exec postgres bash

# Check network connectivity
docker compose exec api ping temporal
docker compose exec api ping postgres
docker compose exec api ping ui

# View container logs
docker compose logs -f api
docker compose logs -f temporal
docker compose logs -f temporal-admin-tools
docker compose logs -f temporal-ui
docker compose logs -f postgres
docker compose logs -f ui

# Test individual services
docker compose exec api uv run -m awa.core.api
docker compose exec ui pnpm run preview --host 0.0.0.0
docker compose exec temporal temporal server start-dev --config /etc/temporal/config/dynamicconfig/development-postgresql.yaml --bind-on-localhost false --db postgresql --db-address postgres:5432 --db-user temporal --db-password temporal --db-name temporal

# Use Temporal admin tools for debugging
docker compose exec temporal-admin-tools temporal operator cluster health
docker compose exec temporal-admin-tools temporal workflow list
docker compose exec temporal-admin-tools temporal namespace list
```

## Monitoring

### Health Checks

All services include health checks:

- **PostgreSQL**: `pg_isready -U temporal -d temporal`
- **Temporal**: `temporal operator cluster health`
- **API**: `curl -f http://localhost:8000/health`
- **UI**: `curl -f http://localhost:4321`

### Logging

Logs are available through:

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api

# With timestamps
docker compose logs -f --timestamps
```
