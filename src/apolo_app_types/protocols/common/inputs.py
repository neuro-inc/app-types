from typing import Unpack

from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types.protocols.common.storage import ApoloStoragePath
from apolo_app_types.protocols.common.validator import validate_complex_type_prop


class AppInputsDeployer(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, protected_namespaces=())


class AppInputs(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, protected_namespaces=())
    app_data_path: ApoloStoragePath | None = Field(default=None)

    def __init_subclass__(cls: type["AppInputs"], **kwargs: Unpack[ConfigDict]) -> None:
        """Validate field types at class definition time."""
        super().__init_subclass__()

        validate_complex_type_prop(cls)
