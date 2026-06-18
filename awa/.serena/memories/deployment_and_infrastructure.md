# AWA Deployment and Infrastructure

## Container Architecture

### Docker Images
AWA provides multiple Docker images for different components:

#### 1. API Server Image
- **Dockerfile**: `Dockerfile.api`
- **Build Command**: `make docker-build-api`
- **Purpose**: FastAPI server for REST endpoints
- **Base**: Python 3.12+ with UV package manager

#### 2. UI Server Image
- **Dockerfile**: `Dockerfile.ui`
- **Build Command**: `make docker-build-ui`
- **Purpose**: Frontend user interface
- **Base**: Node.js with pnpm

#### 3. All-in-One Build
- **Build Command**: `make docker-build`
- **Purpose**: Build all images simultaneously

### Docker Compose Configurations

#### Main Compose File: `docker-compose.yml`
**Services**:
- AWA API server
- AWA UI server
- PostgreSQL database
- Temporal server
- Temporal UI
- Temporal worker

#### Supporting Services: `docker-compose.awa-supporting.yml`
**Services**:
- PostgreSQL for Temporal
- Temporal server cluster
- Temporal UI dashboard
- Redis (if needed for caching)

#### Langfuse Integration: `docker-compose.langfuse.yml`
**Services**:
- Langfuse server for LLM observability
- Langfuse database
- Analytics and monitoring

#### LiteLLM Proxy: `docker-compose.litellm.yml`
**Services**:
- LiteLLM proxy for unified LLM API
- Configuration management
- Load balancing across providers

## Deployment Commands

### Local Development Deployment
```bash
make start-docker              # Full Docker deployment
make start-docker-supporting   # Supporting services only
make docker-up                # Start with docker compose
make docker-down              # Stop and remove containers
make docker-logs              # View service logs
```

### Production-Ready Deployment
```bash
make docker-build             # Build all images
make docker-up               # Start services
# Configure external database and services
```

## Infrastructure Components

### Database Configuration
- **Default**: SQLite for development
- **Production**: PostgreSQL via Docker
- **Temporal**: Dedicated PostgreSQL instance
- **Configuration**: Environment variables for connection strings

### Service Dependencies
1. **Temporal Server**: Workflow orchestration engine
2. **Temporal Worker**: Workflow execution environment
3. **PostgreSQL**: Data persistence and Temporal state
4. **Redis** (Optional): Caching and session management
5. **Langfuse** (Optional): LLM monitoring and analytics

### Network Configuration
- **API Server**: Port 8000 (configurable)
- **UI Server**: Port 3000 (configurable)
- **Temporal Server**: Port 7233
- **Temporal UI**: Port 8088
- **PostgreSQL**: Port 5432
- **Langfuse**: Port 3001

## Environment Configuration

### Environment Files
- **`.env`**: Active environment configuration
- **`.env.example`**: Template with all required variables
- **Development**: Local overrides and API keys
- **Production**: Container environment variables

### Required Environment Variables

#### LLM Provider Configuration
```bash
# OpenAI
OPENAI_API_KEY=your_openai_key

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Google Vertex AI
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
VERTEX_PROJECT_ID=your_gcp_project

# Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_key
```

#### Database Configuration
```bash
# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/awa
TEMPORAL_DATABASE_URL=postgresql://user:password@localhost:5432/temporal

# SQLite (Development)
DATABASE_URL=sqlite:///./awa.db
```

#### Temporal Configuration
```bash
TEMPORAL_HOST=localhost
TEMPORAL_PORT=7233
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_QUEUE=awa-task-queue
```

#### Observability Configuration
```bash
# Langfuse
LANGFUSE_SECRET_KEY=your_langfuse_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_HOST=http://localhost:3001

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Scaling and High Availability

### Horizontal Scaling
- **API Servers**: Multiple instances behind load balancer
- **Temporal Workers**: Scale worker instances based on load
- **Database**: PostgreSQL clustering and read replicas
- **Caching**: Redis cluster for distributed caching

### Load Balancing
```nginx
# Example Nginx configuration
upstream awa_api {
    server awa_api_1:8000;
    server awa_api_2:8000;
    server awa_api_3:8000;
}

