import typing as t

from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import gen_extra_values
from apolo_app_types.helm.apps.custom_deployment import (
    CustomDeploymentChartValueProcessor,
)
from apolo_app_types.protocols.common import (
    ApoloFilesMount,
    ApoloMountMode,
    Container,
    ContainerImage,
    Env,
    MountPath,
    Service,
    StorageMounts,
)
from apolo_app_types.protocols.custom_deployment import CustomDeploymentInputs
from apolo_app_types.protocols.mlflow import (
    MLFlowAppInputs,
    MLFlowStorageBackendEnum,
)


class MLFlowChartValueProcessor(BaseChartValueProcessor[MLFlowAppInputs]):
    """
    Enhanced MLFlow chart processor that supports:
    - SQLite with PVC for DB storage
    - Postgres with URI or app name
    - Artifact storage on Apolo Files
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
        """
        Generate extra Helm values for MLflow, eventually passed to the
        'custom-deployment' chart as values.
        """

        base_vals = await gen_extra_values(
            apolo_client=self.client,
            preset_type=input_.preset,
            ingress=input_.ingress,
            namespace=namespace,
        )

        envs: list[Env] = []
        backend_uri = ""

        storage_backend = input_.mlflow_specific.storage_backend.database
        if storage_backend == MLFlowStorageBackendEnum.SQLITE:
            if not input_.mlflow_specific.sqlite_pvc:
                error_msg = "SQLite chosen but no 'sqlite_pvc' provided."
                raise ValueError(error_msg)

            backend_uri = "sqlite:///mlflow-data/mlflow.db"
        else:
            postgres_uri = input_.mlflow_specific.postgres_uri
            if postgres_uri and postgres_uri.uri:
                backend_uri = postgres_uri.uri
            else:
                error_msg = "Postgres chosen but 'postgres_uri' not provided"
                raise ValueError(error_msg)

        envs.append(Env(name="MLFLOW_TRACKING_URI", value=backend_uri))

        artifact_mounts: StorageMounts | None = None
        artifact_env_val = None
        if input_.mlflow_specific.artifact_store:
            artifact_env_val = "file:///mlflow-artifacts"
            envs.append(Env(name="MLFLOW_ARTIFACT_ROOT", value=artifact_env_val))

            if input_.mlflow_specific.artifact_store.path:
                artifact_mounts = StorageMounts(
                    mounts=[
                        ApoloFilesMount(
                            storage_uri=input_.mlflow_specific.artifact_store.path,
                            mount_path=MountPath(path="/mlflow-artifacts"),
                            mode=ApoloMountMode(mode="rw"),
                        )
                    ]
                )

        mlflow_cmd = ["mlflow"]
        mlflow_args = [
            "server",
            f"--backend-store-uri={backend_uri}",
            "--host=0.0.0.0",
            "--port=5000",
        ]
        if artifact_env_val:
            mlflow_args.append("--default-artifact-root=/mlflow-artifacts")

        cd_inputs = CustomDeploymentInputs(
            preset=input_.preset,
            image=ContainerImage(
                repository="ghcr.io/apolo-actions/mlflow",
                tag="v2.19.0",
            ),
            ingress=input_.ingress,
            container=Container(
                command=mlflow_cmd,
                args=mlflow_args,
                env=envs,
            ),
            service=Service(port=5000),
            storage_mounts=artifact_mounts,
        )

        custom_vals = await self.custom_dep_val_processor.gen_extra_values(
            input_=cd_inputs,
            app_name=app_name,
            namespace=namespace,
        )

        if storage_backend == MLFlowStorageBackendEnum.SQLITE:
            custom_vals["persistentVolumeClaims"] = [
                {
                    "name": "mlflow-sqlite-storage",
                    "size": "5Gi",
                    "storageClassName": "standard",
                    "accessModes": ["ReadWriteOnce"],
                }
            ]
            custom_vals["volumes"] = [
                {
                    "name": "mlflow-db-pvc",
                    "persistentVolumeClaim": {
                        "claimName": "mlflow-sqlite-storage",
                    },
                }
            ]
            custom_vals["volumeMounts"] = [
                {
                    "name": "mlflow-db-pvc",
                    "mountPath": "/mlflow-data",
                }
            ]

        merged_vals = {**base_vals, **custom_vals}
        merged_vals.setdefault("labels", {})
        merged_vals["labels"]["application"] = "mlflow"

        if input_.mlflow_specific.http_auth.enabled:
            merged_vals.setdefault("podAnnotations", {})
            merged_vals["podAnnotations"]["platform.apolo.us/http-auth"] = "true"

        return merged_vals
