import pytest

from apolo_app_types import (
    ContainerImage,
    SparkJobInputs,
)
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.common import APOLO_STORAGE_ANNOTATION
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import Preset
from apolo_app_types.protocols.common.storage import ApoloFilesFile
from apolo_app_types.protocols.spark_job import (
    PythonSpecificConfig,
    SparkApplicationModel,
    SparkApplicationType,
    SparkAutoScalingConfig,
    SparkDependencies,
)


@pytest.mark.asyncio
async def test_spark_job_values_generation(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=SparkJobInputs(
            spark_job=SparkApplicationModel(
                driver_preset=Preset(name="cpu-small"),
                executor_preset=Preset(name="cpu-medium"),
                type=SparkApplicationType.PYTHON,
                image=ContainerImage(repository="myrepo/spark-job", tag="v1.2.3"),
                main_application_file=ApoloFilesFile(path="storage://path/to/main.py"),
                spark_auto_scaling_config=SparkAutoScalingConfig(
                    enabled=True,
                    initial_executors=2,
                    min_executors=1,
                    max_executors=5,
                    shuffle_tracking_timeout=30,
                ),
                dependencies=SparkDependencies(
                    packages=["package1", "package2"],
                ),
                spark_application_config=PythonSpecificConfig(
                    pypi_packages=["scikit-learn==1.0.2"]
                ),
            )
        ),
        apolo_client=setup_clients,
        app_type=AppType.SparkJob,
        app_name="spark-app",
        namespace="default-namespace",
    )

    # Basic configuration assertions
    assert helm_params["namespace"] == "default-namespace"
    assert helm_params["spark"]["type"] == "Python"
    assert helm_params["spark"]["image"] == {
        "repository": "myrepo/spark-job",
        "tag": "v1.2.3",
    }
    assert helm_params["spark"]["mainApplicationFile"] == "local:///opt/spark/main.py"

    # Driver configuration assertions
    assert helm_params["spark"]["driver"]["labels"] == {
        "platform.apolo.us/preset": "cpu-small",
        "platform.apolo.us/component": "app",
        APOLO_STORAGE_ANNOTATION: "true",
    }
    assert "PYSPARK_PYTHON" in helm_params["spark"]["driver"]["env"][0]["name"]

    # Executor configuration assertions
    assert helm_params["spark"]["executor"]["labels"] == {
        "platform.apolo.us/preset": "cpu-medium",
        "platform.apolo.us/component": "app",
        APOLO_STORAGE_ANNOTATION: "true",
    }
    assert "PYSPARK_PYTHON" in helm_params["spark"]["executor"]["env"][0]["name"]

    # Dynamic allocation configuration assertions
    assert helm_params["spark"]["dynamicAllocation"] == {
        "enabled": True,
        "initialExecutors": 2,
        "minExecutors": 1,
        "maxExecutors": 5,
        "shuffleTrackingTimeout": 30,
    }

    # Dependencies configuration assertions
    assert helm_params["deps"] == {
        "pypi_packages": ["scikit-learn==1.0.2"],
        "packages": ["package1", "package2"],
        "repositories": None,
        "jars": None,
        "py_files": None,
        "files": None,
        "exclude_packages": None,
        "archives": None,
    }

    # PySpark dependency manager configuration assertions
    assert helm_params["pyspark_dep_manager"]["labels"] == {
        APOLO_STORAGE_ANNOTATION: "true"
    }
