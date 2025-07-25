import typing as t

from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.protocols.launchpad import LaunchpadAppInputs


class LaunchpadChartValueProcessor(BaseChartValueProcessor[LaunchpadAppInputs]):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)

    async def gen_extra_values(
        self,
        input_: LaunchpadAppInputs,
        app_name: str,
        namespace: str,
        app_id: str,
        app_secrets_name: str,
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        # may need storage later, specially as cache for pulling models
        # base_app_storage_path = get_app_data_files_path_url(
        #     client=self.client,
        #     app_type_name=str(AppType.Launchpad.value),
        #     app_name=app_name,
        # )

        return {
            "LAUNCHPAD_INITIAL_CONFIG": input_.apps_config.model_dump(),
        }
