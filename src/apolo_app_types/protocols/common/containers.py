from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types.protocols.common.schema_extra import SchemaExtraMetadata
from apolo_app_types.protocols.dockerhub import DockerConfigModel


class ContainerImage(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Container Image",
            description="Container image to be used in application",
        ).as_json_schema_extra(),
    )
    repository: str
    tag: str | None = None
    dockerconfigjson: DockerConfigModel | None = Field(
        default=None, title="ImagePullSecrets for DockerHub"
    )
