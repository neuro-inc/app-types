import typing as t

from yarl import URL

from apolo_app_types import (
    ApoloFilesMount,
    ApoloSecret,
    ContainerImage,
    CustomDeploymentInputs,
)
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps import CustomDeploymentChartValueProcessor
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.ingress import append_ingress_middleware_annotations
from apolo_app_types.helm.utils.database import get_postgres_database_url
from apolo_app_types.helm.utils.storage import get_app_data_files_path_url
from apolo_app_types.protocols.common import (
    ApoloFilesPath,
    ApoloMountMode,
    MountPath,
    StorageMounts,
)
from apolo_app_types.protocols.common.health_check import (
    HealthCheck,
    HealthCheckProbesConfig,
    HTTPHealthCheckConfig,
)
from apolo_app_types.protocols.common.k8s import Container, Env, Port
from apolo_app_types.protocols.common.storage import ApoloMountModes
from apolo_app_types.protocols.custom_deployment import NetworkingConfig
from apolo_app_types.protocols.openwebui import DBTypes, OpenWebUIAppInputs


class OpenWebUIChartValueProcessor(BaseChartValueProcessor[OpenWebUIAppInputs]):
    _port = 8080

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        self.custom_dep_val_processor = CustomDeploymentChartValueProcessor(
            *args, **kwargs
        )

    async def _configure_env(
        self, input_: OpenWebUIAppInputs
    ) -> dict[str, str | ApoloSecret]:
        if not input_.llm_chat_api.hf_model:
            err_msg = "llm_chat_api.hf_model is required"
            raise ValueError(err_msg)
        if not input_.embeddings_api.hf_model:
            err_msg = "embeddings_api.hf_model is required"
            raise ValueError(err_msg)

        env = {
            "OPENAI_API_BASE_URL": str(URL(input_.llm_chat_api.complete_url) / "v1"),
            "RAG_EMBEDDING_ENGINE": "openai",
            "RAG_OPENAI_API_BASE_URL": str(
                URL(input_.embeddings_api.complete_url) / "v1"
            ),
        }

        if input_.database_config.database.database_type == DBTypes.POSTGRES:
            database_url = get_postgres_database_url(
                credentials=input_.database_config.database.credentials
            )
            extra_env = {
                "DATABASE_URL": database_url,
                "VECTOR_DB": "pgvector",
                "PGVECTOR_DB_URL": database_url,
            }
            env |= extra_env
        custom_env = {e.name: e.value for e in input_.openwebui_specific.env}
        return {**env, **custom_env}

    async def gen_extra_values(
        self,
        input_: OpenWebUIAppInputs,
        app_name: str,
        namespace: str,
        app_id: str,
        app_secrets_name: str,
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        base_app_storage_path = get_app_data_files_path_url(
            client=self.client,
            app_type_name=str(AppType.OpenWebUI.value),
            app_name=app_name,
        )

        env = await self._configure_env(input_)
        custom_deployment = CustomDeploymentInputs(
            preset=input_.preset,
            image=ContainerImage(
                repository="ghcr.io/open-webui/open-webui",
                tag="git-b5f4c85",
            ),
            container=Container(env=[Env(name=k, value=v) for k, v in env.items()]),
            networking=NetworkingConfig(
                service_enabled=True,
                ingress_http=input_.networking_config.ingress_http,
                ports=[
                    Port(name="http", port=self._port),
                ],
            ),
            storage_mounts=StorageMounts(
                mounts=[
                    ApoloFilesMount(
                        storage_uri=ApoloFilesPath(
                            path=str(base_app_storage_path),
                        ),
                        mount_path=MountPath(path="/app/backend/data"),
                        mode=ApoloMountMode(mode=ApoloMountModes.RW),
                    )
                ]
            ),
            health_checks=HealthCheckProbesConfig(
                liveness=HealthCheck(
                    initial_delay=30,
                    period=5,
                    timeout=5,
                    failure_threshold=20,
                    health_check_config=HTTPHealthCheckConfig(
                        path="/health", port=self._port, http_headers=None
                    ),
                ),
                readiness=HealthCheck(
                    initial_delay=30,
                    period=5,
                    timeout=5,
                    failure_threshold=20,
                    health_check_config=HTTPHealthCheckConfig(
                        path="/health", port=self._port, http_headers=None
                    ),
                ),
            ),
        )

        custom_app_vals = await self.custom_dep_val_processor.gen_extra_values(
            input_=custom_deployment,
            app_name=app_name,
            namespace=namespace,
            app_id=app_id,
            app_secrets_name=app_secrets_name,
            app_type=AppType.OpenWebUI,
        )

        if input_.networking_config.advanced_networking.ingress_middleware:
            custom_app_vals["ingress"][
                "annotations"
            ] = await append_ingress_middleware_annotations(
                custom_app_vals["ingress"]["annotations"],
                namespace,
                input_.networking_config.advanced_networking.ingress_middleware.name,
            )
        return {**custom_app_vals, "labels": {"application": "openwebui"}}
