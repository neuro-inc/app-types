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
    StorageMounts,
)
from apolo_app_types.protocols.common.k8s import Port
from apolo_app_types.protocols.custom_deployment import (
    CustomDeploymentInputs,
    NetworkingConfig,
)
from apolo_app_types.protocols.mlflow import (
    MLFlowAppInputs,
    MLFlowMetadataPostgres,
    MLFlowMetadataSQLite,
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
        app_secrets_name: str,
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
            ingress_http=input_.ingress_http,
            ingress_grpc=None,
            namespace=namespace,
        )

        envs: list[Env] = []
        backend_uri = ""
        pvc_name = "mlflow-sqlite-storage"
        use_sqlite = True

        if isinstance(input_.metadata_storage, MLFlowMetadataPostgres):
            if not input_.metadata_storage.postgres_uri.uri:
                error_msg = "Postgres chosen but 'postgres_uri' not provided"
                raise ValueError(error_msg)
            backend_uri = input_.metadata_storage.postgres_uri.uri
            use_sqlite = False
        elif isinstance(input_.metadata_storage, MLFlowMetadataSQLite):
            pvc_name = input_.metadata_storage.pvc_name
        if use_sqlite:
            backend_uri = "sqlite:///mlflow-data/mlflow.db"

        envs.append(Env(name="MLFLOW_TRACKING_URI", value=backend_uri))

        artifact_mounts: StorageMounts | None = None
        artifact_env_val = None
        if input_.artifact_store:
            artifact_env_val = "file:///mlflow-artifacts"
            envs.append(Env(name="MLFLOW_ARTIFACT_ROOT", value=artifact_env_val))

            artifact_mounts = StorageMounts(
                mounts=[
                    ApoloFilesMount(
                        storage_uri=input_.artifact_store,
                        mount_path=MountPath(path="/mlflow-artifacts"),
                        mode=ApoloMountMode(mode="rw"),
                    )
                ]
            )

        mlflow_cmd = ["mlflow"]
        mlflow_args = [
            "server",
            "--serve-artifacts",
            "--host=0.0.0.0",
            "--port=5000",
            f"--backend-store-uri={backend_uri}",
        ]
        if artifact_env_val:
            mlflow_args.append("--artifacts-destination=/mlflow-artifacts")

        cd_inputs = CustomDeploymentInputs(
            preset=input_.preset,
            image=ContainerImage(
                repository="ghcr.io/apolo-actions/mlflow",
                tag="v2.19.0",
            ),
            container=Container(
                command=mlflow_cmd,
                args=mlflow_args,
                env=envs,
            ),
            networking=NetworkingConfig(
                service_enabled=True,
                ingress_http=input_.ingress_http,
                ports=[
                    Port(name="http", port=5000),
                ],
            ),
            storage_mounts=artifact_mounts,
        )

        custom_vals = await self.custom_dep_val_processor.gen_extra_values(
            input_=cd_inputs,
            app_name=app_name,
            namespace=namespace,
            app_secrets_name=app_secrets_name,
        )

        if use_sqlite:
            custom_vals["persistentVolumeClaims"] = [
                {
                    "name": pvc_name,
                    "size": "5Gi",
                    "storageClassName": "standard",
                    "accessModes": ["ReadWriteOnce"],
                }
            ]
            custom_vals["volumes"] = [
                {
                    "name": "mlflow-db-pvc",
                    "persistentVolumeClaim": {
                        "claimName": pvc_name,
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

        return merged_vals
