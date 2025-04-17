import typing as t

from apolo_app_types.protocols.common import StorageMounts, ApoloFilesPath, MountPath, ApoloMountMode
from apolo_app_types.protocols.common.k8s import Port, Container, Env
from apolo_app_types.protocols.common.secrets_ import serialize_optional_secret
from apolo_app_types.protocols.custom_deployment import NetworkingConfig
from yarl import URL

from apolo_app_types import CustomDeploymentInputs, ContainerImage, ApoloFilesMount
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps import CustomDeploymentChartValueProcessor
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.utils.storage import get_app_data_files_path_url

from apolo_app_types.protocols.private_gpt import PrivateGPTAppInputs


class PrivateGptChartValueProcessor(
    BaseChartValueProcessor[PrivateGPTAppInputs]
):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        self.custom_dep_val_processor = CustomDeploymentChartValueProcessor(
            *args, **kwargs
        )
    async def _configure_env(
        self, input_: PrivateGPTAppInputs,
        app_secrets_name: str,
    ) -> dict[str, str]:
        env_vars = {
            "PGPT_PROFILES": "app, pgvector",
            "VLLM_API_BASE": input_.llm_chat_api.get_api_base_url(),
            "VLLM_MODEL": input_.llm_details.hugging_face_model.model_hf_name,
            "VLLM_TOKENIZER": (
                input_.llm_details.tokenizer_hf_name or input_.llm_details.hugging_face_model.model_hf_name
            ),
            # hardcoded for now, needs investigation,
            # limited by GPU memory and model size
            "VLLM_MAX_NEW_TOKENS": "5000",
            # hardcoded for now, needs investigation,
            # defined by model architecture
            "VLLM_CONTEXT_WINDOW": "8192",
            "VLLM_TEMPERATURE": str(input_.private_gpt_specific.llm_temperature),
            # FIX TEI API
            "EMBEDDING_API_BASE": input_.tei_api.get_api_base_url(),
            "EMBEDDING_MODEL": input_.tei_model.model_hf_name,
            "EMBEDDING_DIM": "768",  # hardcoded for now, need introspection
            "POSTGRES_HOST": input_.pgvector_user.pgbouncer_host,
            "POSTGRES_PORT": input_.pgvector_user.pgbouncer_port,
            "POSTGRES_DB": input_.pgvector_user.dbname,
            "POSTGRES_USER": input_.pgvector_user.user,
            "POSTGRES_PASSWORD": input_.pgvector_user.password,
        }
        env_vars = dict(map(lambda item: (item[0], str(item[1])), env_vars.items()))
        secret_envs = {}
        if input_.llm_details.hugging_face_model.hf_token:
            secret_envs["HUGGINGFACE_TOKEN"] = serialize_optional_secret(
                input_.llm_details.hugging_face_model.hf_token, secret_name=app_secrets_name
            )
        env_vars.update(secret_envs)

        return env_vars

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
            client=self.client, app_type=AppType.PrivateGPT, app_name=app_name
        )
        data_storage_path = base_app_storage_path / "data"
        data_container_dir = URL("/home/worker/app/local_data")
        outputs_storage_path = base_app_storage_path / "tiktoken_cache"
        outputs_container_dir = URL("/home/worker/app/tiktoken_cache")

        env = await self._configure_env(input_, app_secrets_name)
        custom_deployment = CustomDeploymentInputs(
            preset=input_.preset,
            image=ContainerImage(
                repository="ghcr.io/neuro-inc/private-gpt",
                tag="latest",
            ),
            container=Container(env=[Env(name=k, value=v) for k, v in env.items()]),
            networking=NetworkingConfig(
                service_enabled=True,
                ingress=input_.ingress,
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
        )
        return {**custom_app_vals, "labels": {"application": "privategpt"}}
