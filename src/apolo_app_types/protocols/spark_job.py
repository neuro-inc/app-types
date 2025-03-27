from enum import StrEnum

from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    ApoloFilesFile,
    ApoloFilesMount,
    AppInputs,
    AppOutputs,
    ContainerImage,
    Preset,
    SchemaExtraMetadata,
)


class SparkApplicationType(StrEnum):
    PYTHON = "Python"
    SCALA = "Scala"
    JAVA = "Java"
    R = "R"


class SparkExecutorConfig(AbstractAppFieldType):
    instances: int


class PythonSpecificConfig(AbstractAppFieldType):
    pypi_packages: list[str] | ApoloFilesFile | None = None


class JavaSpecificConfig(AbstractAppFieldType):
    main_class: str


class SparkDependencies(AbstractAppFieldType):
    jars: list[str] | None = None
    py_files: list[str] | None = None
    files: list[str] | None = None
    packages: list[str] | None = None
    exclude_packages: list[str] | None = None
    repositories: list[str] | None = None
    archives: list[str] | None = None


class SparkAutoScalingConfig(AbstractAppFieldType):
    enabled: bool = False
    initial_executors: int | None
    min_executors: int
    max_executors: int
    shuffle_tracking_timeout: int


class SparkApplicationModel(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Spark Application",
            description="Run scalable Apache Spark applications",
        ).as_json_schema_extra(),
    )
    type: SparkApplicationType = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Spark Application type",
            description="Choose the type of the Spark application",
        ).as_json_schema_extra(),
    )
    image: ContainerImage = Field(
        default=ContainerImage(repository="spark", tag="3.5.3")
    )
    main_application_file: ApoloFilesFile = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Main Application File",
            description="The main application file to be executed",
        ).as_json_schema_extra(),
    )
    arguments: list[str] | None = None
    dependencies: SparkDependencies | None = None
    spark_application_config: PythonSpecificConfig | JavaSpecificConfig | None = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Spark Application Configuration",
            description="Language specific configuration to the Spark application type",
        ).as_json_schema_extra(),
    )
    spark_auto_scaling_config: SparkAutoScalingConfig | None = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Spark Auto Scaling Configuration",
            description="Configuration for the Spark auto scaling",
        ).as_json_schema_extra(),
    )
    driver_preset: Preset = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Driver Preset",
            description="Preset configuration to be used by the driver",
        ).as_json_schema_extra(),
    )
    executor_preset: Preset = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Executor Preset",
            description="Preset configuration to be used by the executor",
        ).as_json_schema_extra(),
    )
    volumes: list[ApoloFilesMount] | None = None


class SparkJobInputs(AppInputs):
    spark_job: SparkApplicationModel


class SparkJobOutputs(AppOutputs):
    pass
