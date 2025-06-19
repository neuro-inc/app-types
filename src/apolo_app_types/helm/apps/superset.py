import logging
import secrets
import typing as t

from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import gen_extra_values
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts
from apolo_app_types.protocols.superset import (
    SupersetInputs,
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
    async def _get_init_params(self, input_: SupersetInputs) -> dict:
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

    async def _get_postgres_values(self, input_: SupersetInputs):
        if not input_.postgres_user:
            return {}
        return {
            "connections": {
                "db_host": input_.postgres_user.pgbouncer_host,
                "db_port": input_.postgres_user.pgbouncer_port,
                "db_user": input_.postgres_user.user,
                "db_pass": input_.postgres_user.password,
                "db_name": input_.postgres_user.dbname,
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
        values = await gen_extra_values(
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
        )
        init_params = await self._get_init_params(input_)
        postgres_values = await self._get_postgres_values(input_)
        secret = _generate_superset_secret_hex()
        logger.debug("Generated extra Superset values: %s", values)
        ingress_vals = values.pop("ingress", {})
        # TODO: add worker and Celery as well
        return merge_list_of_dicts(
            [
                {
                    "supersetNode": {
                        **values,
                        **postgres_values,
                    },
                    "supersetWorker": worker_values,
                    "extraSecretEnv": {
                        "SUPERSET_SECRET_KEY": secret,
                    },
                },
                {"ingress": ingress_vals} if ingress_vals else {},
                init_params,
                {"postgres": {"enabled": "false"}} if postgres_values else {},
            ]
        )
