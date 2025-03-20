import abc
import logging
import typing as t

import apolo_sdk

from apolo_app_types import AppInputs
from apolo_app_types.app_types import AppType


logger = logging.getLogger()

AppInputT = t.TypeVar("AppInputT", bound="AppInputs")


class BaseChartValueProcessor(abc.ABC, t.Generic[AppInputT]):
    def __init__(self, client: apolo_sdk.Client):
        self.client = client

    async def gen_extra_helm_args(self, *_: t.Any) -> list[str]:
        return ["--timeout", "15m", "--dependency-update"]

    def get_app_data_storage_path(self, app_type: AppType, app_name: str) -> str:
        return f"storage://{self.client.config.cluster_name}/{self.client.config.org_name}/{self.client.config.project_name}/.apps/{app_type.value}/{app_name}"

    @abc.abstractmethod
    async def gen_extra_values(
        self,
        input_: AppInputT,
        app_name: str,
        namespace: str,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        raise NotImplementedError
