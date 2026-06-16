"""Authentication module for AWA API with Cognito OAuth support."""

import hmac
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Annotated

import httpx
from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.config.env_config import EnvConfig

# Initialize authentication logger
logger = get_logger(LoggerComponent.AUTH)

security = HTTPBearer(auto_error=False)

# Simple rate limiting for service token validation attempts
# In production, consider using Redis or a proper rate limiting service
_service_auth_attempts: dict[str, list[float]] = defaultdict(list)
_SERVICE_AUTH_WINDOW = 60  # 1 minute window
_SERVICE_AUTH_MAX_ATTEMPTS = 10  # 10 attempts per minute per IP


def _check_rate_limit(client_ip: str) -> bool:
    """Check if client IP is within rate limit for service auth attempts.

    Args:
        client_ip: Client IP address

    Returns:
        True if within rate limit, False if exceeded

    """
    current_time = time.time()

    # Clean old attempts outside the window
    cutoff_time = current_time - _SERVICE_AUTH_WINDOW
    _service_auth_attempts[client_ip] = [
        attempt_time for attempt_time in _service_auth_attempts[client_ip] if attempt_time > cutoff_time
    ]

    # Check if limit exceeded
    if len(_service_auth_attempts[client_ip]) >= _SERVICE_AUTH_MAX_ATTEMPTS:
        return False

    # Add current attempt
    _service_auth_attempts[client_ip].append(current_time)
    return True


