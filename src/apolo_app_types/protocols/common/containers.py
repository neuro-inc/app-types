from pydantic import ConfigDict

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
)


class ContainerImage(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Container Image",
            description="Container image to be used in application",
        ).as_json_schema_extra(),
    )
    repository: str
    tag: str | None = None
