# Authentication Configuration

How to configure and use AWA's authentication system.

## Overview

AWA supports three authentication modes:

1. **User Authentication** (JWT/OAuth) - UI access and user API calls
2. **Service Authentication** (Bearer tokens) - Worker-to-API communication
3. **Anonymous Mode** - Development and testing

## Authentication Modes

### Anonymous Mode (Default)

All API endpoints accessible without authentication. For development and testing.

```bash
PUBLIC_AUTH_MODE=none
```

- **UI Access**: No authentication required
- **API Endpoints**: All endpoints accessible without tokens
- **Worker Registration**: No authentication needed
- **SocketIO Connections**: Open access (CORS wildcard allowed)

### Cognito OAuth Mode

AWS Cognito for user authentication with service token support.

```bash
PUBLIC_AUTH_MODE=cognito
AUTH_COGNITO_CLIENT_ID=your-client-id
AUTH_COGNITO_CLIENT_SECRET=your-client-secret
AUTH_COGNITO_ISSUER=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_YourPoolId
AWA_SERVICE_TOKEN=your-secure-service-token
```

- **UI Access**: Cognito OAuth with JWT tokens
- **API Endpoints**: JWT tokens for user requests, service tokens for worker communication
- **Worker Registration**: Service token authentication required
- **SocketIO Connections**: Restricted CORS origins, service token authentication required

## Service Token Authentication

### Overview

Service-to-service authentication for:

- **Worker Registration**: Cookbook workers to core AWA API
- **SocketIO Connections**: Real-time log streaming
- **Internal API Calls**: AWA service communication

### Configuration

Set the service token in your environment:

```bash
# Generate a secure token (recommended: 32+ random characters)
AWA_SERVICE_TOKEN=$(openssl rand -base64 32)

# Or set manually
AWA_SERVICE_TOKEN=your-secure-service-token-here
```

## Setting Up Authentication

### 1. Cognito User Pool Setup

Configure AWS Cognito User Pool:

```bash
# Required Cognito configuration
AUTH_COGNITO_CLIENT_ID=your-cognito-client-id
AUTH_COGNITO_CLIENT_SECRET=your-cognito-client-secret
AUTH_COGNITO_ISSUER=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_YourPoolId

# Enable Cognito authentication
PUBLIC_AUTH_MODE=cognito
```

**Cognito User Pool Requirements:**

- **App Client**: Create an app client with client ID and secret
- **OAuth 2.0 Scopes**: Configure scopes (`openid`, `profile`, `email`)
- **Callback URLs**: Add your AWA UI URL to allowed callback URLs
- **Hosted UI**: Enable the Cognito Hosted UI for user authentication

### 2. Service Token Setup

Generate a secure service token:

```bash
# Generate a cryptographically secure token
AWA_SERVICE_TOKEN=$(openssl rand -base64 32)

# Add to your .env file
echo "AWA_SERVICE_TOKEN=$AWA_SERVICE_TOKEN" >> .env
```

### 3. CORS Configuration (Optional)

For production deployments, configure allowed origins:

```bash
# Comma-separated list of allowed origins
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

## SocketIO Authentication

Real-time log streaming requires service token authentication when auth is enabled:

```python
# SocketIO connection with service token
const socket = io('http://localhost:8001', {
  auth: {
    token: 'your-service-token'
  }
});
```

**CORS:**

- **Anonymous Mode**: Wildcard (`*`) for development
- **Auth Modes**: Specific origins including API server URLs

## Obtaining JWT Tokens for Testing

### Browser Console Method

1. **Start AWA** with Cognito authentication and **log in**:

   ```bash
   open http://localhost:8000
   ```

2. **Get your access token**:

   - Open browser Developer Tools (F12)
   - Go to the **Console** tab
   - Paste this command and press Enter:

   ```javascript
   fetch("/api/auth/session")
     .then((response) => response.json())
     .then((session) => {
       if (session?.accessToken) {
         console.log("📋 Copy this token for API calls:");
         console.log(session.accessToken);
       } else {
         console.log("❌ No access token found. Make sure you are logged in.");
       }
     });
   ```

3. **Copy the token** - it will be a long string starting with `eyJ...`

### FastAPI Swagger UI

Swagger UI at `http://localhost:8001/docs` includes authentication:

1. **Access Swagger UI**: `http://localhost:8001/docs`
2. **Authenticate**: Click "Authorize" button, enter JWT token
3. **Test endpoints**: All subsequent calls will include authorization

## Testing Authentication

```bash
# Test health endpoint (always public)
curl http://localhost:8001/api/v1/health

# Test protected endpoint without auth (should fail in Cognito mode)
curl http://localhost:8001/api/v1/workflows/list

# Test with service token
curl -H "Authorization: Bearer $AWA_SERVICE_TOKEN" \
  http://localhost:8001/api/v1/workers/register \
  -d '{"worker_name":"test",...}' \
  -H "Content-Type: application/json"

# Test with JWT token
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8001/api/v1/workflows/list
```

## Troubleshooting

### Common Issues

**Worker Registration Fails (500 Error)**

- Check that `AWA_SERVICE_TOKEN` is set in both core AWA and worker environments
- Verify token matches exactly (no extra whitespace/newlines)
- Check logs for rate limiting or authentication errors

**SocketIO Connection Rejected (403)**

- Ensure `AWA_SERVICE_TOKEN` is configured
- Check CORS origins include the API server URL (`localhost:8001`)
- Verify service token is included in SocketIO auth object

**JWT Authentication Failures**

- Verify Cognito configuration matches your User Pool
- Check token expiration (tokens typically expire after 1 hour)
- Ensure client ID and issuer URL are correct

### Debug Mode

Enable debug logging for authentication troubleshooting:

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Check authentication logs
tail -f logs/api.log | grep -E "(AUTH|Token|Authentication)"
```

## Production Deployment

### Secrets Management

For production deployments, use cloud-native secrets management instead of environment variables for the AWA_SERVICE_TOKEN. Examples are provided below.

**AWS Secrets Manager:**

```bash
# Store service token
aws secretsmanager create-secret \
  --name "awa/service-token" \
  --secret-string "$(openssl rand -base64 32)"

# Retrieve in application
AWA_SERVICE_TOKEN=$(aws secretsmanager get-secret-value \
  --secret-id awa/service-token \
  --query SecretString --output text)
```

**Azure Key Vault:**

```bash
# Store service token
az keyvault secret set \
  --vault-name your-keyvault \
  --name awa-service-token \
  --value "$(openssl rand -base64 32)"

# Reference in container
AWA_SERVICE_TOKEN=$(az keyvault secret show \
  --vault-name your-keyvault \
  --name awa-service-token \
  --query value -o tsv)
```

**Google Secret Manager:**

```bash
# Store service token
echo -n "$(openssl rand -base64 32)" | gcloud secrets create awa-service-token --data-file=-

# Retrieve in application
AWA_SERVICE_TOKEN=$(gcloud secrets versions access latest --secret=awa-service-token)
```