class AuthenticationError(HTTPException):
    """Authentication specific exception."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class CognitoAuthenticator:
    """Handles Cognito JWT token validation with security enhancements."""

    # Cache duration for JWKS in seconds (1 hour)
    JWKS_CACHE_DURATION = 3600
    # Maximum token age in seconds (24 hours)
    MAX_TOKEN_AGE = 86400

    def __init__(self) -> None:
        self.env_config = EnvConfig.get_env_config()
        self._jwks_cache = None
        self._jwks_cache_time = 0
        self._jwks_uri = None

    @property
    def jwks_uri(self) -> str:
        """Get the JWKS URI for Cognito."""
        if not self._jwks_uri:
            issuer = self.env_config.auth_cognito_issuer
            if issuer:
                # Remove trailing slash if present
                issuer = issuer.rstrip("/")
                self._jwks_uri = f"{issuer}/.well-known/jwks.json"
        return self._jwks_uri

    async def get_jwks(self) -> dict:
        """Fetch JWKS from Cognito with caching to prevent DoS."""
        if not self.jwks_uri:
            raise AuthenticationError("Cognito issuer not configured")

        # Check cache
        current_time = time.time()
        if self._jwks_cache and (current_time - self._jwks_cache_time) < self.JWKS_CACHE_DURATION:
            return self._jwks_cache

        try:
            # Use a dedicated auth client for JWKS requests
            async with httpx.AsyncClient(
                timeout=10.0,
                # Add context for logging
                headers={"User-Agent": "AWA-Auth/1.0"},
            ) as client:
                logger.debug(f"Fetching JWKS from {self.jwks_uri}")
                response = await client.get(self.jwks_uri)
                response.raise_for_status()
                jwks = response.json()

                # Validate JWKS structure
                self._validate_jwks_format(jwks)

                # Update cache
                self._jwks_cache = jwks
                self._jwks_cache_time = current_time
                logger.debug(f"JWKS cached successfully, expires in {self.JWKS_CACHE_DURATION} seconds")

                return jwks
        except httpx.TimeoutException:
            logger.warning("JWKS fetch timeout - authentication service may be slow")
            raise AuthenticationError("Authentication service timeout") from None
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            logger.warning(f"Failed to fetch JWKS: {type(e).__name__}")
            # Don't expose internal error details
            raise AuthenticationError("Authentication service unavailable") from None
        except Exception as e:
            logger.exception(f"Unexpected error fetching JWKS: {type(e).__name__}")
            # Don't expose internal error details
            raise AuthenticationError("Authentication service unavailable") from None

    def _validate_jwks_format(self, jwks: dict) -> None:
        """Validate JWKS structure."""
        if not isinstance(jwks, dict) or "keys" not in jwks:
            raise ValueError("Invalid JWKS format")

    def _validate_token_format(self, token: str) -> None:
        """Validate basic token format."""
        if not token or not isinstance(token, str):
            raise AuthenticationError("Invalid token format")

    def _validate_token_header(self, token: str) -> dict:
        """Validate and extract token header."""
        try:
            unverified_header = jwt.get_unverified_header(token)
        except JWTError:
            raise AuthenticationError("Invalid token format") from None

        # Validate algorithm to prevent algorithm confusion attacks
        alg = unverified_header.get("alg")
        if alg != "RS256":
            logger.warning(f"Algorithm confusion attack attempt detected: {alg} (expected RS256)")
            raise AuthenticationError("Invalid token algorithm")

        kid = unverified_header.get("kid")
        if not kid:
            raise AuthenticationError("Token missing key ID")

        return unverified_header

    def _find_jwks_key(self, jwks: dict, kid: str) -> dict:
        """Find the matching key in JWKS."""
        for jwk in jwks.get("keys", []):
            if jwk.get("kid") == kid and jwk.get("use") == "sig":
                return jwk
        raise AuthenticationError("Unable to find matching key")

    def _decode_jwt_payload(self, token: str, key: dict) -> dict:
        """Decode and validate JWT payload."""
        try:
            return jwt.decode(
                token,
                key,
                algorithms=["RS256"],  # Only allow RS256
                issuer=self.env_config.auth_cognito_issuer,
                audience=self.env_config.auth_cognito_client_id,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "require_exp": True,
                    "require_iat": True,
                },
            )
        except jwt.ExpiredSignatureError:
            # Log as info rather than error since this is expected behavior
            logger.info("JWT token has expired - client should refresh")
            raise AuthenticationError("Token has expired") from None
        except jwt.InvalidAudienceError:
            raise AuthenticationError("Invalid token audience") from None
        except jwt.InvalidIssuerError:
            raise AuthenticationError("Invalid token issuer") from None
        except JWTError as e:
            logger.debug(f"JWT decode error: {type(e).__name__}")
            raise AuthenticationError("Invalid token") from None

    def _validate_token_claims(self, payload: dict) -> None:
        """Validate Cognito-specific token claims."""
        # Validate token type
        token_use = payload.get("token_use")
        if token_use not in ["access", "id"]:
            raise AuthenticationError("Invalid token type")

        # Validate required claims
        required_claims = ["sub", "exp", "iat"]
        for claim in required_claims:
            if claim not in payload:
                raise AuthenticationError(f"Missing required claim: {claim}")

        # Validate token age (prevent replay attacks with very old tokens)
        iat = payload.get("iat")
        if iat:
            token_age = datetime.now(UTC) - datetime.fromtimestamp(iat, tz=UTC)
            if token_age.total_seconds() > self.MAX_TOKEN_AGE:
                logger.debug(f"Token rejected due to age: {token_age.total_seconds()}s (max: {self.MAX_TOKEN_AGE}s)")
                raise AuthenticationError("Token too old")

    async def validate_token(self, token: str) -> dict:
        """Validate JWT token from Cognito with comprehensive security checks."""
        try:
            # Validate token format
            self._validate_token_format(token)

            # Validate and extract header
            unverified_header = self._validate_token_header(token)
            kid = unverified_header["kid"]

            # Fetch JWKS and find matching key
            jwks = await self.get_jwks()
            key = self._find_jwks_key(jwks, kid)

            # Decode and validate JWT payload
            payload = self._decode_jwt_payload(token, key)

            # Validate Cognito-specific claims
            self._validate_token_claims(payload)

            return payload

        except AuthenticationError:
            raise
        except (ValueError, KeyError) as e:
            logger.debug(f"Token validation error: {type(e).__name__}")
            raise AuthenticationError("Token validation failed") from None


# Global authenticator instance
cognito_auth = CognitoAuthenticator()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    awa_auth_token: Annotated[str | None, Cookie()] = None,
) -> dict | None:
    """Get current user from JWT token.

    Supports both Authorization header (Bearer token) and httpOnly cookie.
    Returns None if auth_mode is 'anonymous', otherwise validates the token.
    """
    env_config = EnvConfig.get_env_config()

    # Check if authentication is disabled
    if env_config.public_auth_mode.lower() == "none":
        return None

    # Extract token from either Authorization header or cookie
    token = None

    # Priority 1: Authorization header (for API clients)
    if credentials:
        token = credentials.credentials
        logger.debug("Using token from Authorization header")
    # Priority 2: httpOnly cookie (for web UI)
    elif awa_auth_token:
        token = awa_auth_token
        logger.debug("Using token from cookie")

    # No token found
    if not token:
        raise AuthenticationError("Authentication required")

    # Validate token based on auth mode
    if env_config.public_auth_mode.lower() == "cognito":
        return await cognito_auth.validate_token(token)

    # Unknown auth mode
    raise AuthenticationError(f"Unknown auth mode: {env_config.public_auth_mode}")


async def require_authenticated_user(
    current_user: Annotated[dict | None, Depends(get_current_user)],
) -> dict:
    """Require an authenticated user.

    This is the primary authentication dependency for all protected endpoints.
    When AUTH_MODE is 'cognito', validates JWT tokens and returns user claims.
    When AUTH_MODE is 'none', returns empty dict to indicate anonymous access.
    """
    # If we have a valid user, always return it
    if current_user is not None:
        return current_user

    # If no user, check auth mode to determine behavior
    env_config = EnvConfig.get_env_config()

    # In anonymous mode, return empty dict for anonymous access
    if env_config.public_auth_mode.lower() == "none":
        return {}

    # In authenticated modes, require a valid user
    raise AuthenticationError("Authentication required")


async def require_service_authentication(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    request: Request,
) -> dict:
    """Require service token authentication for service-to-service endpoints.

    Returns:
        Service information dict for authenticated services

    Raises:
        AuthenticationError: If service token is invalid or missing

    """
    env_config = EnvConfig.get_env_config()

    # Check if authentication is disabled
    if env_config.public_auth_mode.lower() == "none":
        return {"type": "service", "service_name": "anonymous"}

    # Get client IP for rate limiting
    client_ip = request.client.host if request.client else "unknown"

    # Check rate limiting
    if not _check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for service authentication from IP: {client_ip}")
        raise AuthenticationError("Too many authentication attempts. Please try again later.")

    # Extract token from Authorization header only (services use Bearer tokens)
    if not credentials:
        raise AuthenticationError("Service token required in Authorization header")

    token = credentials.credentials
    logger.debug("Validating service token from Authorization header")

    # Validate service token
    if validate_service_token(token):
        logger.debug("Valid service token authenticated")
        return {"type": "service", "service_name": "worker"}

    raise AuthenticationError("Invalid service token")


def validate_service_token(token: str | None) -> bool:
    """Validate service-to-service authentication token.

    Args:
        token: Service token to validate

    Returns:
        True if token is valid or auth is disabled, False otherwise

    """
    env_config = EnvConfig.get_env_config()

    # In anonymous mode, allow all connections
    if env_config.public_auth_mode.lower() == "none":
        return True

    # Check if service token is configured
    configured_token = env_config.awa_service_token
    if not configured_token:
        logger.warning("Service token not configured but auth is enabled")
        return False

    # Validate the token
    if not token:
        logger.debug("No service token provided")
        return False

    # Use constant-time comparison to prevent timing attacks
    is_valid = hmac.compare_digest(token, configured_token)
    if not is_valid:
        logger.warning("Invalid service token provided")

    return is_valid
