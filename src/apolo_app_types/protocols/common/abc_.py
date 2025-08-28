import abc
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    model_serializer,
)

from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
)


class ApoloBaseModel(BaseModel):
    @model_serializer(when_used="always", mode="wrap")
    def _serialize(
        self, serializer: SerializerFunctionWrapHandler, info: SerializationInfo
    ) -> dict[str, Any]:
        model: dict[str, Any] = serializer(self)
        model["__type__"] = self.__class__.model_config.get(
            "title", self.__class__.__name__
        )
        return model


class AbstractAppFieldType(ApoloBaseModel, abc.ABC):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="",
            description="",
        ).as_json_schema_extra(),
    )


class AppInputsDeployer(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, protected_namespaces=())


class AppInputs(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, protected_namespaces=())


class AppOutputsDeployer(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    external_web_app_url: str | None = Field(
        default=None,
        description="The URL of the external web app.",
        title="External web app URL",
    )


class AppOutputs(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
