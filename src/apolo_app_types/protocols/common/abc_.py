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
from pydantic.config import JsonDict

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

    def __init_subclass__(cls, **kwargs) -> None:  # type: ignore[no-untyped-def]
        """Automatically add x-type to json_schema_extra."""
        x_type: JsonDict = {"x-type": cls.__name__}
        if "json_schema_extra" in cls.model_config and isinstance(
            cls.model_config["json_schema_extra"], dict
        ):
            cls.model_config["json_schema_extra"].update(x_type)
        else:
            cls.model_config["json_schema_extra"] = x_type
        return super().__init_subclass__(**kwargs)


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


class AppOutputsDeployer(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    external_web_app_url: str | None = Field(
        default=None,
        description="The URL of the external web app.",
        title="External web app URL",
    )
