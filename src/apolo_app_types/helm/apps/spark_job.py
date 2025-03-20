import typing as t

from yarl import URL

from apolo_app_types import SparkJobInputs
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import (
    append_apolo_storage_integration_annotations,
    gen_apolo_storage_integration_annotations,
    gen_apolo_storage_integration_labels,
    gen_extra_values,
)
from apolo_app_types.protocols.common.storage import (
    ApoloMountMode,
    ApoloStorageMount,
    ApoloStoragePath,
    MountPath,
)
from apolo_app_types.protocols.spark_job import (
    PythonSpecificConfig,
)


class SparkJobValueProcessor(BaseChartValueProcessor[SparkJobInputs]):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)

    def _configure_application_storage(
        self, input_: SparkJobInputs
    ) -> dict[str, t.Any]:
        extra_annotations: dict[str, str] = {}
        main_app_file_path = URL(input_.spark_job.main_application_file.path)
        main_app_file_mount = ApoloStorageMount(
            storage_path=ApoloStoragePath(path=str(main_app_file_path.parent)),
            mount_path=MountPath(path="/opt/spark"),
            mode=ApoloMountMode(mode="r"),
        )
        extra_annotations.update(
            **gen_apolo_storage_integration_annotations(
                [main_app_file_mount] + (input_.spark_job.volumes or [])
            )
        )
        return extra_annotations

    async def gen_extra_values(
        self,
        input_: SparkJobInputs,
        app_name: str,
        namespace: str,
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """
        Generate extra Helm values for Custom Deployment.
        """

        # Labels and annotations
        driver_extra_values = await gen_extra_values(
            apolo_client=self.client,
            preset_type=input_.spark_job.driver_preset,
            namespace=namespace,
        )
        executor_extra_values = await gen_extra_values(
            apolo_client=self.client,
            preset_type=input_.spark_job.executor_preset,
            namespace=namespace,
        )
        extra_labels = gen_apolo_storage_integration_labels(inject_storage=True)
        storage_annotations = self._configure_application_storage(input_)

        # storages
        # input_.spark_job.main_application_file

        values: dict[str, t.Any] = {
            "spark": {
                "type": input_.spark_job.type.value,
                "image": {
                    "repository": input_.spark_job.image.repository,
                    "tag": input_.spark_job.image.tag or "latest",
                },
                "driver": {
                    "labels": {
                        "platform.apolo.us/preset": input_.spark_job.driver_preset.name,  # noqa: E501
                        "platform.apolo.us/component": "app",
                        **extra_labels,
                    },
                    "annotations": {**storage_annotations, **driver_extra_values},
                },
                "executor": {
                    "labels": {
                        "platform.apolo.us/preset": input_.spark_job.executor_preset.name,  # noqa: E501
                        "platform.apolo.us/component": "app",
                        **extra_labels,
                    },
                    "annotations": {**storage_annotations, **executor_extra_values},
                },
            }
        }

        if input_.spark_job.spark_auto_scaling_config:
            dynamic_allocation: dict[str, t.Any] = {
                "enabled": (input_.spark_job.spark_auto_scaling_config.enabled),
                "initialExecutors": input_.spark_job.spark_auto_scaling_config.initial_executors,  # noqa: E501
                "minExecutors": input_.spark_job.spark_auto_scaling_config.min_executors,  # noqa: E501
                "maxExecutors": input_.spark_job.spark_auto_scaling_config.max_executors,  # noqa: E501
                "shuffleTrackingTimeout": input_.spark_job.spark_auto_scaling_config.shuffle_tracking_timeout,  # noqa: E501
            }
            values["spark"]["dynamicAllocation"] = dynamic_allocation

        deps: dict[str, t.Any] = {}
        if input_.spark_job.dependencies:
            deps = input_.spark_job.dependencies.model_dump()

        if (
            input_.spark_job.spark_application_config
            and isinstance(
                input_.spark_job.spark_application_config, PythonSpecificConfig
            )  # noqa: E501
        ):
            pypi_packages = input_.spark_job.spark_application_config.pypi_packages
            if isinstance(pypi_packages, list):
                pkg_list: list[str] = pypi_packages
                deps["pypi_packages"] = pkg_list

            pypi_packages_storage_path = f"storage://{self.client.config.cluster_name}/{self.client.config.org_name}/{self.client.config.project_name}/{app_name}/{namespace}/spark/deps"
            deps_mount = ApoloStorageMount(
                storage_path=ApoloStoragePath(path=pypi_packages_storage_path),
                mount_path=MountPath(path="/opt/spark/deps"),
                mode=ApoloMountMode(mode="rw"),
            )
            deps_annotation = gen_apolo_storage_integration_annotations([deps_mount])
            values["pyspark_dep_manager"] = {
                "labels": gen_apolo_storage_integration_labels(inject_storage=True),
                "annotations": deps_annotation,
            }
            # append to existing storage annotation
            values["spark"]["driver"]["annotations"] = (
                append_apolo_storage_integration_annotations(
                    values["spark"]["driver"]["annotations"], [deps_mount]
                )
            )
            values["spark"]["executor"]["annotations"] = (
                append_apolo_storage_integration_annotations(
                    values["spark"]["executor"]["annotations"], [deps_mount]
                )
            )

            # add this env var so that pyspark can load the dependencies
            pyspark_env_var = {
                "name": "PYSPARK_PYTHON",
                "value": f"{deps_mount.mount_path.path}/pyspark_pex_env.pex",
            }
            values["spark"]["driver"]["env"] = [pyspark_env_var]
            values["spark"]["executor"]["env"] = [pyspark_env_var]

        values["deps"] = deps

        return values
