# Authentication Development

Development aspects of AWA's authentication system: adding endpoints, enforcement patterns, and architecture.

## Authentication Enforcement

### Automated Testing

The system includes automated tests that scan all endpoints:

```bash
# Run authentication enforcement tests
uv run pytest tests/unit/awa/core/api/test_authentication_enforcement.py -v
```

### Exempt Endpoints

These endpoints are exempt from authentication requirements:

- `/api/v1/health` - Health checks for monitoring
- `/openapi.json` - OpenAPI specification
- `/docs*` - API documentation
- `/redoc` - ReDoc documentation

### Adding New Endpoints

When adding new endpoints, you must either:

1. **Add authentication dependency** using `require_authenticated_user` for user endpoints
2. **Use service authentication** with `require_service_authentication` for service endpoints
3. **Add to exempt list** in tests if truly public

```python
# Standard protected endpoint
async def my_endpoint(
    current_user: Annotated[dict, Depends(require_authenticated_user)],
) -> dict:
    return {"user": current_user.get("sub", "anonymous")}

# Service-only authentication endpoint
async def service_endpoint(
    service_auth: Annotated[dict, Depends(require_service_authentication)],
) -> dict:
    return {"auth_type": service_auth["type"]}
```

## API Authentication Patterns

### Worker Registration Endpoint

The `/api/v1/workers/register` endpoint uses service token authentication only:

```python
# Service-only authentication
async def register_worker(
    registration: WorkerRegistration,
    service_auth: Annotated[dict, Depends(require_service_authentication)],
) -> WorkerRegistrationResponse:
    # Requires service token authentication for worker-to-API communication
```

### Other API Endpoints

Most API endpoints use user authentication only:

```python
async def list_workflows(
    current_user: Annotated[dict, Depends(require_authenticated_user)],
) -> WorkflowListResponse:
    # Requires JWT token in Cognito mode
```
