import logging
import secrets
import typing as t

from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import gen_extra_values
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts
from apolo_app_types.protocols.superset import (
    SupersetInputs,
    SupersetPostgresConfig,
)


logger = logging.getLogger(__name__)


def _generate_superset_secret_hex(length: int = 16) -> str:
    """
    Generates a short random API secret using hexadecimal characters.

    Args:
        length (int): Number of hex characters (must be even for full bytes).

    Returns:
        str: The generated secret.
    """
    num_bytes = length // 2

    secret = secrets.token_hex(num_bytes)

    if length % 2 != 0:
        secret = secret[:-1]

    return secret


class SupersetChartValueProcessor(BaseChartValueProcessor[SupersetInputs]):
    async def _get_init_params(self, input_: SupersetInputs) -> dict[str, t.Any]:
        return {
            "init": {
                "adminUser": {
                    "username": input_.admin_user.username,
                    "firstname": input_.admin_user.firstname,
                    "lastname": input_.admin_user.lastname,
                    "email": input_.admin_user.email,
                    "password": input_.admin_user.password,
                }
            }
        }

    async def gen_extra_values(
        self,
        input_: SupersetInputs,
        app_name: str,
        namespace: str,
        app_id: str,
        app_secrets_name: str,
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """Generate extra values for Weaviate configuration."""

        # Get base values
        node_values = await gen_extra_values(
            apolo_client=self.client,
            preset_type=input_.web_config.preset,
            ingress_http=input_.ingress_http,
            namespace=namespace,
            app_id=app_id,
            app_type=AppType.Superset,
        )
        worker_values = await gen_extra_values(
            apolo_client=self.client,
            preset_type=input_.worker_config.preset,
            component_name="worker",
            namespace=namespace,
            app_id=app_id,
            app_type=AppType.Superset,
        )
        init_params = await self._get_init_params(input_)

        secret = _generate_superset_secret_hex()
        logger.debug("Generated extra Superset values: %s", node_values)
        ingress_vals = node_values.pop("ingress", {})
        additional_values: dict[str, t.Any] = {}

        redis_values = await gen_extra_values(
            self.client,
            input_.redis_preset,
            app_id=app_id,
            app_type=AppType.Superset,
        )
        additional_values.update({"redis": {"master": redis_values}})

        if isinstance(input_.postgres_config, SupersetPostgresConfig):
            postgres_values = await gen_extra_values(
                self.client,
                input_.postgres_config.preset,
                app_id=app_id,
                app_type=AppType.Superset,
            )
            additional_values.update({"postgresql": {"primary": postgres_values}})
        else:
            node_values.update(
                {
                    "connections": {
                        "db_host": input_.postgres_config.pgbouncer_host,
                        "db_port": input_.postgres_config.pgbouncer_port,
                        "db_user": input_.postgres_config.user,
                        "db_pass": input_.postgres_config.password,
                        "db_name": input_.postgres_config.dbname,
                    }
                }
            )
            additional_values.update({"postgresql": {"enabled": False}})
        return merge_list_of_dicts(
            [
                {
                    "supersetNode": {
                        **node_values,
                    },
                    "supersetWorker": worker_values,
                    "extraSecretEnv": {
                        "SUPERSET_SECRET_KEY": secret,
                    },
                },
                {"ingress": ingress_vals} if ingress_vals else {},
                init_params,
                additional_values,
            ]
        )
