import typing as t

from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import gen_extra_values
from apolo_app_types.helm.apps.custom_deployment import (
    CustomDeploymentChartValueProcessor,
)
from apolo_app_types.protocols.buckets import BucketsAppInputs
from apolo_app_types.protocols.common import (
    Container,
    ContainerImage,
)
from apolo_app_types.protocols.common.containers import ContainerImagePullPolicy
from apolo_app_types.protocols.common.k8s import Port
from apolo_app_types.protocols.common.preset import Preset
from apolo_app_types.protocols.custom_deployment import (
    CustomDeploymentInputs,
    NetworkingConfig,
)


class BucketsChartValueProcessor(BaseChartValueProcessor[BucketsAppInputs]):
    _preset = Preset(name="cpu-small")

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self.custom_dep_val_processor = CustomDeploymentChartValueProcessor(
            *args, **kwargs
        )

    async def gen_extra_helm_args(self, *_: t.Any) -> list[str]:
        return ["--timeout", "30m"]

    async def gen_extra_values(
        self,
        input_: BucketsAppInputs,
        app_name: str,
        namespace: str,
        app_secrets_name: str,
        app_id: str | None = None,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """
        Generate extra Helm values for MLflow, eventually passed to the
        'custom-deployment' chart as values.
        """

        base_vals = await gen_extra_values(
            apolo_client=self.client,
            preset_type=self._preset,
            ingress_http=None,
            ingress_grpc=None,
            namespace=namespace,
            app_id=app_id,
        )

        deployment_vals = await self.custom_dep_val_processor.gen_extra_values(
            input_=CustomDeploymentInputs(
                preset=self._preset,
                image=ContainerImage(
                    repository="ghcr.io/neuro-inc/buckets-app",
                    tag="latest",
                    pull_policy=ContainerImagePullPolicy.ALWAYS,
                ),
                container=Container(),
                networking=NetworkingConfig(
                    service_enabled=True,
                    ingress_http=None,  # No HTTP ingress for outputs
                    ports=[Port(name="http", port=8000)],
                ),
            ),
            app_name=app_name,
            namespace=namespace,
            app_secrets_name=app_secrets_name,
        )

        return {**deployment_vals, **base_vals}
