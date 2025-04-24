import logging
import typing as t

import httpx


logger = logging.getLogger(__name__)


class AppsApiClient:
    def __init__(self, api_url: str, api_token: str):
        self.api_url = api_url
        self.api_token = api_token
        self._session: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "AppsApiClient":
        if self._session is None:
            session = httpx.AsyncClient(
                base_url=self.api_url,
                headers={"Authorization": f"Bearer {self.api_token}"},
            )
            self._session = await session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._session is not None:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)
            self._session = None

    async def post_raw_outputs(self, outputs: dict[str, t.Any]) -> None:
        assert self._session is not None
        response = await self._session.post(json={"output": outputs})
        logger.info(
            "API response status code: %s, body: %s",
            response.status_code,
            response.text,
        )
