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


class DriverConfig(AbstractAppFieldType):
    preset: Preset = Field(
        ...,
        title="Driver Preset",
        description="Preset configuration to be used by the driver",
    )


class ExecutorConfig(AbstractAppFieldType):
    instances: int = Field(
        default=1, title="Instances", description="Number of instances"
    )
    preset: Preset = Field(
        ...,
        title="Executor Preset",
        description="Preset configuration to be used by the executor",
    )


class SparkDependencies(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Spark Dependencies",
            description="Dependencies for the Spark application",
        ).as_json_schema_extra(),
    )
    jars: list[str] | None = Field(
        default=None,
        title="Jars",
        description="List of jars to be included as dependencies",
    )
    py_files: list[str] | None = Field(
        default=None,
        title="Python Files",
        description="List of Python files to be included as dependencies",
    )
    files: list[str] | None = Field(
        default=None,
        title="Files",
        description="List of files to be included as dependencies",
    )
    packages: list[str] | None = Field(
        default=None,
        title="Packages",
        description="List of packages to be included as dependencies",
    )
    exclude_packages: list[str] | None = Field(
        default=None,
        title="Exclude Packages",
        description="List of packages to be excluded as dependencies",
    )
    repositories: list[str] | None = Field(
        default=None,
        title="Repositories",
        description="List of repositories to be included as dependencies",
    )
    archives: list[str] | None = Field(
        default=None,
        title="Archives",
        description="List of archives to be included as dependencies",
    )
    pypi_packages: list[str] | ApoloFilesFile | None = Field(
        default=None,
        title="PyPi Packages",
        description=(
            "List of PyPi packages to be downloaded and included as dependencies"
        ),
    )


class SparkAutoScalingConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Spark Auto Scaling Configuration",
            description="Configuration for the Spark auto scaling",
        ).as_json_schema_extra(),
    )
    enabled: bool = Field(
        default=False, title="Enabled", description="Enable auto scaling"
    )
    initial_executors: int | None = Field(
        default=None,
        title="Initial Executors",
        description="Initial number of executors",
    )
    min_executors: int = Field(
        default=1, title="Min Executors", description="Minimum number of executors"
    )
    max_executors: int = Field(
        default=1, title="Max Executors", description="Maximum number of executors"
    )
    shuffle_tracking_timeout: int = Field(
        ..., title="Shuffle Tracking Timeout", description="Shuffle tracking timeout"
    )


class SparkApplicationConfig(AbstractAppFieldType):
    type: SparkApplicationType = Field(
        ...,
        title="Spark Application type",
        description="Choose the type of the Spark application",
    )
    main_application_file: ApoloFilesFile = Field(
        ...,
        title="Main Application File",
        description="The main application file to be executed",
    )
    arguments: list[str] | None = None
    main_class: str | None = Field(default=None, title="Main Class for Java Apps")
    dependencies: SparkDependencies | None = None
    volumes: list[ApoloFilesMount] | None = None


class SparkJobInputs(AppInputs):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Spark Application",
            description="Run scalable Apache Spark applications",
        ).as_json_schema_extra(),
    )
    image: ContainerImage = Field(
        default=ContainerImage(repository="spark", tag="3.5.3")
    )
    spark_application_config: SparkApplicationConfig = Field(
        ...,
        title="Application Configuration",
        description="Configuration for the Spark application",
    )
    spark_auto_scaling_config: SparkAutoScalingConfig | None = Field(
        ...,
        title="Spark Auto Scaling Configuration",
        description="Configuration for the Spark auto scaling",
    )
    driver_config: DriverConfig = Field(
        ..., title="Driver Configuration", description="Configuration for the driver"
    )
    executor_config: ExecutorConfig = Field(
        ...,
        title="Executor Configuration",
        description="Configuration for the executor",
    )


class SparkJobOutputs(AppOutputs):
    pass
