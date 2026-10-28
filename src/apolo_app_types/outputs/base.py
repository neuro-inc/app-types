import abc
import logging
import time
import typing as t

from apolo_app_types import AppOutputs


logger = logging.getLogger(__name__)

AppOutputsT = t.TypeVar("AppOutputsT", bound=AppOutputs)


class BaseAppOutputsProcessor(abc.ABC, t.Generic[AppOutputsT]):
    async def generate_outputs(
        self,
        helm_values: dict[str, t.Any],
        app_instance_id: str,
    ) -> dict[str, t.Any]:
        processor_name = type(self).__name__
        start_time = time.perf_counter()
        logger.info(
            "Generating outputs for App instance %s with %s (%d Helm fields)",
            app_instance_id,
            processor_name,
            len(helm_values),
        )
        outputs = (
            await self._generate_outputs(helm_values, app_instance_id)
        ).model_dump()
        elapsed = time.perf_counter() - start_time
        logger.info(
            "Generated %d output fields for App instance %s with %s in %.2f seconds",
            len(outputs),
            app_instance_id,
            processor_name,
            elapsed,
        )
        return outputs

    @abc.abstractmethod
    async def _generate_outputs(
        self,
        helm_values: dict[str, t.Any],
        app_instance_id: str,
    ) -> AppOutputsT: ...
