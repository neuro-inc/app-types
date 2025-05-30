import logging
import secrets
import typing as t

from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import gen_extra_values
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts
from apolo_app_types.protocols.superset import SupersetInputs


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
    async def gen_extra_values(
        self,
        input_: SupersetInputs,
        app_name: str,
        namespace: str,
        app_secrets_name: str,
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """Generate extra values for Weaviate configuration."""

        # Get base values
        values = await gen_extra_values(
            apolo_client=self.client,
            preset_type=input_.preset,
            ingress_http=input_.ingress_http,
            # ingress_grpc=input_.ingress_grpc,
            namespace=namespace,
        )
        secret = _generate_superset_secret_hex()
        logger.debug("Generated extra Superset values: %s", values)
        ingress_vals = values.pop("ingress", {})
        # TODO: add worker and Celery as well
        return merge_list_of_dicts(
            [
                {
                    "supersetNode": values,
                    "extraSecretEnv": {
                        "SUPERSET_SECRET_KEY": secret,
                    },
                },
                {"ingress": ingress_vals} if ingress_vals else {},
            ]
        )
