"""Tests for API authentication module."""

import time
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from jose import jwt

from awa.core.api.auth import (
    AuthenticationError,
    CognitoAuthenticator,
    get_current_user,
    require_authenticated_user,
)


class TestCognitoAuthenticator:
    """Test Cognito authenticator functionality."""

    @pytest.fixture
    def mock_env_config(self) -> Mock:
        """Mock environment configuration."""
        config = Mock()
        config.auth_cognito_issuer = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TestPool"
        config.auth_cognito_client_id = "test-client-id"
        return config

    @pytest.fixture
    def authenticator(self, mock_env_config: Mock) -> CognitoAuthenticator:
        """Create authenticator with mocked config."""
        with patch("awa.core.api.auth.EnvConfig.get_env_config", return_value=mock_env_config):
            return CognitoAuthenticator()

    def test_jwks_uri_construction(self, authenticator: CognitoAuthenticator) -> None:
        """Test JWKS URI is constructed correctly."""
        expected_uri = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TestPool/.well-known/jwks.json"
        assert authenticator.jwks_uri == expected_uri

    def test_jwks_uri_removes_trailing_slash(self, mock_env_config: Mock) -> None:
        """Test JWKS URI construction removes trailing slash."""
        mock_env_config.auth_cognito_issuer = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TestPool/"
        with patch("awa.core.api.auth.EnvConfig.get_env_config", return_value=mock_env_config):
            authenticator = CognitoAuthenticator()
            expected_uri = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TestPool/.well-known/jwks.json"
            assert authenticator.jwks_uri == expected_uri

    @pytest.mark.asyncio
    async def test_get_jwks_success(self, authenticator: CognitoAuthenticator) -> None:
        """Test successful JWKS fetch."""
        mock_jwks = {
            "keys": [
                {
                    "kty": "RSA",
                    "kid": "test-key-1",
                    "use": "sig",
                    "n": "test-n-value",
                    "e": "AQAB",
                },
            ],
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            jwks = await authenticator.get_jwks()
            assert jwks == mock_jwks
            mock_get.assert_called_once_with(authenticator.jwks_uri)

    @pytest.mark.asyncio
    async def test_get_jwks_failure(self, authenticator: CognitoAuthenticator) -> None:
        """Test JWKS fetch failure."""
        with (
            patch("httpx.AsyncClient.get", side_effect=Exception("Network error")),
            pytest.raises(
                AuthenticationError,
                match="Authentication service unavailable",
            ),
        ):
            await authenticator.get_jwks()

    @pytest.mark.asyncio
    async def test_validate_token_missing_kid(self, authenticator: CognitoAuthenticator) -> None:
        """Test token validation with missing key ID."""
        # Mock a token header without kid but with RS256 algorithm
        with (
            patch("awa.core.api.auth.jwt.get_unverified_header", return_value={"alg": "RS256"}),
            pytest.raises(
                AuthenticationError,
                match="Token missing key ID",
            ),
        ):
            await authenticator.validate_token("fake-token")

    @pytest.mark.asyncio
    async def test_validate_token_expired(self, authenticator: CognitoAuthenticator) -> None:
        """Test validation of expired token."""
        # Mock an expired token scenario

        # Create a mock RSA key
        mock_key = {"kty": "RSA", "kid": "test-key-1", "use": "sig", "n": "test", "e": "AQAB"}

        # Mock the token to have the proper header with RS256 algorithm
        with (
            patch("awa.core.api.auth.jwt.get_unverified_header", return_value={"kid": "test-key-1", "alg": "RS256"}),
            patch.object(authenticator, "get_jwks", return_value={"keys": [mock_key]}),
            patch("awa.core.api.auth.jwt.decode", side_effect=jwt.ExpiredSignatureError("Token has expired")),
            pytest.raises(AuthenticationError, match="Token has expired"),
        ):
            await authenticator.validate_token("fake-token")


class TestAuthenticationDependencies:
    """Test authentication dependency functions."""

    @pytest.fixture
    def mock_env_config_anonymous(self) -> Mock:
        """Mock environment config with anonymous mode."""
        config = Mock()
        config.public_auth_mode = "none"
        return config

    @pytest.fixture
    def mock_env_config_cognito(self) -> Mock:
        """Mock environment config with Cognito mode."""
        config = Mock()
        config.public_auth_mode = "cognito"
        return config

    @pytest.fixture
    def mock_credentials(self) -> Mock:
        """Mock HTTP bearer credentials."""
        creds = Mock()
        creds.credentials = "test-jwt-token"
        return creds

    @pytest.mark.asyncio
    async def test_get_current_user_anonymous_mode(self, mock_env_config_anonymous: Mock) -> None:
        """Test get_current_user in anonymous mode."""
        with patch("awa.core.api.auth.EnvConfig.get_env_config", return_value=mock_env_config_anonymous):
            result = await get_current_user(None)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_cognito_no_credentials(self, mock_env_config_cognito: Mock) -> None:
        """Test get_current_user in Cognito mode without credentials."""
        with (
            patch("awa.core.api.auth.EnvConfig.get_env_config", return_value=mock_env_config_cognito),
            pytest.raises(
                AuthenticationError,
                match="Authentication required",
            ),
        ):
            await get_current_user(None)

    @pytest.mark.asyncio
    async def test_get_current_user_cognito_with_credentials(
        self,
        mock_env_config_cognito: Mock,
        mock_credentials: Mock,
    ) -> None:
        """Test get_current_user in Cognito mode with valid credentials."""
        expected_user = {"sub": "user123", "email": "user@example.com"}

        with (
            patch("awa.core.api.auth.EnvConfig.get_env_config", return_value=mock_env_config_cognito),
            patch("awa.core.api.auth.cognito_auth.validate_token", return_value=expected_user),
        ):
            result = await get_current_user(mock_credentials)
            assert result == expected_user

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("unknown_mode", "expected_error"),
        [
            ("unknown", "Unknown auth mode: unknown"),
            ("invalid", "Unknown auth mode: invalid"),
            ("ldap", "Unknown auth mode: ldap"),
            ("oauth", "Unknown auth mode: oauth"),
        ],
    )
    async def test_get_current_user_unknown_mode(
        self,
        mock_credentials: Mock,
        unknown_mode: str,
        expected_error: str,
    ) -> None:
        """Test get_current_user with unknown auth mode."""
        config = Mock()
        config.public_auth_mode = unknown_mode

        with (
            patch("awa.core.api.auth.EnvConfig.get_env_config", return_value=config),
            pytest.raises(AuthenticationError, match=expected_error),
        ):
            await get_current_user(mock_credentials)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("user_data", "expected"),
        [
            ({"sub": "user123", "email": "user@example.com"}, {"sub": "user123", "email": "user@example.com"}),
            ({"sub": "user456", "username": "testuser"}, {"sub": "user456", "username": "testuser"}),
        ],
    )
    async def test_require_authenticated_user_with_user(self, user_data: dict, expected: dict) -> None:
        """Test require_authenticated_user with authenticated user."""
        result = await require_authenticated_user(user_data)
        assert result == expected

    @pytest.mark.asyncio
    async def test_require_authenticated_user_without_user(self) -> None:
        """Test require_authenticated_user without authenticated user in cognito mode."""
        # Mock environment config to simulate cognito mode
        mock_config = Mock()
        mock_config.public_auth_mode = "cognito"

        with (
            patch("awa.core.api.auth.EnvConfig.get_env_config", return_value=mock_config),
            pytest.raises(AuthenticationError, match="Authentication required"),
        ):
            await require_authenticated_user(None)

    @pytest.mark.asyncio
    async def test_require_authenticated_user_without_user_anonymous_mode(self) -> None:
        """Test require_authenticated_user without authenticated user in anonymous mode."""
        # Mock environment config to simulate anonymous mode
        mock_config = Mock()
        mock_config.public_auth_mode = "none"

        with patch("awa.core.api.auth.EnvConfig.get_env_config", return_value=mock_config):
            result = await require_authenticated_user(None)
            assert result == {}


