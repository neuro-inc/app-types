from enum import StrEnum

from pydantic import BaseModel

from apolo_app_types.protocols.common import AppInputsV2, AppOutputsV2
from apolo_app_types.protocols.common.containers import ContainerImage
from apolo_app_types.protocols.common.preset import Preset


class File:
    filepath: str


class SparkApplicationType(StrEnum):
    PYTHON = "Python"
    SCALA = "Scala"
    JAVA = "Java"
    R = "R"


class SparkExecutorConfig(BaseModel):
    instances: int


class PythonSpecificConfig(BaseModel):
    pypi_packages: list[str] | File | None = None


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
    initial_executor: int | None
    min_executor: int
    max_executor: int
    shuffle_tracking_timeout: int


class SparkJobModel(BaseModel):
    spark_application_type: SparkApplicationType
    image: ContainerImage
    main_application_file: str
    arguments: list[str] | None = None
    dependencies: SparkDependencies | None = None
    spark_application_config: PythonSpecificConfig | JavaSpecificConfig | None
    spark_auto_scaling_config: SparkAutoScalingConfig | None
    driver_preset: Preset
    executor_preset: Preset


class SparkJobInputs(AppInputsV2):
    spark_job: SparkJobModel


class SparkJobOutputs(AppOutputsV2):
    pass
