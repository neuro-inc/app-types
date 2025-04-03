import typing as t

from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import (
    gen_extra_values,
)
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
    MLFlowStorageBackend,
)


class MLFlowChartValueProcessor(BaseChartValueProcessor[MLFlowAppInputs]):
    """
    This chart value processor reuses 'custom-deployment' under the hood,
    just like fooocus.py does.
    """

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self.custom_dep_val_processor = CustomDeploymentChartValueProcessor(
            *args, **kwargs
        )

    async def gen_extra_helm_args(self, *_: t.Any) -> list[str]:
        """
        Add any additional Helm CLI flags, e.g. a longer timeout.
        """
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
        Build the final Helm values for MLFlow by:
         1) Setting environment variables
         2) Possibly setting up a persistent volume if using local SQLite
         3) Defining a service port
         4) Delegating to 'CustomDeploymentChartValueProcessor'
        """

        # 1) Base resources / ingress from the 'common' gen_extra_values
        #    (This sets 'preset_name', 'ingress' config, etc.)
        base_extra_vals = await gen_extra_values(
            apolo_client=self.client,
            preset_type=input_.preset,
            ingress=input_.ingress,
            namespace=namespace,
        )

        # 2) Decide which backend to use
        #    - For 'sqlite', we store a local DB file on Apolo Disk
        #    - For 'postgres', we might pass environment var MLFLOW_TRACKING_URI
        envs: list[Env] = []

        if input_.mlflow_specific.storage_backend == MLFlowStorageBackend.SQLITE:
            # We'll mount Apolo Files to store the local SQLite DB
            # Example: /mlflow-data in the container
            # We'll also set MLFLOW_TRACKING_URI=sqlite:///mlflow.db or similar

            envs.append(Env(name="MLFLOW_TRACKING_URI", value="sqlite:///mlflow.db"))

            # Plan to mount a directory:
            # storage://.../.apps/mlflow/<app_name>/data => /mlflow-data
            base_app_storage = get_app_data_files_path_url(
                client=self.client, app_type=AppType.MLFlow, app_name=app_name
            )
            data_storage_path = base_app_storage / "data"
            container_mount_path = MountPath(path="/mlflow-data")

            # We'll store the DB in /mlflow-data/mlflow.db
            extra_storage_mounts = StorageMounts(
                mounts=[
                    ApoloFilesMount(
                        storage_path=ApoloFilesPath(path=str(data_storage_path)),
                        mount_path=container_mount_path,
                        mode=ApoloMountMode(mode="rw"),
                    ),
                ]
            )

        else:
            # If using Postgres, let’s assume the user references an external Postgres
            # We'll set MLFLOW_TRACKING_URI for them.
            # In real usage, you'd discover the PG host from another platform app
            # or from environment variables. This is a placeholder:
            pg_host = f"{input_.mlflow_specific.postgres_app_name or 'SOME_DB'}.default"
            envs.append(
                Env(name="MLFLOW_TRACKING_URI", value=f"postgresql://{pg_host}/mlflow")
            )

            extra_storage_mounts = StorageMounts(mounts=[])

        # 3) Construct the "CustomDeploymentInputs"
        #    Let’s say we run port 5000 by default for MLFlow server
        from apolo_app_types.protocols.custom_deployment import CustomDeploymentInputs

        custom_dep_inputs = CustomDeploymentInputs(
            preset=input_.preset,
            image=ContainerImage(
                repository="ghcr.io/neuro-inc/mlflow",  # your own MLFlow image
                tag="latest",
            ),
            ingress=input_.ingress,
            container=Container(
                command=[],  # MLFlow often starts from an ENTRYPOINT
                args=[],  # Possibly `mlflow server --host 0.0.0.0 --port 5000`
                env=envs,
            ),
            service=Service(port=5000),
            storage_mounts=extra_storage_mounts,
        )

        # 4) Convert them to a dict by calling the existing custom deployment logic
        custom_vals = await self.custom_dep_val_processor.gen_extra_values(
            input_=custom_dep_inputs,
            app_name=app_name,
            namespace=namespace,
        )

        # Merge in the “base” resources like tolerations, ingress config, etc.
        # (The custom deployment processor might do some of that,
        # but we also have base_extra_vals from gen_extra_values.)
        # We'll do a naive merge:
        merged_values = {**base_extra_vals, **custom_vals}

        # Optionally add a label to identify the app
        merged_values.setdefault("labels", {})
        merged_values["labels"]["application"] = "mlflow"

        return merged_values
