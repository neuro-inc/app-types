from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.base import AppInputs, AppOutputs
from apolo_app_types.protocols.common.custom_validators import (
    storage_path_validator,
)
from apolo_app_types.protocols.common.networking import GrpcAPI, RestAPI
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)
from apolo_app_types.protocols.common.storage import ApoloFilesPath


TRITON_MODEL_REPOSITORY_SCHEMA_EXTRA = SchemaExtraMetadata(
    title="Triton Model Repository",
    description="Apolo Files directory with a Triton model repository: one "
    "sub-directory per model with config.pbtxt and numbered version "
    "directories. Layout: https://docs.nvidia.com/deeplearning/"
    "triton-inference-server/user-guide/docs/user_guide/"
    "model_repository.html#repository-layout",
    meta_type=SchemaMetaType.INTEGRATION,
    custom_validators=[
        storage_path_validator(
            exists=True, is_dir=True, same_project=True, subfolder=True
        )
    ],
)


class TritonModelRepository(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=TRITON_MODEL_REPOSITORY_SCHEMA_EXTRA.as_json_schema_extra(),
    )

    files_path: ApoloFilesPath = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Repository Path",
            description="Storage path of an existing directory, "
            "e.g. storage:triton/models. "
            "It must be a subfolder of the project of the Triton app, "
            "not the project root.",
        ).as_json_schema_extra(),
    )


class TritonModelRepositoryAppInputs(AppInputs):
    model_repository: TritonModelRepository = Field(
        ...,
        json_schema_extra=TRITON_MODEL_REPOSITORY_SCHEMA_EXTRA.model_copy(
            update={"meta_type": SchemaMetaType.INLINE}
        ).as_json_schema_extra(),
    )


class TritonModelRepositoryAppOutputs(AppOutputs):
    model_repository: TritonModelRepository


class TritonServerHttpEndpoint(RestAPI):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Triton Server HTTP Endpoint",
            description="Triton Inference Server HTTP/REST API (KServe v2 protocol).",
        ).as_json_schema_extra(),
    )


class TritonServerGRPCEndpoint(GrpcAPI):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Triton Server gRPC Endpoint",
            description="Triton Inference Server gRPC API (KServe v2 protocol).",
        ).as_json_schema_extra(),
    )
