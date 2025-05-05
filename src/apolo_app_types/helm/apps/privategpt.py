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
from apolo_app_types.helm.utils.storage import get_app_data_files_path_url
from apolo_app_types.protocols.common import (
    ApoloFilesPath,
    ApoloMountMode,
    MountPath,
    StorageMounts,
)
from apolo_app_types.protocols.common.k8s import Container, Env, Port
from apolo_app_types.protocols.common.openai_compat import get_api_base_url
from apolo_app_types.protocols.custom_deployment import NetworkingConfig
from apolo_app_types.protocols.private_gpt import PrivateGPTAppInputs


class PrivateGptChartValueProcessor(BaseChartValueProcessor[PrivateGPTAppInputs]):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        self.custom_dep_val_processor = CustomDeploymentChartValueProcessor(
            *args, **kwargs
        )

    async def _configure_env(
        self, input_: PrivateGPTAppInputs
    ) -> dict[str, str | int | ApoloSecret | None]:
        if not input_.llm_chat_api.hf_model:
            err_msg = "llm_chat_api.hf_model is required"
            raise ValueError(err_msg)
        if not input_.embeddings_api.hf_model:
            err_msg = "embeddings_api.hf_model is required"
            raise ValueError(err_msg)

        return {
            "PGPT_PROFILES": "app, pgvector",
            "VLLM_API_BASE": get_api_base_url(input_.llm_chat_api),
            "VLLM_MODEL": input_.llm_chat_api.hf_model.model_hf_name,
            "VLLM_TOKENIZER": (
                input_.private_gpt_specific.llm_tokenizer_name
                or input_.llm_chat_api.hf_model.model_hf_name
            ),
            # hardcoded for now, needs investigation,
            "VLLM_MAX_NEW_TOKENS": input_.private_gpt_specific.llm_max_new_tokens,
            # hardcoded for now, needs investigation,
            "VLLM_CONTEXT_WINDOW": input_.private_gpt_specific.llm_context_window,
            "VLLM_TEMPERATURE": str(input_.private_gpt_specific.llm_temperature),
            # FIX TEI API
            "EMBEDDING_API_BASE": get_api_base_url(input_.embeddings_api),
            "EMBEDDING_MODEL": input_.embeddings_api.hf_model.model_hf_name,
            "EMBEDDING_DIM": input_.private_gpt_specific.embeddings_dimension,
            "POSTGRES_HOST": input_.pgvector_user.pgbouncer_host,
            "POSTGRES_PORT": input_.pgvector_user.pgbouncer_port,
            "POSTGRES_DB": input_.pgvector_user.dbname or "postgres",
            "POSTGRES_USER": input_.pgvector_user.user,
            "POSTGRES_PASSWORD": input_.pgvector_user.password,
            "HUGGINGFACE_TOKEN": input_.llm_chat_api.hf_model.hf_token,
        }

    async def gen_extra_values(
        self,
        input_: PrivateGPTAppInputs,
        app_name: str,
        namespace: str,
        app_secrets_name: str,
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        base_app_storage_path = get_app_data_files_path_url(
            client=self.client,
            app_type_name=str(AppType.PrivateGPT.value),
            app_name=app_name,
        )
        data_storage_path = base_app_storage_path / "data"
        data_container_dir = URL("/home/worker/app/local_data")
        outputs_storage_path = base_app_storage_path / "tiktoken_cache"
        outputs_container_dir = URL("/home/worker/app/tiktoken_cache")

        env = await self._configure_env(input_)
        custom_deployment = CustomDeploymentInputs(
            preset=input_.preset,
            image=ContainerImage(
                repository="ghcr.io/neuro-inc/private-gpt",
                tag="latest",
            ),
            container=Container(env=[Env(name=k, value=v) for k, v in env.items()]),
            networking=NetworkingConfig(
                service_enabled=True,
                ingress_http=input_.ingress_http,
                ports=[
                    Port(name="http", port=8080),
                ],
            ),
            storage_mounts=StorageMounts(
                mounts=[
                    ApoloFilesMount(
                        storage_uri=ApoloFilesPath(
                            path=str(data_storage_path),
                        ),
                        mount_path=MountPath(path=str(data_container_dir)),
                        mode=ApoloMountMode(mode="rw"),
                    ),
                    ApoloFilesMount(
                        storage_uri=ApoloFilesPath(
                            path=str(outputs_storage_path),
                        ),
                        mount_path=MountPath(path=str(outputs_container_dir)),
                        mode=ApoloMountMode(mode="rw"),
                    ),
                ]
            ),
        )

        custom_app_vals = await self.custom_dep_val_processor.gen_extra_values(
            input_=custom_deployment,
            app_name=app_name,
            namespace=namespace,
            app_secrets_name=app_secrets_name,
        )
        return {**custom_app_vals, "labels": {"application": "privategpt"}}