server {
    listen 80;
    location /api/ {
        proxy_pass http://awa_api;
    }
}
```

### Health Monitoring
- **Health Endpoints**: `/health` for API server status
- **Temporal Monitoring**: Built-in Temporal UI dashboard
- **Custom Metrics**: Prometheus/Grafana integration
- **Log Aggregation**: ELK stack or similar

## Security Configuration

### API Security
- **Authentication**: JWT tokens with configurable expiration
- **HTTPS**: TLS termination at load balancer
- **CORS**: Configurable cross-origin policies
- **Rate Limiting**: Request throttling per client

### Container Security
- **Non-root User**: Containers run with restricted privileges
- **Secrets Management**: Environment variables and volumes
- **Image Scanning**: Security vulnerability scanning
- **Network Isolation**: Container network policies

### Database Security
- **Encryption**: Data at rest and in transit
- **Access Control**: Role-based database permissions
- **Backup Encryption**: Encrypted database backups
- **Connection Security**: SSL/TLS database connections

## Backup and Recovery

### Database Backups
```bash
# PostgreSQL backup
pg_dump $DATABASE_URL > awa_backup_$(date +%Y%m%d).sql

# Automated backup script
./scripts/backup_database.sh
```

### Workflow State Recovery
- **Temporal History**: Complete workflow execution history
- **State Persistence**: Durable execution guarantees
- **Disaster Recovery**: Cross-region Temporal clusters
- **Point-in-Time Recovery**: Historical state reconstruction

### Configuration Backup
- **Config Files**: Version controlled configuration
- **Environment Variables**: Secure secret management
- **Infrastructure as Code**: Terraform/CloudFormation templates

## CI/CD Integration

### Dagger Pipeline
```bash
make ci                    # Run full CI pipeline
make ci-workflow-tests     # Run workflow integration tests
make ci-publish-sdk        # Publish SDK artifacts
```

### Build Pipeline Stages
1. **Code Quality**: Linting, formatting, type checking
2. **Unit Tests**: Fast test execution with coverage
3. **Integration Tests**: API and workflow testing
4. **Security Scanning**: Vulnerability assessment
5. **Image Building**: Docker image creation and pushing
6. **Deployment**: Automated deployment to staging/production

### Deployment Strategies
- **Blue-Green**: Zero-downtime deployment
- **Rolling Updates**: Gradual service updates
- **Canary Releases**: Gradual traffic shifting
- **Feature Flags**: Configuration-based feature control

## Monitoring and Observability

### Application Metrics
- **API Performance**: Request latency, throughput, error rates
- **Workflow Metrics**: Execution time, success rate, retry counts
- **LLM Metrics**: Token usage, response time, cost tracking
- **Resource Usage**: CPU, memory, disk, network utilization

### Log Management
- **Structured Logging**: JSON format with correlation IDs
- **Log Levels**: Configurable verbosity (DEBUG, INFO, WARN, ERROR)
- **Log Aggregation**: Centralized log collection and searching
- **Alert Rules**: Automated alerting on error patterns

### Distributed Tracing
- **Request Tracing**: End-to-end request tracking
- **Workflow Tracing**: Activity execution visibility
- **LLM Call Tracing**: AI operation monitoring
- **Performance Profiling**: Bottleneck identification

## Production Deployment Checklist

### Pre-Deployment
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Security configurations validated
- [ ] SSL certificates installed
- [ ] Load balancer configured
- [ ] Monitoring alerts configured

### Deployment Process
- [ ] Build and test all Docker images
- [ ] Deploy to staging environment
- [ ] Run integration test suite
- [ ] Validate service health
- [ ] Deploy to production with rolling update
- [ ] Monitor deployment metrics

### Post-Deployment
- [ ] Verify all services are healthy
- [ ] Check workflow execution
- [ ] Validate LLM integrations
- [ ] Monitor error rates and performance
- [ ] Update documentation and runbooks
