import typing as t

from yarl import URL

from apolo_app_types import ContainerImage, SparkJobInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import (
    append_apolo_storage_integration_annotations,
    gen_apolo_storage_integration_labels,
    gen_extra_values,
)
from apolo_app_types.helm.utils.storage import get_app_data_files_path_url
from apolo_app_types.protocols.common.storage import (
    ApoloFilesMount,
    ApoloFilesPath,
    ApoloMountMode,
    ApoloMountModes,
    MountPath,
)
from apolo_app_types.protocols.spark_job import _SPARK_DEFAULTS


class SparkJobValueProcessor(BaseChartValueProcessor[SparkJobInputs]):
    def _configure_application_storage(
        self, input_: SparkJobInputs
    ) -> tuple[dict[str, t.Any], str]:
        """
        Configure the storage for the application.

        Args:
            input_: The input data for the SparkJob.

        Returns:
            A tuple with the extra annotations and the main application file
            for spark application.
        """
        extra_annotations: dict[str, str] = {}
        main_app_file_path = URL(
            input_.spark_application_config.main_application_file.path
        )
        mount_path = "/opt/spark/app"
        main_app_file_mount = ApoloFilesMount(
            storage_uri=ApoloFilesPath(path=str(main_app_file_path.parent)),
            mount_path=MountPath(path=mount_path),
            mode=ApoloMountMode(mode="r"),
        )
        extra_annotations = append_apolo_storage_integration_annotations(
            extra_annotations,
            [main_app_file_mount] + (input_.spark_application_config.volumes or []),
            self.client,
        )

        main_application_file = f"local://{mount_path}/{main_app_file_path.name}"
        return extra_annotations, main_application_file

    def _get_default_container_image(self) -> ContainerImage:
        return ContainerImage(
            repository=_SPARK_DEFAULTS["image"], tag=_SPARK_DEFAULTS["tag"]
        )

    async def gen_extra_values(
        self,
        input_: SparkJobInputs,
        app_name: str,
        namespace: str,
        app_id: str,
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """
        Generate extra Helm values for Custom Deployment.
        """

        # Labels and annotations
        driver_extra_values = await gen_extra_values(
            apolo_client=self.client,
            preset_type=input_.driver_config.preset,
            namespace=namespace,
            app_id=app_id,
            app_type=AppType.SparkJob,
        )
        executor_extra_values = await gen_extra_values(
            apolo_client=self.client,
            preset_type=input_.executor_config.preset,
            namespace=namespace,
            app_id=app_id,
            app_type=AppType.SparkJob,
        )
        extra_labels = gen_apolo_storage_integration_labels(
            client=self.client, inject_storage=True
        )
        storage_annotations, main_application_file = (
            self._configure_application_storage(input_)
        )

        image = input_.image or self._get_default_container_image()

        values: dict[str, t.Any] = {
            "namespace": namespace,
            "spark": {
                "mainApplicationFile": main_application_file,
                "type": input_.spark_application_config.type.value,
                "arguments": input_.spark_application_config.arguments,
                "image": {
                    "repository": image.repository,
                    "tag": image.tag or "latest",
                },
                "driver": {
                    "labels": {
                        "platform.apolo.us/preset": input_.driver_config.preset.name,  # noqa: E501
                        "platform.apolo.us/component": "app",
                        **extra_labels,
                    },
                    "annotations": storage_annotations,
                    **driver_extra_values,
                },
                "executor": {
                    "labels": {
                        "platform.apolo.us/preset": input_.executor_config.preset.name,  # noqa: E501
                        "platform.apolo.us/component": "app",
                        **extra_labels,
                    },
                    "annotations": storage_annotations,
                    "instances": input_.executor_config.instances,
                    **executor_extra_values,
                },
            },
        }

        self.add_autoscaling_config(values=values, input_=input_)
        self.add_dependencies(input_=input_, app_name=app_name, values=values)

        return values

    def add_autoscaling_config(
        self, values: dict[str, t.Any], input_: SparkJobInputs
    ) -> None:
        if input_.spark_auto_scaling_config:
            dynamic_allocation: dict[str, t.Any] = {
                "enabled": True,
                "initialExecutors": input_.spark_auto_scaling_config.initial_executors,  # noqa: E501
                "minExecutors": input_.spark_auto_scaling_config.min_executors,  # noqa: E501
                "maxExecutors": input_.spark_auto_scaling_config.max_executors,  # noqa: E501
                "shuffleTrackingTimeout": input_.spark_auto_scaling_config.shuffle_tracking_timeout,  # noqa: E501
            }
            values["spark"]["dynamicAllocation"] = dynamic_allocation

    def add_dependencies(
        self,
        input_: SparkJobInputs,
        app_name: str,
        values: dict[str, t.Any],
    ) -> None:
        deps: dict[str, t.Any] = {}
        if input_.spark_application_config.dependencies:
            deps = input_.spark_application_config.dependencies.model_dump()

        if (
            input_.spark_application_config.dependencies
            and input_.spark_application_config.dependencies.pypi_packages
        ):
            pypi_packages = input_.spark_application_config.dependencies.pypi_packages
            if isinstance(pypi_packages, list):
                pkg_list: list[str] = pypi_packages
                deps["pypi_packages"] = pkg_list + [
                    "pyspark==3.5.5"
                ]  # must install pyspark too

            pypi_packages_storage_path = (
                get_app_data_files_path_url(
                    client=self.client,
                    app_type_name=str(AppType.SparkJob.value),
                    app_name=app_name,
                )
                / "spark"
                / "deps"
                / "pypi"
            )
            deps_mount = ApoloFilesMount(
                storage_uri=ApoloFilesPath(path=str(pypi_packages_storage_path)),
                mount_path=MountPath(path="/opt/spark/deps"),
                mode=ApoloMountMode(mode=ApoloMountModes.RW),
            )
            deps_annotation = append_apolo_storage_integration_annotations(
                {}, [deps_mount], self.client
            )
            values["pyspark_dep_manager"] = {
                "labels": gen_apolo_storage_integration_labels(
                    client=self.client, inject_storage=True
                ),
                "annotations": deps_annotation,
            }
            # append to existing storage annotation
            values["spark"]["driver"]["annotations"] = (
                append_apolo_storage_integration_annotations(
                    values["spark"]["driver"]["annotations"], [deps_mount], self.client
                )
            )
            values["spark"]["executor"]["annotations"] = (
                append_apolo_storage_integration_annotations(
                    values["spark"]["executor"]["annotations"],
                    [deps_mount],
                    self.client,
                )
            )

            # add this env var so that pyspark can load the dependencies
            pyspark_env_var = {
                "name": "PYSPARK_PYTHON",
                "value": f"{deps_mount.mount_path.path}/pyspark_pex_env.pex",
            }
            values["spark"]["driver"]["env"] = [pyspark_env_var]
            values["spark"]["executor"]["env"] = [pyspark_env_var]

        values["spark"]["deps"] = deps
