import typing as t
from pathlib import Path

from apolo_app_types import SparkJobInputs
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import (
    gen_apolo_storage_integration_annotations,
    gen_apolo_storage_integration_labels,
    gen_extra_values,
)
from apolo_app_types.protocols.common.storage import (
    ApoloMountMode,
    ApoloStorageMount,
    MountPath,
)


class SparkJobValueProcessor(BaseChartValueProcessor[SparkJobInputs]):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)

    def _configure_application_storage(
        self, input_: SparkJobInputs
    ) -> dict[str, t.Any]:
        extra_annotations: dict[str, str] = {}
        main_app_file_path = Path(input_.spark_job.main_application_file.path)
        filename = str(main_app_file_path.name)
        main_app_file_mount = ApoloStorageMount(
            storage_path=str(main_app_file_path.parent),
            mount_path=MountPath(path=f"/opt/spark/{filename}"),
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

        values = {
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

        # values: dict[str, t.Any] = {
        #     "image": {
        #         "repository": input_.spark_job.image.repository,
        #         "tag": input_.spark_job.image.tag or "latest",
        #     },
        #     **extra_values,
        # }

        values["deps"] = {}
        return values

        # return {
        #     "spark-operator": {
        #         "spark": {
        #             "jobNamespaces": [namespace],
        #             "serviceAccount": {
        #                 "create": True,
        #                 "name": "",
        #                 "annotations": {},
        #                 "automountServiceAccountToken": True,
        #             },
        #             "rbac": {"create": True, "annotations": {}},
        #         }
        #     },
        #     "spark": {
        #         "type": "Python",
        #         "pythonVersion": None,
        #         "image": {"repository": "spark", "tag": "3.5.3"},
        #         "mainApplicationFile": "main.py",
        #         "volumes": [],
        #         "driver": {"env": [], "volumeMounts": []},
        #         "executor": {"volumeMounts": [], "env": []},
        #         "dynamicAllocation": {
        #             "enabled": False,
        #             "initialExecutors": None,
        #             "minExecutors": None,
        #             "maxExecutors": None,
        #             "shuffleTrackingTimeout": None,
        #         },
        #         "deps": {
        #             "jars": [],
        #             "files": [],
        #             "pyFiles": [],
        #             "packages": [],
        #             "excludePackages": [],
        #             "repositories": [],
        #             "archives": [],
        #         },
        #     },
        # }
