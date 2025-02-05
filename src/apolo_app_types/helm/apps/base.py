import abc
import logging
import typing as t

import apolo_sdk
from apolo_app_types import AppInputs


logger = logging.getLogger()


class BaseChartValueProcessor(abc.ABC):
    def __init__(self, client: apolo_sdk.Client):
        self.client = client

    async def gen_extra_helm_args(self, *_: t.Any) -> list[str]:
        return ["--timeout", "15m", "--dependency-update"]

    @abc.abstractmethod
    async def gen_extra_values(
        self,
        input_: AppInputs,
        app_name: str,
        namespace: str,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        raise NotImplementedError
