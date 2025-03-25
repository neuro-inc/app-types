from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from apolo_app_types.protocols.common import AppInputs, AppOutputs
from apolo_app_types.protocols.common.containers import ContainerImage
from apolo_app_types.protocols.common.preset import Preset
from apolo_app_types.protocols.common.schema_extra import SchemaExtraMetadata
from apolo_app_types.protocols.common.storage import ApoloStorageFile, ApoloStorageMount


class SparkApplicationType(StrEnum):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Spark Application type",
            description="Choose the type of the Spark application",
        ).as_json_schema_extra(),
    )
    PYTHON = "Python"
    SCALA = "Scala"
    JAVA = "Java"
    R = "R"


class SparkExecutorConfig(BaseModel):
    instances: int


class PythonSpecificConfig(BaseModel):
    pypi_packages: list[str] | ApoloStorageFile | None = None


class JavaSpecificConfig(BaseModel):
    main_class: str


class SparkDependencies(BaseModel):
    jars: list[str] | None = None
    py_files: list[str] | None = None
    files: list[str] | None = None
    packages: list[str] | None = None
    exclude_packages: list[str] | None = None
    repositories: list[str] | None = None
    archives: list[str] | None = None


class SparkAutoScalingConfig(BaseModel):
    enabled: bool = False
    initial_executors: int | None
    min_executors: int
    max_executors: int
    shuffle_tracking_timeout: int


class SparkApplicationModel(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Spark Application",
            description="Run scalable Apache Spark applications",
        ).as_json_schema_extra(),
    )
    type: SparkApplicationType
    image: ContainerImage
    main_application_file: ApoloStorageFile
    arguments: list[str] | None = None
    dependencies: SparkDependencies | None = None
    spark_application_config: PythonSpecificConfig | JavaSpecificConfig | None
    spark_auto_scaling_config: SparkAutoScalingConfig | None
    driver_preset: Preset
    executor_preset: Preset
    volumes: list[ApoloStorageMount] | None = None


class SparkJobInputs(AppInputs):
    spark_job: SparkApplicationModel


class SparkJobOutputs(AppOutputs):
    pass
