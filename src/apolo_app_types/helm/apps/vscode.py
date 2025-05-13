import typing as t

from apolo_app_types import (
    ContainerImage,
    CustomDeploymentInputs,
)
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.custom_deployment import (
    CustomDeploymentChartValueProcessor,
)
from apolo_app_types.protocols.common import Container, Env, StorageMounts
from apolo_app_types.protocols.common.ingress import IngressHttp
from apolo_app_types.protocols.common.k8s import Port
from apolo_app_types.protocols.custom_deployment import NetworkingConfig
from apolo_app_types.protocols.vscode import VSCodeAppInputs


class VSCodeChartValueProcessor(BaseChartValueProcessor[VSCodeAppInputs]):
    _port: int = 8080

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        self.custom_dep_val_processor = CustomDeploymentChartValueProcessor(
            *args, **kwargs
        )

    async def gen_extra_values(
        self,
        input_: VSCodeAppInputs,
        app_name: str,
        namespace: str,
        app_secrets_name: str,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """
        Generate extra Helm values for Foocus configuration.
        """

        code_storage_mount = input_.vscode_specific.code_storage_mount
        storage_mounts = input_.extra_storage_mounts or StorageMounts(mounts=[])
        storage_mounts.mounts.append(code_storage_mount)

        env_vars = [
            Env(name="CODER_HTTP_ADDRESS", value=f"0.0.0.0:{self._port}"),
        ]
        if input_.mlflow_integration and input_.mlflow_integration.internal_web_app_url:
            env_vars.append(
                Env(
                    name="MLFLOW_TRACKING_URI",
                    value=input_.mlflow_integration.internal_web_app_url.complete_url,
                )
            )

        custom_deployment = CustomDeploymentInputs(
            preset=input_.preset,
            image=ContainerImage(
                repository="ghcr.io/neuro-inc/vscode-server",
                tag="development",
            ),
            container=Container(
                env=env_vars,
            ),
            networking=NetworkingConfig(
                service_enabled=True,
                ingress=IngressHttp(http_auth=input_.networking.http_auth),
                ports=[
                    Port(name="http", port=self._port),
                ],
            ),
            storage_mounts=storage_mounts,
        )

        custom_app_vals = await self.custom_dep_val_processor.gen_extra_values(
            input_=custom_deployment,
            app_name=app_name,
            namespace=namespace,
            app_secrets_name=app_secrets_name,
        )
        return {**custom_app_vals, "labels": {"application": "vscode"}}