class TestCognitoAuthenticatorSecurity(TestCognitoAuthenticator):
    """Additional security-focused tests for CognitoAuthenticator."""

    @pytest.mark.asyncio
    async def test_jwks_caching(self, authenticator: CognitoAuthenticator) -> None:
        """Test JWKS caching to prevent DoS."""
        mock_jwks = {
            "keys": [
                {
                    "kty": "RSA",
                    "kid": "test-key-1",
                    "use": "sig",
                    "n": "test-n-value",
                    "e": "AQAB",
                },
            ],
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            # First call should fetch from network
            jwks1 = await authenticator.get_jwks()
            assert mock_get.call_count == 1

            # Second call should use cache
            jwks2 = await authenticator.get_jwks()
            assert mock_get.call_count == 1  # Should not increase
            assert jwks1 == jwks2

    @pytest.mark.asyncio
    async def test_jwks_cache_expiry(self, authenticator: CognitoAuthenticator) -> None:
        """Test JWKS cache expiration."""
        mock_jwks = {"keys": [{"kid": "test-key"}]}

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            # First call
            await authenticator.get_jwks()

            # Simulate cache expiry
            authenticator._jwks_cache_time = time.time() - authenticator.JWKS_CACHE_DURATION - 1

            # Should fetch again
            await authenticator.get_jwks()
            assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_validate_token_algorithm_confusion_attack(self, authenticator: CognitoAuthenticator) -> None:
        """Test protection against algorithm confusion attacks."""
        # Create a token with HS256 algorithm (symmetric) instead of RS256
        malicious_token = jwt.encode(
            {"sub": "user123", "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp())},
            "secret",
            algorithm="HS256",
        )

        with pytest.raises(AuthenticationError, match="Invalid token algorithm"):
            await authenticator.validate_token(malicious_token)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "malformed_token",
        [
            "not.a.token",
            "invalid-jwt-format",
            "",
            None,
            123,  # Not a string
            "eyJhbGciOiJIUzI1NiJ9",  # Incomplete JWT
        ],
    )
    async def test_validate_token_malformed(
        self,
        authenticator: CognitoAuthenticator,
        malformed_token: str | None | int,
    ) -> None:
        """Test validation of malformed tokens."""
        with pytest.raises(AuthenticationError, match="Invalid token"):
            await authenticator.validate_token(malformed_token)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("missing_claim", "expected_error"),
        [
            ("sub", "Missing required claim: sub"),
            ("exp", "Missing required claim: exp"),
            ("iat", "Missing required claim: iat"),
        ],
    )
    async def test_validate_token_missing_claims(
        self,
        authenticator: CognitoAuthenticator,
        mock_env_config: Mock,
        missing_claim: str,
        expected_error: str,
    ) -> None:
        """Test validation fails for tokens missing required claims."""
        # Create base payload with all claims
        base_payload = {
            "sub": "user123",
            "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now(UTC).timestamp()),
            "iss": mock_env_config.auth_cognito_issuer,
            "aud": mock_env_config.auth_cognito_client_id,
            "token_use": "access",
        }

        # Remove the specific claim we're testing
        payload = base_payload.copy()
        del payload[missing_claim]

        mock_key = {"kty": "RSA", "kid": "test-key-1", "use": "sig", "n": "test", "e": "AQAB"}

        with (
            patch("awa.core.api.auth.jwt.get_unverified_header", return_value={"kid": "test-key-1", "alg": "RS256"}),
            patch.object(authenticator, "get_jwks", return_value={"keys": [mock_key]}),
            patch("awa.core.api.auth.jwt.decode", return_value=payload),
            pytest.raises(AuthenticationError, match=expected_error),
        ):
            await authenticator.validate_token("fake-token")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("invalid_token_use", "expected_error"),
        [
            ("refresh", "Invalid token type"),
            ("unknown", "Invalid token type"),
            (None, "Invalid token type"),
            ("", "Invalid token type"),
        ],
    )
    async def test_validate_token_invalid_token_use(
        self,
        authenticator: CognitoAuthenticator,
        mock_env_config: Mock,
        invalid_token_use: str,
        expected_error: str,
    ) -> None:
        """Test validation fails for invalid token_use."""
        payload = {
            "sub": "user123",
            "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now(UTC).timestamp()),
            "iss": mock_env_config.auth_cognito_issuer,
            "aud": mock_env_config.auth_cognito_client_id,
            "token_use": invalid_token_use,
        }

        mock_key = {"kty": "RSA", "kid": "test-key-1", "use": "sig", "n": "test", "e": "AQAB"}

        with (
            patch("awa.core.api.auth.jwt.get_unverified_header", return_value={"kid": "test-key-1", "alg": "RS256"}),
            patch.object(authenticator, "get_jwks", return_value={"keys": [mock_key]}),
            patch("awa.core.api.auth.jwt.decode", return_value=payload),
            pytest.raises(AuthenticationError, match=expected_error),
        ):
            await authenticator.validate_token("fake-token")

    @pytest.mark.asyncio
    async def test_validate_token_too_old(self, authenticator: CognitoAuthenticator, mock_env_config: Mock) -> None:
        """Test validation fails for tokens that are too old."""
        # Token issued 2 days ago
        old_iat = datetime.now(UTC) - timedelta(days=2)
        payload = {
            "sub": "user123",
            "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
            "iat": int(old_iat.timestamp()),
            "iss": mock_env_config.auth_cognito_issuer,
            "aud": mock_env_config.auth_cognito_client_id,
            "token_use": "access",
        }

        mock_key = {"kty": "RSA", "kid": "test-key-1", "use": "sig", "n": "test", "e": "AQAB"}

        with (
            patch("awa.core.api.auth.jwt.get_unverified_header", return_value={"kid": "test-key-1", "alg": "RS256"}),
            patch.object(authenticator, "get_jwks", return_value={"keys": [mock_key]}),
            patch("awa.core.api.auth.jwt.decode", return_value=payload),
            pytest.raises(AuthenticationError, match="Token too old"),
        ):
            await authenticator.validate_token("fake-token")

    @pytest.mark.asyncio
    async def test_jwks_timeout_handling(self, authenticator: CognitoAuthenticator) -> None:
        """Test proper handling of JWKS fetch timeout."""
        import httpx

        with (
            patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Timeout")),
            pytest.raises(
                AuthenticationError,
                match="Authentication service timeout",
            ),
        ):
            await authenticator.get_jwks()

    @pytest.mark.asyncio
    async def test_jwks_invalid_format(self, authenticator: CognitoAuthenticator) -> None:
        """Test handling of invalid JWKS format."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"invalid": "format"}  # Missing 'keys'
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            with pytest.raises(AuthenticationError, match="Authentication service unavailable"):
                await authenticator.get_jwks()
