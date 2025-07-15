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


_SPARK_DEFAULTS = {
    "image": "spark",
    "tag": "3.5.3",
}


class SparkApplicationType(StrEnum):
    PYTHON = "Python"
    SCALA = "Scala"
    JAVA = "Java"
    R = "R"


class DriverConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Driver Configuration",
            description="Configure resources and environment for the Spark driver.",
        ).as_json_schema_extra(),
    )
    preset: Preset = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Driver Preset",
            description="Specify preset configuration to be used by the driver",
        ).as_json_schema_extra(),
    )


class ExecutorConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Executor Configuration",
            description=(
                "Define the compute resources and behavior for Spark executors."
            ),
        ).as_json_schema_extra(),
    )
    instances: int = Field(
        default=1,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            title="Instances", description="Specify number of instances"
        ).as_json_schema_extra(),
    )
    preset: Preset = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Executor Preset",
            description="Specify preset configuration to be used by the executor.",
        ).as_json_schema_extra(),
    )


class SparkDependencies(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Spark Dependencies",
            description="Define libraries, files, and packages"
            " required to run your Spark application.",
        ).as_json_schema_extra(),
    )

    jars: list[str] | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="JARs",
            description="Specify a list of JAR files to include as Spark dependencies.",
        ).as_json_schema_extra(),
    )

    py_files: list[str] | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Python Files",
            description="Include additional Python files (e.g., .py or .zip)"
            " to be distributed with your Spark job.",
        ).as_json_schema_extra(),
    )

    files: list[str] | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Files",
            description="Attach additional files needed by your Spark job at runtime.",
        ).as_json_schema_extra(),
    )

    packages: list[str] | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Packages",
            description="Specify Maven coordinates of packages"
            " to include as Spark dependencies.",
        ).as_json_schema_extra(),
    )

    exclude_packages: list[str] | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Exclude Packages",
            description="List any packages to exclude "
            "from the Spark dependency resolution.",
        ).as_json_schema_extra(),
    )

    repositories: list[str] | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Repositories",
            description="Define custom Maven repositories for resolving packages.",
        ).as_json_schema_extra(),
    )

    archives: list[str] | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Archives",
            description="Provide archive files (e.g., .zip, .tar.gz)"
            " to be extracted on worker nodes.",
        ).as_json_schema_extra(),
    )

    pypi_packages: list[str] | ApoloFilesFile | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="PyPI Packages",
            description="List PyPI packages or a requirements "
            "file to install on all Spark nodes.",
        ).as_json_schema_extra(),
    )


class SparkAutoScalingConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Spark Auto Scaling Configuration",
            description="Configure dynamic executor scaling for "
            "your Spark application based on workload demand.",
        ).as_json_schema_extra(),
    )

    initial_executors: int | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Initial Executors",
            description="Set the initial number of Spark "
            "executors to launch at application start.",
        ).as_json_schema_extra(),
    )

    min_executors: int = Field(
        default=1,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            title="Minimum Executors",
            description="Define the minimum "
            "number of executors to maintain during runtime.",
        ).as_json_schema_extra(),
    )

    max_executors: int = Field(
        default=1,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            title="Maximum Executors",
            description="Set the upper limit on the"
            " number of executors that can be scaled up.",
        ).as_json_schema_extra(),
    )

    shuffle_tracking_timeout: int = Field(
        ...,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            title="Shuffle Tracking Timeout",
            description="Set the timeout (in seconds)"
            " for shuffle tracking during executor deallocation.",
        ).as_json_schema_extra(),
    )


class SparkApplicationConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Spark App Settings",
            description="Configure the main application file, type, and arguments.",
        ).as_json_schema_extra(),
    )
    type: SparkApplicationType = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Spark Application Type",
            description="Select the type of Spark"
            " application, such as Python, Java, or Scala.",
        ).as_json_schema_extra(),
    )

    main_application_file: ApoloFilesFile = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Main Application File",
            description="Provide the main"
            " application file to be executed by Spark (e.g., .py, .jar).",
        ).as_json_schema_extra(),
    )

    arguments: list[str] | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Application Arguments",
            description="Pass command-line "
            "arguments to your Spark application at runtime.",
        ).as_json_schema_extra(),
    )

    main_class: str | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Main Class for Java Apps",
            description="Specify the main class to run"
            " if your Spark application is written in Java.",
        ).as_json_schema_extra(),
    )

    dependencies: SparkDependencies | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Dependencies",
            description="Configure files, libraries, "
            "and packages required to run your Spark job.",
        ).as_json_schema_extra(),
    )

    volumes: list[ApoloFilesMount] | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Mounted Volumes",
            description="Attach external storage "
            "volumes needed by your Spark application.",
        ).as_json_schema_extra(),
    )


class SparkJobInputs(AppInputs):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Spark Application",
            description="Run scalable Apache Spark "
            "applications using configurable drivers, executors, and auto-scaling.",
        ).as_json_schema_extra(),
    )

    spark_application_config: SparkApplicationConfig = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Application Configuration",
            description="Define the main Spark "
            "application file, type, arguments, and dependencies.",
        ).as_json_schema_extra(),
    )

    spark_auto_scaling_config: SparkAutoScalingConfig | None = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Auto Scaling Configuration",
            description="Enable and configure dynamic "
            "scaling of Spark executors based on workload.",
        ).as_json_schema_extra(),
    )

    image: ContainerImage | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Override Spark Container Image",
            description="Modify this to select the container image used "
            "to run your Spark job. Defaults to "
            f"{_SPARK_DEFAULTS['image']}:{_SPARK_DEFAULTS['tag']}.",
            is_advanced_field=True,
        ).as_json_schema_extra(),
    )

    driver_config: DriverConfig = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Driver Configuration",
            description="Configure resources and environment for the Spark driver.",
            is_advanced_field=True,
        ).as_json_schema_extra(),
    )

    executor_config: ExecutorConfig = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Executor Configuration",
            description="Define the compute resources "
            "and behavior for Spark executors.",
            is_advanced_field=True,
        ).as_json_schema_extra(),
    )


class SparkJobOutputs(AppOutputs):
    pass
