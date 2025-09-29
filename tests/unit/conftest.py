import itertools
from dataclasses import dataclass

import pytest

from tests.unit.constants import (
    CUSTOM_AUTH_MIDDLEWARE,
    CUSTOM_RATE_LIMITING_MIDDLEWARE,
    DATABASE_POSTGRES,
    DATABASE_SQLITE,
    DEFAULT_AUTH_MIDDLEWARE,
)


pytest_plugins = ["apolo_app_types_fixtures"]


# OpenWebUI Test Case Generation


@dataclass
class OpenWebUITestCase:
    """Configuration for a single OpenWebUI test case."""

    auth_enabled: bool
    middleware_name: str | None
    database_type: str

    @property
    def expected_middleware(self) -> list[str]:
        """Compute expected middleware based on configuration."""
        middleware = []
        if self.auth_enabled:
            middleware.append(DEFAULT_AUTH_MIDDLEWARE)
        if self.middleware_name:
            middleware.append(self.middleware_name)
        return middleware

    @property
    def expected_db_url(self) -> str | None:
        """Compute expected database URL for assertions."""
        if self.database_type == DATABASE_SQLITE:
            return None
        if self.database_type == DATABASE_POSTGRES:
            return "postgresql://pgvector_user:pgvector_password@pgbouncer_host:4321/db_name"
        return None

    @property
    def test_id(self) -> str:
        """Generate a descriptive test ID."""
        auth_part = "auth_enabled" if self.auth_enabled else "auth_disabled"

        if self.middleware_name:
            # Extract the descriptive part from middleware name
            if "custom-auth-middleware" in self.middleware_name:
                middleware_part = "with_auth_middleware"
            elif "rate-limiting-middleware" in self.middleware_name:
                middleware_part = "with_rate_limiting_middleware"
            else:
                middleware_part = "with_middleware"
        else:
            middleware_part = "no_middleware"

        return f"{auth_part}_{middleware_part}_{self.database_type}"


def _generate_openwebui_test_cases() -> list[OpenWebUITestCase]:
    """Generate all combinations of OpenWebUI test configurations."""
    auth_options = [True, False]
    middleware_options = [None, CUSTOM_AUTH_MIDDLEWARE, CUSTOM_RATE_LIMITING_MIDDLEWARE]
    database_options = [DATABASE_SQLITE, DATABASE_POSTGRES]

    test_cases = []

    for auth, middleware, db_type in itertools.product(
        auth_options, middleware_options, database_options
    ):
        test_cases.append(
            OpenWebUITestCase(
                auth_enabled=auth,
                middleware_name=middleware,
                database_type=db_type,
            )
        )

    return test_cases


@pytest.fixture(params=_generate_openwebui_test_cases(), ids=lambda tc: tc.test_id)
def openwebui_test_case(request):
    """Provide individual OpenWebUI test case configurations."""
    return request.param
