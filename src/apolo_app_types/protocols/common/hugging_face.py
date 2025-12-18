import typing as t

from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)
from apolo_app_types.protocols.common.secrets_ import ApoloSecret
from apolo_app_types.protocols.common.storage import ApoloFilesPath


HF_SCHEMA_EXTRA = SchemaExtraMetadata(
    title="Hugging Face Model",
    description="Configure the Hugging Face model. "
    "Ensure it is available on the Hugging Face Hub and provide"
    " an API token with access rights if the repository is gated.",
    meta_type=SchemaMetaType.INTEGRATION,
)
HF_TOKEN_SCHEMA_EXTRA = SchemaExtraMetadata(
    description="Provide a Hugging Face API token linked "
    "to an account with access to the model "
    "specified above. This token will be used to download model"
    " files from the Hugging Face Hub, including "
    "gated or private repositories where applicable.",
    title="Hugging Face Token",
    meta_type=SchemaMetaType.INTEGRATION,
)


class HuggingFaceModelDetailDynamic(AbstractAppFieldType):
    """Detailed HuggingFace model information."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="HuggingFace Model Detail",
            description="Detailed information about a HuggingFace model.",
            meta_type=SchemaMetaType.DYNAMIC,
        ).as_json_schema_extra(),
    )

    id: t.Annotated[
        str,
        Field(
            json_schema_extra=SchemaExtraMetadata(
                title="Repository ID",
                description="The HuggingFace repository identifier.",
            ).as_json_schema_extra()
        ),
    ]

    name: t.Annotated[
        str,
        Field(
            json_schema_extra=SchemaExtraMetadata(
                title="Model Name",
                description="The model name.",
            ).as_json_schema_extra()
        ),
    ]

    visibility: t.Annotated[
        str,
        Field(
            json_schema_extra=SchemaExtraMetadata(
                title="Visibility",
                description="Repository visibility (public or private).",
            ).as_json_schema_extra()
        ),
    ]

    gated: bool = Field(
        default=False,
        json_schema_extra=SchemaExtraMetadata(
            title="Gated",
            description="Whether the model requires access approval.",
        ).as_json_schema_extra(),
    )

    tags: list[str] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Tags",
            description="Tags associated with the model.",
        ).as_json_schema_extra(),
    )

    cached: bool = Field(
        default=False,
        json_schema_extra=SchemaExtraMetadata(
            title="Cached",
            description="Whether the model is cached locally.",
        ).as_json_schema_extra(),
    )

    last_modified: (
        t.Annotated[
            str,
            Field(
                json_schema_extra=SchemaExtraMetadata(
                    title="Last Modified",
                    description="Timestamp when the model was last modified.",
                ).as_json_schema_extra()
            ),
        ]
        | None
    ) = None

    files_path: ApoloFilesPath | None = None


class HuggingFaceToken(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=HF_TOKEN_SCHEMA_EXTRA.as_json_schema_extra(),
    )
    token_name: str = Field(  # noqa: N814
        ...,
        min_length=0,
        json_schema_extra=SchemaExtraMetadata(
            title="Token Name",
            description="The name of the Hugging Face token.",
        ).as_json_schema_extra(),
    )
    token: ApoloSecret = Field(  # noqa: N814
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Hugging Face Token",
            description="The Hugging Face API token used to access models.",
        ).as_json_schema_extra(),
    )


class HuggingFaceCache(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Hugging Face Cache",
            description="Configuration for the Hugging Face cache.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    files_path: ApoloFilesPath = Field(
        default=ApoloFilesPath(path="storage:.apps/hugging-face-cache"),
        json_schema_extra=SchemaExtraMetadata(
            description="The path to the Apolo Files directory where Hugging Face artifacts are cached.",  # noqa: E501
            title="Files Path",
        ).as_json_schema_extra(),
    )


class HuggingFaceModel(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=HF_SCHEMA_EXTRA.as_json_schema_extra(),
    )
    model_hf_name: str = Field(  # noqa: N815
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="The name of the Hugging Face model.",
            title="Hugging Face Model Name",
        ).as_json_schema_extra(),
    )
    hf_token: HuggingFaceToken | None = Field(  # noqa: N815
        default=None,
        json_schema_extra=HF_TOKEN_SCHEMA_EXTRA.as_json_schema_extra(),
    )
    hf_cache: HuggingFaceCache | None = Field(  # noqa: N815
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Model Cache",
            description=(
                "Enables caching of model files to reduce"
                " redundant downloads and speed up load times."
            ),
        ).as_json_schema_extra(),
    )
