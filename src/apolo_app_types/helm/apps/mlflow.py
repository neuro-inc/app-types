import typing as t

from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import gen_extra_values
from apolo_app_types.helm.apps.custom_deployment import (
    CustomDeploymentChartValueProcessor,
)
from apolo_app_types.helm.utils.storage import get_app_data_files_path_url
from apolo_app_types.protocols.common import (
    ApoloFilesMount,
    ApoloFilesPath,
    ApoloMountMode,
    Container,
    ContainerImage,
    Env,
    MountPath,
    Service,
    StorageMounts,
)
from apolo_app_types.protocols.mlflow import (
    MLFlowAppInputs,
    MLFlowStorageBackendEnum,
)


class MLFlowChartValueProcessor(BaseChartValueProcessor[MLFlowAppInputs]):
    """
    Creates a CustomDeploymentInputs object with environment variables,
    volume mounts, etc. for MLFlow, then calls the custom deployment logic.
    """

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self.custom_dep_val_processor = CustomDeploymentChartValueProcessor(
            *args, **kwargs
        )

    async def gen_extra_helm_args(self, *_: t.Any) -> list[str]:
        return ["--timeout", "30m"]

    async def gen_extra_values(
        self,
        input_: MLFlowAppInputs,
        app_name: str,
        namespace: str,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        # 1) Basic resources/ingress from the 'common' helper
        base_vals = await gen_extra_values(
            apolo_client=self.client,
            preset_type=input_.preset,
            ingress=input_.ingress,
            namespace=namespace,
        )

        # 2) Decide environment variables & volume mounts
        envs: list[Env] = []
        storage_mounts: StorageMounts | None = None

        if (
            input_.mlflow_specific.storage_backend.backend
            == MLFlowStorageBackendEnum.SQLITE
        ):
            # For SQLite, store local DB in /mlflow-data
            envs.append(Env(name="MLFLOW_TRACKING_URI", value="sqlite:///mlflow.db"))

            base_app_url = get_app_data_files_path_url(
                client=self.client, app_type=AppType.MLFlow, app_name=app_name
            )
            db_storage_path = base_app_url / "data"

            # Create StorageMounts only for SQLite
            storage_mounts = StorageMounts(
                mounts=[
                    ApoloFilesMount(
                        storage_path=ApoloFilesPath(path=str(db_storage_path)),
                        mount_path=MountPath(path="/mlflow-data"),
                        mode=ApoloMountMode(mode="rw"),
                    ),
                ]
            )
        else:
            # For Postgres, point to a PG host
            pg_app_name_config = input_.mlflow_specific.postgres_app_name
            pg_app_name = (
                pg_app_name_config.name if pg_app_name_config else "default-postgres"
            )
            pg_uri = f"postgresql://{pg_app_name}.default/mlflow"
            envs.append(Env(name="MLFLOW_TRACKING_URI", value=pg_uri))
            # storage_mounts remains None for Postgres

        # 3) Construct a custom deployment for the actual container
        from apolo_app_types.protocols.custom_deployment import CustomDeploymentInputs

        custom_dep_inputs = CustomDeploymentInputs(
            preset=input_.preset,
            image=ContainerImage(repository="ghcr.io/neuro-inc/mlflow", tag="latest"),
            ingress=input_.ingress,
            container=Container(env=envs),
            service=Service(port=5000),
            storage_mounts=storage_mounts,
        )

        # 4) Convert that to helm values via the existing custom_deployment logic
        custom_vals = await self.custom_dep_val_processor.gen_extra_values(
            input_=custom_dep_inputs,
            app_name=app_name,
            namespace=namespace,
        )

        # 5) Merge with base_vals, add a label
        merged_vals = {**base_vals, **custom_vals}
        merged_vals.setdefault("labels", {})
        merged_vals["labels"]["application"] = "mlflow"

        # 6) Add HTTP auth configuration if enabled
        if input_.mlflow_specific.http_auth.enabled:
            merged_vals.setdefault("podAnnotations", {})
            merged_vals["podAnnotations"]["platform.apolo.us/http-auth"] = "true"

        return merged_vals
