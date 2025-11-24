from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel
from tenacity import RetryError

from apolo_app_types.outputs.utils.cleanup import (
    cleanup_secrets,
    delete_secret_with_retry,
    get_app_outputs,
)
from apolo_app_types.protocols.common import ApoloSecret, AppOutputs


# Test fixtures with generic AppOutputs


class NestedCredentials(BaseModel):
    """Nested model containing secrets."""

    username: str
    password: ApoloSecret
    api_key: ApoloSecret | None = None


class MockAppOutputs(AppOutputs):
    """Generic mock AppOutputs class with various secret configurations."""

    primary_secret: ApoloSecret | None = None
    credentials: NestedCredentials | None = None
    secondary_credentials: list[NestedCredentials] | None = None


@pytest.fixture
def complete_app_outputs():
    """
    Complete AppOutputs structure with all fields populated.
    Contains 4 secrets total across different nesting levels.
    """
    return MockAppOutputs(
        primary_secret=ApoloSecret(key="primary-secret-key"),
        credentials=NestedCredentials(
            username="admin",
            password=ApoloSecret(key="admin-password"),
            api_key=ApoloSecret(key="admin-api-key"),
        ),
        secondary_credentials=[
            NestedCredentials(
                username="user1",
                password=ApoloSecret(key="user1-password"),
            ),
        ],
    )


@pytest.fixture
def mock_apolo_client():
    """Mock apolo_sdk.Client for testing."""
    mock_client = MagicMock()
    mock_client.secrets.rm = AsyncMock()
    mock_client.apps.get_output = AsyncMock()
    return mock_client


class TestCleanupSecrets:
    """Tests for the cleanup_secrets function."""

    @pytest.mark.asyncio
    async def test_deletes_all_secrets_from_outputs(
        self, complete_app_outputs, mock_apolo_client
    ):
        """
        Test that cleanup_secrets finds and deletes all secrets in outputs.
        This tests REAL BEHAVIOR: that secrets are actually deleted.
        """
        mock_apolo_client.apps.get_output.return_value = (
            complete_app_outputs.model_dump()
        )

        await cleanup_secrets(
            app_id="test-app-123",
            output_class=MockAppOutputs,
            client=mock_apolo_client,
        )

        # Verify behavior: all 4 secrets should be deleted
        assert mock_apolo_client.secrets.rm.call_count == 4

        # Verify the correct secrets were targeted
        deleted_keys = {
            call.kwargs["key"] for call in mock_apolo_client.secrets.rm.call_args_list
        }
        assert deleted_keys == {
            "primary-secret-key",
            "admin-password",
            "admin-api-key",
            "user1-password",
        }

    @pytest.mark.asyncio
    async def test_handles_empty_outputs(self, mock_apolo_client):
        """Test cleanup_secrets when outputs contain no secrets."""
        empty_outputs = MockAppOutputs()

        mock_apolo_client.apps.get_output.return_value = empty_outputs.model_dump()

        await cleanup_secrets(
            app_id="test-app-123",
            output_class=MockAppOutputs,
            client=mock_apolo_client,
        )

        # Should complete successfully without attempting deletions
        assert mock_apolo_client.secrets.rm.call_count == 0

    @pytest.mark.asyncio
    async def test_continues_on_deletion_errors(
        self, complete_app_outputs, mock_apolo_client, caplog
    ):
        """
        Test that cleanup_secrets continues processing when individual
        secret deletions fail.
        """
        mock_apolo_client.apps.get_output.return_value = (
            complete_app_outputs.model_dump()
        )

        # Make first deletion fail, rest succeed
        call_count = 0

        async def mock_rm_with_failure(key):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                msg = "Temporary API error"
                raise Exception(msg)

        mock_apolo_client.secrets.rm.side_effect = mock_rm_with_failure

        await cleanup_secrets(
            app_id="test-app-123",
            output_class=MockAppOutputs,
            client=mock_apolo_client,
        )

        # Should attempt all deletions despite errors
        # First secret fails once then succeeds on retry (2 calls),
        # plus 3 other secrets = 5 total
        assert mock_apolo_client.secrets.rm.call_count == 5

    @pytest.mark.asyncio
    async def test_handles_null_output_from_api(self, mock_apolo_client):
        """Test cleanup_secrets when get_output returns None."""
        mock_apolo_client.apps.get_output.return_value = None

        await cleanup_secrets(
            app_id="test-app-123",
            output_class=MockAppOutputs,
            client=mock_apolo_client,
        )

        assert mock_apolo_client.secrets.rm.call_count == 0


class TestDeleteSecretWithRetry:
    """Tests for the delete_secret_with_retry function."""

    @pytest.mark.asyncio
    async def test_deletes_secret_successfully(self, mock_apolo_client):
        """Test successful secret deletion on first attempt."""
        await delete_secret_with_retry("test-secret-key", mock_apolo_client)

        mock_apolo_client.secrets.rm.assert_called_once_with(key="test-secret-key")

    @pytest.mark.asyncio
    async def test_retries_on_failure(self, mock_apolo_client):
        """Test that function retries with exponential backoff on failure."""
        # Fail twice, then succeed
        mock_apolo_client.secrets.rm.side_effect = [
            Exception("Temporary failure"),
            Exception("Temporary failure"),
            None,  # Success
        ]

        await delete_secret_with_retry("test-secret-key", mock_apolo_client)

        # Should have retried 3 times total
        assert mock_apolo_client.secrets.rm.call_count == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self, mock_apolo_client):
        """Test that function raises exception after maximum retry attempts."""
        # Fail all 5 attempts
        mock_apolo_client.secrets.rm.side_effect = Exception("Persistent failure")

        with pytest.raises(RetryError):
            await delete_secret_with_retry("test-secret-key", mock_apolo_client)

        # Should have attempted 5 times
        assert mock_apolo_client.secrets.rm.call_count == 5


class TestGetAppOutputs:
    """Tests for the get_app_outputs function."""

    @pytest.mark.asyncio
    async def test_returns_app_outputs_when_available(
        self, complete_app_outputs, mock_apolo_client
    ):
        """Test get_app_outputs returns valid AppOutputs."""
        mock_apolo_client.apps.get_output.return_value = (
            complete_app_outputs.model_dump()
        )

        result = await get_app_outputs(
            app_id="test-app-123",
            output_class=MockAppOutputs,
            client=mock_apolo_client,
        )

        assert isinstance(result, MockAppOutputs)
        assert result.primary_secret is not None
        assert result.credentials is not None
        mock_apolo_client.apps.get_output.assert_called_once_with(app_id="test-app-123")

    @pytest.mark.asyncio
    async def test_returns_none_when_no_output(self, mock_apolo_client):
        """Test get_app_outputs returns None when API returns no output."""
        mock_apolo_client.apps.get_output.return_value = None

        result = await get_app_outputs(
            app_id="test-app-123",
            output_class=MockAppOutputs,
            client=mock_apolo_client,
        )

        assert result is None
