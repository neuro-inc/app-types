import typing as t

from apolo_app_types import SparkJobInputs
from apolo_app_types.helm.apps.base import BaseChartValueProcessor


class SparkJobValueProcessor(BaseChartValueProcessor[SparkJobInputs]):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)

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
        # driver_extra_values = await gen_extra_values(
        #     apolo_client=self.client,
        #     preset_type=input_.spark_job.preset,
        #     namespace=namespace,
        # )
        # executor_extra_values = await gen_extra_values(
        #     apolo_client=self.client,
        #     preset_type=input_.spark_job.preset,
        #     namespace=namespace,
        # )

        # values: dict[str, t.Any] = {
        #     "image": {
        #         "repository": input_.spark_job.image.repository,
        #         "tag": input_.spark_job.image.tag or "latest",
        #     },
        #     **extra_values,
        # }

        return {
            "spark-operator": {
                "spark": {
                    "jobNamespaces": [namespace],
                    "serviceAccount": {
                        "create": True,
                        "name": "",
                        "annotations": {},
                        "automountServiceAccountToken": True,
                    },
                    "rbac": {"create": True, "annotations": {}},
                }
            },
            "spark": {
                "type": "Python",
                "pythonVersion": None,
                "image": {"repository": "spark", "tag": "3.5.3"},
                "mainApplicationFile": "main.py",
                "volumes": [],
                "driver": {"env": [], "volumeMounts": []},
                "executor": {"volumeMounts": [], "env": []},
                "dynamicAllocation": {
                    "enabled": False,
                    "initialExecutors": None,
                    "minExecutors": None,
                    "maxExecutors": None,
                    "shuffleTrackingTimeout": None,
                },
                "deps": {
                    "jars": [],
                    "files": [],
                    "pyFiles": [],
                    "packages": [],
                    "excludePackages": [],
                    "repositories": [],
                    "archives": [],
                },
            },
        }
