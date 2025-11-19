"""Tests for authentication parameter validation."""

from unittest.mock import AsyncMock, MagicMock, patch

import click
import pytest

from apolo_app_types.utils.auth_validator import validate_auth_params


class TestValidateAuthParams:
    """Tests for the validate_auth_params function."""

    @pytest.mark.asyncio
    async def test_raises_when_token_provided_without_url(self):
        """Test that providing token without URL raises an error."""
        with pytest.raises(click.BadParameter) as exc_info:
            await validate_auth_params(
                apolo_api_token="test-token",
                apolo_api_url=None,
                apolo_passed_config=None,
            )

        assert "apolo-api-token" in str(exc_info.value).lower()
        assert "apolo-api-url" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_succeeds_when_token_and_url_provided(self):
        """Test that providing both token and URL succeeds."""
        # Should not raise
        await validate_auth_params(
            apolo_api_token="test-token",
            apolo_api_url="https://api.example.com",
            apolo_passed_config=None,
        )

    @pytest.mark.asyncio
    async def test_succeeds_when_passed_config_provided(self):
        """Test that providing passed_config succeeds."""
        # Should not raise
        await validate_auth_params(
            apolo_api_token=None,
            apolo_api_url=None,
            apolo_passed_config="config-string",
        )

    @pytest.mark.asyncio
    async def test_sets_environment_variable_for_passed_config(self, monkeypatch):
        """Test that passed_config is set in environment if not already present."""
        monkeypatch.delenv("APOLO_PASSED_CONFIG", raising=False)

        await validate_auth_params(
            apolo_api_token=None,
            apolo_api_url=None,
            apolo_passed_config="config-string",
        )

        import os

        assert os.getenv("APOLO_PASSED_CONFIG") == "config-string"

    @pytest.mark.asyncio
    async def test_does_not_override_existing_environment_variable(self, monkeypatch):
        """Test that existing APOLO_PASSED_CONFIG is not overridden."""
        monkeypatch.setenv("APOLO_PASSED_CONFIG", "existing-config")

        await validate_auth_params(
            apolo_api_token=None,
            apolo_api_url=None,
            apolo_passed_config="new-config",
        )

        import os

        assert os.getenv("APOLO_PASSED_CONFIG") == "existing-config"

    @pytest.mark.asyncio
    async def test_attempts_default_client_when_no_auth_provided(self):
        """Test that default client is attempted when no auth params provided."""
        mock_client = MagicMock()
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_client
        mock_context_manager.__aexit__.return_value = None

        with patch("apolo_app_types.utils.auth_validator.apolo_sdk.get") as mock_get:
            mock_get.return_value = mock_context_manager

            # Should not raise when default client works
            await validate_auth_params(
                apolo_api_token=None,
                apolo_api_url=None,
                apolo_passed_config=None,
            )

            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_when_no_auth_and_default_client_fails(self):
        """Test that error is raised when no auth provided and default client fails."""
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.side_effect = Exception("Connection failed")

        with patch("apolo_app_types.utils.auth_validator.apolo_sdk.get") as mock_get:
            mock_get.return_value = mock_context_manager

            with pytest.raises(click.BadParameter) as exc_info:
                await validate_auth_params(
                    apolo_api_token=None,
                    apolo_api_url=None,
                    apolo_passed_config=None,
                )

            error_msg = str(exc_info.value).lower()
            assert "apolo-api-token" in error_msg or "apolo-passed-config" in error_msg
            assert "connection failed" in error_msg

    @pytest.mark.asyncio
    async def test_prefers_explicit_auth_over_default_client(self):
        """Test that explicit token or config skips default client check."""
        with patch("apolo_app_types.utils.auth_validator.apolo_sdk.get") as mock_get:
            # Should not call apolo_sdk.get when token+URL provided
            await validate_auth_params(
                apolo_api_token="test-token",
                apolo_api_url="https://api.example.com",
                apolo_passed_config=None,
            )
            mock_get.assert_not_called()

            # Should not call apolo_sdk.get when passed_config provided
            await validate_auth_params(
                apolo_api_token=None,
                apolo_api_url=None,
                apolo_passed_config="config-string",
            )
            mock_get.assert_not_called()
