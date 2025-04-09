import pytest

from apolo_app_types import (
    ContainerImage,
)
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.common import (
    APOLO_ORG_LABEL,
    APOLO_PROJECT_LABEL,
    APOLO_STORAGE_LABEL,
)
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import Preset
from apolo_app_types.protocols.common.storage import ApoloFilesFile
from apolo_app_types.protocols.spark_job import (
    DriverConfig,
    ExecutorConfig,
    SparkApplicationConfig,
    SparkApplicationType,
    SparkAutoScalingConfig,
    SparkDependencies,
    SparkJobInputs,
)

from tests.unit.constants import APP_SECRETS_NAME


@pytest.mark.asyncio
async def test_spark_job_values_generation(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=SparkJobInputs(
            spark_application_config=SparkApplicationConfig(
                type=SparkApplicationType.PYTHON,
                main_application_file=ApoloFilesFile(path="storage://path/to/main.py"),
                dependencies=SparkDependencies(
                    packages=["package1", "package2"],
                    pypi_packages=["scikit-learn==1.0.2"],
                ),
            ),
            driver_config=DriverConfig(preset=Preset(name="cpu-small")),
            executor_config=ExecutorConfig(
                preset=Preset(name="cpu-medium"), instances=1
            ),
            image=ContainerImage(repository="myrepo/spark-job", tag="v1.2.3"),
            spark_auto_scaling_config=SparkAutoScalingConfig(
                enabled=True,
                initial_executors=2,
                min_executors=1,
                max_executors=5,
                shuffle_tracking_timeout=30,
            ),
        ),
        apolo_client=setup_clients,
        app_type=AppType.SparkJob,
        app_name="spark-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
    )

    # Basic configuration assertions
    assert helm_params["namespace"] == "default-namespace"
    assert helm_params["spark"]["type"] == "Python"
    assert helm_params["spark"]["image"] == {
        "repository": "myrepo/spark-job",
        "tag": "v1.2.3",
    }
    assert (
        helm_params["spark"]["mainApplicationFile"] == "local:///opt/spark/app/main.py"
    )

    # Driver configuration assertions
    assert helm_params["spark"]["driver"]["labels"] == {
        "platform.apolo.us/preset": "cpu-small",
        "platform.apolo.us/component": "app",
        APOLO_STORAGE_LABEL: "true",
        APOLO_ORG_LABEL: "test-org",
        APOLO_PROJECT_LABEL: "test-project",
    }
    assert "PYSPARK_PYTHON" in helm_params["spark"]["driver"]["env"][0]["name"]

    # Executor configuration assertions
    assert helm_params["spark"]["executor"]["labels"] == {
        "platform.apolo.us/preset": "cpu-medium",
        "platform.apolo.us/component": "app",
        APOLO_STORAGE_LABEL: "true",
        APOLO_ORG_LABEL: "test-org",
        APOLO_PROJECT_LABEL: "test-project",
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
        APOLO_STORAGE_LABEL: "true",
        APOLO_ORG_LABEL: "test-org",
        APOLO_PROJECT_LABEL: "test-project",
    }
