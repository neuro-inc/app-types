from typing import Literal

from pydantic import ConfigDict, Field

from apolo_app_types import AppInputs
from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import SchemaExtraMetadata


class BucketsInfo(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Apolo Buckets Integration",
            description="Integrate Apolo Buckets into applications",
        ).as_json_schema_extra(),
    )
    app: Literal["buckets"] = Field(default="buckets")


class BucketsAppInputs(AppInputs):
    buckets_info: BucketsInfo = Field(default_factory=lambda _: BucketsInfo())
