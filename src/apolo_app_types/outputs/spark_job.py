import logging
import typing as t


logger = logging.getLogger()


async def get_spark_job_outputs(
    helm_values: dict[str, t.Any],
    app_instance_id: str,
) -> dict[str, t.Any]:
    return {}
