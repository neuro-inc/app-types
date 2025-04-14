import abc
import logging
import typing as t

from apolo_app_types import AppOutputs


logger = logging.getLogger(__name__)

AppOutputsT = t.TypeVar("AppOutputsT", bound=AppOutputs)


class BaseAppOutputsProcessor(abc.ABC, t.Generic[AppOutputsT]):
    async def generate_outputs(
        self,
        helm_values: dict[str, t.Any],
    ) -> dict[str, t.Any]:
        logger.info("Generating outputs for %s", helm_values)
        return (await self._generate_outputs(helm_values)).model_dump()

    @abc.abstractmethod
    async def _generate_outputs(
        self,
        helm_values: dict[str, t.Any],
    ) -> AppOutputsT: ...
